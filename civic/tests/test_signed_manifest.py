from __future__ import annotations

import copy
import unittest

from civic.codec import CborTag, decode_deterministic, encode_deterministic
from civic.cose import build_protected_header, parse_cose_sign1
from civic.epoch_manifest import derive_key_id
from civic.signed_manifest import (
    CivicSignedManifestError,
    sign_epoch_manifest_fixture,
    verify_signed_epoch_manifest,
)
from civic.tests.test_epoch_manifest import P1, P2, fixture_manifest


class CivicSignedManifestTests(unittest.TestCase):
    def test_complete_fixture_signed_manifest_verifies(self) -> None:
        manifest = fixture_manifest()
        signed = sign_epoch_manifest_fixture(
            manifest,
            private_scalar=2,
            nonce_scalar=7,
        )
        self.assertEqual(manifest, verify_signed_epoch_manifest(signed))

    def test_fixture_private_scalar_must_match_declared_signing_node(self) -> None:
        manifest = fixture_manifest()
        with self.assertRaises(CivicSignedManifestError):
            sign_epoch_manifest_fixture(
                manifest,
                private_scalar=1,
                nonce_scalar=7,
            )

    def test_cose_kid_mismatch_is_rejected(self) -> None:
        manifest = fixture_manifest()
        signed = sign_epoch_manifest_fixture(
            manifest,
            private_scalar=2,
            nonce_scalar=7,
        )
        decoded = decode_deterministic(signed)
        self.assertIsInstance(decoded, CborTag)

        body = list(decoded.value)
        wrong_key_id = derive_key_id(P1)
        body[0] = build_protected_header(wrong_key_id)
        tampered = encode_deterministic(CborTag(decoded.tag, body))

        with self.assertRaises(CivicSignedManifestError):
            verify_signed_epoch_manifest(tampered)

    def test_signature_tamper_is_rejected(self) -> None:
        manifest = fixture_manifest()
        signed = sign_epoch_manifest_fixture(
            manifest,
            private_scalar=2,
            nonce_scalar=7,
        )
        decoded = decode_deterministic(signed)
        self.assertIsInstance(decoded, CborTag)

        body = list(decoded.value)
        signature = bytearray(body[3])
        signature[-1] ^= 0x01
        body[3] = bytes(signature)
        tampered = encode_deterministic(CborTag(decoded.tag, body))

        with self.assertRaises(CivicSignedManifestError):
            verify_signed_epoch_manifest(tampered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
