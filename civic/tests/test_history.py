from __future__ import annotations

import hashlib
import unittest

from civic.codec import encode_deterministic
from civic.history import (
    CivicHistoryError,
    append_history_record,
    decode_history_sequence,
    history_record_sha256,
)


class CivicHistoryTests(unittest.TestCase):
    def test_empty_sequence_decodes_to_no_records(self) -> None:
        self.assertEqual((), decode_history_sequence(b""))

    def test_append_preserves_existing_bytes_and_record_order(self) -> None:
        first = encode_deterministic(
            {"kind": "accepted", "sequence": 1, "value": b"first"}
        )
        second = encode_deterministic(
            {"kind": "accepted", "sequence": 2, "value": b"second"}
        )

        sequence = append_history_record(b"", first)
        before_second_append = sequence
        sequence = append_history_record(sequence, second)

        self.assertEqual(first, before_second_append)
        self.assertTrue(sequence.startswith(before_second_append))
        self.assertEqual(first + second, sequence)

        records = decode_history_sequence(sequence)
        self.assertEqual(2, len(records))
        self.assertEqual(first, records[0].encoded)
        self.assertEqual(second, records[1].encoded)
        self.assertEqual(
            [{"kind": "accepted", "sequence": 1, "value": b"first"},
             {"kind": "accepted", "sequence": 2, "value": b"second"}],
            [record.value for record in records],
        )

    def test_record_offsets_lengths_and_hashes_match_exact_bytes(self) -> None:
        first = encode_deterministic(["witness", 1])
        second = encode_deterministic(["witness", 2, b"payload"])
        sequence = first + second

        records = decode_history_sequence(sequence)

        self.assertEqual(0, records[0].offset)
        self.assertEqual(len(first), records[0].byte_length)
        self.assertEqual(hashlib.sha256(first).digest(), records[0].sha256)

        self.assertEqual(len(first), records[1].offset)
        self.assertEqual(len(second), records[1].byte_length)
        self.assertEqual(hashlib.sha256(second).digest(), records[1].sha256)

        self.assertEqual(hashlib.sha256(first).digest(), history_record_sha256(first))
        self.assertEqual(hashlib.sha256(second).digest(), history_record_sha256(second))

    def test_non_deterministic_record_is_rejected(self) -> None:
        # Integer zero encoded non-canonically as additional-info 24 followed by 0.
        non_deterministic_zero = b"\x18\x00"

        with self.assertRaises(CivicHistoryError):
            decode_history_sequence(non_deterministic_zero)

        with self.assertRaises(CivicHistoryError):
            append_history_record(b"", non_deterministic_zero)

        with self.assertRaises(CivicHistoryError):
            history_record_sha256(non_deterministic_zero)

    def test_truncated_record_is_rejected(self) -> None:
        complete = encode_deterministic(b"abcdef")
        truncated = complete[:-1]

        with self.assertRaises(CivicHistoryError):
            decode_history_sequence(truncated)

        good_prefix = encode_deterministic({"ok": True})
        with self.assertRaises(CivicHistoryError):
            decode_history_sequence(good_prefix + truncated)


if __name__ == "__main__":
    unittest.main(verbosity=2)
