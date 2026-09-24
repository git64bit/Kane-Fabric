from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
from pathlib import Path
import tempfile
import unittest

from civic.accepted_operator_selection import (
    RECORD_TYPE as OPERATOR_SELECTION_RECORD_TYPE,
)
from civic.accepted_participant_issuance import (
    RECORD_TYPE as PARTICIPANT_ISSUANCE_RECORD_TYPE,
)
from civic.accepted_participant_standing import (
    RECORD_TYPE as PARTICIPANT_STANDING_RECORD_TYPE,
)
from civic.accepted_signing_node_authorization import (
    RECORD_TYPE as SIGNING_NODE_AUTHORIZATION_RECORD_TYPE,
)
from civic.authority_transaction import (
    AcceptedStateSelection,
    CivicAuthorityTransactionError,
    FileAcceptedStateSelector,
    VerifiedAuthorityCandidate,
    VerifiedAuthorityState,
    build_candidate_authority_state_replica,
    commit_verified_candidate,
    compose_reference_accepted_history,
    object_store_loader,
    persist_immutable_objects,
    selection_for_state,
    verify_persisted_transition_candidate,
)
from civic.cose import HISTORY_RECORD_CONTENT_TYPE, parse_cose_sign1
from civic.ecdsa import public_key_from_private_scalar
from civic.epoch_manifest import CRYPTO_PROFILE, derive_key_id, manifest_sha256
from civic.governance import (
    POLICY_MEDIA_TYPE,
    POLICY_SEMANTIC_ROLE,
    PROOF_MEDIA_TYPE,
    PROOF_SEMANTIC_ROLE,
    encode_governance_policy,
    governance_transition_subject_sha256,
    sign_governance_proof_fixture,
)
from civic.history import decode_history_sequence
from civic.object_store import object_path
from civic.signed_history_record import (
    decode_history_record_payload,
    sign_history_record_fixture,
)
from civic.signed_manifest import sign_epoch_manifest_fixture
from civic.tests.test_accepted_participant_standing import (
    PARTICIPATION_POLICY,
    QUALIFICATION_BYTES,
    QUALIFICATION_PATH,
    STANDING_CLASS,
    VALID_FROM_MS,
    VALID_UNTIL_MS,
)
from civic.tests.test_ceremony import (
    bind_ceremony,
    ceremony_from_manifest,
)
from civic.tests.test_epoch_manifest import P1, P2, h
from civic.tests.test_governance_transition import (
    POLICY_ID,
    add_object,
    authority_manifest,
    evidence_descriptor,
    policy_fixture,
    proof_payload,
)


P3 = public_key_from_private_scalar(3)

BOOTSTRAP_EFFECTIVE_TIME_MS = VALID_FROM_MS + 100_000
SUCCESSOR_EFFECTIVE_TIME_MS = VALID_FROM_MS + 200_000


@dataclass(frozen=True)
class CandidateFixture:
    manifest: dict[str, object]
    signed_manifest_bytes: bytes
    accepted_history_bytes: bytes
    replica_bytes: bytes
    replica_sha256: bytes


def _participant_private_scalar(manifest: dict[str, object]) -> int:
    participant = manifest["participants"][0]  # type: ignore[index]
    public_key = participant["participant_public_key"]
    if public_key == P1:
        return 1
    if public_key == P3:
        return 3
    raise AssertionError("unsupported fixture participant public key")


def _history_payload(
    manifest: dict[str, object],
    *,
    record_type: str,
    predecessor_record_sha256: bytes | None,
    signer_kind: str,
    body: dict[str, object],
) -> dict[str, object]:
    ceremony = manifest["ceremony"]
    signing_node = manifest["signing_node"]
    participant = manifest["participants"][0]  # type: ignore[index]
    assert isinstance(ceremony, dict)
    assert isinstance(signing_node, dict)

    if signer_kind == "signing_node":
        signer = {
            "kind": "signing_node",
            "key_id": signing_node["key_id"],
            "participant_record_sha256": None,
        }
    elif signer_kind == "participant":
        signer = {
            "kind": "participant",
            "key_id": participant["participant_key_id"],
            "participant_record_sha256": participant[
                "participant_record_sha256"
            ],
        }
    else:
        raise AssertionError("unsupported signer kind")

    return {
        "format": "kane-civic-history-record",
        "version": 1,
        "crypto_profile": CRYPTO_PROFILE,
        "hoa_root_id": manifest["hoa_root_id"],
        "epoch_sequence": manifest["epoch_sequence"],
        "ceremony_record_sha256": ceremony[
            "ceremony_record_sha256"
        ],
        "record_type": record_type,
        "history_link": {
            "stream": "accepted",
            "predecessor_record_sha256": (
                predecessor_record_sha256
            ),
        },
        "signer": signer,
        "body": body,
    }


