from __future__ import annotations

import base64
import copy
import hashlib
import unittest

from ms5.tools.kane_fabric_firmware_authorization import (
    FirmwareAuthorizationContractError,
    PAYLOAD_BYTES,
    authorization_payload_sha256,
    build_authorization_envelope,
    build_authorization_payload,
    decode_authorization_signature,
    derive_key_id_sha256,
    validate_authorization_envelope,
)

MANIFEST = "a" * 64
FIRMWARE = "b" * 64
PUBLIC_KEY = b"\x04" + bytes(range(1, 65))
SIGNATURE = bytes(range(64))


class FirmwareAuthorizationTests(unittest.TestCase):
    def _payload_kwargs(self):
        return {
            "device_family": "esp32-s3",
            "target": "esp32s3",
            "manifest_sha256": MANIFEST,
            "firmware_sha256": FIRMWARE,
            "firmware_byte_length": 900000,
            "release_sequence": 7,
            "rollback_floor_sequence": 3,
        }

    def test_fixed_payload_is_deterministic_and_binds_every_update_field(self):
        payload = build_authorization_payload(**self._payload_kwargs())
        self.assertEqual(PAYLOAD_BYTES, len(payload))
        self.assertEqual(
            hashlib.sha256(payload).hexdigest(),
            authorization_payload_sha256(**self._payload_kwargs()),
        )

        for key, replacement in (
            ("manifest_sha256", "c" * 64),
            ("firmware_sha256", "d" * 64),
            ("firmware_byte_length", 900001),
            ("release_sequence", 8),
            ("rollback_floor_sequence", 4),
        ):
            changed = self._payload_kwargs()
            changed[key] = replacement
            self.assertNotEqual(
                payload,
                build_authorization_payload(**changed),
                key,
            )

    def test_envelope_round_trip_is_exact_and_provider_independent(self):
        key_id = derive_key_id_sha256(PUBLIC_KEY)
        payload_sha = authorization_payload_sha256(**self._payload_kwargs())
        envelope = build_authorization_envelope(
            authorization_payload_sha256=payload_sha,
            key_id_sha256=key_id,
            signature=SIGNATURE,
        )
        validate_authorization_envelope(envelope)
        self.assertEqual("ecdsa-p256-sha256", envelope["algorithm"])
        self.assertEqual("p1363-r-s-64", envelope["signature_encoding"])
        self.assertEqual(payload_sha, envelope["authorization_payload_sha256"])
        self.assertEqual(SIGNATURE, decode_authorization_signature(envelope))

    def test_public_key_id_is_sha256_of_exact_sec1_bytes(self):
        first = derive_key_id_sha256(PUBLIC_KEY)
        changed = bytearray(PUBLIC_KEY)
        changed[-1] ^= 0x01
        second = derive_key_id_sha256(bytes(changed))
        self.assertNotEqual(first, second)

    def test_non_uncompressed_or_wrong_length_public_key_is_rejected(self):
        with self.assertRaises(FirmwareAuthorizationContractError):
            derive_key_id_sha256(b"\x03" + bytes(64))
        with self.assertRaises(FirmwareAuthorizationContractError):
            derive_key_id_sha256(b"\x04" + bytes(63))

    def test_wrong_signature_size_is_rejected(self):
        with self.assertRaises(FirmwareAuthorizationContractError):
            build_authorization_envelope(
                authorization_payload_sha256="e" * 64,
                key_id_sha256=derive_key_id_sha256(PUBLIC_KEY),
                signature=b"x" * 63,
            )

    def test_envelope_rejects_algorithm_or_signature_shape_drift(self):
        envelope = build_authorization_envelope(
            authorization_payload_sha256="e" * 64,
            key_id_sha256=derive_key_id_sha256(PUBLIC_KEY),
            signature=SIGNATURE,
        )
        changed = copy.deepcopy(envelope)
        changed["algorithm"] = "other"
        with self.assertRaises(FirmwareAuthorizationContractError):
            validate_authorization_envelope(changed)

        changed = copy.deepcopy(envelope)
        changed["signature_base64"] = base64.b64encode(b"x" * 63).decode("ascii")
        with self.assertRaises(FirmwareAuthorizationContractError):
            validate_authorization_envelope(changed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
