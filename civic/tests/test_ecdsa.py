from __future__ import annotations

import unittest

from civic.ecdsa import (
    CivicEcdsaError,
    public_key_from_private_scalar,
    sign_sig_structure_fixture,
    verify_sig_structure,
)


P1 = bytes.fromhex(
    "04"
    "6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296"
    "4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5"
)

P2 = bytes.fromhex(
    "04"
    "7cf27b188d034f7e8a52380304b51ac3c08969e277f21b35a60b48fc47669978"
    "07775510db8ed040293d9ac69f7430dbba7dade63ce982299e04b79d227873d1"
)


class CivicEcdsaTests(unittest.TestCase):
    def test_known_public_keys_from_fixture_scalars(self) -> None:
        self.assertEqual(P1, public_key_from_private_scalar(1))
        self.assertEqual(P2, public_key_from_private_scalar(2))

    def test_fixture_signature_verifies(self) -> None:
        sig_structure = b"fixture Sig_structure bytes"
        public_key = public_key_from_private_scalar(2)
        signature = sign_sig_structure_fixture(
            private_scalar=2,
            nonce_scalar=7,
            sig_structure=sig_structure,
        )

        self.assertEqual(64, len(signature))
        self.assertTrue(
            verify_sig_structure(public_key, sig_structure, signature)
        )

    def test_tampered_sig_structure_fails_verification(self) -> None:
        sig_structure = b"fixture Sig_structure bytes"
        public_key = public_key_from_private_scalar(2)
        signature = sign_sig_structure_fixture(
            private_scalar=2,
            nonce_scalar=7,
            sig_structure=sig_structure,
        )

        self.assertFalse(
            verify_sig_structure(
                public_key,
                sig_structure + b"!",
                signature,
            )
        )

    def test_wrong_signature_length_is_rejected_as_invalid(self) -> None:
        public_key = public_key_from_private_scalar(1)
        self.assertFalse(
            verify_sig_structure(
                public_key,
                b"fixture",
                b"\x00" * 63,
            )
        )

    def test_invalid_public_key_point_is_rejected(self) -> None:
        invalid = b"\x04" + (b"\x00" * 64)
        with self.assertRaises(CivicEcdsaError):
            verify_sig_structure(
                invalid,
                b"fixture",
                b"\x01" * 64,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
