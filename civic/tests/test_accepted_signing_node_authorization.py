from __future__ import annotations

import copy
import unittest

from civic.accepted_signing_node_authorization import (
    RECORD_TYPE,
    CivicSigningNodeAuthorizationError,
    verify_accepted_signing_node_authorization,
)
from civic.epoch_manifest import CRYPTO_PROFILE, derive_key_id
from civic.signed_history_record import (
    sign_history_record_fixture,
    verify_signed_history_record,
)
from civic.tests.test_epoch_manifest import P1, P2, fixture_manifest, h


def authorization_fixture(
    *,
    signer_kind: str = "signing_node",
    stream: str = "accepted",
    body_key_id: bytes | None = None,
    body_public_key: bytes | None = None,
    body_proofs: list[bytes] | None = None,
) -> tuple[dict[str, object], dict[str, object], int]:
    manifest = fixture_manifest()
    manifest_proofs = [h(30), h(31)]
    manifest["ceremony"]["governance_proof_sha256"] = manifest_proofs  # type: ignore[index]

    if body_key_id is None:
        body_key_id = derive_key_id(P2)
    if body_public_key is None:
        body_public_key = P2
    if body_proofs is None:
        body_proofs = list(manifest_proofs)

    if signer_kind == "signing_node":
        signer = {
            "kind": "signing_node",
            "key_id": derive_key_id(P2),
            "participant_record_sha256": None,
        }
        private_scalar = 2
    elif signer_kind == "participant":
        signer = {
            "kind": "participant",
            "key_id": derive_key_id(P1),
            "participant_record_sha256": h(16),
        }
        private_scalar = 1
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
            "authorized_key_id": body_key_id,
            "authorized_public_key": body_public_key,
            "governance_proof_sha256": body_proofs,
        },
    }

    return manifest, payload, private_scalar


def verified_authorization_fixture(
    **kwargs: object,
):
    manifest, payload, private_scalar = authorization_fixture(**kwargs)

    signed = sign_history_record_fixture(
        payload,
        epoch_manifest=manifest,
        private_scalar=private_scalar,
        nonce_scalar=37,
    )

    import hashlib

    manifest["signing_node"]["authorization_record_sha256"] = hashlib.sha256(signed).digest()  # type: ignore[index]
    verified = verify_signed_history_record(
        signed,
        epoch_manifests=[manifest],
    )
    return manifest, verified


class CivicAcceptedSigningNodeAuthorizationTests(unittest.TestCase):
    def test_valid_authorization_binds_key_manifest_record_and_proofs(self) -> None:
        manifest, verified = verified_authorization_fixture()

        result = verify_accepted_signing_node_authorization(
            verified,
            epoch_manifest=manifest,
        )

        self.assertEqual(verified.record_sha256, result.record_sha256)
        self.assertEqual(derive_key_id(P2), result.authorized_key_id)
        self.assertEqual(P2, result.authorized_public_key)
        self.assertEqual((h(30), h(31)), result.governance_proof_sha256)

    def test_wrong_stream_is_rejected(self) -> None:
        manifest, verified = verified_authorization_fixture(stream="witness")

        with self.assertRaises(CivicSigningNodeAuthorizationError):
            verify_accepted_signing_node_authorization(
                verified,
                epoch_manifest=manifest,
            )

    def test_participant_signer_is_rejected(self) -> None:
        manifest, verified = verified_authorization_fixture(
            signer_kind="participant",
        )

        with self.assertRaises(CivicSigningNodeAuthorizationError):
            verify_accepted_signing_node_authorization(
                verified,
                epoch_manifest=manifest,
            )

    def test_authorized_key_mismatch_is_rejected(self) -> None:
        manifest, verified = verified_authorization_fixture(
            body_key_id=derive_key_id(P1),
            body_public_key=P1,
        )

        with self.assertRaises(CivicSigningNodeAuthorizationError):
            verify_accepted_signing_node_authorization(
                verified,
                epoch_manifest=manifest,
            )

    def test_manifest_authorization_record_identity_mismatch_is_rejected(self) -> None:
        manifest, verified = verified_authorization_fixture()
        wrong_manifest = copy.deepcopy(manifest)
        wrong_manifest["signing_node"]["authorization_record_sha256"] = h(40)  # type: ignore[index]

        with self.assertRaises(CivicSigningNodeAuthorizationError):
            verify_accepted_signing_node_authorization(
                verified,
                epoch_manifest=wrong_manifest,
            )

    def test_governance_proof_set_mismatch_is_rejected(self) -> None:
        manifest, verified = verified_authorization_fixture(
            body_proofs=[h(30), h(32)],
        )

        with self.assertRaises(CivicSigningNodeAuthorizationError):
            verify_accepted_signing_node_authorization(
                verified,
                epoch_manifest=manifest,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
