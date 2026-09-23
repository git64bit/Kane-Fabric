from __future__ import annotations

import copy
import hashlib
import unittest

from civic.ceremony import (
    FORMAT,
    MEDIA_TYPE,
    SEMANTIC_ROLE,
    VERSION,
    CivicCeremonyError,
    ceremony_record_sha256,
    decode_ceremony_record,
    encode_ceremony_record,
    verify_ceremony_record,
)
from civic.ecdsa import public_key_from_private_scalar
from civic.epoch_manifest import (
    CRYPTO_PROFILE,
    derive_key_id,
    manifest_sha256,
)
from civic.tests.test_epoch_manifest import P1, P2, fixture_manifest, h


P3 = public_key_from_private_scalar(3)
P4 = public_key_from_private_scalar(4)

POLICY_ID = "fixture-governance-policy-v1"
POLICY_SHA256 = h(40)
PROOF_HASHES = [h(41), h(42)]


def ceremony_from_manifest(
    manifest: dict[str, object],
    *,
    transition_kind: str = "bootstrap",
    governance_proof_sha256: list[bytes] | None = None,
) -> dict[str, object]:
    participants = manifest["participants"]
    operator = manifest["operator"]
    signing_node = manifest["signing_node"]

    assert isinstance(participants, list)
    assert isinstance(operator, dict)
    assert isinstance(signing_node, dict)

    return {
        "format": FORMAT,
        "version": VERSION,
        "crypto_profile": CRYPTO_PROFILE,
        "transition_kind": transition_kind,
        "hoa_root_id": manifest["hoa_root_id"],
        "epoch_sequence": manifest["epoch_sequence"],
        "predecessor_manifest_sha256": manifest[
            "predecessor_manifest_sha256"
        ],
        "effective_time_ms": manifest["effective_time_ms"],
        "governing_profile": copy.deepcopy(manifest["governing_profile"]),
        "participants": [
            {
                "participant_record_sha256": item[
                    "participant_record_sha256"
                ],
                "participant_key_id": item["participant_key_id"],
                "participant_public_key": item["participant_public_key"],
            }
            for item in participants
        ],
        "operator_participant_record_sha256": operator[
            "participant_record_sha256"
        ],
        "signing_node": {
            "key_id": signing_node["key_id"],
            "public_key": signing_node["public_key"],
        },
        "governance_policy": {
            "policy_id": POLICY_ID,
            "policy_sha256": POLICY_SHA256,
        },
        "governance_proof_sha256": (
            list(PROOF_HASHES)
            if governance_proof_sha256 is None
            else list(governance_proof_sha256)
        ),
    }


def bind_ceremony(
    manifest: dict[str, object],
    ceremony: dict[str, object],
    *,
    inline: bool = True,
) -> bytes:
    ceremony_bytes = encode_ceremony_record(ceremony)
    digest = hashlib.sha256(ceremony_bytes).digest()

    manifest_ceremony = manifest["ceremony"]
    object_index = manifest["object_index"]

    assert isinstance(manifest_ceremony, dict)
    assert isinstance(object_index, list)

    manifest_ceremony["ceremony_record_sha256"] = digest
    manifest_ceremony["governance_proof_sha256"] = list(
        ceremony["governance_proof_sha256"]  # type: ignore[arg-type]
    )

    object_index.append(
        {
            "sha256": digest,
            "byte_length": len(ceremony_bytes),
            "media_type": MEDIA_TYPE,
            "semantic_role": SEMANTIC_ROLE,
            "name": "ceremony.cbor",
            "cid": None,
            "inline": ceremony_bytes if inline else None,
        }
    )
    object_index.sort(key=lambda item: item["sha256"])

    return ceremony_bytes


def bootstrap_fixture() -> tuple[
    dict[str, object],
    dict[str, object],
    bytes,
]:
    manifest = fixture_manifest()
    ceremony = ceremony_from_manifest(manifest)
    ceremony_bytes = bind_ceremony(manifest, ceremony)
    return manifest, ceremony, ceremony_bytes