def _sign_record(
    manifest: dict[str, object],
    *,
    payload: dict[str, object],
    signer_kind: str,
    nonce_scalar: int,
) -> bytes:
    private_scalar = (
        2
        if signer_kind == "signing_node"
        else _participant_private_scalar(manifest)
    )
    return sign_history_record_fixture(
        payload,
        epoch_manifest=manifest,
        private_scalar=private_scalar,
        nonce_scalar=nonce_scalar,
    )


def _standing_body(
    manifest: dict[str, object],
) -> dict[str, object]:
    participant = manifest["participants"][0]  # type: ignore[index]
    operator = manifest["operator"]
    assert isinstance(operator, dict)

    return {
        "participant_record_sha256": participant[
            "participant_record_sha256"
        ],
        "governing_profile": copy.deepcopy(
            manifest["governing_profile"]
        ),
        "standing_class": STANDING_CLASS,
        "valid_from_ms": VALID_FROM_MS,
        "valid_until_ms": VALID_UNTIL_MS,
        "participation": {
            "required": True,
            "policy_id": PARTICIPATION_POLICY,
            "valid_from_ms": VALID_FROM_MS,
            "valid_until_ms": VALID_UNTIL_MS,
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
                    semantic_role=(
                        "standing-qualification-evidence"
                    ),
                )
            ],
            "supplementary_evidence": [],
        },
        "recording_operator_participant_record_sha256": operator[
            "participant_record_sha256"
        ],
    }


def _finalize_governance(
    manifest: dict[str, object],
    *,
    transition_kind: str,
    proof_nonce: int,
) -> tuple[bytes, bytes, bytes]:
    policy_value = policy_fixture(
        manifest,
        transition_kind=transition_kind,
        approval={"kind": "all"},
        quorum={"kind": "all"},
    )
    policy_bytes = encode_governance_policy(
        policy_value,
        governing_sources=manifest["governing_sources"],
    )
    policy_sha256 = hashlib.sha256(policy_bytes).digest()

    ceremony_value = ceremony_from_manifest(
        manifest,
        transition_kind=transition_kind,
        governance_proof_sha256=[h(250)],
    )
    ceremony_value["governance_policy"] = {
        "policy_id": POLICY_ID,
        "policy_sha256": policy_sha256,
    }

    subject_sha256 = governance_transition_subject_sha256(
        ceremony_value
    )

    proof_public_key = (
        P1
        if transition_kind in {"bootstrap", "successor"}
        else None
    )
    assert proof_public_key is not None

    proof = sign_governance_proof_fixture(
        proof_payload(
            subject_sha256=subject_sha256,
            policy_sha256=policy_sha256,
            participant_key_id=derive_key_id(P1),
            decision="approve",
        ),
        expected_public_key=proof_public_key,
        private_scalar=1,
        nonce_scalar=proof_nonce,
    )
    proof_sha256 = hashlib.sha256(proof).digest()

    ceremony_value["governance_proof_sha256"] = [
        proof_sha256
    ]
    ceremony_bytes = bind_ceremony(
        manifest,
        ceremony_value,
    )

    add_object(
        manifest,
        data=policy_bytes,
        media_type=POLICY_MEDIA_TYPE,
        semantic_role=POLICY_SEMANTIC_ROLE,
        name=f"{transition_kind}-governance-policy.cbor",
    )
    add_object(
        manifest,
        data=proof,
        media_type=PROOF_MEDIA_TYPE,
        semantic_role=PROOF_SEMANTIC_ROLE,
        name=f"{transition_kind}-governance-proof.cose",
    )

    return ceremony_bytes, policy_bytes, proof


