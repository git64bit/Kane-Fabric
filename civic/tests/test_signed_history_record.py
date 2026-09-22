from __future__ import annotations

import copy
import hashlib
import unittest

from civic.codec import CborTag, decode_deterministic, encode_deterministic
from civic.cose import (
    EPOCH_CONTENT_TYPE,
    HISTORY_RECORD_CONTENT_TYPE,
    build_cose_sign1,
    build_sig_structure,
    parse_cose_sign1,
)
from civic.ecdsa import sign_sig_structure_fixture
from civic.epoch_manifest import CRYPTO_PROFILE, derive_key_id
from civic.signed_history_record import (
    CivicSignedHistoryRecordError,
    decode_history_record_payload,
    encode_history_record_payload,
    sign_history_record_fixture,
    verify_signed_history_record,
)
from civic.tests.test_epoch_manifest import P1, P2, fixture_manifest, h


def signing_node_payload() -> dict[str, object]:
    return {
        "format": "kane-civic-history-record",
        "version": 1,
        "crypto_profile": CRYPTO_PROFILE,
        "hoa_root_id": h(1),
        "epoch_sequence": 1,
        "ceremony_record_sha256": h(25),
        "record_type": "fixture-accepted-event",
        "history_link": {
            "stream": "accepted",
            "predecessor_record_sha256": None,
        },
        "signer": {
            "kind": "signing_node",
            "key_id": derive_key_id(P2),
            "participant_record_sha256": None,
        },
        "body": {
            "fixture": "signing-node",
            "sequence": 1,
        },
    }


def participant_payload() -> dict[str, object]:
    return {
        "format": "kane-civic-history-record",
        "version": 1,
        "crypto_profile": CRYPTO_PROFILE,
        "hoa_root_id": h(1),
        "epoch_sequence": 1,
        "ceremony_record_sha256": h(25),
        "record_type": "fixture-witness-event",
        "history_link": {
            "stream": "witness",
            "predecessor_record_sha256": None,
        },
        "signer": {
            "kind": "participant",
            "key_id": derive_key_id(P1),
            "participant_record_sha256": h(16),
        },
        "body": {
            "fixture": "participant",
            "observation": b"fixture observation",
        },
    }


def low_level_fixture_envelope(
    payload: dict[str, object],
    *,
    private_scalar: int,
    nonce_scalar: int,
    content_type: str = HISTORY_RECORD_CONTENT_TYPE,
) -> bytes:
    payload_bytes = encode_history_record_payload(payload)
    key_id = payload["signer"]["key_id"]  # type: ignore[index]
    assert isinstance(key_id, bytes)

    sig_structure = build_sig_structure(
        payload_bytes,
        key_id,
        content_type=content_type,
    )
    signature = sign_sig_structure_fixture(
        private_scalar=private_scalar,
        nonce_scalar=nonce_scalar,
        sig_structure=sig_structure,
    )
    return build_cose_sign1(
        payload_bytes,
        key_id,
        signature,
        content_type=content_type,
    )


