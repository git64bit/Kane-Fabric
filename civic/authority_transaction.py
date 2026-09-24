from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import secrets
from typing import Protocol, runtime_checkable

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX implementations use another selector.
    fcntl = None  # type: ignore[assignment]

from civic.accepted_operator_selection import (
    CivicOperatorSelectionError,
    verify_accepted_operator_selection,
)
from civic.accepted_participant_issuance import (
    CivicParticipantIssuanceError,
    verify_accepted_participant_issuance,
)
from civic.accepted_participant_standing import (
    CivicParticipantStandingError,
    RECORD_TYPE as PARTICIPANT_STANDING_RECORD_TYPE,
    verify_accepted_participant_standing,
)
from civic.accepted_signing_node_authorization import (
    CivicSigningNodeAuthorizationError,
    verify_accepted_signing_node_authorization,
)
from civic.authority_state import (
    CivicAuthorityStateError,
    authority_state_replica_sha256,
    decode_authority_state_replica,
    encode_authority_state_replica,
    verify_authority_state_replica,
)
from civic.ceremony import CivicCeremonyError, verify_ceremony_record
from civic.cose import CivicCoseError, parse_cose_sign1
from civic.epoch_manifest import (
    CivicManifestError,
    manifest_sha256,
)
from civic.governance import (
    CivicGovernanceError,
    VerifiedGovernanceTransition,
    verify_governance_policy,
    verify_governance_transition,
)
from civic.history import (
    CivicHistoryError,
    append_history_record,
    decode_history_sequence,
)
from civic.object_store import (
    CivicObjectStoreError,
    get_object,
    object_sha256,
    put_object,
    verify_object_bytes,
)
from civic.signed_history_record import (
    CivicSignedHistoryRecordError,
    VerifiedHistoryRecord,
    decode_history_record_payload,
    verify_signed_history_record,
)
from civic.signed_manifest import (
    CivicSignedManifestError,
    verify_signed_epoch_manifest,
)


SHA256_BYTES = 32

SELECTOR_FORMAT = "kane-civic-local-accepted-state-selector"
SELECTOR_VERSION = 1
SELECTOR_FIELDS = {
    "format",
    "version",
    "generation",
    "replica_sha256",
    "replica_byte_length",
    "current_manifest_sha256",
    "current_epoch_sequence",
}

ACCEPTED_HISTORY_RECORD_ORDER = (
    "kane-civic-accepted-signing-node-authorization-v1",
    "kane-civic-accepted-operator-selection-v1",
    "kane-civic-accepted-participant-standing-v1",
    "kane-civic-accepted-participant-issuance-v1",
)


class CivicAuthorityTransactionError(ValueError):
    """Raised when Civic authority transaction semantics are violated."""


class CivicTransactionState(str, Enum):
    BUILDING = "building"
    SEALED = "sealed"
    VERIFIED = "verified"
    COMMITTED = "committed"
    ABORTED = "aborted"


@dataclass(frozen=True)
class AcceptedStateSelection:
    replica_sha256: bytes
    replica_byte_length: int
    current_manifest_sha256: bytes
    current_epoch_sequence: int
    generation: int

    def __post_init__(self) -> None:
        _sha256(self.replica_sha256, "replica_sha256")
        _uint(self.replica_byte_length, "replica_byte_length", positive=True)
        _sha256(
            self.current_manifest_sha256,
            "current_manifest_sha256",
        )
        _uint(
            self.current_epoch_sequence,
            "current_epoch_sequence",
            positive=True,
        )
        _uint(self.generation, "generation")


@dataclass(frozen=True)
class VerifiedAuthorityState:
    """One exact persisted, fully verified Civic authority-state replica."""

    replica_bytes: bytes
    replica_sha256: bytes
    replica: dict[str, object]
    lineage: tuple[dict[str, object], ...]
    current_manifest: dict[str, object]
    predecessor_manifest: dict[str, object] | None
    accepted_history_bytes: bytes
    accepted_history_records: tuple[VerifiedHistoryRecord, ...]
    governance_transition: VerifiedGovernanceTransition


@dataclass(frozen=True)
class VerifiedAuthorityCandidate:
    """One complete transition candidate verified from persisted exact bytes."""

    state: VerifiedAuthorityState
    expected_predecessor_replica_sha256: bytes | None
    transition_kind: str

    @property
    def replica_sha256(self) -> bytes:
        return self.state.replica_sha256

    @property
    def replica_bytes(self) -> bytes:
        return self.state.replica_bytes

    @property
    def current_manifest(self) -> dict[str, object]:
        return self.state.current_manifest


@dataclass(frozen=True)
class CommitResult:
    selection: AcceptedStateSelection
    idempotent: bool


ObjectLoader = Callable[[bytes], bytes]


@runtime_checkable
class AcceptedStateSelector(Protocol):
    """Platform-neutral compare-and-select current-state boundary."""

    def read(self) -> AcceptedStateSelection | None:
        ...

    def compare_and_select(
        self,
        *,
        expected_replica_sha256: bytes | None,
        candidate: AcceptedStateSelection,
    ) -> CommitResult:
        ...


def _sha256(value: object, label: str) -> bytes:
    if not isinstance(value, bytes) or len(value) != SHA256_BYTES:
        raise CivicAuthorityTransactionError(
            f"{label} must be exactly 32 bytes"
        )
    return value


def _uint(
    value: object,
    label: str,
    *,
    positive: bool = False,
) -> int:
    minimum = 1 if positive else 0
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < minimum
        or value > 0xFFFFFFFFFFFFFFFF
    ):
        qualifier = "positive " if positive else ""
        raise CivicAuthorityTransactionError(
            f"{label} must be a {qualifier}uint64"
        )
    return value


