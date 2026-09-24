from __future__ import annotations

import copy
import hashlib
import unittest

from civic.ceremony import verify_ceremony_record
from civic.cose import parse_cose_sign1
from civic.ecdsa import public_key_from_private_scalar
from civic.epoch_manifest import CRYPTO_PROFILE, derive_key_id, manifest_sha256
from civic.governance import (
    POLICY_FORMAT,
    POLICY_MEDIA_TYPE,
    POLICY_SEMANTIC_ROLE,
    POLICY_VERSION,
    PROOF_FORMAT,
    PROOF_MEDIA_TYPE,
    PROOF_SEMANTIC_ROLE,
    PROOF_VERSION,
    CivicGovernanceError,
    canonical_governance_transition_subject,
    decode_governance_policy,
    decode_governance_proof_payload,
    encode_governance_policy,
    encode_governance_proof_payload,
    encode_governance_transition_subject,
    governance_policy_sha256,
    governance_transition_subject_sha256,
    sign_governance_proof_fixture,
    validate_governance_policy,
    validate_governance_proof_payload,
    verify_governance_policy,
    verify_signed_governance_proof,
)
from civic.governing_profile import governing_source_set_sha256
from civic.tests.test_ceremony import (
    bind_ceremony,
    ceremony_from_manifest,
)
from civic.tests.test_epoch_manifest import P1, h
from civic.tests.test_governing_profile import (
    STANDING_CLASS,
    manifest_with_profile,
)


P3 = public_key_from_private_scalar(3)
POLICY_ID = "fixture-governance-policy-v1"


def provenance() -> dict[str, object]:
    return {
        "kind": "civic_mechanism",
        "source_ids": [],
    }


def policy_fixture(
    manifest: dict[str, object],
    *,
    transition_kind: str = "bootstrap",
    evidence_only: bool = False,
) -> dict[str, object]:
    basis = (
        "candidate_participants"
        if transition_kind == "bootstrap"
        else "predecessor_participants"
    )

    decision_rule: dict[str, object]
    authority_evidence: list[dict[str, object]]

    if evidence_only:
        decision_rule = {
            "quorum": None,
            "approval": None,
            "provenance": provenance(),
        }
        authority_evidence = [
            {
                "semantic_role": "governance-authority-evidence",
                "min_count": 1,
                "max_count": 1,
                "media_types": ["text/plain"],
                "provenance": provenance(),
            }
        ]
    else:
        decision_rule = {
            "quorum": {"kind": "all"},
            "approval": {"kind": "all"},
            "provenance": provenance(),
        }
        authority_evidence = []

    sources = manifest["governing_sources"]

    return {
        "format": POLICY_FORMAT,
        "version": POLICY_VERSION,
        "policy_id": POLICY_ID,
        "source_set_sha256": governing_source_set_sha256(sources),
        "transition_kinds": [transition_kind],
        "electorate": {
            "basis": basis,
            "standing_class": STANDING_CLASS,
            "membership_rule": "all_matching_standing_class",
            "weight_mode": "equal",
            "members": [
                {
                    "participant_record_sha256": h(16),
                    "weight": 1,
                }
            ],
            "operator_must_be_elector": True,
            "provenance": provenance(),
        },
        "decision_rule": decision_rule,
        "authority_evidence": authority_evidence,
        "supplementary_evidence": [],
        "provenance": provenance(),
    }


def proof_payload(
    *,
    subject_sha256: bytes,
    policy_sha256: bytes,
    participant_key_id: bytes,
    decision: str | None = "approve",
    authority_evidence: list[dict[str, object]] | None = None,
    supplementary_evidence: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "format": PROOF_FORMAT,
        "version": PROOF_VERSION,
        "crypto_profile": CRYPTO_PROFILE,
        "subject_sha256": subject_sha256,
        "governance_policy": {
            "policy_id": POLICY_ID,
            "policy_sha256": policy_sha256,
        },
        "signer": {
            "participant_record_sha256": h(16),
            "participant_key_id": participant_key_id,
        },
        "decision": decision,
        "authority_evidence": (
            [] if authority_evidence is None else authority_evidence
        ),
        "supplementary_evidence": (
            []
            if supplementary_evidence is None
            else supplementary_evidence
        ),
    }