class CivicSignedHistoryRecordTests(unittest.TestCase):
    def test_signing_node_record_verifies_and_exposes_authenticated_link(self) -> None:
        manifest = fixture_manifest()
        payload = signing_node_payload()

        signed = sign_history_record_fixture(
            payload,
            epoch_manifest=manifest,
            private_scalar=2,
            nonce_scalar=7,
        )
        verified = verify_signed_history_record(
            signed,
            epoch_manifests=[manifest],
        )

        self.assertEqual(payload, verified.payload)
        self.assertEqual(hashlib.sha256(signed).digest(), verified.record_sha256)
        self.assertEqual("accepted", verified.history_link.stream)
        self.assertIsNone(verified.history_link.predecessor_record_sha256)
        self.assertEqual(P2, verified.signer_public_key)
        self.assertEqual(derive_key_id(P2), verified.signer_key_id)

    def test_participant_record_verifies_against_epoch_participant_key(self) -> None:
        manifest = fixture_manifest()
        payload = participant_payload()

        signed = sign_history_record_fixture(
            payload,
            epoch_manifest=manifest,
            private_scalar=1,
            nonce_scalar=11,
        )
        verified = verify_signed_history_record(
            signed,
            epoch_manifests=[manifest],
        )

        self.assertEqual(payload, verified.payload)
        self.assertEqual("witness", verified.history_link.stream)
        self.assertEqual(P1, verified.signer_public_key)
        self.assertEqual(derive_key_id(P1), verified.signer_key_id)

    def test_history_payload_round_trips_deterministically(self) -> None:
        payload = participant_payload()
        encoded = encode_history_record_payload(payload)

        self.assertEqual(payload, decode_history_record_payload(encoded))
        self.assertEqual(encoded, encode_history_record_payload(payload))

    def test_wrong_content_type_is_rejected(self) -> None:
        manifest = fixture_manifest()
        payload = signing_node_payload()

        signed_with_epoch_type = low_level_fixture_envelope(
            payload,
            private_scalar=2,
            nonce_scalar=7,
            content_type=EPOCH_CONTENT_TYPE,
        )

        with self.assertRaises(CivicSignedHistoryRecordError):
            verify_signed_history_record(
                signed_with_epoch_type,
                epoch_manifests=[manifest],
            )

    def test_signer_key_binding_mismatch_is_rejected(self) -> None:
        manifest = fixture_manifest()
        payload = participant_payload()
        payload["signer"]["key_id"] = derive_key_id(P2)  # type: ignore[index]

        signed = low_level_fixture_envelope(
            payload,
            private_scalar=2,
            nonce_scalar=13,
        )

        with self.assertRaises(CivicSignedHistoryRecordError):
            verify_signed_history_record(
                signed,
                epoch_manifests=[manifest],
            )

    def test_wrong_epoch_context_is_rejected(self) -> None:
        manifest = fixture_manifest()
        payload = signing_node_payload()
        payload["ceremony_record_sha256"] = h(26)

        signed = low_level_fixture_envelope(
            payload,
            private_scalar=2,
            nonce_scalar=17,
        )

        with self.assertRaises(CivicSignedHistoryRecordError):
            verify_signed_history_record(
                signed,
                epoch_manifests=[manifest],
            )

    def test_signature_tamper_is_rejected(self) -> None:
        manifest = fixture_manifest()
        payload = signing_node_payload()

        signed = sign_history_record_fixture(
            payload,
            epoch_manifest=manifest,
            private_scalar=2,
            nonce_scalar=19,
        )
        decoded = decode_deterministic(signed)
        self.assertIsInstance(decoded, CborTag)

        body = list(decoded.value)
        signature = bytearray(body[3])
        signature[-1] ^= 0x01
        body[3] = bytes(signature)
        tampered = encode_deterministic(CborTag(decoded.tag, body))

        with self.assertRaises(CivicSignedHistoryRecordError):
            verify_signed_history_record(
                tampered,
                epoch_manifests=[manifest],
            )

    def test_cose_kid_must_match_payload_signer_key_id(self) -> None:
        manifest = fixture_manifest()
        payload = signing_node_payload()

        signed = sign_history_record_fixture(
            payload,
            epoch_manifest=manifest,
            private_scalar=2,
            nonce_scalar=23,
        )
        parsed = parse_cose_sign1(
            signed,
            expected_content_type=HISTORY_RECORD_CONTENT_TYPE,
        )

        wrong_kid = derive_key_id(P1)
        rebuilt = build_cose_sign1(
            parsed.payload,
            wrong_kid,
            parsed.signature,
            content_type=HISTORY_RECORD_CONTENT_TYPE,
        )

        with self.assertRaises(CivicSignedHistoryRecordError):
            verify_signed_history_record(
                rebuilt,
                epoch_manifests=[manifest],
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
