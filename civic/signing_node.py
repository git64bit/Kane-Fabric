from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
import hashlib
from pathlib import Path
from typing import Protocol, runtime_checkable

from civic.authority_state import (
    CivicAuthorityStateError,
    decode_authority_state_replica,
)
from civic.authority_transaction import (
    AcceptedStateSelection,
    AcceptedStateSelector,
    CivicAuthorityTransactionError,
    CommitResult,
    VerifiedAuthorityCandidate,
    VerifiedAuthorityState,
    commit_verified_candidate,
    selection_for_state,
    verify_persisted_authority_state,
    verify_persisted_transition_candidate,
    verify_selected_state,
)
from civic.epoch_manifest import CivicManifestError, derive_key_id, manifest_sha256
from civic.object_store import (
    CivicObjectStoreError,
    get_object,
    put_object,
    verify_object_bytes,
)
from civic.production_signing import (
    CivicAuthorityKeyBinding,
    CivicCustodyState,
    CivicKeyRole,
    CivicLocalKeyMetadata,
    CivicProductionSigningError,
    CivicSignerProvider,
    make_current_binding,
)


REFERENCE_NAME = "Kane Fabric Civic Authority Reference"
REFERENCE_VERSION = "v1"
SHA256_BYTES = 32


class CivicSigningNodeError(ValueError):
    """Raised when Signing Node conformance or orchestration fails."""


class CivicSigningNodeOperationalState(str, Enum):
    UNINITIALIZED = "uninitialized"
    STATE_VERIFIED = "state_verified"
    READY_CURRENT = "ready_current"
    RECOVERY_REQUIRED = "recovery_required"
    DEGRADED = "degraded"
    FAILED_CLOSED = "failed_closed"


@dataclass(frozen=True)
class CivicReplicaClosureObject:
    sha256: bytes
    byte_length: int
    exact_bytes: bytes

    def __post_init__(self) -> None:
        _sha256(self.sha256, "closure object sha256")
        _uint(self.byte_length, "closure object byte_length")

        if not isinstance(self.exact_bytes, bytes):
            raise CivicSigningNodeError(
                "closure object exact_bytes must be bytes"
            )
        try:
            verify_object_bytes(
                self.exact_bytes,
                expected_sha256=self.sha256,
                expected_byte_length=self.byte_length,
            )
        except CivicObjectStoreError as exc:
            raise CivicSigningNodeError(
                "closure object exact bytes do not match identity"
            ) from exc


@dataclass(frozen=True)
class CivicReplicaClosure:
    """Transport-neutral exact-byte participant authority-state closure."""

    replica_bytes: bytes
    objects: tuple[CivicReplicaClosureObject, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.replica_bytes, bytes):
            raise CivicSigningNodeError(
                "replica_bytes must be bytes"
            )

        digests = [item.sha256 for item in self.objects]
        if digests != sorted(digests):
            raise CivicSigningNodeError(
                "closure objects must be sorted by SHA-256 bytes"
            )
        if len(digests) != len(set(digests)):
            raise CivicSigningNodeError(
                "closure object SHA-256 identities must be unique"
            )


@dataclass(frozen=True)
class CivicSigningNodeStartupResult:
    operational_state: CivicSigningNodeOperationalState
    verified_state: VerifiedAuthorityState | None
    current_binding: CivicAuthorityKeyBinding | None
    current_key_ref: str | None
    failure_classification: str | None

    @property
    def current_signing_enabled(self) -> bool:
        return (
            self.operational_state
            == CivicSigningNodeOperationalState.READY_CURRENT
        )


@dataclass(frozen=True)
class CivicSigningNodeCommitResult:
    commit: CommitResult
    startup: CivicSigningNodeStartupResult


@runtime_checkable
class CivicObjectRepository(Protocol):
    """Platform-neutral exact-byte content-addressed object repository."""

    def put(self, exact_bytes: bytes) -> bytes:
        ...

    def get(self, sha256: bytes) -> bytes:
        ...