def add_object(
    manifest: dict[str, object],
    *,
    data: bytes,
    media_type: str,
    semantic_role: str,
    name: str,
) -> bytes:
    digest = hashlib.sha256(data).digest()
    object_index = manifest["object_index"]
    assert isinstance(object_index, list)

    object_index.append(
        {
            "sha256": digest,
            "byte_length": len(data),
            "media_type": media_type,
            "semantic_role": semantic_role,
            "name": name,
            "cid": None,
            "inline": data,
        }
    )
    object_index.sort(key=lambda item: item["sha256"])
    return digest


def bootstrap_governance_fixture(
    *,
    evidence_only: bool = False,
    decision: str | None = "approve",
    proof_subject_sha256: bytes | None = None,
    proof_policy_sha256: bytes | None = None,
) -> tuple[
    dict[str, object],
    dict[str, object],
    bytes,
    bytes,
    bytes,
]:
    manifest, _, _ = manifest_with_profile()

    policy = policy_fixture(
        manifest,
        transition_kind="bootstrap",
        evidence_only=evidence_only,
    )
    policy_bytes = encode_governance_policy(
        policy,
        governing_sources=manifest["governing_sources"],
    )
    policy_digest = hashlib.sha256(policy_bytes).digest()

    ceremony = ceremony_from_manifest(
        manifest,
        transition_kind="bootstrap",
        governance_proof_sha256=[h(250)],
    )
    ceremony["governance_policy"] = {
        "policy_id": POLICY_ID,
        "policy_sha256": policy_digest,
    }

    subject_digest = governance_transition_subject_sha256(ceremony)

    authority_evidence: list[dict[str, object]] = []
    if evidence_only:
        evidence_bytes = b"fixture governance authority evidence\n"
        evidence_digest = add_object(
            manifest,
            data=evidence_bytes,
            media_type="text/plain",
            semantic_role="governance-authority-evidence",
            name="governance-authority.txt",
        )
        authority_evidence = [
            {
                "sha256": evidence_digest,
                "byte_length": len(evidence_bytes),
                "media_type": "text/plain",
                "semantic_role": "governance-authority-evidence",
            }
        ]

    payload = proof_payload(
        subject_sha256=(
            subject_digest
            if proof_subject_sha256 is None
            else proof_subject_sha256
        ),
        policy_sha256=(
            policy_digest
            if proof_policy_sha256 is None
            else proof_policy_sha256
        ),
        participant_key_id=derive_key_id(P1),
        decision=decision,
        authority_evidence=authority_evidence,
    )
    proof_bytes = sign_governance_proof_fixture(
        payload,
        expected_public_key=P1,
        private_scalar=1,
        nonce_scalar=7,
    )
    proof_digest = hashlib.sha256(proof_bytes).digest()

    ceremony["governance_proof_sha256"] = [proof_digest]
    ceremony_bytes = bind_ceremony(manifest, ceremony)

    add_object(
        manifest,
        data=policy_bytes,
        media_type=POLICY_MEDIA_TYPE,
        semantic_role=POLICY_SEMANTIC_ROLE,
        name="governance-policy.cbor",
    )
    add_object(
        manifest,
        data=proof_bytes,
        media_type=PROOF_MEDIA_TYPE,
        semantic_role=PROOF_SEMANTIC_ROLE,
        name="governance-proof.cose",
    )

    return (
        manifest,
        ceremony,
        ceremony_bytes,
        policy_bytes,
        proof_bytes,
    )