def successor_fixture() -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    bytes,
]:
    predecessor = fixture_manifest()

    successor = copy.deepcopy(predecessor)
    successor["epoch_sequence"] = 2
    successor["predecessor_manifest_sha256"] = manifest_sha256(predecessor)
    successor["effective_time_ms"] = predecessor["effective_time_ms"] + 1000  # type: ignore[operator]

    participant = successor["participants"][0]  # type: ignore[index]
    participant["participant_key_id"] = derive_key_id(P3)
    participant["participant_public_key"] = P3

    successor["ceremony"]["ceremony_record_sha256"] = h(60)  # type: ignore[index]
    successor["ceremony"]["governance_proof_sha256"] = list(PROOF_HASHES)  # type: ignore[index]

    ceremony = ceremony_from_manifest(
        successor,
        transition_kind="successor",
    )
    ceremony_bytes = bind_ceremony(successor, ceremony)

    return predecessor, successor, ceremony, ceremony_bytes


class CivicCeremonyTests(unittest.TestCase):
    def test_valid_bootstrap_round_trips_binds_manifest_and_exact_identity(self) -> None:
        manifest, ceremony, ceremony_bytes = bootstrap_fixture()

        self.assertEqual(
            ceremony,
            decode_ceremony_record(ceremony_bytes),
        )
        self.assertEqual(
            ceremony_bytes,
            encode_ceremony_record(
                decode_ceremony_record(ceremony_bytes)
            ),
        )
        self.assertEqual(
            hashlib.sha256(ceremony_bytes).digest(),
            ceremony_record_sha256(ceremony_bytes),
        )

        verified = verify_ceremony_record(
            ceremony_bytes,
            epoch_manifest=manifest,
        )

        self.assertEqual("bootstrap", verified.transition_kind)
        self.assertEqual(
            hashlib.sha256(ceremony_bytes).digest(),
            verified.ceremony_record_sha256,
        )
        self.assertEqual(POLICY_ID, verified.governance_policy_id)
        self.assertEqual(POLICY_SHA256, verified.governance_policy_sha256)
        self.assertEqual(tuple(PROOF_HASHES), verified.governance_proof_sha256)
        self.assertEqual(ceremony_bytes, verified.exact_bytes)

    def test_governance_proof_set_must_be_nonempty_sorted_and_unique(self) -> None:
        manifest = fixture_manifest()

        for proofs in (
            [],
            [h(42), h(41)],
            [h(41), h(41)],
        ):
            ceremony = ceremony_from_manifest(
                manifest,
                governance_proof_sha256=proofs,
            )
            with self.assertRaises(CivicCeremonyError):
                encode_ceremony_record(ceremony)

    def test_bootstrap_transition_shape_is_strict(self) -> None:
        manifest = fixture_manifest()

        wrong_sequence = ceremony_from_manifest(manifest)
        wrong_sequence["epoch_sequence"] = 2
        with self.assertRaises(CivicCeremonyError):
            encode_ceremony_record(wrong_sequence)

        wrong_predecessor = ceremony_from_manifest(manifest)
        wrong_predecessor["predecessor_manifest_sha256"] = h(50)
        with self.assertRaises(CivicCeremonyError):
            encode_ceremony_record(wrong_predecessor)

    def test_manifest_ceremony_hash_and_proof_set_are_exact_bindings(self) -> None:
        manifest, _, ceremony_bytes = bootstrap_fixture()

        wrong_hash = copy.deepcopy(manifest)
        wrong_hash["ceremony"]["ceremony_record_sha256"] = h(51)  # type: ignore[index]
        with self.assertRaises(CivicCeremonyError):
            verify_ceremony_record(
                ceremony_bytes,
                epoch_manifest=wrong_hash,
            )

        wrong_proofs = copy.deepcopy(manifest)
        wrong_proofs["ceremony"]["governance_proof_sha256"] = [  # type: ignore[index]
            h(41),
            h(43),
        ]
        with self.assertRaises(CivicCeremonyError):
            verify_ceremony_record(
                ceremony_bytes,
                epoch_manifest=wrong_proofs,
            )

    def test_object_index_descriptor_is_authority_binding(self) -> None:
        manifest, _, ceremony_bytes = bootstrap_fixture()

        descriptor = next(
            item
            for item in manifest["object_index"]  # type: ignore[union-attr]
            if item["sha256"] == hashlib.sha256(ceremony_bytes).digest()
        )

        wrong_media = copy.deepcopy(manifest)
        wrong_descriptor = next(
            item
            for item in wrong_media["object_index"]  # type: ignore[union-attr]
            if item["sha256"] == hashlib.sha256(ceremony_bytes).digest()
        )
        wrong_descriptor["media_type"] = "application/octet-stream"
        with self.assertRaises(CivicCeremonyError):
            verify_ceremony_record(
                ceremony_bytes,
                epoch_manifest=wrong_media,
            )

        missing = copy.deepcopy(manifest)
        missing["object_index"] = [  # type: ignore[index]
            item
            for item in missing["object_index"]  # type: ignore[union-attr]
            if item["sha256"] != descriptor["sha256"]
        ]
        with self.assertRaises(CivicCeremonyError):
            verify_ceremony_record(
                ceremony_bytes,
                epoch_manifest=missing,
            )

    def test_manifest_projection_mismatch_is_rejected(self) -> None:
        manifest, ceremony, _ = bootstrap_fixture()

        changed = copy.deepcopy(ceremony)
        changed["signing_node"] = {
            "key_id": derive_key_id(P4),
            "public_key": P4,
        }
        changed_bytes = encode_ceremony_record(changed)

        rebound_manifest = copy.deepcopy(manifest)
        old_digest = rebound_manifest["ceremony"]["ceremony_record_sha256"]  # type: ignore[index]
        new_digest = hashlib.sha256(changed_bytes).digest()
        rebound_manifest["ceremony"]["ceremony_record_sha256"] = new_digest  # type: ignore[index]

        for item in rebound_manifest["object_index"]:  # type: ignore[union-attr]
            if item["sha256"] == old_digest:
                item["sha256"] = new_digest
                item["byte_length"] = len(changed_bytes)
                item["inline"] = changed_bytes
                break
        rebound_manifest["object_index"].sort(key=lambda item: item["sha256"])  # type: ignore[union-attr]

        with self.assertRaises(CivicCeremonyError):
            verify_ceremony_record(
                changed_bytes,
                epoch_manifest=rebound_manifest,
            )

    def test_valid_successor_requires_predecessor_and_rotated_participant_key(self) -> None:
        predecessor, successor, _, ceremony_bytes = successor_fixture()

        verified = verify_ceremony_record(
            ceremony_bytes,
            epoch_manifest=successor,
            predecessor_manifest=predecessor,
        )
        self.assertEqual("successor", verified.transition_kind)
        self.assertEqual(2, verified.epoch_sequence)
        self.assertEqual(
            manifest_sha256(predecessor),
            verified.predecessor_manifest_sha256,
        )

        with self.assertRaises(CivicCeremonyError):
            verify_ceremony_record(
                ceremony_bytes,
                epoch_manifest=successor,
            )

    def test_successor_rejects_reused_continuing_participant_key(self) -> None:
        predecessor, successor, _, _ = successor_fixture()

        participant = successor["participants"][0]  # type: ignore[index]
        previous = predecessor["participants"][0]  # type: ignore[index]
        participant["participant_key_id"] = previous["participant_key_id"]
        participant["participant_public_key"] = previous[
            "participant_public_key"
        ]

        ceremony = ceremony_from_manifest(
            successor,
            transition_kind="successor",
        )

        successor["object_index"] = [  # type: ignore[index]
            item
            for item in successor["object_index"]  # type: ignore[union-attr]
            if item["semantic_role"] != SEMANTIC_ROLE
        ]
        ceremony_bytes = bind_ceremony(successor, ceremony)

        with self.assertRaises(CivicCeremonyError):
            verify_ceremony_record(
                ceremony_bytes,
                epoch_manifest=successor,
                predecessor_manifest=predecessor,
            )

    def test_successor_predecessor_identity_is_exact(self) -> None:
        predecessor, successor, _, ceremony_bytes = successor_fixture()

        wrong_predecessor = copy.deepcopy(predecessor)
        wrong_predecessor["effective_time_ms"] = predecessor[
            "effective_time_ms"
        ] + 1  # type: ignore[operator]

        with self.assertRaises(CivicCeremonyError):
            verify_ceremony_record(
                ceremony_bytes,
                epoch_manifest=successor,
                predecessor_manifest=wrong_predecessor,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
