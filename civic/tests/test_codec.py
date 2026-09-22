from __future__ import annotations

import unittest

from civic.codec import CborTag, CivicCodecError, decode_deterministic, encode_deterministic


class CivicDeterministicCborTests(unittest.TestCase):
    def test_round_trip_supported_values(self) -> None:
        value = {
            "text": "civic",
            "bytes": b"\x00\x01\x02",
            "positive": 42,
            "negative": -7,
            "array": [True, False, None, 0],
            "tagged": CborTag(18, [b"payload"]),
        }

        encoded = encode_deterministic(value)

        self.assertEqual(value, decode_deterministic(encoded))
        self.assertEqual(encoded, encode_deterministic(decode_deterministic(encoded)))

    def test_map_order_is_core_deterministic(self) -> None:
        encoded = encode_deterministic({"aa": 1, "b": 2})

        # RFC 8949 core deterministic order is shorter encoded key first.
        self.assertEqual(bytes.fromhex("a261620262616101"), encoded)
        self.assertEqual({"b": 2, "aa": 1}, decode_deterministic(encoded))

    def test_non_shortest_integer_encoding_is_rejected(self) -> None:
        # Integer 0 encoded with an unnecessary one-byte argument.
        with self.assertRaises(CivicCodecError):
            decode_deterministic(bytes.fromhex("1800"))

    def test_indefinite_length_and_float_are_rejected(self) -> None:
        with self.assertRaises(CivicCodecError):
            decode_deterministic(bytes.fromhex("9fff"))

        with self.assertRaises(CivicCodecError):
            decode_deterministic(bytes.fromhex("f90000"))

        with self.assertRaises(CivicCodecError):
            encode_deterministic(1.5)

    def test_non_nfc_text_is_rejected(self) -> None:
        decomposed = "e\u0301"

        with self.assertRaises(CivicCodecError):
            encode_deterministic(decomposed)

        # A two-code-point decomposed UTF-8 text string.
        with self.assertRaises(CivicCodecError):
            decode_deterministic(bytes.fromhex("6365cc81"))

    def test_duplicate_map_key_is_rejected(self) -> None:
        # {"a": 1, "a": 2}
        with self.assertRaises(CivicCodecError):
            decode_deterministic(bytes.fromhex("a2616101616102"))

    def test_trailing_bytes_are_rejected(self) -> None:
        with self.assertRaises(CivicCodecError):
            decode_deterministic(b"\x00\x00")


if __name__ == "__main__":
    unittest.main(verbosity=2)