def _compose_epoch_records(
    manifest: dict[str, object],
    *,
    predecessor_sequence: bytes,
    predecessor_head_sha256: bytes | None,
    nonce_base: int,
) -> bytes:
    ceremony = manifest["ceremony"]
    signing_node = manifest["signing_node"]
    operator = manifest["operator"]
    participant = manifest["participants"][0]  # type: ignore[index]

    assert isinstance(ceremony, dict)
    assert isinstance(signing_node, dict)
    assert isinstance(operator, dict)

    proof_hashes = list(
        ceremony["governance_proof_sha256"]
    )

    authorization = _sign_record(
        manifest,
        payload=_history_payload(
            manifest,
            record_type=SIGNING_NODE_AUTHORIZATION_RECORD_TYPE,
            predecessor_record_sha256=predecessor_head_sha256,
            signer_kind="signing_node",
            body={
                "authorized_key_id": signing_node["key_id"],
                "authorized_public_key": signing_node[
                    "public_key"
                ],
                "governance_proof_sha256": proof_hashes,
            },
        ),
        signer_kind="signing_node",
        nonce_scalar=nonce_base,
    )
    authorization_sha256 = hashlib.sha256(
        authorization
    ).digest()

    selection = _sign_record(
        manifest,
        payload=_history_payload(
            manifest,
            record_type=OPERATOR_SELECTION_RECORD_TYPE,
            predecessor_record_sha256=authorization_sha256,
            signer_kind="participant",
            body={
                "selected_participant_record_sha256": operator[
                    "participant_record_sha256"
                ],
                "selection_proof_sha256": proof_hashes,
            },
        ),
        signer_kind="participant",
        nonce_scalar=nonce_base + 1,
    )
    selection_sha256 = hashlib.sha256(selection).digest()

    standing = _sign_record(
        manifest,
        payload=_history_payload(
            manifest,
            record_type=PARTICIPANT_STANDING_RECORD_TYPE,
            predecessor_record_sha256=selection_sha256,
            signer_kind="participant",
            body=_standing_body(manifest),
        ),
        signer_kind="participant",
        nonce_scalar=nonce_base + 2,
    )
    standing_sha256 = hashlib.sha256(standing).digest()

    issuance = _sign_record(
        manifest,
        payload=_history_payload(
            manifest,
            record_type=PARTICIPANT_ISSUANCE_RECORD_TYPE,
            predecessor_record_sha256=standing_sha256,
            signer_kind="participant",
            body={
                "participant_record_sha256": participant[
                    "participant_record_sha256"
                ],
                "participant_key_id": participant[
                    "participant_key_id"
                ],
                "participant_public_key": participant[
                    "participant_public_key"
                ],
                "standing_record_sha256": standing_sha256,
                "issuing_operator_participant_record_sha256": operator[
                    "participant_record_sha256"
                ],
            },
        ),
        signer_kind="participant",
        nonce_scalar=nonce_base + 3,
    )
    issuance_sha256 = hashlib.sha256(issuance).digest()

    signing_node["authorization_record_sha256"] = (
        authorization_sha256
    )
    operator["selection_record_sha256"] = selection_sha256
    participant["standing_record_sha256"] = standing_sha256
    participant["issuance_record_sha256"] = issuance_sha256
    manifest["history"]["accepted_history_head_sha256"] = (  # type: ignore[index]
        issuance_sha256
    )

    return compose_reference_accepted_history(
        predecessor_sequence=predecessor_sequence,
        predecessor_head_sha256=predecessor_head_sha256,
        signing_node_authorization=authorization,
        operator_selection=selection,
        participant_standing={
            participant["participant_record_sha256"]: standing
        },
        participant_issuance={
            participant["participant_record_sha256"]: issuance
        },
    )


def build_bootstrap_fixture() -> CandidateFixture:
    manifest = authority_manifest(
        effective_time_ms=BOOTSTRAP_EFFECTIVE_TIME_MS,
    )
    _finalize_governance(
        manifest,
        transition_kind="bootstrap",
        proof_nonce=101,
    )

    history = _compose_epoch_records(
        manifest,
        predecessor_sequence=b"",
        predecessor_head_sha256=None,
        nonce_base=201,
    )

    signed_manifest = sign_epoch_manifest_fixture(
        manifest,
        private_scalar=2,
        nonce_scalar=301,
    )
    replica_bytes = build_candidate_authority_state_replica(
        signed_manifest_bytes=signed_manifest,
        accepted_history_bytes=history,
    )

    return CandidateFixture(
        manifest=manifest,
        signed_manifest_bytes=signed_manifest,
        accepted_history_bytes=history,
        replica_bytes=replica_bytes,
        replica_sha256=hashlib.sha256(replica_bytes).digest(),
    )