class FileCivicObjectRepository:
    """Reference filesystem adapter over civic.object_store primitives."""

    def __init__(self, root: Path | str) -> None:
        self._root = Path(root)

    def put(self, exact_bytes: bytes) -> bytes:
        try:
            return put_object(self._root, exact_bytes)
        except CivicObjectStoreError as exc:
            raise CivicSigningNodeError(
                "object repository persistence failed"
            ) from exc

    def get(self, sha256: bytes) -> bytes:
        try:
            return get_object(self._root, sha256)
        except CivicObjectStoreError as exc:
            raise CivicSigningNodeError(
                "object repository retrieval failed"
            ) from exc


SigningKeyRefResolver = Callable[[bytes], str | None]


def _sha256(value: object, label: str) -> bytes:
    if not isinstance(value, bytes) or len(value) != SHA256_BYTES:
        raise CivicSigningNodeError(
            f"{label} must be exactly 32 bytes"
        )
    return value


def _uint(value: object, label: str) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
        or value > 0xFFFFFFFFFFFFFFFF
    ):
        raise CivicSigningNodeError(
            f"{label} must be a uint64"
        )
    return value


def _optional_root(value: bytes | None) -> bytes | None:
    if value is None:
        return None
    return _sha256(value, "expected_hoa_root_id")


def _replica_root(state: VerifiedAuthorityState) -> bytes:
    root = state.current_manifest["hoa_root_id"]
    return _sha256(root, "verified HOA root")


def _signing_node_projection(
    state: VerifiedAuthorityState,
) -> tuple[bytes, bytes]:
    signing_node = state.current_manifest["signing_node"]
    if not isinstance(signing_node, Mapping):
        raise CivicSigningNodeError(
            "verified current Manifest Signing Node projection is invalid"
        )

    public_key = signing_node.get("public_key")
    key_id = signing_node.get("key_id")

    if not isinstance(public_key, bytes):
        raise CivicSigningNodeError(
            "verified current Signing Node public key is invalid"
        )
    key_id = _sha256(
        key_id,
        "verified current Signing Node key_id",
    )

    try:
        derived = derive_key_id(public_key)
    except CivicManifestError as exc:
        raise CivicSigningNodeError(
            "verified current Signing Node public key is invalid"
        ) from exc

    if derived != key_id:
        raise CivicSigningNodeError(
            "verified current Signing Node key_id does not match public key"
        )

    return public_key, key_id


def _closure_inventory(
    replica: Mapping[str, object],
) -> dict[bytes, int]:
    """Return exact external object identities required by one replica."""

    inventory: dict[bytes, int] = {}

    def add(
        digest_value: object,
        length_value: object,
        *,
        label: str,
    ) -> None:
        digest = _sha256(digest_value, f"{label}.sha256")
        length = _uint(
            length_value,
            f"{label}.byte_length",
        )
        if length == 0:
            raise CivicSigningNodeError(
                f"{label}.byte_length must be positive"
            )

        prior = inventory.get(digest)
        if prior is not None and prior != length:
            raise CivicSigningNodeError(
                "replica closure contains conflicting byte lengths"
            )
        inventory[digest] = length

    lineage = replica["epoch_lineage"]
    history_streams = replica["history_streams"]
    required_objects = replica["required_objects"]

    if not isinstance(lineage, list):
        raise CivicSigningNodeError(
            "replica epoch_lineage is invalid"
        )
    if not isinstance(history_streams, Mapping):
        raise CivicSigningNodeError(
            "replica history_streams is invalid"
        )
    if not isinstance(required_objects, list):
        raise CivicSigningNodeError(
            "replica required_objects is invalid"
        )

    for index, raw in enumerate(lineage):
        if not isinstance(raw, Mapping):
            raise CivicSigningNodeError(
                "replica lineage descriptor is invalid"
            )
        add(
            raw.get("signed_manifest_sha256"),
            raw.get("signed_manifest_byte_length"),
            label=f"epoch_lineage[{index}] signed Manifest",
        )

    for stream_name in (
        "accepted",
        "witness",
        "diagnostics",
        "knowledge",
    ):
        raw = history_streams.get(stream_name)
        if not isinstance(raw, Mapping):
            raise CivicSigningNodeError(
                f"replica {stream_name} history descriptor is invalid"
            )

        head = raw.get("head_sha256")
        sequence_id = raw.get("sequence_sha256")
        byte_length = raw.get("byte_length")

        if head is None:
            if sequence_id is not None or byte_length != 0:
                raise CivicSigningNodeError(
                    f"empty {stream_name} history descriptor is inconsistent"
                )
            continue

        _sha256(head, f"{stream_name} history head")
        add(
            sequence_id,
            byte_length,
            label=f"{stream_name} history sequence",
        )

    for index, raw in enumerate(required_objects):
        if not isinstance(raw, Mapping):
            raise CivicSigningNodeError(
                "replica required-object descriptor is invalid"
            )
        add(
            raw.get("sha256"),
            raw.get("byte_length"),
            label=f"required_objects[{index}]",
        )

    return inventory


