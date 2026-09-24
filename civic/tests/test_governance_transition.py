from __future__ import annotations

import copy
import hashlib
import unittest

from civic.accepted_participant_standing import RECORD_TYPE
from civic.ceremony import verify_ceremony_record
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
    encode_governance_policy,
    governance_transition_subject_sha256,
    sign_governance_proof_fixture,
    verify_governance_policy,
    verify_governance_transition,
)
from civic.governing_profile import (
    PROFILE_MEDIA_TYPE,
    PROFILE_SEMANTIC_ROLE,
)
from civic.signed_history_record import (
    sign_history_record_fixture,
    verify_signed_history_record,
)
from civic.tests.test_accepted_participant_standing import (
    GOVERNING_SOURCES,
    PARTICIPATION_POLICY,
    PROFILE_BYTES,
    PROFILE_ID,
    PROFILE_SHA256,
    QUALIFICATION_BYTES,
    QUALIFICATION_PATH,
    QUALIFICATION_SHA256,
    SOURCE_BYTES,
    SOURCE_SHA256,
    SOURCE_SET_SHA256,
    STANDING_CLASS,
    VALID_FROM_MS,
    VALID_UNTIL_MS,
)
from civic.tests.test_ceremony import (
    bind_ceremony,
    ceremony_from_manifest,
)
from civic.tests.test_epoch_manifest import P1, fixture_manifest, h


P3 = public_key_from_private_scalar(3)

POLICY_ID = "fixture-governance-transition-v1"
GOVERNANCE_EVIDENCE_BYTES = b"fixture governance authority evidence\n"
GOVERNANCE_EVIDENCE_SHA256 = hashlib.sha256(
    GOVERNANCE_EVIDENCE_BYTES
).digest()

BOOTSTRAP_EFFECTIVE_TIME_MS = VALID_FROM_MS + 300_000
PREDECESSOR_EFFECTIVE_TIME_MS = VALID_FROM_MS + 100_000
SUCCESSOR_EFFECTIVE_TIME_MS = VALID_FROM_MS + 300_000


def provenance() -> dict[str, object]:
    return {
        "kind": "civic_mechanism",
        "source_ids": [],
    }


def object_descriptor(
    *,
    data: bytes,
    media_type: str,
    semantic_role: str,
    name: str,
    inline: bool = True,
) -> dict[str, object]:
    return {
        "sha256": hashlib.sha256(data).digest(),
        "byte_length": len(data),
        "media_type": media_type,
        "semantic_role": semantic_role,
        "name": name,
        "cid": None,
        "inline": data if inline else None,
    }


def evidence_descriptor(
    *,
    data: bytes,
    media_type: str,
    semantic_role: str,
) -> dict[str, object]:
    return {
        "sha256": hashlib.sha256(data).digest(),
        "byte_length": len(data),
        "media_type": media_type,
        "semantic_role": semantic_role,
    }


def add_object(
    manifest: dict[str, object],
    *,
    data: bytes,
    media_type: str,
    semantic_role: str,
    name: str,
    inline: bool = True,
) -> bytes:
    descriptor = object_descriptor(
        data=data,
        media_type=media_type,
        semantic_role=semantic_role,
        name=name,
        inline=inline,
    )
    object_index = manifest["object_index"]
    assert isinstance(object_index, list)
    object_index.append(descriptor)
    object_index.sort(key=lambda item: item["sha256"])
    return descriptor["sha256"]  # type: ignore[return-value]


def authority_manifest(
    *,
    effective_time_ms: int,
) -> dict[str, object]:
    manifest = fixture_manifest()
    manifest["effective_time_ms"] = effective_time_ms
    manifest["governing_profile"] = {
        "profile_id": PROFILE_ID,
        "profile_sha256": PROFILE_SHA256,
        "source_set_sha256": SOURCE_SET_SHA256,
    }
    manifest["governing_sources"] = [
        dict(source)
        for source in GOVERNING_SOURCES
    ]

    add_object(
        manifest,
        data=PROFILE_BYTES,
        media_type=PROFILE_MEDIA_TYPE,
        semantic_role=PROFILE_SEMANTIC_ROLE,
        name="governance-transition-profile.cbor",
    )
    add_object(
        manifest,
        data=SOURCE_BYTES,
        media_type="text/plain",
        semantic_role="governing-source",
        name="governing-source.txt",
    )
    add_object(
        manifest,
        data=QUALIFICATION_BYTES,
        media_type="text/plain",
        semantic_role="standing-qualification-evidence",
        name="qualification-evidence.txt",
    )

    return manifest