def build_successor_fixture(
    predecessor_state: VerifiedAuthorityState,
    *,
    variant: int,
) -> CandidateFixture:
    manifest = copy.deepcopy(
        predecessor_state.current_manifest
    )
    manifest["epoch_sequence"] = (
        predecessor_state.current_manifest["epoch_sequence"] + 1
    )
    manifest["predecessor_manifest_sha256"] = manifest_sha256(
        predecessor_state.current_manifest
    )
    manifest["effective_time_ms"] = (
        SUCCESSOR_EFFECTIVE_TIME_MS + variant
    )

    participant = manifest["participants"][0]  # type: ignore[index]
    participant["participant_key_id"] = derive_key_id(P3)
    participant["participant_public_key"] = P3
    participant["standing_record_sha256"] = h(170 + variant)
    participant["issuance_record_sha256"] = h(180 + variant)

    manifest["operator"]["selection_record_sha256"] = h(190 + variant)  # type: ignore[index]
    manifest["signing_node"]["authorization_record_sha256"] = h(200 + variant)  # type: ignore[index]

    _finalize_governance(
        manifest,
        transition_kind="successor",
        proof_nonce=401 + variant,
    )

    predecessor_head = predecessor_state.current_manifest[
        "history"
    ]["accepted_history_head_sha256"]  # type: ignore[index]

    history = _compose_epoch_records(
        manifest,
        predecessor_sequence=(
            predecessor_state.accepted_history_bytes
        ),
        predecessor_head_sha256=predecessor_head,
        nonce_base=501 + (variant * 10),
    )

    signed_manifest = sign_epoch_manifest_fixture(
        manifest,
        private_scalar=2,
        nonce_scalar=601 + variant,
    )
    replica_bytes = build_candidate_authority_state_replica(
        signed_manifest_bytes=signed_manifest,
        accepted_history_bytes=history,
        predecessor_state=predecessor_state,
    )

    return CandidateFixture(
        manifest=manifest,
        signed_manifest_bytes=signed_manifest,
        accepted_history_bytes=history,
        replica_bytes=replica_bytes,
        replica_sha256=hashlib.sha256(replica_bytes).digest(),
    )


def persist_fixture(
    root: Path,
    fixture: CandidateFixture,
) -> None:
    persist_immutable_objects(
        root,
        [
            fixture.signed_manifest_bytes,
            fixture.accepted_history_bytes,
            fixture.replica_bytes,
        ],
    )


def verify_fixture(
    root: Path,
    fixture: CandidateFixture,
    *,
    predecessor_state: VerifiedAuthorityState | None,
) -> VerifiedAuthorityCandidate:
    return verify_persisted_transition_candidate(
        fixture.replica_sha256,
        load_object=object_store_loader(root),
        predecessor_state=predecessor_state,
    )


class RaceInjectingSelector:
    def __init__(
        self,
        selector: FileAcceptedStateSelector,
        *,
        competing: VerifiedAuthorityCandidate,
    ) -> None:
        self._selector = selector
        self._competing = competing
        self._injected = False

    def read(self) -> AcceptedStateSelection | None:
        return self._selector.read()

    def compare_and_select(
        self,
        *,
        expected_replica_sha256: bytes | None,
        candidate: AcceptedStateSelection,
    ):
        if not self._injected:
            self._injected = True
            current = self._selector.read()
            generation = (
                0
                if current is None
                else current.generation + 1
            )
            self._selector.compare_and_select(
                expected_replica_sha256=(
                    expected_replica_sha256
                ),
                candidate=selection_for_state(
                    self._competing.state,
                    generation=generation,
                ),
            )

        return self._selector.compare_and_select(
            expected_replica_sha256=(
                expected_replica_sha256
            ),
            candidate=candidate,
        )