def _load_exact(
    load_object: ObjectLoader,
    *,
    sha256: bytes,
    byte_length: int | None = None,
    label: str,
) -> bytes:
    _sha256(sha256, f"{label}.sha256")

    try:
        data = load_object(sha256)
    except Exception as exc:
        raise CivicAuthorityTransactionError(
            f"{label} is unavailable"
        ) from exc

    if not isinstance(data, bytes):
        raise CivicAuthorityTransactionError(
            f"{label} loader result must be bytes"
        )

    expected_length = len(data) if byte_length is None else byte_length

    try:
        verify_object_bytes(
            data,
            expected_sha256=sha256,
            expected_byte_length=expected_length,
        )
    except CivicObjectStoreError as exc:
        raise CivicAuthorityTransactionError(
            f"{label} failed exact-byte verification"
        ) from exc

    return data


def persist_immutable_objects(
    root: Path | str,
    objects: Sequence[bytes],
) -> tuple[bytes, ...]:
    """Persist exact immutable candidate bytes by Civic SHA-256 identity.

    Storage presence is not authority activation.  This helper only establishes
    durable content-addressed availability for later verification/commit.
    """

    if isinstance(objects, (bytes, bytearray, str)):
        raise CivicAuthorityTransactionError(
            "objects must be a sequence of exact byte strings"
        )

    digests: list[bytes] = []

    for index, data in enumerate(objects):
        if not isinstance(data, bytes):
            raise CivicAuthorityTransactionError(
                f"objects[{index}] must be bytes"
            )
        try:
            digest = put_object(root, data)
            persisted = get_object(
                root,
                digest,
                expected_byte_length=len(data),
            )
        except CivicObjectStoreError as exc:
            raise CivicAuthorityTransactionError(
                f"objects[{index}] could not be durably persisted"
            ) from exc

        if persisted != data:
            raise CivicAuthorityTransactionError(
                f"objects[{index}] persisted bytes changed"
            )

        digests.append(digest)

    return tuple(digests)


def object_store_loader(root: Path | str) -> ObjectLoader:
    """Return an exact-byte loader over one Civic content-addressed store."""

    root_path = Path(root)

    def load_object(digest: bytes) -> bytes:
        return get_object(root_path, digest)

    return load_object


def _decode_signed_history_payload(
    signed_record: bytes,
) -> dict[str, object]:
    try:
        parsed = parse_cose_sign1(
            signed_record,
            expected_content_type="application/kane-civic-history-record+cbor",
        )
        return decode_history_record_payload(parsed.payload)
    except (CivicCoseError, CivicSignedHistoryRecordError) as exc:
        raise CivicAuthorityTransactionError(
            "candidate accepted-history record is malformed"
        ) from exc


def _record_identity_and_link(
    signed_record: bytes,
) -> tuple[bytes, str, bytes | None, bytes | None]:
    payload = _decode_signed_history_payload(signed_record)

    record_type = payload.get("record_type")
    history_link = payload.get("history_link")
    body = payload.get("body")

    if not isinstance(record_type, str):
        raise CivicAuthorityTransactionError(
            "candidate history record_type is invalid"
        )
    if not isinstance(history_link, Mapping):
        raise CivicAuthorityTransactionError(
            "candidate history_link is invalid"
        )
    if not isinstance(body, Mapping):
        raise CivicAuthorityTransactionError(
            "candidate history body is invalid"
        )

    if history_link.get("stream") != "accepted":
        raise CivicAuthorityTransactionError(
            "reference transaction composes only accepted-history records"
        )

    predecessor = history_link.get("predecessor_record_sha256")
    if predecessor is not None:
        _sha256(predecessor, "predecessor_record_sha256")

    participant_id = body.get("participant_record_sha256")
    if participant_id is not None:
        _sha256(participant_id, "participant_record_sha256")

    return (
        hashlib.sha256(signed_record).digest(),
        record_type,
        predecessor,
        participant_id,
    )


def compose_reference_accepted_history(
    *,
    predecessor_sequence: bytes,
    predecessor_head_sha256: bytes | None,
    signing_node_authorization: bytes,
    operator_selection: bytes,
    participant_standing: Mapping[bytes, bytes],
    participant_issuance: Mapping[bytes, bytes],
) -> bytes:
    """Compose the canonical mandatory current-epoch accepted-history suffix.

    The records must already be signed exact bytes.  This function does not
    re-sign them and does not claim they are authoritative.  It only enforces
    the reference transaction's deterministic suffix order and authenticated
    link values encoded in those candidate records.
    """

    if not isinstance(predecessor_sequence, bytes):
        raise CivicAuthorityTransactionError(
            "predecessor_sequence must be bytes"
        )

    try:
        prior_records = decode_history_sequence(predecessor_sequence)
    except CivicHistoryError as exc:
        raise CivicAuthorityTransactionError(
            "predecessor accepted-history sequence is invalid"
        ) from exc

    if predecessor_head_sha256 is None:
        if prior_records:
            raise CivicAuthorityTransactionError(
                "null predecessor head requires empty predecessor sequence"
            )
    else:
        expected = _sha256(
            predecessor_head_sha256,
            "predecessor_head_sha256",
        )
        if not prior_records or prior_records[-1].sha256 != expected:
            raise CivicAuthorityTransactionError(
                "predecessor sequence does not end at predecessor head"
            )

    standing_ids = tuple(sorted(participant_standing))
    issuance_ids = tuple(sorted(participant_issuance))

    if standing_ids != issuance_ids:
        raise CivicAuthorityTransactionError(
            "standing and issuance participant sets must be identical"
        )
    if not standing_ids:
        raise CivicAuthorityTransactionError(
            "candidate participant set must be nonempty"
        )

    ordered: list[tuple[bytes, str, bytes | None]] = [
        (
            signing_node_authorization,
            "kane-civic-accepted-signing-node-authorization-v1",
            None,
        ),
        (
            operator_selection,
            "kane-civic-accepted-operator-selection-v1",
            None,
        ),
    ]

    for participant_id in standing_ids:
        _sha256(participant_id, "participant standing map key")
        ordered.append(
            (
                participant_standing[participant_id],
                PARTICIPANT_STANDING_RECORD_TYPE,
                participant_id,
            )
        )

    for participant_id in issuance_ids:
        _sha256(participant_id, "participant issuance map key")
        ordered.append(
            (
                participant_issuance[participant_id],
                "kane-civic-accepted-participant-issuance-v1",
                participant_id,
            )
        )

    sequence = predecessor_sequence
    expected_predecessor = predecessor_head_sha256

    for index, (signed_record, expected_type, expected_participant) in enumerate(
        ordered
    ):
        if not isinstance(signed_record, bytes):
            raise CivicAuthorityTransactionError(
                f"candidate history record {index} must be bytes"
            )

        (
            _,
            record_type,
            declared_predecessor,
            participant_id,
        ) = _record_identity_and_link(signed_record)

        if record_type != expected_type:
            raise CivicAuthorityTransactionError(
                "candidate accepted-history record order/type is invalid"
            )
        if declared_predecessor != expected_predecessor:
            raise CivicAuthorityTransactionError(
                "candidate accepted-history predecessor link is invalid"
            )
        if (
            expected_participant is not None
            and participant_id != expected_participant
        ):
            raise CivicAuthorityTransactionError(
                "candidate participant record does not match sorted participant key"
            )

        try:
            sequence = append_history_record(
                sequence,
                signed_record,
            )
        except CivicHistoryError as exc:
            raise CivicAuthorityTransactionError(
                "candidate accepted-history append failed"
            ) from exc

        expected_predecessor = hashlib.sha256(
            signed_record
        ).digest()

    return sequence