def policy_fixture(
    manifest: dict[str, object],
    *,
    transition_kind: str,
    approval: dict[str, object] | None = None,
    quorum: dict[str, object] | None = None,
    evidence_min_count: int = 0,
) -> dict[str, object]:
    basis = (
        "candidate_participants"
        if transition_kind == "bootstrap"
        else "predecessor_participants"
    )

    if approval is None and evidence_min_count == 0:
        approval = {"kind": "all"}

    authority_evidence = (
        [
            {
                "semantic_role": "governance-authority-evidence",
                "min_count": evidence_min_count,
                "max_count": None,
                "media_types": ["text/plain"],
                "provenance": provenance(),
            }
        ]
        if evidence_min_count > 0
        else []
    )

    return {
        "format": POLICY_FORMAT,
        "version": POLICY_VERSION,
        "policy_id": POLICY_ID,
        "source_set_sha256": manifest["governing_profile"][
            "source_set_sha256"
        ],  # type: ignore[index]
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
        "decision_rule": {
            "quorum": quorum,
            "approval": approval,
            "provenance": provenance(),
        },
        "authority_evidence": authority_evidence,
        "supplementary_evidence": [],
        "provenance": provenance(),
    }


def proof_payload(
    *,
    subject_sha256: bytes,
    policy_sha256: bytes,
    participant_key_id: bytes,
    decision: str | None,
    authority_evidence: list[dict[str, object]] | None = None,
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
        "supplementary_evidence": [],
    }


def make_standing_record(
    manifest: dict[str, object],
    *,
    valid_until_ms: int = VALID_UNTIL_MS,
) -> object:
    payload = {
        "format": "kane-civic-history-record",
        "version": 1,
        "crypto_profile": CRYPTO_PROFILE,
        "hoa_root_id": manifest["hoa_root_id"],
        "epoch_sequence": manifest["epoch_sequence"],
        "ceremony_record_sha256": manifest["ceremony"][
            "ceremony_record_sha256"
        ],  # type: ignore[index]
        "record_type": RECORD_TYPE,
        "history_link": {
            "stream": "accepted",
            "predecessor_record_sha256": None,
        },
        "signer": {
            "kind": "participant",
            "key_id": derive_key_id(P1),
            "participant_record_sha256": h(16),
        },
        "body": {
            "participant_record_sha256": h(16),
            "governing_profile": copy.deepcopy(
                manifest["governing_profile"]
            ),
            "standing_class": STANDING_CLASS,
            "valid_from_ms": VALID_FROM_MS,
            "valid_until_ms": valid_until_ms,
            "participation": {
                "required": True,
                "policy_id": PARTICIPATION_POLICY,
                "valid_from_ms": VALID_FROM_MS,
                "valid_until_ms": valid_until_ms,
                "authority_evidence": [],
                "supplementary_evidence": [],
            },
            "qualification": {
                "path_id": QUALIFICATION_PATH,
                "claim_responsibility": "participant_claimed",
                "authority_evidence": [
                    evidence_descriptor(
                        data=QUALIFICATION_BYTES,
                        media_type="text/plain",
                        semantic_role="standing-qualification-evidence",
                    )
                ],
                "supplementary_evidence": [],
            },
            "recording_operator_participant_record_sha256": h(16),
        },
    }

    signed = sign_history_record_fixture(
        payload,
        epoch_manifest=manifest,
        private_scalar=1,
        nonce_scalar=47,
    )
    digest = hashlib.sha256(signed).digest()

    participant = manifest["participants"][0]  # type: ignore[index]
    participant["standing_record_sha256"] = digest

    return verify_signed_history_record(
        signed,
        epoch_manifests=[manifest],
    )


def empty_loader(_: bytes) -> bytes:
    raise KeyError("all test authority objects are inline")


