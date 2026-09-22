from __future__ import annotations

import copy
import hashlib
import unittest

from civic.accepted_operator_selection import (
    RECORD_TYPE,
    CivicOperatorSelectionError,
    verify_accepted_operator_selection,
)
from civic.epoch_manifest import CRYPTO_PROFILE, derive_key_id
from civic.signed_history_record import (
    sign_history_record_fixture,
    verify_signed_history_record,
)
from civic.tests.test_epoch_manifest import P1, P2, fixture_manifest, h


def selection_fixture(
    *,
    signer_kind: str = "participant",
    stream: str = "accepted",
    selected_participant_record_sha256: bytes | None = None,
    body_proofs: list[bytes] | None = None,
) -> tuple[dict[str, object], dict[str, object], int]:
    manifest = fixture_manifest()
    manifest["ceremony"]["governance_proof_sha256"] = [h(30), h(31)]  # type: ignore[index]

    if selected_participant_record_sha256 is None:
        selected_participant_record_sha256 = h(16)
    if body_proofs is None:
        body_proofs = [h(30)]

    if signer_kind == "participant":
        signer = {
            "kind": "participant",
            "key_id": derive_key_id(P1),
            "participant_record_sha256": h(16),
        }
        private_scalar = 1
    elif signer_kind == "signing_node":
        signer = {
            "kind": "signing_node",
            "key_id": derive_key_id(P2),
            "participant_record_sha256": None,
        }
        private_scalar = 2
    else:
        raise AssertionError("unsupported fixture signer kind")

    payload = {
        "format": "kane-civic-history-record",
        "version": 1,
        "crypto_profile": CRYPTO_PROFILE,
        "hoa_root_id": manifest["hoa_root_id"],
        "epoch_sequence": manifest["epoch_sequence"],
        "ceremony_record_sha256": manifest["ceremony"]["ceremony_record_sha256"],  # type: ignore[index]
        "record_type": RECORD_TYPE,
        "history_link": {
            "stream": stream,
            "predecessor_record_sha256": None,
        },
        "signer": signer,
        "body": {
            "selected_participant_record_sha256": selected_participant_record_sha256,
            "selection_proof_sha256": body_proofs,
        },
    }

    return manifest, payload, private_scalar


def verified_selection_fixture(
    **kwargs: object,
):
    manifest, payload, private_scalar = selection_fixture(**kwargs)

    signed = sign_history_record_fixture(
        payload,
        epoch_manifest=manifest,
        private_scalar=private_scalar,
        nonce_scalar=41,
    )

    manifest["operator"]["selection_record_sha256"] = hashlib.sha256(signed).digest()  # type: ignore[index]

    verified = verify_signed_history_record(
        signed,
        epoch_manifests=[manifest],
    )
    return manifest, verified


class CivicAcceptedOperatorSelectionTests(unittest.TestCase):
    def test_valid_participant_signed_selection_binds_operator_and_proof_subset(self) -> None:
        manifest, verified = verified_selection_fixture(
            signer_kind="participant",
            body_proofs=[h(30)],
        )

        result = verify_accepted_operator_selection(
            verified,
            epoch_manifest=manifest,
        )

        self.assertEqual(verified.record_sha256, result.record_sha256)
        self.assertEqual(h(16), result.selected_participant_record_sha256)
        self.assertEqual((h(30),), result.selection_proof_sha256)
        self.assertEqual("participant", result.signer_kind)
        self.assertEqual(derive_key_id(P1), result.signer_key_id)

    def test_valid_signing_node_selection_allows_empty_proof_subset(self) -> None:
        manifest, verified = verified_selection_fixture(
            signer_kind="signing_node",
            body_proofs=[],
        )

        result = verify_accepted_operator_selection(
            verified,
            epoch_manifest=manifest,
        )

        self.assertEqual(h(16), result.selected_participant_record_sha256)
        self.assertEqual((), result.selection_proof_sha256)
        self.assertEqual("signing_node", result.signer_kind)
        self.assertEqual(derive_key_id(P2), result.signer_key_id)

    def test_wrong_stream_is_rejected(self) -> None:
        manifest, verified = verified_selection_fixture(stream="witness")

        with self.assertRaises(CivicOperatorSelectionError):
            verify_accepted_operator_selection(
                verified,
                epoch_manifest=manifest,
            )

    def test_selected_participant_must_match_manifest_operator(self) -> None:
        manifest, verified = verified_selection_fixture(
            selected_participant_record_sha256=h(40),
        )

        with self.assertRaises(CivicOperatorSelectionError):
            verify_accepted_operator_selection(
                verified,
                epoch_manifest=manifest,
            )

    def test_manifest_selection_record_identity_mismatch_is_rejected(self) -> None:
        manifest, verified = verified_selection_fixture()
        wrong_manifest = copy.deepcopy(manifest)
        wrong_manifest["operator"]["selection_record_sha256"] = h(41)  # type: ignore[index]

        with self.assertRaises(CivicOperatorSelectionError):
            verify_accepted_operator_selection(
                verified,
                epoch_manifest=wrong_manifest,
            )

    def test_selection_proof_outside_ceremony_set_is_rejected(self) -> None:
        manifest, verified = verified_selection_fixture(
            body_proofs=[h(30), h(32)],
        )

        with self.assertRaises(CivicOperatorSelectionError):
            verify_accepted_operator_selection(
                verified,
                epoch_manifest=manifest,
            )

    def test_unsorted_selection_proofs_are_rejected(self) -> None:
        manifest, verified = verified_selection_fixture(
            body_proofs=[h(31), h(30)],
        )

        with self.assertRaises(CivicOperatorSelectionError):
            verify_accepted_operator_selection(
                verified,
                epoch_manifest=manifest,
            )

    def test_duplicate_selection_proofs_are_rejected(self) -> None:
        manifest, verified = verified_selection_fixture(
            body_proofs=[h(30), h(30)],
        )

        with self.assertRaises(CivicOperatorSelectionError):
            verify_accepted_operator_selection(
                verified,
                epoch_manifest=manifest,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