def successor_governance_fixture(
    *,
    proof_uses_successor_key: bool = False,
) -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    bytes,
    bytes,
    bytes,
]:
    predecessor, _, _ = manifest_with_profile()

    successor = copy.deepcopy(predecessor)
    successor["epoch_sequence"] = 2
    successor["predecessor_manifest_sha256"] = manifest_sha256(predecessor)
    successor["effective_time_ms"] = predecessor["effective_time_ms"] + 1000  # type: ignore[operator]

    successor_participant = successor["participants"][0]  # type: ignore[index]
    successor_participant["participant_key_id"] = derive_key_id(P3)
    successor_participant["participant_public_key"] = P3

    policy = policy_fixture(
        successor,
        transition_kind="successor",
    )
    policy_bytes = encode_governance_policy(
        policy,
        governing_sources=successor["governing_sources"],
    )
    policy_digest = hashlib.sha256(policy_bytes).digest()

    ceremony = ceremony_from_manifest(
        successor,
        transition_kind="successor",
        governance_proof_sha256=[h(250)],
    )
    ceremony["governance_policy"] = {
        "policy_id": POLICY_ID,
        "policy_sha256": policy_digest,
    }

    subject_digest = governance_transition_subject_sha256(ceremony)

    if proof_uses_successor_key:
        public_key = P3
        private_scalar = 3
        participant_key_id = derive_key_id(P3)
    else:
        public_key = P1
        private_scalar = 1
        participant_key_id = derive_key_id(P1)

    payload = proof_payload(
        subject_sha256=subject_digest,
        policy_sha256=policy_digest,
        participant_key_id=participant_key_id,
    )
    proof_bytes = sign_governance_proof_fixture(
        payload,
        expected_public_key=public_key,
        private_scalar=private_scalar,
        nonce_scalar=11,
    )
    proof_digest = hashlib.sha256(proof_bytes).digest()

    ceremony["governance_proof_sha256"] = [proof_digest]
    ceremony_bytes = bind_ceremony(successor, ceremony)

    add_object(
        successor,
        data=policy_bytes,
        media_type=POLICY_MEDIA_TYPE,
        semantic_role=POLICY_SEMANTIC_ROLE,
        name="governance-policy.cbor",
    )
    add_object(
        successor,
        data=proof_bytes,
        media_type=PROOF_MEDIA_TYPE,
        semantic_role=PROOF_SEMANTIC_ROLE,
        name="governance-proof.cose",
    )

    return (
        predecessor,
        successor,
        ceremony,
        ceremony_bytes,
        policy_bytes,
        proof_bytes,
    )


