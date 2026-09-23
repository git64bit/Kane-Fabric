from __future__ import annotations

import copy
import hashlib
import unittest

from civic.accepted_participant_issuance import (
    RECORD_TYPE,
    CivicParticipantIssuanceError,
    verify_accepted_participant_issuance,
)
from civic.ecdsa import public_key_from_private_scalar
from civic.epoch_manifest import CRYPTO_PROFILE, derive_key_id
from civic.signed_history_record import (
    sign_history_record_fixture,
    verify_signed_history_record,
)
from civic.tests.test_epoch_manifest import P1, P2, fixture_manifest, h


P3 = public_key_from_private_scalar(3)


def issuance_fixture(
    *,
    signer_kind: str = "participant",
    stream: str = "accepted",
    participant_record_sha256: bytes | None = None,
    participant_key_id: bytes | None = None,
    participant_public_key: bytes | None = None,
    standing_record_sha256: bytes | None = None,
    issuing_operator_participant_record_sha256: bytes | None = None,
    add_second_participant: bool = False,
    signer_participant_record_sha256: bytes | None = None,
) -> tuple[dict[str, object], dict[str, object], int]:
    manifest = fixture_manifest()

    if add_second_participant:
        manifest["participants"].append(  # type: ignore[union-attr]
            {
                "participant_record_sha256": h(22),
                "participant_key_id": derive_key_id(P3),
                "participant_public_key": P3,
                "standing_record_sha256": h(23),
                "issuance_record_sha256": h(24),
            }
        )

    if participant_record_sha256 is None:
        participant_record_sha256 = h(16)
    if participant_key_id is None:
        participant_key_id = derive_key_id(P1)
    if participant_public_key is None:
        participant_public_key = P1
    if standing_record_sha256 is None:
        standing_record_sha256 = h(17)
    if issuing_operator_participant_record_sha256 is None:
        issuing_operator_participant_record_sha256 = h(16)

    if signer_kind == "participant":
        if signer_participant_record_sha256 is None:
            signer_participant_record_sha256 = h(16)

        if signer_participant_record_sha256 == h(16):
            signer_key_id = derive_key_id(P1)
            private_scalar = 1
        elif signer_participant_record_sha256 == h(22):
            signer_key_id = derive_key_id(P3)
            private_scalar = 3
        else:
            raise AssertionError("unsupported fixture participant signer")

        signer = {
            "kind": "participant",
            "key_id": signer_key_id,
            "participant_record_sha256": signer_participant_record_sha256,
        }
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
            "participant_record_sha256": participant_record_sha256,
            "participant_key_id": participant_key_id,
            "participant_public_key": participant_public_key,
            "standing_record_sha256": standing_record_sha256,
            "issuing_operator_participant_record_sha256": issuing_operator_participant_record_sha256,
        },
    }

    return manifest, payload, private_scalar


def verified_issuance_fixture(
    **kwargs: object,
):
    manifest, payload, private_scalar = issuance_fixture(**kwargs)

    signed = sign_history_record_fixture(
        payload,
        epoch_manifest=manifest,
        private_scalar=private_scalar,
        nonce_scalar=43,
    )

    participant_id = payload["body"]["participant_record_sha256"]  # type: ignore[index]
    matches = [
        item
        for item in manifest["participants"]  # type: ignore[union-attr]
        if item["participant_record_sha256"] == participant_id
    ]
    if len(matches) == 1:
        matches[0]["issuance_record_sha256"] = hashlib.sha256(signed).digest()

    verified = verify_signed_history_record(
        signed,
        epoch_manifests=[manifest],
    )
    return manifest, verified


class CivicAcceptedParticipantIssuanceTests(unittest.TestCase):
    def test_valid_operator_participant_signed_issuance_binds_all_authority_fields(self) -> None:
        manifest, verified = verified_issuance_fixture(
            signer_kind="participant",
        )

        result = verify_accepted_participant_issuance(
            verified,
            epoch_manifest=manifest,
        )

        self.assertEqual(verified.record_sha256, result.record_sha256)
        self.assertEqual(h(16), result.participant_record_sha256)
        self.assertEqual(derive_key_id(P1), result.participant_key_id)
        self.assertEqual(P1, result.participant_public_key)
        self.assertEqual(h(17), result.standing_record_sha256)
        self.assertEqual(h(16), result.issuing_operator_participant_record_sha256)
        self.assertEqual("participant", result.signer_kind)
        self.assertEqual(derive_key_id(P1), result.signer_key_id)

    def test_valid_signing_node_signed_issuance_preserves_operator_provenance(self) -> None:
        manifest, verified = verified_issuance_fixture(
            signer_kind="signing_node",
        )

        result = verify_accepted_participant_issuance(
            verified,
            epoch_manifest=manifest,
        )

        self.assertEqual(h(16), result.participant_record_sha256)
        self.assertEqual(h(16), result.issuing_operator_participant_record_sha256)
        self.assertEqual("signing_node", result.signer_kind)
        self.assertEqual(derive_key_id(P2), result.signer_key_id)

    def test_wrong_stream_is_rejected(self) -> None:
        manifest, verified = verified_issuance_fixture(stream="witness")

        with self.assertRaises(CivicParticipantIssuanceError):
            verify_accepted_participant_issuance(
                verified,
                epoch_manifest=manifest,
            )

    def test_participant_key_must_match_manifest_participant(self) -> None:
        manifest, verified = verified_issuance_fixture(
            participant_key_id=derive_key_id(P3),
            participant_public_key=P3,
        )

        with self.assertRaises(CivicParticipantIssuanceError):
            verify_accepted_participant_issuance(
                verified,
                epoch_manifest=manifest,
            )

    def test_standing_record_must_match_manifest_participant(self) -> None:
        manifest, verified = verified_issuance_fixture(
            standing_record_sha256=h(40),
        )

        with self.assertRaises(CivicParticipantIssuanceError):
            verify_accepted_participant_issuance(
                verified,
                epoch_manifest=manifest,
            )

    def test_issuing_operator_must_match_manifest_operator(self) -> None:
        manifest, verified = verified_issuance_fixture(
            issuing_operator_participant_record_sha256=h(41),
        )

        with self.assertRaises(CivicParticipantIssuanceError):
            verify_accepted_participant_issuance(
                verified,
                epoch_manifest=manifest,
            )

    def test_manifest_issuance_record_identity_mismatch_is_rejected(self) -> None:
        manifest, verified = verified_issuance_fixture()
        wrong_manifest = copy.deepcopy(manifest)
        wrong_manifest["participants"][0]["issuance_record_sha256"] = h(42)  # type: ignore[index]

        with self.assertRaises(CivicParticipantIssuanceError):
            verify_accepted_participant_issuance(
                verified,
                epoch_manifest=wrong_manifest,
            )

    def test_non_operator_participant_signer_is_rejected(self) -> None:
        manifest, verified = verified_issuance_fixture(
            add_second_participant=True,
            signer_kind="participant",
            signer_participant_record_sha256=h(22),
        )

        with self.assertRaises(CivicParticipantIssuanceError):
            verify_accepted_participant_issuance(
                verified,
                epoch_manifest=manifest,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
