from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import unittest

from civic.cose import build_cose_sign1, build_protected_header, build_sig_structure


VECTOR = (
    Path(__file__).resolve().parents[1]
    / "test-vectors"
    / "epoch-manifest-v1.json"
)


class CivicInteroperabilityVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.vector = json.loads(VECTOR.read_text(encoding="utf-8"))

    def _bytes(self, section: str) -> bytes:
        return base64.b64decode(
            self.vector[section]["base64"],
            validate=True,
        )

    def test_recorded_lengths_and_hashes_match_bytes(self) -> None:
        for section in (
            "epoch_manifest_payload",
            "cose_protected_header",
            "cose_sig_structure",
            "cose_sign1",
        ):
            raw = self._bytes(section)
            self.assertEqual(self.vector[section]["byte_length"], len(raw))
            self.assertEqual(
                self.vector[section]["sha256_hex"],
                hashlib.sha256(raw).hexdigest(),
            )

    def test_protected_header_matches_implementation(self) -> None:
        key_id = bytes.fromhex(
            self.vector["fixture"]["signing_node_key_id_hex"]
        )
        self.assertEqual(
            self._bytes("cose_protected_header"),
            build_protected_header(key_id),
        )

    def test_sig_structure_matches_implementation(self) -> None:
        payload = self._bytes("epoch_manifest_payload")
        key_id = bytes.fromhex(
            self.vector["fixture"]["signing_node_key_id_hex"]
        )
        self.assertEqual(
            self._bytes("cose_sig_structure"),
            build_sig_structure(payload, key_id),
        )

    def test_cose_sign1_matches_implementation(self) -> None:
        payload = self._bytes("epoch_manifest_payload")
        key_id = bytes.fromhex(
            self.vector["fixture"]["signing_node_key_id_hex"]
        )
        signature = bytes.fromhex(
            self.vector["fixture"]["signature_hex"]
        )
        self.assertEqual(
            self._bytes("cose_sign1"),
            build_cose_sign1(payload, key_id, signature),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
