from __future__ import annotations

import hashlib
import json
import unittest

from civic.codec import CborTag, decode_deterministic, encode_deterministic
from civic.cose import parse_cose_sign1
from civic.diagnostic_projection import (
    AUTHORITY_STATUS,
    FORMAT,
    VERSION,
    build_diagnostic_projection,
    encode_diagnostic_projection_json,
)
from civic.signed_manifest import (
    CivicSignedManifestError,
    sign_epoch_manifest_fixture,
)
from civic.tests.test_epoch_manifest import fixture_manifest


class CivicDiagnosticProjectionTests(unittest.TestCase):
    def _signed_fixture(self) -> bytes:
        return sign_epoch_manifest_fixture(
            fixture_manifest(),
            private_scalar=2,
            nonce_scalar=7,
        )

    def test_projection_records_authority_boundary_and_source_hashes(self) -> None:
        signed = self._signed_fixture()
        parsed = parse_cose_sign1(signed)
        projection = build_diagnostic_projection(signed)

        self.assertEqual(FORMAT, projection["format"])
        self.assertEqual(VERSION, projection["version"])
        self.assertEqual(AUTHORITY_STATUS, projection["authority_status"])

        source = projection["source"]
        self.assertEqual(
            hashlib.sha256(signed).hexdigest(),
            source["cose_sign1_sha256"],
        )
        self.assertEqual(len(signed), source["cose_sign1_byte_length"])
        self.assertEqual(
            hashlib.sha256(parsed.payload).hexdigest(),
            source["manifest_payload_sha256"],
        )
        self.assertEqual(
            len(parsed.payload),
            source["manifest_payload_byte_length"],
        )
        self.assertEqual(
            hashlib.sha256(parsed.protected).hexdigest(),
            source["protected_header_sha256"],
        )
        self.assertEqual(
            len(parsed.protected),
            source["protected_header_byte_length"],
        )
        self.assertEqual(
            parsed.key_id.hex(),
            source["signing_node_key_id_hex"],
        )

    def test_binary_manifest_values_are_explicit_hex_objects(self) -> None:
        projection = build_diagnostic_projection(self._signed_fixture())
        hoa_root_id = projection["manifest"]["hoa_root_id"]

        self.assertEqual("hex", hoa_root_id["encoding"])
        self.assertEqual(32, hoa_root_id["byte_length"])
        self.assertEqual("01" * 32, hoa_root_id["value"])

    def test_json_encoding_is_deterministic(self) -> None:
        signed = self._signed_fixture()

        first = encode_diagnostic_projection_json(signed)
        second = encode_diagnostic_projection_json(signed)

        self.assertEqual(first, second)
        self.assertTrue(first.endswith(b"\n"))
        decoded = json.loads(first.decode("utf-8"))
        self.assertEqual(AUTHORITY_STATUS, decoded["authority_status"])

    def test_tampered_signed_input_is_rejected_before_projection(self) -> None:
        signed = self._signed_fixture()
        decoded = decode_deterministic(signed)
        self.assertIsInstance(decoded, CborTag)

        body = list(decoded.value)
        signature = bytearray(body[3])
        signature[0] ^= 0x01
        body[3] = bytes(signature)
        tampered = encode_deterministic(CborTag(decoded.tag, body))

        with self.assertRaises(CivicSignedManifestError):
            build_diagnostic_projection(tampered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