def _manifest_inline_identities(
    manifest: Mapping[str, object],
) -> set[bytes]:
    object_index = manifest["object_index"]
    assert isinstance(object_index, list)

    result: set[bytes] = set()

    for raw in object_index:
        if not isinstance(raw, Mapping):
            raise CivicAuthorityTransactionError(
                "manifest object_index entry is invalid"
            )
        digest = raw.get("sha256")
        inline = raw.get("inline")
        if not isinstance(digest, bytes):
            raise CivicAuthorityTransactionError(
                "manifest object_index digest is invalid"
            )
        if inline is not None:
            result.add(digest)

    return result


def _derive_required_objects(
    lineage: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], ...]:
    external: dict[bytes, int] = {}
    inline: set[bytes] = set()

    for manifest in lineage:
        object_index = manifest["object_index"]
        governing_sources = manifest["governing_sources"]
        assert isinstance(object_index, list)
        assert isinstance(governing_sources, list)

        inline.update(_manifest_inline_identities(manifest))

        for raw in object_index:
            assert isinstance(raw, Mapping)
            digest = raw["sha256"]
            length = raw["byte_length"]
            inline_bytes = raw["inline"]
            assert isinstance(digest, bytes)
            assert isinstance(length, int)

            if inline_bytes is None:
                prior = external.get(digest)
                if prior is not None and prior != length:
                    raise CivicAuthorityTransactionError(
                        "authority object has conflicting byte lengths across lineage"
                    )
                external[digest] = length

        for raw in governing_sources:
            assert isinstance(raw, Mapping)
            digest = raw["sha256"]
            length = raw["byte_length"]
            assert isinstance(digest, bytes)
            assert isinstance(length, int)

            prior = external.get(digest)
            if prior is not None and prior != length:
                raise CivicAuthorityTransactionError(
                    "governing source has conflicting byte lengths across lineage"
                )
            external[digest] = length

    return tuple(
        {
            "sha256": digest,
            "byte_length": external[digest],
        }
        for digest in sorted(external)
        if digest not in inline
    )


