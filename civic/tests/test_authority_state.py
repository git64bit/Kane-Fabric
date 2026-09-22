from __future__ import annotations

import copy
import hashlib
import unittest

from civic.authority_state import (
    CivicAuthorityStateError,
    authority_state_replica_sha256,
    decode_authority_state_replica,
    encode_authority_state_replica,
    verify_authority_state_replica,
)
from civic.codec import encode_deterministic
from civic.epoch_manifest import manifest_sha256
from civic.signed_manifest import sign_epoch_manifest_fixture
from civic.tests.test_epoch_manifest import fixture_manifest


def replica_fixture() -> tuple[dict[str, object], dict[bytes, bytes], dict[str, object]]:
    source_bytes = b"authoritative governing source\n"
    source_sha256 = hashlib.sha256(source_bytes).digest()

    accepted_record = encode_deterministic(
        {
            "history_link": {
                "stream": "accepted",
                "predecessor_record_sha256": None,
            },
            "sequence": 1,
        }
    )
    accepted_head = hashlib.sha256(accepted_record).digest()
    accepted_sequence_sha256 = hashlib.sha256(accepted_record).digest()

    manifest = fixture_manifest()
    manifest["history"]["accepted_history_head_sha256"] = accepted_head  # type: ignore[index]
    manifest["governing_sources"] = [
        {
            "source_id": "governing-source-1",
            "role": "governing",
            "sha256": source_sha256,
            "byte_length": len(source_bytes),
            "media_type": "text/plain",
            "title": "Fixture governing source",
            "source_uri": None,
        }
    ]

    object_index = manifest["object_index"]
    assert isinstance(object_index, list)
    object_index.append(
        {
            "sha256": source_sha256,
            "byte_length": len(source_bytes),
            "media_type": "text/plain",
            "semantic_role": "governing-source",
            "name": "governing-source.txt",
            "cid": None,
            "inline": None,
        }
    )
    object_index.sort(key=lambda item: item["sha256"])

    signed_manifest = sign_epoch_manifest_fixture(
        manifest,
        private_scalar=2,
        nonce_scalar=7,
    )
    signed_manifest_sha256 = hashlib.sha256(signed_manifest).digest()
    manifest_id = manifest_sha256(manifest)

    replica = {
        "format": "kane-civic-participant-authority-state-replica",
        "version": 1,
        "hoa_root_id": manifest["hoa_root_id"],
        "current_epoch_sequence": 1,
        "current_manifest_sha256": manifest_id,
        "epoch_lineage": [
            {
                "epoch_sequence": 1,
                "manifest_sha256": manifest_id,
                "signed_manifest_sha256": signed_manifest_sha256,
                "signed_manifest_byte_length": len(signed_manifest),
            }
        ],
        "history_streams": {
            "accepted": {
                "head_sha256": accepted_head,
                "sequence_sha256": accepted_sequence_sha256,
                "byte_length": len(accepted_record),
            },
            "witness": {
                "head_sha256": None,
                "sequence_sha256": None,
                "byte_length": 0,
            },
            "diagnostics": {
                "head_sha256": None,
                "sequence_sha256": None,
                "byte_length": 0,
            },
            "knowledge": {
                "head_sha256": None,
                "sequence_sha256": None,
                "byte_length": 0,
            },
        },
        "required_objects": [
            {
                "sha256": source_sha256,
                "byte_length": len(source_bytes),
            }
        ],
    }

    objects = {
        signed_manifest_sha256: signed_manifest,
        accepted_sequence_sha256: accepted_record,
        source_sha256: source_bytes,
    }
    return replica, objects, manifest


def object_loader(objects: dict[bytes, bytes]):
    def load(sha256: bytes) -> bytes:
        return objects[sha256]

    return load


class CivicAuthorityStateTests(unittest.TestCase):
    def test_valid_replica_round_trips_deterministically(self) -> None:
        replica, _, _ = replica_fixture()

        encoded = encode_authority_state_replica(replica)

        self.assertEqual(replica, decode_authority_state_replica(encoded))
        self.assertEqual(encoded, encode_authority_state_replica(replica))
        self.assertEqual(
            hashlib.sha256(encoded).digest(),
            authority_state_replica_sha256(replica),
        )
        self.assertEqual(
            hashlib.sha256(encoded).digest(),
            authority_state_replica_sha256(encoded),
        )

    def test_complete_replica_verifies_signed_lineage_objects_and_history(self) -> None:
        replica, objects, manifest = replica_fixture()

        lineage = verify_authority_state_replica(
            replica,
            load_object=object_loader(objects),
        )

        self.assertEqual((manifest,), lineage)

    def test_non_contiguous_or_wrong_current_lineage_is_rejected(self) -> None:
        replica, _, _ = replica_fixture()

        wrong_sequence = copy.deepcopy(replica)
        wrong_sequence["epoch_lineage"][0]["epoch_sequence"] = 2  # type: ignore[index]
        with self.assertRaises(CivicAuthorityStateError):
            encode_authority_state_replica(wrong_sequence)

        wrong_current = copy.deepcopy(replica)
        wrong_current["current_manifest_sha256"] = b"\xff" * 32
        with self.assertRaises(CivicAuthorityStateError):
            encode_authority_state_replica(wrong_current)

    def test_required_authority_object_coverage_is_enforced(self) -> None:
        replica, objects, _ = replica_fixture()
        incomplete = copy.deepcopy(replica)
        incomplete["required_objects"] = []

        with self.assertRaises(CivicAuthorityStateError):
            verify_authority_state_replica(
                incomplete,
                load_object=object_loader(objects),
            )

    def test_missing_or_corrupted_retained_artifact_is_rejected(self) -> None:
        replica, objects, _ = replica_fixture()

        missing_objects = dict(objects)
        signed_id = replica["epoch_lineage"][0]["signed_manifest_sha256"]  # type: ignore[index]
        del missing_objects[signed_id]
        with self.assertRaises(CivicAuthorityStateError):
            verify_authority_state_replica(
                replica,
                load_object=object_loader(missing_objects),
            )

        corrupted_objects = dict(objects)
        required_id = replica["required_objects"][0]["sha256"]  # type: ignore[index]
        corrupted_objects[required_id] = b"corrupted"
        with self.assertRaises(CivicAuthorityStateError):
            verify_authority_state_replica(
                replica,
                load_object=object_loader(corrupted_objects),
            )

    def test_history_head_must_match_current_epoch_manifest(self) -> None:
        replica, objects, _ = replica_fixture()
        wrong_head = copy.deepcopy(replica)
        wrong_head["history_streams"]["accepted"]["head_sha256"] = b"\xee" * 32  # type: ignore[index]

        with self.assertRaises(CivicAuthorityStateError):
            verify_authority_state_replica(
                wrong_head,
                load_object=object_loader(objects),
            )

    def test_replica_schema_rejects_private_key_material(self) -> None:
        replica, _, _ = replica_fixture()
        replica["private_key"] = b"must-not-be-here"

        with self.assertRaises(CivicAuthorityStateError):
            encode_authority_state_replica(replica)


if __name__ == "__main__":
    unittest.main(verbosity=2)