class CivicSigningNode:
    """Platform-neutral orchestration of accepted Civic authority modules.

    The node does not define canonical Civic formats or cryptography.  It
    coordinates exact-byte storage, accepted-state selection, verification,
    local private-key custody, replica transfer, and recovery.
    """

    def __init__(
        self,
        *,
        objects: CivicObjectRepository,
        selector: AcceptedStateSelector,
        signer_provider: CivicSignerProvider | None = None,
        resolve_signing_key_ref: SigningKeyRefResolver | None = None,
        expected_hoa_root_id: bytes | None = None,
    ) -> None:
        if not isinstance(objects, CivicObjectRepository):
            raise CivicSigningNodeError(
                "objects does not implement CivicObjectRepository"
            )
        if not isinstance(selector, AcceptedStateSelector):
            raise CivicSigningNodeError(
                "selector does not implement AcceptedStateSelector"
            )

        if (signer_provider is None) != (
            resolve_signing_key_ref is None
        ):
            raise CivicSigningNodeError(
                "signer provider and key-ref resolver must be configured together"
            )
        if (
            signer_provider is not None
            and not isinstance(signer_provider, CivicSignerProvider)
        ):
            raise CivicSigningNodeError(
                "signer_provider does not implement CivicSignerProvider"
            )
        if (
            resolve_signing_key_ref is not None
            and not callable(resolve_signing_key_ref)
        ):
            raise CivicSigningNodeError(
                "resolve_signing_key_ref must be callable"
            )

        self._objects = objects
        self._selector = selector
        self._signer_provider = signer_provider
        self._resolve_signing_key_ref = resolve_signing_key_ref
        self._expected_hoa_root_id = _optional_root(
            expected_hoa_root_id
        )

    def _load_object(self, digest: bytes) -> bytes:
        try:
            data = self._objects.get(digest)
        except Exception as exc:
            raise CivicAuthorityTransactionError(
                "Signing Node object repository could not load exact bytes"
            ) from exc

        if not isinstance(data, bytes):
            raise CivicAuthorityTransactionError(
                "Signing Node object repository returned non-bytes"
            )
        return data

    def _verify_expected_root(
        self,
        state: VerifiedAuthorityState,
    ) -> None:
        if (
            self._expected_hoa_root_id is not None
            and _replica_root(state)
            != self._expected_hoa_root_id
        ):
            raise CivicSigningNodeError(
                "selected authority state HOA root does not match configured node domain"
            )

    def verify_selected_public_state(
        self,
    ) -> VerifiedAuthorityState | None:
        """Verify selected public authority without requiring private custody."""

        try:
            selection = self._selector.read()
        except Exception as exc:
            raise CivicSigningNodeError(
                "accepted-state selector could not be read"
            ) from exc

        if selection is None:
            return None

        try:
            state = verify_selected_state(
                selection,
                load_object=self._load_object,
            )
        except CivicAuthorityTransactionError as exc:
            raise CivicSigningNodeError(
                "selected Civic authority state failed verification"
            ) from exc

        self._verify_expected_root(state)
        return state

    def _state_verified_result(
        self,
        state: VerifiedAuthorityState,
    ) -> CivicSigningNodeStartupResult:
        return CivicSigningNodeStartupResult(
            operational_state=(
                CivicSigningNodeOperationalState.STATE_VERIFIED
            ),
            verified_state=state,
            current_binding=None,
            current_key_ref=None,
            failure_classification=None,
        )

    def startup(self) -> CivicSigningNodeStartupResult:
        """Run the complete fail-closed startup gate.

        Public authority is verified before local key custody is inspected.
        """

        try:
            selection = self._selector.read()
        except Exception:
            return CivicSigningNodeStartupResult(
                operational_state=(
                    CivicSigningNodeOperationalState.FAILED_CLOSED
                ),
                verified_state=None,
                current_binding=None,
                current_key_ref=None,
                failure_classification="selector-integrity-failure",
            )

        if selection is None:
            return CivicSigningNodeStartupResult(
                operational_state=(
                    CivicSigningNodeOperationalState.UNINITIALIZED
                ),
                verified_state=None,
                current_binding=None,
                current_key_ref=None,
                failure_classification=None,
            )

        try:
            state = verify_selected_state(
                selection,
                load_object=self._load_object,
            )
            self._verify_expected_root(state)
            public_key, expected_key_id = (
                _signing_node_projection(state)
            )
            binding = make_current_binding(
                hoa_root_id=_replica_root(state),
                epoch_sequence=state.current_manifest[
                    "epoch_sequence"
                ],  # type: ignore[arg-type]
                role=CivicKeyRole.SIGNING_NODE,
                public_key=public_key,
            )
        except (
            CivicAuthorityTransactionError,
            CivicProductionSigningError,
            CivicSigningNodeError,
        ):
            return CivicSigningNodeStartupResult(
                operational_state=(
                    CivicSigningNodeOperationalState.FAILED_CLOSED
                ),
                verified_state=None,
                current_binding=None,
                current_key_ref=None,
                failure_classification="selected-state-verification-failure",
            )

        if binding.key_id != expected_key_id:
            return CivicSigningNodeStartupResult(
                operational_state=(
                    CivicSigningNodeOperationalState.FAILED_CLOSED
                ),
                verified_state=None,
                current_binding=None,
                current_key_ref=None,
                failure_classification="current-key-identity-failure",
            )

        if (
            self._signer_provider is None
            and self._resolve_signing_key_ref is None
        ):
            return self._state_verified_result(state)

        assert self._signer_provider is not None
        assert self._resolve_signing_key_ref is not None

        try:
            key_ref = self._resolve_signing_key_ref(
                expected_key_id
            )
        except Exception:
            key_ref = None

        if key_ref is None:
            return CivicSigningNodeStartupResult(
                operational_state=(
                    CivicSigningNodeOperationalState.RECOVERY_REQUIRED
                ),
                verified_state=state,
                current_binding=binding,
                current_key_ref=None,
                failure_classification="current-key-not-locally-resolved",
            )

        if not isinstance(key_ref, str) or not key_ref:
            return CivicSigningNodeStartupResult(
                operational_state=(
                    CivicSigningNodeOperationalState.RECOVERY_REQUIRED
                ),
                verified_state=state,
                current_binding=binding,
                current_key_ref=None,
                failure_classification="current-key-ref-invalid",
            )

        try:
            metadata = self._signer_provider.metadata(
                key_ref
            )
            provider_public_key = (
                self._signer_provider.public_key(key_ref)
            )
        except Exception:
            return CivicSigningNodeStartupResult(
                operational_state=(
                    CivicSigningNodeOperationalState.RECOVERY_REQUIRED
                ),
                verified_state=state,
                current_binding=binding,
                current_key_ref=None,
                failure_classification="current-key-custody-unavailable",
            )

        if not isinstance(metadata, CivicLocalKeyMetadata):
            return CivicSigningNodeStartupResult(
                operational_state=(
                    CivicSigningNodeOperationalState.RECOVERY_REQUIRED
                ),
                verified_state=state,
                current_binding=binding,
                current_key_ref=None,
                failure_classification="current-key-metadata-invalid",
            )

        if metadata.role != CivicKeyRole.SIGNING_NODE:
            return CivicSigningNodeStartupResult(
                operational_state=(
                    CivicSigningNodeOperationalState.RECOVERY_REQUIRED
                ),
                verified_state=state,
                current_binding=binding,
                current_key_ref=None,
                failure_classification="current-key-role-mismatch",
            )

        if metadata.custody_state != CivicCustodyState.AVAILABLE:
            return CivicSigningNodeStartupResult(
                operational_state=(
                    CivicSigningNodeOperationalState.RECOVERY_REQUIRED
                ),
                verified_state=state,
                current_binding=binding,
                current_key_ref=None,
                failure_classification="current-key-unavailable",
            )

        if (
            metadata.public_key != binding.public_key
            or provider_public_key != binding.public_key
            or metadata.key_id != binding.key_id
        ):
            return CivicSigningNodeStartupResult(
                operational_state=(
                    CivicSigningNodeOperationalState.RECOVERY_REQUIRED
                ),
                verified_state=state,
                current_binding=binding,
                current_key_ref=None,
                failure_classification="current-key-binding-mismatch",
            )

        return CivicSigningNodeStartupResult(
            operational_state=(
                CivicSigningNodeOperationalState.READY_CURRENT
            ),
            verified_state=state,
            current_binding=binding,
            current_key_ref=key_ref,
            failure_classification=None,
        )

    def status(self) -> dict[str, object]:
        """Return a secret-free diagnostic projection of current node state."""

        startup = self.startup()
        state = startup.verified_state
        binding = startup.current_binding

        result: dict[str, object] = {
            "reference_name": REFERENCE_NAME,
            "reference_version": REFERENCE_VERSION,
            "operational_state": startup.operational_state.value,
            "accepted_state_selected": state is not None,
            "hoa_root_id": None,
            "current_epoch_sequence": None,
            "current_manifest_sha256": None,
            "selected_replica_sha256": None,
            "expected_signing_node_key_id": None,
            "signer_provider_available": (
                self._signer_provider is not None
            ),
            "current_key_available": (
                startup.operational_state
                == CivicSigningNodeOperationalState.READY_CURRENT
            ),
            "current_signing_enabled": (
                startup.current_signing_enabled
            ),
            "failure_classification": (
                startup.failure_classification
            ),
        }

        if state is not None:
            result["hoa_root_id"] = _replica_root(
                state
            ).hex()
            result["current_epoch_sequence"] = (
                state.current_manifest["epoch_sequence"]
            )
            result["current_manifest_sha256"] = (
                manifest_sha256(
                    state.current_manifest
                ).hex()
            )
            result["selected_replica_sha256"] = (
                state.replica_sha256.hex()
            )

        if binding is not None:
            result["expected_signing_node_key_id"] = (
                binding.key_id.hex()
            )

        return result

    def current_signing_binding(
        self,
    ) -> CivicAuthorityKeyBinding:
        """Return only a verified READY_CURRENT public authority binding."""

        startup = self.startup()

        if (
            startup.operational_state
            != CivicSigningNodeOperationalState.READY_CURRENT
            or startup.current_binding is None
        ):
            raise CivicSigningNodeError(
                "current Signing Node authority is not ready"
            )

        return startup.current_binding

    def export_selected_replica_closure(
        self,
    ) -> CivicReplicaClosure:
        """Export exact accepted public authority bytes without recomposition."""

        state = self.verify_selected_public_state()
        if state is None:
            raise CivicSigningNodeError(
                "no accepted authority state is selected"
            )

        inventory = _closure_inventory(state.replica)
        objects: list[CivicReplicaClosureObject] = []

        for digest in sorted(inventory):
            length = inventory[digest]
            try:
                exact_bytes = self._objects.get(digest)
            except Exception as exc:
                raise CivicSigningNodeError(
                    "selected replica closure object is unavailable"
                ) from exc

            try:
                verify_object_bytes(
                    exact_bytes,
                    expected_sha256=digest,
                    expected_byte_length=length,
                )
            except CivicObjectStoreError as exc:
                raise CivicSigningNodeError(
                    "selected replica closure object failed exact-byte verification"
                ) from exc

            objects.append(
                CivicReplicaClosureObject(
                    sha256=digest,
                    byte_length=length,
                    exact_bytes=exact_bytes,
                )
            )

        return CivicReplicaClosure(
            replica_bytes=state.replica_bytes,
            objects=tuple(objects),
        )

    def import_replica_closure(
        self,
        closure: CivicReplicaClosure,
        *,
        expected_hoa_root_id: bytes | None = None,
    ) -> VerifiedAuthorityState:
        """Import and verify exact replica closure without selecting it current."""

        if not isinstance(closure, CivicReplicaClosure):
            raise CivicSigningNodeError(
                "closure must be CivicReplicaClosure"
            )

        expected_root = _optional_root(
            expected_hoa_root_id
        )

        try:
            replica = decode_authority_state_replica(
                closure.replica_bytes
            )
        except CivicAuthorityStateError as exc:
            raise CivicSigningNodeError(
                "imported replica failed canonical decoding"
            ) from exc

        replica_root = _sha256(
            replica["hoa_root_id"],
            "imported replica HOA root",
        )

        if (
            expected_root is not None
            and replica_root != expected_root
        ):
            raise CivicSigningNodeError(
                "imported replica HOA root does not match expected recovery root"
            )
        if (
            self._expected_hoa_root_id is not None
            and replica_root != self._expected_hoa_root_id
        ):
            raise CivicSigningNodeError(
                "imported replica HOA root does not match configured node domain"
            )

        inventory = _closure_inventory(replica)
        supplied = {
            item.sha256: item
            for item in closure.objects
        }

        if set(supplied) != set(inventory):
            raise CivicSigningNodeError(
                "imported replica closure object set is incomplete or contains extras"
            )

        for digest, length in inventory.items():
            item = supplied[digest]
            if item.byte_length != length:
                raise CivicSigningNodeError(
                    "imported replica closure byte length conflicts with replica"
                )
            try:
                verify_object_bytes(
                    item.exact_bytes,
                    expected_sha256=digest,
                    expected_byte_length=length,
                )
            except CivicObjectStoreError as exc:
                raise CivicSigningNodeError(
                    "imported replica closure object failed exact verification"
                ) from exc

        replica_sha256 = hashlib.sha256(
            closure.replica_bytes
        ).digest()

        try:
            for digest in sorted(inventory):
                stored = self._objects.put(
                    supplied[digest].exact_bytes
                )
                if stored != digest:
                    raise CivicSigningNodeError(
                        "object repository changed imported Civic identity"
                    )

            stored_replica = self._objects.put(
                closure.replica_bytes
            )
            if stored_replica != replica_sha256:
                raise CivicSigningNodeError(
                    "object repository changed imported replica identity"
                )
        except CivicSigningNodeError:
            raise
        except Exception as exc:
            raise CivicSigningNodeError(
                "imported replica closure could not be persisted"
            ) from exc

        try:
            state = verify_persisted_authority_state(
                replica_sha256,
                load_object=self._load_object,
            )
        except CivicAuthorityTransactionError as exc:
            raise CivicSigningNodeError(
                "imported replica closure failed complete authority verification"
            ) from exc

        if _replica_root(state) != replica_root:
            raise CivicSigningNodeError(
                "imported replica root changed during verification"
            )

        return state

    def restore_verified_state(
        self,
        state: VerifiedAuthorityState,
        *,
        expected_hoa_root_id: bytes,
    ) -> CivicSigningNodeStartupResult:
        """Restore one already accepted verified state on an empty node.

        This operation does not create a new epoch and does not authorize a
        replacement key.  The exact persisted state is reverified immediately
        before the empty selector is atomically restored.
        """

        if not isinstance(state, VerifiedAuthorityState):
            raise CivicSigningNodeError(
                "state must be VerifiedAuthorityState"
            )

        expected_root = _optional_root(
            expected_hoa_root_id
        )
        assert expected_root is not None

        try:
            current = self._selector.read()
        except Exception as exc:
            raise CivicSigningNodeError(
                "accepted-state selector could not be read for recovery"
            ) from exc

        if current is not None:
            raise CivicSigningNodeError(
                "recovery restore requires an empty accepted-state selector"
            )

        try:
            reverified = verify_persisted_authority_state(
                state.replica_sha256,
                load_object=self._load_object,
            )
        except CivicAuthorityTransactionError as exc:
            raise CivicSigningNodeError(
                "recovery state failed complete persisted verification"
            ) from exc

        if (
            reverified.replica_sha256
            != state.replica_sha256
            or reverified.replica_bytes
            != state.replica_bytes
        ):
            raise CivicSigningNodeError(
                "recovery state changed during re-verification"
            )

        root = _replica_root(reverified)
        if root != expected_root:
            raise CivicSigningNodeError(
                "recovery state HOA root does not match expected root"
            )
        if (
            self._expected_hoa_root_id is not None
            and root != self._expected_hoa_root_id
        ):
            raise CivicSigningNodeError(
                "recovery state HOA root does not match configured node domain"
            )

        selection = selection_for_state(
            reverified,
            generation=0,
        )

        try:
            self._selector.compare_and_select(
                expected_replica_sha256=None,
                candidate=selection,
            )
        except CivicAuthorityTransactionError as exc:
            raise CivicSigningNodeError(
                "recovery selector restore failed"
            ) from exc

        return self.startup()

    def verify_candidate(
        self,
        replica_sha256: bytes,
    ) -> VerifiedAuthorityCandidate:
        """Verify one persisted bootstrap/successor candidate against selected state."""

        _sha256(
            replica_sha256,
            "candidate replica_sha256",
        )

        try:
            selection = self._selector.read()
        except Exception as exc:
            raise CivicSigningNodeError(
                "accepted-state selector could not be read"
            ) from exc

        predecessor_state: VerifiedAuthorityState | None

        if selection is None:
            predecessor_state = None
        else:
            try:
                predecessor_state = verify_selected_state(
                    selection,
                    load_object=self._load_object,
                )
            except CivicAuthorityTransactionError as exc:
                raise CivicSigningNodeError(
                    "selected predecessor authority state failed verification"
                ) from exc

            self._verify_expected_root(
                predecessor_state
            )

        try:
            candidate = verify_persisted_transition_candidate(
                replica_sha256,
                load_object=self._load_object,
                predecessor_state=predecessor_state,
            )
        except CivicAuthorityTransactionError as exc:
            raise CivicSigningNodeError(
                "authority transition candidate failed verification"
            ) from exc

        candidate_root = _replica_root(candidate.state)
        if (
            self._expected_hoa_root_id is not None
            and candidate_root != self._expected_hoa_root_id
        ):
            raise CivicSigningNodeError(
                "candidate HOA root does not match configured node domain"
            )

        return candidate

    def commit_candidate(
        self,
        candidate: VerifiedAuthorityCandidate,
    ) -> CivicSigningNodeCommitResult:
        """Commit one verified candidate, then re-run startup without rollback."""

        if not isinstance(
            candidate,
            VerifiedAuthorityCandidate,
        ):
            raise CivicSigningNodeError(
                "candidate must be VerifiedAuthorityCandidate"
            )

        try:
            result = commit_verified_candidate(
                self._selector,
                candidate,
            )
        except CivicAuthorityTransactionError as exc:
            raise CivicSigningNodeError(
                "authority transition commit failed"
            ) from exc

        startup = self.startup()

        return CivicSigningNodeCommitResult(
            commit=result,
            startup=startup,
        )