def build_candidate_authority_state_replica(
    *,
    signed_manifest_bytes: bytes,
    accepted_history_bytes: bytes,
    predecessor_state: VerifiedAuthorityState | None = None,
) -> bytes:
    """Build the deterministic replica inventory for one finalized candidate.

    This helper never selects the replica as current.  It supports the minimum
    reference behavior in which witness/diagnostics/knowledge streams are
    carried forward unchanged across a successor and are empty at bootstrap.
    """

    if not isinstance(signed_manifest_bytes, bytes):
        raise CivicAuthorityTransactionError(
            "signed_manifest_bytes must be bytes"
        )
    if not isinstance(accepted_history_bytes, bytes):
        raise CivicAuthorityTransactionError(
            "accepted_history_bytes must be bytes"
        )

    try:
        candidate_manifest = verify_signed_epoch_manifest(
            signed_manifest_bytes
        )
    except CivicSignedManifestError as exc:
        raise CivicAuthorityTransactionError(
            "candidate signed Epoch Manifest failed verification"
        ) from exc

    candidate_manifest_id = manifest_sha256(candidate_manifest)
    epoch_sequence = candidate_manifest["epoch_sequence"]
    predecessor_manifest_id = candidate_manifest[
        "predecessor_manifest_sha256"
    ]
    hoa_root_id = candidate_manifest["hoa_root_id"]
    history = candidate_manifest["history"]

    assert isinstance(epoch_sequence, int)
    assert isinstance(hoa_root_id, bytes)
    assert isinstance(history, Mapping)

    try:
        history_records = decode_history_sequence(
            accepted_history_bytes
        )
    except CivicHistoryError as exc:
        raise CivicAuthorityTransactionError(
            "candidate accepted-history sequence is invalid"
        ) from exc

    if not history_records:
        raise CivicAuthorityTransactionError(
            "candidate accepted-history sequence must be nonempty"
        )

    accepted_head = history["accepted_history_head_sha256"]
    if history_records[-1].sha256 != accepted_head:
        raise CivicAuthorityTransactionError(
            "candidate accepted-history sequence does not end at Manifest head"
        )

    if predecessor_state is None:
        if epoch_sequence != 1 or predecessor_manifest_id is not None:
            raise CivicAuthorityTransactionError(
                "bootstrap replica requires Epoch 1 with no predecessor"
            )
        prior_lineage: list[dict[str, object]] = []
        optional_streams = {
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
        }

        for stream, field in (
            ("witness", "witness_head_sha256"),
            ("diagnostics", "diagnostics_head_sha256"),
            ("knowledge", "knowledge_head_sha256"),
        ):
            if history[field] is not None:
                raise CivicAuthorityTransactionError(
                    f"bootstrap reference composer requires null {stream} history head"
                )
    else:
        predecessor_manifest = predecessor_state.current_manifest
        predecessor_id = manifest_sha256(predecessor_manifest)

        if hoa_root_id != predecessor_manifest["hoa_root_id"]:
            raise CivicAuthorityTransactionError(
                "successor candidate HOA root does not match predecessor"
            )
        if epoch_sequence != predecessor_manifest["epoch_sequence"] + 1:
            raise CivicAuthorityTransactionError(
                "successor candidate epoch sequence is not predecessor + 1"
            )
        if predecessor_manifest_id != predecessor_id:
            raise CivicAuthorityTransactionError(
                "successor candidate predecessor Manifest identity is wrong"
            )
        if not accepted_history_bytes.startswith(
            predecessor_state.accepted_history_bytes
        ):
            raise CivicAuthorityTransactionError(
                "successor accepted history does not preserve predecessor bytes exactly"
            )

        prior_lineage = [
            dict(item)
            for item in predecessor_state.replica["epoch_lineage"]  # type: ignore[index]
        ]

        predecessor_streams = predecessor_state.replica[
            "history_streams"
        ]
        assert isinstance(predecessor_streams, Mapping)

        optional_streams: dict[str, dict[str, object]] = {}
        for stream, field in (
            ("witness", "witness_head_sha256"),
            ("diagnostics", "diagnostics_head_sha256"),
            ("knowledge", "knowledge_head_sha256"),
        ):
            raw = predecessor_streams[stream]
            assert isinstance(raw, Mapping)
            if history[field] != raw["head_sha256"]:
                raise CivicAuthorityTransactionError(
                    f"successor reference composer must carry {stream} history unchanged"
                )
            optional_streams[stream] = dict(raw)

    signed_manifest_digest = hashlib.sha256(
        signed_manifest_bytes
    ).digest()

    lineage_entry = {
        "epoch_sequence": epoch_sequence,
        "manifest_sha256": candidate_manifest_id,
        "signed_manifest_sha256": signed_manifest_digest,
        "signed_manifest_byte_length": len(signed_manifest_bytes),
    }

    lineage_descriptors = prior_lineage + [lineage_entry]

    lineage_manifests: list[Mapping[str, object]] = []
    if predecessor_state is not None:
        lineage_manifests.extend(predecessor_state.lineage)
    lineage_manifests.append(candidate_manifest)

    accepted_sequence_sha256 = hashlib.sha256(
        accepted_history_bytes
    ).digest()

    replica = {
        "format": "kane-civic-participant-authority-state-replica",
        "version": 1,
        "hoa_root_id": hoa_root_id,
        "current_epoch_sequence": epoch_sequence,
        "current_manifest_sha256": candidate_manifest_id,
        "epoch_lineage": lineage_descriptors,
        "history_streams": {
            "accepted": {
                "head_sha256": accepted_head,
                "sequence_sha256": accepted_sequence_sha256,
                "byte_length": len(accepted_history_bytes),
            },
            **optional_streams,
        },
        "required_objects": list(
            _derive_required_objects(lineage_manifests)
        ),
    }

    try:
        return encode_authority_state_replica(replica)
    except CivicAuthorityStateError as exc:
        raise CivicAuthorityTransactionError(
            "candidate authority-state replica could not be encoded"
        ) from exc


def _object_descriptor(
    manifest: Mapping[str, object],
    digest: bytes,
    *,
    label: str,
) -> Mapping[str, object]:
    object_index = manifest["object_index"]
    assert isinstance(object_index, list)

    matches = [
        item
        for item in object_index
        if (
            isinstance(item, Mapping)
            and item.get("sha256") == digest
        )
    ]

    if len(matches) != 1:
        raise CivicAuthorityTransactionError(
            f"{label} must resolve to exactly one Manifest object descriptor"
        )

    return matches[0]


def _load_manifest_object(
    manifest: Mapping[str, object],
    digest: bytes,
    *,
    load_object: ObjectLoader,
    label: str,
) -> bytes:
    descriptor = _object_descriptor(
        manifest,
        digest,
        label=label,
    )

    length = descriptor.get("byte_length")
    inline = descriptor.get("inline")

    if not isinstance(length, int) or isinstance(length, bool) or length < 0:
        raise CivicAuthorityTransactionError(
            f"{label} descriptor byte_length is invalid"
        )

    if inline is not None:
        if not isinstance(inline, bytes):
            raise CivicAuthorityTransactionError(
                f"{label} inline object must be bytes"
            )
        try:
            verify_object_bytes(
                inline,
                expected_sha256=digest,
                expected_byte_length=length,
            )
        except CivicObjectStoreError as exc:
            raise CivicAuthorityTransactionError(
                f"{label} inline bytes failed exact verification"
            ) from exc
        return inline

    return _load_exact(
        load_object,
        sha256=digest,
        byte_length=length,
        label=label,
    )


def _load_accepted_history_bytes(
    replica: Mapping[str, object],
    *,
    load_object: ObjectLoader,
) -> bytes:
    streams = replica["history_streams"]
    assert isinstance(streams, Mapping)
    accepted = streams["accepted"]
    assert isinstance(accepted, Mapping)

    digest = accepted["sequence_sha256"]
    length = accepted["byte_length"]

    if not isinstance(digest, bytes) or not isinstance(length, int):
        raise CivicAuthorityTransactionError(
            "accepted history descriptor is invalid"
        )

    return _load_exact(
        load_object,
        sha256=digest,
        byte_length=length,
        label="accepted history sequence",
    )


