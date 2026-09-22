from __future__ import annotations

import unittest

from civic.codec import CborTag, decode_deterministic, encode_deterministic
from civic.cose import (
    CONTENT_TYPE,
    COSE_ALG_ESP256,
    CivicCoseError,
    build_cose_sign1,
    build_protected_header,
    build_sig_structure,
    parse_cose_sign1,
)


KEY_ID = bytes(range(32))
PAYLOAD = b"epoch-manifest-fixture"
SIGNATURE = bytes(range(64))


class CivicCoseTests(unittest.TestCase):
    def test_protected_header_is_exact(self) -> None:
        protected = build_protected_header(KEY_ID)
        self.assertEqual(
            {1: COSE_ALG_ESP256, 3: CONTENT_TYPE, 4: KEY_ID},
            decode_deterministic(protected),
        )

    def test_sig_structure_is_exact(self) -> None:
        protected = build_protected_header(KEY_ID)
        expected = encode_deterministic(
            ["Signature1", protected, b"", PAYLOAD]
        )
        self.assertEqual(expected, build_sig_structure(PAYLOAD, KEY_ID))

    def test_sign1_round_trip(self) -> None:
        encoded = build_cose_sign1(PAYLOAD, KEY_ID, SIGNATURE)
        parsed = parse_cose_sign1(encoded)
        self.assertEqual(PAYLOAD, parsed.payload)
        self.assertEqual(KEY_ID, parsed.key_id)
        self.assertEqual(SIGNATURE, parsed.signature)

    def test_wrong_algorithm_is_rejected(self) -> None:
        protected = encode_deterministic({1: -7, 3: CONTENT_TYPE, 4: KEY_ID})
        encoded = encode_deterministic(
            CborTag(18, [protected, {}, PAYLOAD, SIGNATURE])
        )
        with self.assertRaises(CivicCoseError):
            parse_cose_sign1(encoded)


if __name__ == "__main__":
    unittest.main(verbosity=2)