def build_bootstrap_transition(
    *,
    decisions: list[str | None],
    nonces: list[int] | None = None,
    approval: dict[str, object] | None = None,
    quorum: dict[str, object] | None = None,
    evidence_min_count: int = 0,
    include_governance_evidence: bool = False,
    standing_valid_until_ms: int = VALID_UNTIL_MS,
) -> tuple[
    dict[str, object],
    object,
    object,
    list[bytes],
    list[object],
]:
    if nonces is None:
        nonces = [
            101 + index
            for index in range(len(decisions))
        ]
    if len(nonces) != len(decisions):
        raise AssertionError("nonce count must match decision count")

    manifest = authority_manifest(
        effective_time_ms=BOOTSTRAP_EFFECTIVE_TIME_MS,
    )
    policy_value = policy_fixture(
        manifest,
        transition_kind="bootstrap",
        approval=approval,
        quorum=quorum,
        evidence_min_count=evidence_min_count,
    )
    policy_bytes = encode_governance_policy(
        policy_value,
        governing_sources=manifest["governing_sources"],
    )
    policy_digest = hashlib.sha256(policy_bytes).digest()

    ceremony_value = ceremony_from_manifest(
        manifest,
        transition_kind="bootstrap",
        governance_proof_sha256=[h(250)],
    )
    ceremony_value["governance_policy"] = {
        "policy_id": POLICY_ID,
        "policy_sha256": policy_digest,
    }

    subject_sha256 = governance_transition_subject_sha256(
        ceremony_value
    )

    governance_evidence: list[dict[str, object]] = []
    if include_governance_evidence:
        add_object(
            manifest,
            data=GOVERNANCE_EVIDENCE_BYTES,
            media_type="text/plain",
            semantic_role="governance-authority-evidence",
            name="governance-authority-evidence.txt",
        )
        governance_evidence = [
            evidence_descriptor(
                data=GOVERNANCE_EVIDENCE_BYTES,
                media_type="text/plain",
                semantic_role="governance-authority-evidence",
            )
        ]

    proof_bytes: list[bytes] = []

    for decision, nonce in zip(decisions, nonces):
        payload = proof_payload(
            subject_sha256=subject_sha256,
            policy_sha256=policy_digest,
            participant_key_id=derive_key_id(P1),
            decision=decision,
            authority_evidence=governance_evidence,
        )
        proof_bytes.append(
            sign_governance_proof_fixture(
                payload,
                expected_public_key=P1,
                private_scalar=1,
                nonce_scalar=nonce,
            )
        )

    proof_hashes = sorted(
        hashlib.sha256(item).digest()
        for item in proof_bytes
    )
    ceremony_value["governance_proof_sha256"] = proof_hashes

    ceremony_bytes = bind_ceremony(
        manifest,
        ceremony_value,
    )

    add_object(
        manifest,
        data=policy_bytes,
        media_type=POLICY_MEDIA_TYPE,
        semantic_role=POLICY_SEMANTIC_ROLE,
        name="governance-policy.cbor",
    )

    for index, exact_bytes in enumerate(proof_bytes):
        add_object(
            manifest,
            data=exact_bytes,
            media_type=PROOF_MEDIA_TYPE,
            semantic_role=PROOF_SEMANTIC_ROLE,
            name=f"governance-proof-{index}.cose",
        )

    standing = make_standing_record(
        manifest,
        valid_until_ms=standing_valid_until_ms,
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

    return manifest, ceremony, policy, proof_bytes, [standing]


def build_successor_transition() -> tuple[
    dict[str, object],
    dict[str, object],
    object,
    object,
    list[bytes],
    list[object],
]:
    predecessor = authority_manifest(
        effective_time_ms=PREDECESSOR_EFFECTIVE_TIME_MS,
    )
    predecessor_standing = make_standing_record(predecessor)

    successor = copy.deepcopy(predecessor)
    successor["epoch_sequence"] = 2
    successor["predecessor_manifest_sha256"] = manifest_sha256(
        predecessor
    )
    successor["effective_time_ms"] = SUCCESSOR_EFFECTIVE_TIME_MS

    participant = successor["participants"][0]  # type: ignore[index]
    participant["participant_key_id"] = derive_key_id(P3)
    participant["participant_public_key"] = P3

    policy_value = policy_fixture(
        successor,
        transition_kind="successor",
        approval={"kind": "all"},
        quorum={"kind": "all"},
    )
    policy_bytes = encode_governance_policy(
        policy_value,
        governing_sources=successor["governing_sources"],
    )
    policy_digest = hashlib.sha256(policy_bytes).digest()

    ceremony_value = ceremony_from_manifest(
        successor,
        transition_kind="successor",
        governance_proof_sha256=[h(250)],
    )
    ceremony_value["governance_policy"] = {
        "policy_id": POLICY_ID,
        "policy_sha256": policy_digest,
    }

    subject_sha256 = governance_transition_subject_sha256(
        ceremony_value
    )
    payload = proof_payload(
        subject_sha256=subject_sha256,
        policy_sha256=policy_digest,
        participant_key_id=derive_key_id(P1),
        decision="approve",
    )
    proof_bytes = sign_governance_proof_fixture(
        payload,
        expected_public_key=P1,
        private_scalar=1,
        nonce_scalar=131,
    )

    ceremony_value["governance_proof_sha256"] = [
        hashlib.sha256(proof_bytes).digest()
    ]
    ceremony_bytes = bind_ceremony(
        successor,
        ceremony_value,
    )

    add_object(
        successor,
        data=policy_bytes,
        media_type=POLICY_MEDIA_TYPE,
        semantic_role=POLICY_SEMANTIC_ROLE,
        name="successor-governance-policy.cbor",
    )
    add_object(
        successor,
        data=proof_bytes,
        media_type=PROOF_MEDIA_TYPE,
        semantic_role=PROOF_SEMANTIC_ROLE,
        name="successor-governance-proof.cose",
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

    return (
        predecessor,
        successor,
        ceremony,
        policy,
        [proof_bytes],
        [predecessor_standing],
    )


class CivicGovernanceTransitionTests(unittest.TestCase):
    def test_valid_bootstrap_reconstructs_electorate_and_authorizes_transition(self) -> None:
        (
            manifest,
            ceremony,
            policy,
            proofs,
            standing,
        ) = build_bootstrap_transition(
            decisions=["approve"],
            quorum={"kind": "all"},
            approval={"kind": "all"},
        )

        result = verify_governance_transition(
            policy=policy,
            ceremony=ceremony,
            governance_proof_bytes=proofs,
            candidate_manifest=manifest,
            standing_records=standing,
            load_object=empty_loader,
        )

        self.assertEqual("bootstrap", result.transition_kind)
        self.assertEqual((h(16),), tuple(
            member.participant_record_sha256
            for member in result.electorate_members
        ))
        self.assertEqual((h(16),), result.participating_participant_record_sha256)
        self.assertEqual((h(16),), result.approving_participant_record_sha256)
        self.assertEqual(1, result.total_electorate_weight)
        self.assertEqual(1, result.participating_weight)
        self.assertEqual(1, result.approving_weight)
        self.assertTrue(result.quorum_result)
        self.assertTrue(result.approval_result)

    def test_expired_standing_is_excluded_and_policy_electorate_mismatch_fails(self) -> None:
        (
            manifest,
            ceremony,
            policy,
            proofs,
            standing,
        ) = build_bootstrap_transition(
            decisions=["approve"],
            standing_valid_until_ms=(
                BOOTSTRAP_EFFECTIVE_TIME_MS - 1
            ),
        )

        with self.assertRaises(CivicGovernanceError):
            verify_governance_transition(
                policy=policy,
                ceremony=ceremony,
                governance_proof_bytes=proofs,
                candidate_manifest=manifest,
                standing_records=standing,
                load_object=empty_loader,
            )

    def test_provided_proof_set_must_exactly_equal_ceremony(self) -> None:
        (
            manifest,
            ceremony,
            policy,
            proofs,
            standing,
        ) = build_bootstrap_transition(
            decisions=["approve"],
        )

        with self.assertRaises(CivicGovernanceError):
            verify_governance_transition(
                policy=policy,
                ceremony=ceremony,
                governance_proof_bytes=[],
                candidate_manifest=manifest,
                standing_records=standing,
                load_object=empty_loader,
            )

        self.assertEqual(1, len(proofs))

    def test_duplicate_non_null_decisions_from_one_participant_fail(self) -> None:
        (
            manifest,
            ceremony,
            policy,
            proofs,
            standing,
        ) = build_bootstrap_transition(
            decisions=["approve", "approve"],
            nonces=[151, 157],
            quorum={"kind": "all"},
            approval={"kind": "all"},
        )

        with self.assertRaises(CivicGovernanceError):
            verify_governance_transition(
                policy=policy,
                ceremony=ceremony,
                governance_proof_bytes=proofs,
                candidate_manifest=manifest,
                standing_records=standing,
                load_object=empty_loader,
            )

    def test_duplicate_authority_evidence_across_proofs_counts_once(self) -> None:
        (
            manifest,
            ceremony,
            policy,
            proofs,
            standing,
        ) = build_bootstrap_transition(
            decisions=[None, None],
            nonces=[163, 167],
            approval=None,
            quorum=None,
            evidence_min_count=2,
            include_governance_evidence=True,
        )

        with self.assertRaises(CivicGovernanceError):
            verify_governance_transition(
                policy=policy,
                ceremony=ceremony,
                governance_proof_bytes=proofs,
                candidate_manifest=manifest,
                standing_records=standing,
                load_object=empty_loader,
            )

    def test_evidence_only_transition_succeeds_with_one_exact_authority_object(self) -> None:
        (
            manifest,
            ceremony,
            policy,
            proofs,
            standing,
        ) = build_bootstrap_transition(
            decisions=[None, None],
            nonces=[173, 179],
            approval=None,
            quorum=None,
            evidence_min_count=1,
            include_governance_evidence=True,
        )

        result = verify_governance_transition(
            policy=policy,
            ceremony=ceremony,
            governance_proof_bytes=proofs,
            candidate_manifest=manifest,
            standing_records=standing,
            load_object=empty_loader,
        )

        self.assertIsNone(result.quorum_result)
        self.assertIsNone(result.approval_result)
        self.assertEqual((), result.participating_participant_record_sha256)
        self.assertEqual(1, len(result.verified_authority_evidence))
        self.assertEqual(
            GOVERNANCE_EVIDENCE_SHA256,
            result.verified_authority_evidence[0].sha256,
        )

    def test_quorum_failure_is_distinct_from_proof_signature_validity(self) -> None:
        (
            manifest,
            ceremony,
            policy,
            proofs,
            standing,
        ) = build_bootstrap_transition(
            decisions=[None],
            quorum={"kind": "all"},
            approval={"kind": "all"},
        )

        with self.assertRaises(CivicGovernanceError):
            verify_governance_transition(
                policy=policy,
                ceremony=ceremony,
                governance_proof_bytes=proofs,
                candidate_manifest=manifest,
                standing_records=standing,
                load_object=empty_loader,
            )

    def test_approval_failure_after_quorum_is_rejected(self) -> None:
        (
            manifest,
            ceremony,
            policy,
            proofs,
            standing,
        ) = build_bootstrap_transition(
            decisions=["reject"],
            quorum={"kind": "all"},
            approval={"kind": "all"},
        )

        with self.assertRaises(CivicGovernanceError):
            verify_governance_transition(
                policy=policy,
                ceremony=ceremony,
                governance_proof_bytes=proofs,
                candidate_manifest=manifest,
                standing_records=standing,
                load_object=empty_loader,
            )

    def test_successor_reconstructs_electorate_from_predecessor_standing_and_key(self) -> None:
        (
            predecessor,
            successor,
            ceremony,
            policy,
            proofs,
            standing,
        ) = build_successor_transition()

        result = verify_governance_transition(
            policy=policy,
            ceremony=ceremony,
            governance_proof_bytes=proofs,
            candidate_manifest=successor,
            predecessor_manifest=predecessor,
            standing_records=standing,
            load_object=empty_loader,
        )

        self.assertEqual("successor", result.transition_kind)
        self.assertEqual((h(16),), result.approving_participant_record_sha256)
        self.assertEqual(derive_key_id(P1), result.verified_proofs[0].participant_key_id)
        self.assertNotEqual(
            successor["participants"][0]["participant_key_id"],  # type: ignore[index]
            result.verified_proofs[0].participant_key_id,
        )
        self.assertTrue(result.quorum_result)
        self.assertTrue(result.approval_result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