def _verified_history_records(
    accepted_history_bytes: bytes,
    *,
    lineage: Sequence[Mapping[str, object]],
) -> tuple[VerifiedHistoryRecord, ...]:
    try:
        sequence = decode_history_sequence(
            accepted_history_bytes
        )
    except CivicHistoryError as exc:
        raise CivicAuthorityTransactionError(
            "accepted history sequence failed decoding"
        ) from exc

    verified: list[VerifiedHistoryRecord] = []

    for index, item in enumerate(sequence):
        try:
            record = verify_signed_history_record(
                item.encoded,
                epoch_manifests=lineage,
            )
        except CivicSignedHistoryRecordError as exc:
            raise CivicAuthorityTransactionError(
                f"accepted history record {index} failed signed-envelope verification"
            ) from exc

        if record.record_sha256 != item.sha256:
            raise CivicAuthorityTransactionError(
                "accepted history record identity changed during verification"
            )

        verified.append(record)

    return tuple(verified)


def _record_by_sha256(
    records: Sequence[VerifiedHistoryRecord],
    digest: bytes,
    *,
    label: str,
) -> VerifiedHistoryRecord:
    matches = [
        record
        for record in records
        if record.record_sha256 == digest
    ]
    if len(matches) != 1:
        raise CivicAuthorityTransactionError(
            f"{label} must occur exactly once in accepted history"
        )
    return matches[0]


def _expected_current_epoch_suffix(
    manifest: Mapping[str, object],
) -> tuple[bytes, ...]:
    signing_node = manifest["signing_node"]
    operator = manifest["operator"]
    participants = manifest["participants"]

    assert isinstance(signing_node, Mapping)
    assert isinstance(operator, Mapping)
    assert isinstance(participants, list)

    standing: list[tuple[bytes, bytes]] = []
    issuance: list[tuple[bytes, bytes]] = []

    for raw in participants:
        assert isinstance(raw, Mapping)
        participant_id = raw["participant_record_sha256"]
        standing_id = raw["standing_record_sha256"]
        issuance_id = raw["issuance_record_sha256"]
        assert isinstance(participant_id, bytes)
        assert isinstance(standing_id, bytes)
        assert isinstance(issuance_id, bytes)
        standing.append((participant_id, standing_id))
        issuance.append((participant_id, issuance_id))

    standing.sort(key=lambda item: item[0])
    issuance.sort(key=lambda item: item[0])

    auth_id = signing_node["authorization_record_sha256"]
    selection_id = operator["selection_record_sha256"]
    assert isinstance(auth_id, bytes)
    assert isinstance(selection_id, bytes)

    return (
        auth_id,
        selection_id,
        *(digest for _, digest in standing),
        *(digest for _, digest in issuance),
    )


def _verify_current_epoch_history_semantics(
    manifest: Mapping[str, object],
    *,
    records: Sequence[VerifiedHistoryRecord],
    load_object: ObjectLoader,
) -> None:
    expected_suffix = _expected_current_epoch_suffix(manifest)

    if len(records) < len(expected_suffix):
        raise CivicAuthorityTransactionError(
            "accepted history is shorter than mandatory current-epoch suffix"
        )

    actual_suffix = tuple(
        record.record_sha256
        for record in records[-len(expected_suffix):]
    )
    if actual_suffix != expected_suffix:
        raise CivicAuthorityTransactionError(
            "current epoch accepted-history suffix is not in canonical reference order"
        )

    signing_node = manifest["signing_node"]
    operator = manifest["operator"]
    participants = manifest["participants"]
    assert isinstance(signing_node, Mapping)
    assert isinstance(operator, Mapping)
    assert isinstance(participants, list)

    try:
        verify_accepted_signing_node_authorization(
            _record_by_sha256(
                records,
                signing_node["authorization_record_sha256"],  # type: ignore[arg-type]
                label="Signing Node authorization record",
            ),
            epoch_manifest=manifest,
        )

        verify_accepted_operator_selection(
            _record_by_sha256(
                records,
                operator["selection_record_sha256"],  # type: ignore[arg-type]
                label="operator-selection record",
            ),
            epoch_manifest=manifest,
        )

        for raw in participants:
            assert isinstance(raw, Mapping)

            standing = _record_by_sha256(
                records,
                raw["standing_record_sha256"],  # type: ignore[arg-type]
                label="participant-standing record",
            )
            issuance = _record_by_sha256(
                records,
                raw["issuance_record_sha256"],  # type: ignore[arg-type]
                label="participant-issuance record",
            )

            verify_accepted_participant_standing(
                standing,
                epoch_manifest=manifest,
                evaluation_time_ms=manifest["effective_time_ms"],  # type: ignore[arg-type]
                load_object=load_object,
            )
            verify_accepted_participant_issuance(
                issuance,
                epoch_manifest=manifest,
            )

    except (
        CivicSigningNodeAuthorizationError,
        CivicOperatorSelectionError,
        CivicParticipantStandingError,
        CivicParticipantIssuanceError,
    ) as exc:
        raise CivicAuthorityTransactionError(
            "current epoch accepted authority record verification failed"
        ) from exc


def _governance_standing_records(
    *,
    policy: object,
    candidate_manifest: Mapping[str, object],
    predecessor_manifest: Mapping[str, object] | None,
    records: Sequence[VerifiedHistoryRecord],
) -> tuple[VerifiedHistoryRecord, ...]:
    basis = getattr(policy, "electorate_basis", None)

    if basis == "candidate_participants":
        basis_manifest = candidate_manifest
    elif basis == "predecessor_participants":
        if predecessor_manifest is None:
            raise CivicAuthorityTransactionError(
                "predecessor electorate requires predecessor Manifest"
            )
        basis_manifest = predecessor_manifest
    else:
        raise CivicAuthorityTransactionError(
            "verified governance policy electorate basis is unsupported"
        )

    participants = basis_manifest["participants"]
    assert isinstance(participants, list)

    result: list[VerifiedHistoryRecord] = []

    for raw in participants:
        assert isinstance(raw, Mapping)
        standing_id = raw["standing_record_sha256"]
        assert isinstance(standing_id, bytes)
        result.append(
            _record_by_sha256(
                records,
                standing_id,
                label="governance electorate standing record",
            )
        )

    return tuple(result)