class CivicGovernancePrimitiveTests(unittest.TestCase):
    def test_transition_subject_is_canonical_and_excludes_proof_hashes(self) -> None:
        manifest, _, _ = manifest_with_profile()
        policy = policy_fixture(manifest)
        policy_bytes = encode_governance_policy(
            policy,
            governing_sources=manifest["governing_sources"],
        )
        policy_digest = hashlib.sha256(policy_bytes).digest()

        first = ceremony_from_manifest(
            manifest,
            governance_proof_sha256=[h(70)],
        )
        second = ceremony_from_manifest(
            manifest,
            governance_proof_sha256=[h(71)],
        )

        for ceremony in (first, second):
            ceremony["governance_policy"] = {
                "policy_id": POLICY_ID,
                "policy_sha256": policy_digest,
            }

        first_subject = canonical_governance_transition_subject(first)
        second_subject = canonical_governance_transition_subject(second)

        self.assertNotIn("governance_proof_sha256", first_subject)
        self.assertEqual(first_subject, second_subject)
        self.assertEqual(
            encode_governance_transition_subject(first),
            encode_governance_transition_subject(second),
        )
        self.assertEqual(
            governance_transition_subject_sha256(first),
            governance_transition_subject_sha256(second),
        )

    def test_policy_round_trips_hashes_and_binds_ceremony_object_descriptor(self) -> None:
        (
            manifest,
            _,
            ceremony_bytes,
            policy_bytes,
            _,
        ) = bootstrap_governance_fixture()

        decoded = decode_governance_policy(
            policy_bytes,
            governing_sources=manifest["governing_sources"],
        )
        self.assertEqual(
            policy_bytes,
            encode_governance_policy(
                decoded,
                governing_sources=manifest["governing_sources"],
            ),
        )
        self.assertEqual(
            hashlib.sha256(policy_bytes).digest(),
            governance_policy_sha256(
                policy_bytes,
                governing_sources=manifest["governing_sources"],
            ),
        )

        ceremony = verify_ceremony_record(
            ceremony_bytes,
            epoch_manifest=manifest,
        )
        verified = verify_governance_policy(
            policy_bytes,
            ceremony=ceremony,
            epoch_manifest=manifest,
        )

        self.assertEqual(POLICY_ID, verified.policy_id)
        self.assertEqual("candidate_participants", verified.electorate_basis)
        self.assertEqual(STANDING_CLASS, verified.electorate_standing_class)
        self.assertEqual("all", verified.quorum.kind)  # type: ignore[union-attr]
        self.assertEqual("all", verified.approval.kind)  # type: ignore[union-attr]

    def test_policy_rejects_source_set_and_quorum_fraction_errors(self) -> None:
        manifest, _, _ = manifest_with_profile()
        policy = policy_fixture(manifest)

        wrong_source = copy.deepcopy(policy)
        wrong_source["source_set_sha256"] = h(90)
        with self.assertRaises(CivicGovernanceError):
            validate_governance_policy(
                wrong_source,
                governing_sources=manifest["governing_sources"],
            )

        wrong_quorum = copy.deepcopy(policy)
        wrong_quorum["decision_rule"]["quorum"] = {  # type: ignore[index]
            "kind": "fraction_at_least",
            "numerator": 1,
            "denominator": 2,
            "base": "participating",
        }
        with self.assertRaises(CivicGovernanceError):
            validate_governance_policy(
                wrong_quorum,
                governing_sources=manifest["governing_sources"],
            )

    def test_bootstrap_signed_proof_binds_subject_policy_and_candidate_key(self) -> None:
        (
            manifest,
            _,
            ceremony_bytes,
            policy_bytes,
            proof_bytes,
        ) = bootstrap_governance_fixture()

        ceremony = verify_ceremony_record(
            ceremony_bytes,
            epoch_manifest=manifest,
        )
        policy = verify_governance_policy(
            policy_bytes,
            ceremony=ceremony,
            epoch_manifest=manifest,
        )

        proof_digest = hashlib.sha256(proof_bytes).digest()
        verified = verify_signed_governance_proof(
            proof_bytes,
            expected_proof_sha256=proof_digest,
            ceremony=ceremony,
            policy=policy,
            epoch_manifest=manifest,
        )

        self.assertEqual(h(16), verified.participant_record_sha256)
        self.assertEqual(derive_key_id(P1), verified.participant_key_id)
        self.assertEqual(P1, verified.participant_public_key)
        self.assertEqual("approve", verified.decision)
        self.assertEqual(
            governance_transition_subject_sha256(ceremony),
            verified.subject_sha256,
        )

        parsed = parse_cose_sign1(
            proof_bytes,
            expected_content_type="application/kane-civic-governance-proof+cbor",
        )
        decoded_payload = decode_governance_proof_payload(parsed.payload)
        self.assertEqual(verified.payload, decoded_payload)

    def test_proof_subject_and_policy_mismatches_are_rejected(self) -> None:
        for fixture_kwargs in (
            {"proof_subject_sha256": h(91)},
            {"proof_policy_sha256": h(92)},
        ):
            (
                manifest,
                _,
                ceremony_bytes,
                policy_bytes,
                proof_bytes,
            ) = bootstrap_governance_fixture(**fixture_kwargs)

            ceremony = verify_ceremony_record(
                ceremony_bytes,
                epoch_manifest=manifest,
            )
            policy = verify_governance_policy(
                policy_bytes,
                ceremony=ceremony,
                epoch_manifest=manifest,
            )

            with self.assertRaises(CivicGovernanceError):
                verify_signed_governance_proof(
                    proof_bytes,
                    expected_proof_sha256=hashlib.sha256(
                        proof_bytes
                    ).digest(),
                    ceremony=ceremony,
                    policy=policy,
                    epoch_manifest=manifest,
                )

    def test_proof_object_descriptor_media_type_is_authority_binding(self) -> None:
        (
            manifest,
            _,
            ceremony_bytes,
            policy_bytes,
            proof_bytes,
        ) = bootstrap_governance_fixture()

        ceremony = verify_ceremony_record(
            ceremony_bytes,
            epoch_manifest=manifest,
        )
        policy = verify_governance_policy(
            policy_bytes,
            ceremony=ceremony,
            epoch_manifest=manifest,
        )

        wrong = copy.deepcopy(manifest)
        proof_digest = hashlib.sha256(proof_bytes).digest()
        descriptor = next(
            item
            for item in wrong["object_index"]  # type: ignore[union-attr]
            if item["sha256"] == proof_digest
        )
        descriptor["media_type"] = "application/octet-stream"

        with self.assertRaises(CivicGovernanceError):
            verify_signed_governance_proof(
                proof_bytes,
                expected_proof_sha256=proof_digest,
                ceremony=ceremony,
                policy=policy,
                epoch_manifest=wrong,
            )

    def test_successor_proof_verifies_only_under_predecessor_participant_key(self) -> None:
        (
            predecessor,
            successor,
            _,
            ceremony_bytes,
            policy_bytes,
            proof_bytes,
        ) = successor_governance_fixture()

        ceremony = verify_ceremony_record(
            ceremony_bytes,
            epoch_manifest=successor,
            predecessor_manifest=predecessor,
        )
        policy = verify_governance_policy(
            policy_bytes,
            ceremony=ceremony,
            epoch_manifest=successor,
        )

        verified = verify_signed_governance_proof(
            proof_bytes,
            expected_proof_sha256=hashlib.sha256(proof_bytes).digest(),
            ceremony=ceremony,
            policy=policy,
            epoch_manifest=successor,
            predecessor_manifest=predecessor,
        )
        self.assertEqual(P1, verified.participant_public_key)
        self.assertNotEqual(
            successor["participants"][0]["participant_key_id"],  # type: ignore[index]
            verified.participant_key_id,
        )

        (
            predecessor,
            successor,
            _,
            ceremony_bytes,
            policy_bytes,
            wrong_proof_bytes,
        ) = successor_governance_fixture(
            proof_uses_successor_key=True,
        )

        ceremony = verify_ceremony_record(
            ceremony_bytes,
            epoch_manifest=successor,
            predecessor_manifest=predecessor,
        )
        policy = verify_governance_policy(
            policy_bytes,
            ceremony=ceremony,
            epoch_manifest=successor,
        )

        with self.assertRaises(CivicGovernanceError):
            verify_signed_governance_proof(
                wrong_proof_bytes,
                expected_proof_sha256=hashlib.sha256(
                    wrong_proof_bytes
                ).digest(),
                ceremony=ceremony,
                policy=policy,
                epoch_manifest=successor,
                predecessor_manifest=predecessor,
            )

    def test_evidence_only_policy_rejects_non_null_decision(self) -> None:
        (
            manifest,
            _,
            ceremony_bytes,
            policy_bytes,
            proof_bytes,
        ) = bootstrap_governance_fixture(
            evidence_only=True,
            decision="approve",
        )

        ceremony = verify_ceremony_record(
            ceremony_bytes,
            epoch_manifest=manifest,
        )
        policy = verify_governance_policy(
            policy_bytes,
            ceremony=ceremony,
            epoch_manifest=manifest,
        )

        self.assertIsNone(policy.approval)

        with self.assertRaises(CivicGovernanceError):
            verify_signed_governance_proof(
                proof_bytes,
                expected_proof_sha256=hashlib.sha256(
                    proof_bytes
                ).digest(),
                ceremony=ceremony,
                policy=policy,
                epoch_manifest=manifest,
            )

    def test_proof_payload_rejects_duplicate_evidence_identity_across_classes(self) -> None:
        evidence_digest = h(100)
        descriptor = {
            "sha256": evidence_digest,
            "byte_length": 5,
            "media_type": "text/plain",
            "semantic_role": "fixture-evidence",
        }
        payload = proof_payload(
            subject_sha256=h(101),
            policy_sha256=h(102),
            participant_key_id=derive_key_id(P1),
            authority_evidence=[copy.deepcopy(descriptor)],
            supplementary_evidence=[copy.deepcopy(descriptor)],
        )

        with self.assertRaises(CivicGovernanceError):
            validate_governance_proof_payload(payload)

        payload["supplementary_evidence"] = []
        encoded = encode_governance_proof_payload(payload)
        self.assertEqual(
            payload,
            decode_governance_proof_payload(encoded),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
