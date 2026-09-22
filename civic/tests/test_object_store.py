from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from civic.object_store import (
    CivicObjectStoreError,
    get_object,
    has_object,
    object_path,
    object_sha256,
    put_object,
    verify_object_bytes,
)


class CivicObjectStoreTests(unittest.TestCase):
    def test_object_sha256_matches_exact_bytes(self) -> None:
        data = b"civic-object-bytes"
        self.assertEqual(hashlib.sha256(data).digest(), object_sha256(data))

    def test_object_path_is_deterministic_digest_projection(self) -> None:
        digest = bytes.fromhex("ab" + "cd" * 31)
        path = object_path("/tmp/civic-store", digest)

        self.assertEqual(
            Path("/tmp/civic-store") / "ab" / ("cd" * 31),
            path,
        )

    def test_put_get_and_has_object_verify_exact_bytes(self) -> None:
        data = b"exact civic object payload"

        with tempfile.TemporaryDirectory() as directory:
            digest = put_object(directory, data)

            self.assertTrue(has_object(directory, digest))
            self.assertEqual(
                data,
                get_object(
                    directory,
                    digest,
                    expected_byte_length=len(data),
                ),
            )

    def test_repeated_put_of_same_object_is_idempotent(self) -> None:
        data = b"same object"

        with tempfile.TemporaryDirectory() as directory:
            first = put_object(directory, data)
            target = object_path(directory, first)
            before = target.read_bytes()

            second = put_object(directory, data)

            self.assertEqual(first, second)
            self.assertEqual(before, target.read_bytes())
            self.assertEqual(data, target.read_bytes())

    def test_descriptor_mismatch_is_rejected(self) -> None:
        data = b"descriptor check"
        digest = hashlib.sha256(data).digest()

        with self.assertRaises(CivicObjectStoreError):
            verify_object_bytes(
                data,
                expected_sha256=b"\x00" * 32,
                expected_byte_length=len(data),
            )

        with self.assertRaises(CivicObjectStoreError):
            verify_object_bytes(
                data,
                expected_sha256=digest,
                expected_byte_length=len(data) + 1,
            )

    def test_missing_object_is_reported(self) -> None:
        missing = hashlib.sha256(b"missing").digest()

        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(has_object(directory, missing))

            with self.assertRaises(CivicObjectStoreError):
                get_object(directory, missing)

    def test_corrupted_stored_bytes_are_detected(self) -> None:
        data = b"original object"

        with tempfile.TemporaryDirectory() as directory:
            digest = put_object(directory, data)
            target = object_path(directory, digest)
            target.write_bytes(b"corrupted object")

            self.assertFalse(has_object(directory, digest))

            with self.assertRaises(CivicObjectStoreError):
                get_object(directory, digest)

            with self.assertRaises(CivicObjectStoreError):
                put_object(directory, data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