def _verify_governance(
    manifest: Mapping[str, object],
    *,
    predecessor_manifest: Mapping[str, object] | None,
    records: Sequence[VerifiedHistoryRecord],
    load_object: ObjectLoader,
) -> tuple[str, VerifiedGovernanceTransition]:
    ceremony_descriptor = manifest["ceremony"]
    assert isinstance(ceremony_descriptor, Mapping)

    ceremony_sha256 = ceremony_descriptor["ceremony_record_sha256"]
    assert isinstance(ceremony_sha256, bytes)

    ceremony_bytes = _load_manifest_object(
        manifest,
        ceremony_sha256,
        load_object=load_object,
        label="ceremony",
    )

    try:
        ceremony = verify_ceremony_record(
            ceremony_bytes,
            epoch_manifest=manifest,
            predecessor_manifest=predecessor_manifest,
        )
    except CivicCeremonyError as exc:
        raise CivicAuthorityTransactionError(
            "candidate ceremony failed verification"
        ) from exc

    policy_bytes = _load_manifest_object(
        manifest,
        ceremony.governance_policy_sha256,
        load_object=load_object,
        label="governance policy",
    )

    try:
        policy = verify_governance_policy(
            policy_bytes,
            ceremony=ceremony,
            epoch_manifest=manifest,
        )
    except CivicGovernanceError as exc:
        raise CivicAuthorityTransactionError(
            "candidate governance policy failed verification"
        ) from exc

    proof_bytes = [
        _load_manifest_object(
            manifest,
            digest,
            load_object=load_object,
            label="governance proof",
        )
        for digest in ceremony.governance_proof_sha256
    ]

    standing_records = _governance_standing_records(
        policy=policy,
        candidate_manifest=manifest,
        predecessor_manifest=predecessor_manifest,
        records=records,
    )

    try:
        transition = verify_governance_transition(
            policy=policy,
            ceremony=ceremony,
            governance_proof_bytes=proof_bytes,
            candidate_manifest=manifest,
            predecessor_manifest=predecessor_manifest,
            standing_records=standing_records,
            load_object=load_object,
        )
    except CivicGovernanceError as exc:
        raise CivicAuthorityTransactionError(
            "candidate governance transition failed verification"
        ) from exc

    return ceremony.transition_kind, transition


def verify_persisted_authority_state(
    replica_sha256: bytes,
    *,
    load_object: ObjectLoader,
) -> VerifiedAuthorityState:
    """Verify one complete persisted replica including current transition semantics."""

    digest = _sha256(replica_sha256, "replica_sha256")
    replica_bytes = _load_exact(
        load_object,
        sha256=digest,
        label="authority-state replica",
    )

    try:
        replica = decode_authority_state_replica(
            replica_bytes
        )
    except CivicAuthorityStateError as exc:
        raise CivicAuthorityTransactionError(
            "authority-state replica failed canonical decoding"
        ) from exc

    if authority_state_replica_sha256(replica_bytes) != digest:
        raise CivicAuthorityTransactionError(
            "authority-state replica identity mismatch"
        )

    try:
        lineage = verify_authority_state_replica(
            replica,
            load_object=load_object,
        )
    except CivicAuthorityStateError as exc:
        raise CivicAuthorityTransactionError(
            "authority-state replica reconstruction failed"
        ) from exc

    current_manifest = lineage[-1]
    predecessor_manifest = (
        lineage[-2]
        if len(lineage) > 1
        else None
    )

    accepted_history_bytes = _load_accepted_history_bytes(
        replica,
        load_object=load_object,
    )
    records = _verified_history_records(
        accepted_history_bytes,
        lineage=lineage,
    )

    _verify_current_epoch_history_semantics(
        current_manifest,
        records=records,
        load_object=load_object,
    )

    transition_kind, governance_transition = _verify_governance(
        current_manifest,
        predecessor_manifest=predecessor_manifest,
        records=records,
        load_object=load_object,
    )

    expected_kind = (
        "bootstrap"
        if current_manifest["epoch_sequence"] == 1
        else "successor"
    )
    if transition_kind != expected_kind:
        raise CivicAuthorityTransactionError(
            "current transition kind does not match epoch lineage position"
        )

    return VerifiedAuthorityState(
        replica_bytes=replica_bytes,
        replica_sha256=digest,
        replica=replica,
        lineage=tuple(lineage),
        current_manifest=current_manifest,
        predecessor_manifest=predecessor_manifest,
        accepted_history_bytes=accepted_history_bytes,
        accepted_history_records=records,
        governance_transition=governance_transition,
    )