class CivicAuthorityTransactionTests(unittest.TestCase):
    def test_bootstrap_persist_verify_commit_and_exact_retry_are_atomic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            object_root = root / "objects"
            selector = FileAcceptedStateSelector(
                root / "selector"
            )
            fixture = build_bootstrap_fixture()

            persist_fixture(object_root, fixture)

            self.assertIsNone(selector.read())

            candidate = verify_fixture(
                object_root,
                fixture,
                predecessor_state=None,
            )

            first = commit_verified_candidate(
                selector,
                candidate,
            )
            self.assertFalse(first.idempotent)
            self.assertEqual(
                fixture.replica_sha256,
                first.selection.replica_sha256,
            )
            self.assertEqual(0, first.selection.generation)

            retry = commit_verified_candidate(
                selector,
                candidate,
            )
            self.assertTrue(retry.idempotent)
            self.assertEqual(first.selection, retry.selection)

    def test_reference_history_suffix_has_exact_canonical_record_order(self) -> None:
        fixture = build_bootstrap_fixture()
        records = decode_history_sequence(
            fixture.accepted_history_bytes
        )
        record_types = []

        for record in records:
            parsed = parse_cose_sign1(
                record.encoded,
                expected_content_type=HISTORY_RECORD_CONTENT_TYPE,
            )
            payload = decode_history_record_payload(
                parsed.payload
            )
            record_types.append(payload["record_type"])

        self.assertEqual(
            [
                SIGNING_NODE_AUTHORIZATION_RECORD_TYPE,
                OPERATOR_SELECTION_RECORD_TYPE,
                PARTICIPANT_STANDING_RECORD_TYPE,
                PARTICIPANT_ISSUANCE_RECORD_TYPE,
            ],
            record_types,
        )

        with self.assertRaises(
            CivicAuthorityTransactionError
        ):
            compose_reference_accepted_history(
                predecessor_sequence=b"",
                predecessor_head_sha256=None,
                signing_node_authorization=(
                    records[1].encoded
                ),
                operator_selection=records[0].encoded,
                participant_standing={
                    h(16): records[2].encoded
                },
                participant_issuance={
                    h(16): records[3].encoded
                },
            )

    def test_successor_preserves_predecessor_bytes_and_commits_generation_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            object_root = root / "objects"
            selector = FileAcceptedStateSelector(
                root / "selector"
            )

            bootstrap = build_bootstrap_fixture()
            persist_fixture(object_root, bootstrap)
            bootstrap_candidate = verify_fixture(
                object_root,
                bootstrap,
                predecessor_state=None,
            )
            commit_verified_candidate(
                selector,
                bootstrap_candidate,
            )

            successor = build_successor_fixture(
                bootstrap_candidate.state,
                variant=1,
            )
            persist_fixture(object_root, successor)
            successor_candidate = verify_fixture(
                object_root,
                successor,
                predecessor_state=bootstrap_candidate.state,
            )

            self.assertTrue(
                successor_candidate.state.accepted_history_bytes.startswith(
                    bootstrap_candidate.state.accepted_history_bytes
                )
            )
            self.assertEqual(
                bootstrap_candidate.state.replica["epoch_lineage"],
                successor_candidate.state.replica[
                    "epoch_lineage"
                ][:-1],
            )

            result = commit_verified_candidate(
                selector,
                successor_candidate,
            )
            self.assertFalse(result.idempotent)
            self.assertEqual(1, result.selection.generation)
            self.assertEqual(
                2,
                result.selection.current_epoch_sequence,
            )

    def test_missing_or_corrupted_persisted_dependency_prevents_verification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            object_root = root / "objects"
            fixture = build_bootstrap_fixture()
            persist_fixture(object_root, fixture)

            signed_manifest_sha256 = hashlib.sha256(
                fixture.signed_manifest_bytes
            ).digest()
            object_path(
                object_root,
                signed_manifest_sha256,
            ).unlink()

            with self.assertRaises(
                CivicAuthorityTransactionError
            ):
                verify_fixture(
                    object_root,
                    fixture,
                    predecessor_state=None,
                )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            object_root = root / "objects"
            fixture = build_bootstrap_fixture()
            persist_fixture(object_root, fixture)

            history_sha256 = hashlib.sha256(
                fixture.accepted_history_bytes
            ).digest()
            history_path = object_path(
                object_root,
                history_sha256,
            )
            history_path.write_bytes(b"corrupted")

            with self.assertRaises(
                CivicAuthorityTransactionError
            ):
                verify_fixture(
                    object_root,
                    fixture,
                    predecessor_state=None,
                )

    def test_competing_successor_becomes_stale_after_first_successor_commits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            object_root = root / "objects"
            selector = FileAcceptedStateSelector(
                root / "selector"
            )

            bootstrap = build_bootstrap_fixture()
            persist_fixture(object_root, bootstrap)
            bootstrap_candidate = verify_fixture(
                object_root,
                bootstrap,
                predecessor_state=None,
            )
            commit_verified_candidate(
                selector,
                bootstrap_candidate,
            )

            first = build_successor_fixture(
                bootstrap_candidate.state,
                variant=2,
            )
            second = build_successor_fixture(
                bootstrap_candidate.state,
                variant=3,
            )
            persist_fixture(object_root, first)
            persist_fixture(object_root, second)

            first_candidate = verify_fixture(
                object_root,
                first,
                predecessor_state=bootstrap_candidate.state,
            )
            second_candidate = verify_fixture(
                object_root,
                second,
                predecessor_state=bootstrap_candidate.state,
            )

            commit_verified_candidate(
                selector,
                first_candidate,
            )

            with self.assertRaises(
                CivicAuthorityTransactionError
            ):
                commit_verified_candidate(
                    selector,
                    second_candidate,
                )

            selected = selector.read()
            self.assertIsNotNone(selected)
            assert selected is not None
            self.assertEqual(
                first.replica_sha256,
                selected.replica_sha256,
            )

    def test_race_immediately_before_compare_and_select_cannot_overwrite_competing_commit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            object_root = root / "objects"
            base_selector = FileAcceptedStateSelector(
                root / "selector"
            )

            bootstrap = build_bootstrap_fixture()
            persist_fixture(object_root, bootstrap)
            bootstrap_candidate = verify_fixture(
                object_root,
                bootstrap,
                predecessor_state=None,
            )
            commit_verified_candidate(
                base_selector,
                bootstrap_candidate,
            )

            first = build_successor_fixture(
                bootstrap_candidate.state,
                variant=4,
            )
            second = build_successor_fixture(
                bootstrap_candidate.state,
                variant=5,
            )
            persist_fixture(object_root, first)
            persist_fixture(object_root, second)

            first_candidate = verify_fixture(
                object_root,
                first,
                predecessor_state=bootstrap_candidate.state,
            )
            second_candidate = verify_fixture(
                object_root,
                second,
                predecessor_state=bootstrap_candidate.state,
            )

            racing_selector = RaceInjectingSelector(
                base_selector,
                competing=second_candidate,
            )

            with self.assertRaises(
                CivicAuthorityTransactionError
            ):
                commit_verified_candidate(
                    racing_selector,
                    first_candidate,
                )

            selected = base_selector.read()
            self.assertIsNotNone(selected)
            assert selected is not None
            self.assertEqual(
                second.replica_sha256,
                selected.replica_sha256,
            )
            self.assertNotEqual(
                first.replica_sha256,
                selected.replica_sha256,
            )

    def test_candidate_persistence_and_verification_do_not_activate_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            object_root = root / "objects"
            selector = FileAcceptedStateSelector(
                root / "selector"
            )
            fixture = build_bootstrap_fixture()

            persist_fixture(object_root, fixture)
            candidate = verify_fixture(
                object_root,
                fixture,
                predecessor_state=None,
            )

            self.assertEqual(
                fixture.replica_sha256,
                candidate.replica_sha256,
            )
            self.assertIsNone(selector.read())

    def test_successor_requires_verified_predecessor_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            object_root = root / "objects"

            bootstrap = build_bootstrap_fixture()
            persist_fixture(object_root, bootstrap)
            bootstrap_candidate = verify_fixture(
                object_root,
                bootstrap,
                predecessor_state=None,
            )

            successor = build_successor_fixture(
                bootstrap_candidate.state,
                variant=6,
            )
            persist_fixture(object_root, successor)

            with self.assertRaises(
                CivicAuthorityTransactionError
            ):
                verify_fixture(
                    object_root,
                    successor,
                    predecessor_state=None,
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
