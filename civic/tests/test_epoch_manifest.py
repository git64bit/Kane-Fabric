from __future__ import annotations

import copy
import hashlib
import unittest

from civic.epoch_manifest import (
    CRYPTO_PROFILE,
    CivicManifestError,
    decode_epoch_manifest,
    derive_key_id,
    encode_epoch_manifest,
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


def h(byte: int) -> bytes:
    return bytes([byte]) * 32


def fixture_manifest() -> dict[str, object]:
    inline = b"fixture evidence\n"
    return {
        "format": "kane-civic-epoch-manifest",
        "version": 1,
        "crypto_profile": CRYPTO_PROFILE,
        "hoa_root_id": h(1),
        "epoch_sequence": 1,
        "predecessor_manifest_sha256": None,
        "effective_time_ms": 1_800_000_000_123,
        "governing_profile": {
            "profile_id": "illinois-condominium-v1",
            "profile_sha256": h(2),
            "source_set_sha256": h(3),
        },
        "governing_sources": [],
        "participants": [
            {
                "participant_record_sha256": h(16),
                "participant_key_id": derive_key_id(P1),
                "participant_public_key": P1,
                "standing_record_sha256": h(17),
                "issuance_record_sha256": h(18),
            }
        ],
        "operator": {
            "participant_record_sha256": h(16),
            "selection_record_sha256": h(19),
        },
        "signing_node": {
            "key_id": derive_key_id(P2),
            "public_key": P2,
            "authorization_record_sha256": h(20),
        },
        "history": {
            "accepted_history_head_sha256": h(21),
            "witness_head_sha256": None,
            "diagnostics_head_sha256": None,
            "knowledge_head_sha256": None,
        },
        "ceremony": {
            "ceremony_record_sha256": h(25),
            "governance_proof_sha256": [],
        },
        "object_index": [
            {
                "sha256": hashlib.sha256(inline).digest(),
                "byte_length": len(inline),
                "media_type": "text/plain",
                "semantic_role": "fixture",
                "name": "fixture.txt",
                "cid": None,
                "inline": inline,
            }
        ],
    }


class EpochManifestSchemaTests(unittest.TestCase):
    def test_valid_manifest_round_trips(self) -> None:
        manifest = fixture_manifest()
        encoded = encode_epoch_manifest(manifest)
        self.assertEqual(manifest, decode_epoch_manifest(encoded))

    def test_epoch_one_rejects_predecessor(self) -> None:
        manifest = fixture_manifest()
        manifest["predecessor_manifest_sha256"] = h(30)
        with self.assertRaises(CivicManifestError):
            encode_epoch_manifest(manifest)

    def test_participant_key_id_must_match_public_key(self) -> None:
        manifest = fixture_manifest()
        manifest["participants"][0]["participant_key_id"] = h(31)  # type: ignore[index]
        with self.assertRaises(CivicManifestError):
            encode_epoch_manifest(manifest)

    def test_inline_object_hash_must_match_bytes(self) -> None:
        manifest = copy.deepcopy(fixture_manifest())
        manifest["object_index"][0]["inline"] = b"changed"  # type: ignore[index]
        with self.assertRaises(CivicManifestError):
            encode_epoch_manifest(manifest)


if __name__ == "__main__":
    unittest.main(verbosity=2)