def verify_persisted_transition_candidate(
    replica_sha256: bytes,
    *,
    load_object: ObjectLoader,
    predecessor_state: VerifiedAuthorityState | None,
) -> VerifiedAuthorityCandidate:
    """Verify one candidate and its exact bootstrap/successor predecessor relation."""

    state = verify_persisted_authority_state(
        replica_sha256,
        load_object=load_object,
    )
    manifest = state.current_manifest
    epoch_sequence = manifest["epoch_sequence"]
    predecessor_manifest_id = manifest["predecessor_manifest_sha256"]

    assert isinstance(epoch_sequence, int)

    if epoch_sequence == 1:
        if predecessor_state is not None:
            raise CivicAuthorityTransactionError(
                "bootstrap candidate must not receive predecessor accepted state"
            )
        if predecessor_manifest_id is not None:
            raise CivicAuthorityTransactionError(
                "bootstrap candidate unexpectedly names a predecessor"
            )
        transition_kind = "bootstrap"
        expected_predecessor_replica_sha256 = None

    else:
        if predecessor_state is None:
            raise CivicAuthorityTransactionError(
                "successor candidate requires verified predecessor accepted state"
            )

        predecessor_manifest = predecessor_state.current_manifest
        predecessor_id = manifest_sha256(
            predecessor_manifest
        )

        if manifest["hoa_root_id"] != predecessor_manifest["hoa_root_id"]:
            raise CivicAuthorityTransactionError(
                "candidate HOA root does not match predecessor accepted state"
            )
        if epoch_sequence != predecessor_manifest["epoch_sequence"] + 1:
            raise CivicAuthorityTransactionError(
                "candidate epoch is not exactly predecessor + 1"
            )
        if predecessor_manifest_id != predecessor_id:
            raise CivicAuthorityTransactionError(
                "candidate predecessor Manifest does not match selected predecessor"
            )

        predecessor_lineage = predecessor_state.replica[
            "epoch_lineage"
        ]
        candidate_lineage = state.replica["epoch_lineage"]
        assert isinstance(predecessor_lineage, list)
        assert isinstance(candidate_lineage, list)

        if candidate_lineage[:-1] != predecessor_lineage:
            raise CivicAuthorityTransactionError(
                "candidate signed-Manifest lineage does not preserve predecessor lineage exactly"
            )

        if not state.accepted_history_bytes.startswith(
            predecessor_state.accepted_history_bytes
        ):
            raise CivicAuthorityTransactionError(
                "candidate accepted history does not preserve predecessor bytes exactly"
            )

        transition_kind = "successor"
        expected_predecessor_replica_sha256 = (
            predecessor_state.replica_sha256
        )

    return VerifiedAuthorityCandidate(
        state=state,
        expected_predecessor_replica_sha256=(
            expected_predecessor_replica_sha256
        ),
        transition_kind=transition_kind,
    )


def selection_for_state(
    state: VerifiedAuthorityState,
    *,
    generation: int,
) -> AcceptedStateSelection:
    """Project one verified state into local non-authoritative selector metadata."""

    return AcceptedStateSelection(
        replica_sha256=state.replica_sha256,
        replica_byte_length=len(state.replica_bytes),
        current_manifest_sha256=manifest_sha256(
            state.current_manifest
        ),
        current_epoch_sequence=state.current_manifest[
            "epoch_sequence"
        ],  # type: ignore[arg-type]
        generation=generation,
    )


def verify_selected_state(
    selection: AcceptedStateSelection,
    *,
    load_object: ObjectLoader,
) -> VerifiedAuthorityState:
    """Verify selector metadata against the exact selected persisted replica."""

    if not isinstance(selection, AcceptedStateSelection):
        raise CivicAuthorityTransactionError(
            "selection must be AcceptedStateSelection"
        )

    state = verify_persisted_authority_state(
        selection.replica_sha256,
        load_object=load_object,
    )

    if len(state.replica_bytes) != selection.replica_byte_length:
        raise CivicAuthorityTransactionError(
            "selector replica byte length does not match selected replica"
        )

    if (
        manifest_sha256(state.current_manifest)
        != selection.current_manifest_sha256
    ):
        raise CivicAuthorityTransactionError(
            "selector current Manifest identity does not match selected replica"
        )

    if (
        state.current_manifest["epoch_sequence"]
        != selection.current_epoch_sequence
    ):
        raise CivicAuthorityTransactionError(
            "selector current epoch does not match selected replica"
        )

    return state


def _selection_to_bytes(
    selection: AcceptedStateSelection,
) -> bytes:
    value = {
        "format": SELECTOR_FORMAT,
        "version": SELECTOR_VERSION,
        "generation": selection.generation,
        "replica_sha256": selection.replica_sha256.hex(),
        "replica_byte_length": selection.replica_byte_length,
        "current_manifest_sha256": (
            selection.current_manifest_sha256.hex()
        ),
        "current_epoch_sequence": selection.current_epoch_sequence,
    }

    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _selection_from_bytes(
    data: bytes,
) -> AcceptedStateSelection:
    if not isinstance(data, bytes):
        raise CivicAuthorityTransactionError(
            "selector bytes must be bytes"
        )

    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CivicAuthorityTransactionError(
            "accepted-state selector is malformed"
        ) from exc

    if not isinstance(value, dict) or set(value) != SELECTOR_FIELDS:
        raise CivicAuthorityTransactionError(
            "accepted-state selector fields are invalid"
        )
    if (
        value.get("format") != SELECTOR_FORMAT
        or value.get("version") != SELECTOR_VERSION
    ):
        raise CivicAuthorityTransactionError(
            "accepted-state selector format/version is unsupported"
        )

    try:
        replica_sha256 = bytes.fromhex(value["replica_sha256"])
        current_manifest_sha256 = bytes.fromhex(
            value["current_manifest_sha256"]
        )
    except (TypeError, ValueError) as exc:
        raise CivicAuthorityTransactionError(
            "accepted-state selector digest is malformed"
        ) from exc

    return AcceptedStateSelection(
        replica_sha256=replica_sha256,
        replica_byte_length=value["replica_byte_length"],
        current_manifest_sha256=current_manifest_sha256,
        current_epoch_sequence=value["current_epoch_sequence"],
        generation=value["generation"],
    )


class FileAcceptedStateSelector:
    """POSIX filesystem compare-and-select implementation.

    The selector is local operational metadata, not Civic authority.  Its root
    path is supplied by the deployment and is intentionally not part of any
    canonical Civic format.
    """

    def __init__(self, root: Path | str) -> None:
        if fcntl is None:
            raise CivicAuthorityTransactionError(
                "FileAcceptedStateSelector requires POSIX file locking"
            )

        self._root = Path(root)
        self._selector_path = self._root / "accepted-state.json"
        self._lock_path = self._root / ".accepted-state.lock"

        try:
            self._root.mkdir(
                mode=0o700,
                parents=True,
                exist_ok=True,
            )
            if not self._root.is_dir():
                raise CivicAuthorityTransactionError(
                    "selector root is not a directory"
                )
            if os.name == "posix":
                os.chmod(self._root, 0o700)
        except OSError as exc:
            raise CivicAuthorityTransactionError(
                "selector root is unavailable"
            ) from exc

    def _read_unlocked(self) -> AcceptedStateSelection | None:
        try:
            data = self._selector_path.read_bytes()
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise CivicAuthorityTransactionError(
                "accepted-state selector is unavailable"
            ) from exc

        return _selection_from_bytes(data)

    def read(self) -> AcceptedStateSelection | None:
        return self._read_unlocked()

    def _write_unlocked(
        self,
        selection: AcceptedStateSelection,
    ) -> None:
        temporary = self._root / (
            f".accepted-state.{secrets.token_hex(8)}.tmp"
        )
        data = _selection_to_bytes(selection)

        try:
            fd = os.open(
                temporary,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
            except BaseException:
                try:
                    temporary.unlink()
                except OSError:
                    pass
                raise

            os.replace(
                temporary,
                self._selector_path,
            )
            if os.name == "posix":
                os.chmod(
                    self._selector_path,
                    0o600,
                )

            directory_fd = os.open(
                self._root,
                os.O_RDONLY,
            )
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)

        except OSError as exc:
            raise CivicAuthorityTransactionError(
                "accepted-state selector commit failed"
            ) from exc
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass

    def compare_and_select(
        self,
        *,
        expected_replica_sha256: bytes | None,
        candidate: AcceptedStateSelection,
    ) -> CommitResult:
        if expected_replica_sha256 is not None:
            _sha256(
                expected_replica_sha256,
                "expected_replica_sha256",
            )
        if not isinstance(candidate, AcceptedStateSelection):
            raise CivicAuthorityTransactionError(
                "candidate selector value must be AcceptedStateSelection"
            )

        try:
            lock_fd = os.open(
                self._lock_path,
                os.O_RDWR | os.O_CREAT,
                0o600,
            )
        except OSError as exc:
            raise CivicAuthorityTransactionError(
                "accepted-state selector lock is unavailable"
            ) from exc

        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            current = self._read_unlocked()

            if (
                current is not None
                and current.replica_sha256
                == candidate.replica_sha256
            ):
                if (
                    current.replica_byte_length
                    != candidate.replica_byte_length
                    or current.current_manifest_sha256
                    != candidate.current_manifest_sha256
                    or current.current_epoch_sequence
                    != candidate.current_epoch_sequence
                ):
                    raise CivicAuthorityTransactionError(
                        "selector already names candidate replica with conflicting metadata"
                    )
                return CommitResult(
                    selection=current,
                    idempotent=True,
                )

            current_digest = (
                None
                if current is None
                else current.replica_sha256
            )
            if current_digest != expected_replica_sha256:
                raise CivicAuthorityTransactionError(
                    "accepted-state selector no longer matches expected predecessor"
                )

            next_generation = (
                0
                if current is None
                else current.generation + 1
            )
            committed = AcceptedStateSelection(
                replica_sha256=candidate.replica_sha256,
                replica_byte_length=candidate.replica_byte_length,
                current_manifest_sha256=(
                    candidate.current_manifest_sha256
                ),
                current_epoch_sequence=(
                    candidate.current_epoch_sequence
                ),
                generation=next_generation,
            )

            self._write_unlocked(committed)

            reread = self._read_unlocked()
            if reread != committed:
                raise CivicAuthorityTransactionError(
                    "accepted-state selector post-commit verification failed"
                )

            return CommitResult(
                selection=committed,
                idempotent=False,
            )

        finally:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
            finally:
                os.close(lock_fd)


def commit_verified_candidate(
    selector: AcceptedStateSelector,
    candidate: VerifiedAuthorityCandidate,
) -> CommitResult:
    """Atomically select one fully verified candidate as current authority."""

    if not isinstance(selector, AcceptedStateSelector):
        raise CivicAuthorityTransactionError(
            "selector does not implement AcceptedStateSelector"
        )
    if not isinstance(candidate, VerifiedAuthorityCandidate):
        raise CivicAuthorityTransactionError(
            "candidate must be VerifiedAuthorityCandidate"
        )

    current = selector.read()

    if (
        current is not None
        and current.replica_sha256
        == candidate.replica_sha256
    ):
        candidate_selection = selection_for_state(
            candidate.state,
            generation=current.generation,
        )
        return selector.compare_and_select(
            expected_replica_sha256=(
                candidate.expected_predecessor_replica_sha256
            ),
            candidate=candidate_selection,
        )

    if candidate.transition_kind == "bootstrap":
        if current is not None:
            raise CivicAuthorityTransactionError(
                "bootstrap commit requires no accepted state"
            )
    elif candidate.transition_kind == "successor":
        expected = candidate.expected_predecessor_replica_sha256
        if expected is None:
            raise CivicAuthorityTransactionError(
                "successor candidate lacks expected predecessor replica identity"
            )
        if current is None or current.replica_sha256 != expected:
            raise CivicAuthorityTransactionError(
                "successor candidate is stale or forked from selected current state"
            )
        if (
            current.current_manifest_sha256
            != candidate.current_manifest[
                "predecessor_manifest_sha256"
            ]
        ):
            raise CivicAuthorityTransactionError(
                "selected predecessor Manifest does not match candidate predecessor"
            )
    else:
        raise CivicAuthorityTransactionError(
            "candidate transition kind is unsupported"
        )

    generation = (
        0
        if current is None
        else current.generation + 1
    )
    candidate_selection = selection_for_state(
        candidate.state,
        generation=generation,
    )

    return selector.compare_and_select(
        expected_replica_sha256=(
            candidate.expected_predecessor_replica_sha256
        ),
        candidate=candidate_selection,
    )
