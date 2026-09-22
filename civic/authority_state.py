from __future__ import annotations

from collections.abc import Callable, Mapping
import hashlib

from civic.codec import CivicCodecError, decode_deterministic, encode_deterministic
from civic.epoch_manifest import manifest_sha256
from civic.history import CivicHistoryError, verify_linked_history_sequence
from civic.object_store import CivicObjectStoreError, verify_object_bytes
from civic.signed_history_record import (
    CivicSignedHistoryRecordError,
    verify_signed_history_record,
)
from civic.signed_manifest import (
    CivicSignedManifestError,
    verify_signed_epoch_manifest,
)


FORMAT = "kane-civic-participant-authority-state-replica"
VERSION = 1
SHA256_BYTES = 32

STREAMS = ("accepted", "witness", "diagnostics", "knowledge")

TOP_LEVEL_FIELDS = {
    "format",
    "version",
    "hoa_root_id",
    "current_epoch_sequence",
    "current_manifest_sha256",
    "epoch_lineage",
    "history_streams",
    "required_objects",
}


class CivicAuthorityStateError(ValueError):
    """Raised when a participant authority-state replica is invalid."""


def _map(
    value: object,
    label: str,
    required_fields: set[str],
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise CivicAuthorityStateError(f"{label} must be a map")
    if any(not isinstance(key, str) for key in value):
        raise CivicAuthorityStateError(f"{label} map keys must be text")
    if set(value) != required_fields:
        raise CivicAuthorityStateError(f"{label} fields are invalid")
    return value


def _sha256(value: object, label: str, *, optional: bool = False) -> bytes | None:
    if optional and value is None:
        return None
    if not isinstance(value, bytes) or len(value) != SHA256_BYTES:
        raise CivicAuthorityStateError(f"{label} must be exactly 32 bytes")
    return value


def _uint(
    value: object,
    label: str,
    *,
    positive: bool = False,
) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise CivicAuthorityStateError(f"{label} must be a uint")
    if positive and value == 0:
        raise CivicAuthorityStateError(f"{label} must be greater than zero")
    return value


def _validate_epoch_lineage(
    value: object,
) -> list[Mapping[str, object]]:
    if not isinstance(value, list) or not value:
        raise CivicAuthorityStateError("epoch_lineage must be a nonempty array")

    lineage: list[Mapping[str, object]] = []
    manifest_ids: list[bytes] = []
    signed_ids: list[bytes] = []

    for index, raw in enumerate(value):
        item = _map(
            raw,
            f"epoch_lineage[{index}]",
            {
                "epoch_sequence",
                "manifest_sha256",
                "signed_manifest_sha256",
                "signed_manifest_byte_length",
            },
        )
        sequence = _uint(
            item["epoch_sequence"],
            f"epoch_lineage[{index}].epoch_sequence",
            positive=True,
        )
        if sequence != index + 1:
            raise CivicAuthorityStateError(
                "epoch_lineage must begin at epoch 1 and be contiguous"
            )

        manifest_id = _sha256(
            item["manifest_sha256"],
            f"epoch_lineage[{index}].manifest_sha256",
        )
        signed_id = _sha256(
            item["signed_manifest_sha256"],
            f"epoch_lineage[{index}].signed_manifest_sha256",
        )
        assert manifest_id is not None
        assert signed_id is not None

        _uint(
            item["signed_manifest_byte_length"],
            f"epoch_lineage[{index}].signed_manifest_byte_length",
            positive=True,
        )

        manifest_ids.append(manifest_id)
        signed_ids.append(signed_id)
        lineage.append(item)

    if len(manifest_ids) != len(set(manifest_ids)):
        raise CivicAuthorityStateError(
            "epoch_lineage manifest_sha256 values must be unique"
        )
    if len(signed_ids) != len(set(signed_ids)):
        raise CivicAuthorityStateError(
            "epoch_lineage signed_manifest_sha256 values must be unique"
        )

    return lineage


def _validate_history_streams(
    value: object,
) -> Mapping[str, object]:
    streams = _map(value, "history_streams", set(STREAMS))

    for stream in STREAMS:
        item = _map(
            streams[stream],
            f"history_streams.{stream}",
            {
                "head_sha256",
                "sequence_sha256",
                "byte_length",
            },
        )
        head = _sha256(
            item["head_sha256"],
            f"history_streams.{stream}.head_sha256",
            optional=(stream != "accepted"),
        )
        sequence_id = _sha256(
            item["sequence_sha256"],
            f"history_streams.{stream}.sequence_sha256",
            optional=(stream != "accepted"),
        )
        byte_length = _uint(
            item["byte_length"],
            f"history_streams.{stream}.byte_length",
        )

        if stream == "accepted":
            if head is None or sequence_id is None or byte_length == 0:
                raise CivicAuthorityStateError(
                    "accepted history stream must be present and nonempty"
                )
            continue

        if head is None:
            if sequence_id is not None or byte_length != 0:
                raise CivicAuthorityStateError(
                    f"empty {stream} history requires null sequence and zero length"
                )
        else:
            if sequence_id is None or byte_length == 0:
                raise CivicAuthorityStateError(
                    f"nonempty {stream} history requires sequence identity and bytes"
                )

    return streams


def _validate_required_objects(
    value: object,
) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        raise CivicAuthorityStateError("required_objects must be an array")

    result: list[Mapping[str, object]] = []
    digests: list[bytes] = []

    for index, raw in enumerate(value):
        item = _map(
            raw,
            f"required_objects[{index}]",
            {"sha256", "byte_length"},
        )
        digest = _sha256(
            item["sha256"],
            f"required_objects[{index}].sha256",
        )
        assert digest is not None
        _uint(
            item["byte_length"],
            f"required_objects[{index}].byte_length",
        )
        digests.append(digest)
        result.append(item)

    if digests != sorted(digests):
        raise CivicAuthorityStateError(
            "required_objects must be sorted by SHA-256 bytes"
        )
    if len(digests) != len(set(digests)):
        raise CivicAuthorityStateError(
            "required_objects SHA-256 values must be unique"
        )

    return result


def validate_authority_state_replica(value: Mapping[str, object]) -> None:
    """Validate the machine-readable participant replica inventory."""

    replica = _map(value, "authority_state_replica", TOP_LEVEL_FIELDS)

    if replica["format"] != FORMAT or replica["version"] != VERSION:
        raise CivicAuthorityStateError(
            "authority-state replica format/version is unsupported"
        )

    _sha256(replica["hoa_root_id"], "hoa_root_id")
    current_epoch = _uint(
        replica["current_epoch_sequence"],
        "current_epoch_sequence",
        positive=True,
    )
    current_manifest_id = _sha256(
        replica["current_manifest_sha256"],
        "current_manifest_sha256",
    )
    assert current_manifest_id is not None

    lineage = _validate_epoch_lineage(replica["epoch_lineage"])
    _validate_history_streams(replica["history_streams"])
    _validate_required_objects(replica["required_objects"])

    if len(lineage) != current_epoch:
        raise CivicAuthorityStateError(
            "current_epoch_sequence must equal complete lineage length"
        )

    final_manifest_id = lineage[-1]["manifest_sha256"]
    if final_manifest_id != current_manifest_id:
        raise CivicAuthorityStateError(
            "current_manifest_sha256 must identify final lineage epoch"
        )

    try:
        encode_deterministic(dict(replica))
    except CivicCodecError as exc:
        raise CivicAuthorityStateError(str(exc)) from exc


def encode_authority_state_replica(value: Mapping[str, object]) -> bytes:
    validate_authority_state_replica(value)
    return encode_deterministic(dict(value))


def decode_authority_state_replica(data: bytes) -> dict[str, object]:
    try:
        value = decode_deterministic(data)
    except CivicCodecError as exc:
        raise CivicAuthorityStateError(str(exc)) from exc

    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise CivicAuthorityStateError(
            "authority-state replica must decode to a text-keyed map"
        )

    validate_authority_state_replica(value)
    return value  # type: ignore[return-value]


def authority_state_replica_sha256(
    value_or_bytes: Mapping[str, object] | bytes,
) -> bytes:
    if isinstance(value_or_bytes, bytes):
        decode_authority_state_replica(value_or_bytes)
        data = value_or_bytes
    else:
        data = encode_authority_state_replica(value_or_bytes)
    return hashlib.sha256(data).digest()


def _load_verified(
    load_object: Callable[[bytes], bytes],
    *,
    sha256: bytes,
    byte_length: int,
    label: str,
) -> bytes:
    try:
        data = load_object(sha256)
    except Exception as exc:
        raise CivicAuthorityStateError(f"{label} is unavailable") from exc

    try:
        verify_object_bytes(
            data,
            expected_sha256=sha256,
            expected_byte_length=byte_length,
        )
    except CivicObjectStoreError as exc:
        raise CivicAuthorityStateError(f"{label} failed exact-byte verification") from exc

    return data


def verify_authority_state_replica(
    value: Mapping[str, object],
    *,
    load_object: Callable[[bytes], bytes],
) -> tuple[dict[str, object], ...]:
    """Verify retained replica bytes and return the verified Epoch Manifest lineage.

    The loader resolves exact bytes by SHA-256. This verifier checks signed Epoch
    Manifests, lineage continuity, externally retained required objects, and each
    retained history record as an authenticated Civic signed-history envelope.
    Only an authenticated history_link is accepted for predecessor-chain and
    final-head verification.
    """

    validate_authority_state_replica(value)

    hoa_root_id = value["hoa_root_id"]
    current_manifest_id = value["current_manifest_sha256"]
    lineage_descriptors = value["epoch_lineage"]
    required_descriptors = value["required_objects"]
    history_descriptors = value["history_streams"]

    assert isinstance(hoa_root_id, bytes)
    assert isinstance(current_manifest_id, bytes)
    assert isinstance(lineage_descriptors, list)
    assert isinstance(required_descriptors, list)
    assert isinstance(history_descriptors, Mapping)

    verified_lineage: list[dict[str, object]] = []
    previous_manifest_id: bytes | None = None
    externally_required: dict[bytes, int] = {}
    inline_available: dict[bytes, int] = {}

    for index, raw_descriptor in enumerate(lineage_descriptors):
        descriptor = raw_descriptor
        assert isinstance(descriptor, Mapping)
        signed_id = descriptor["signed_manifest_sha256"]
        signed_length = descriptor["signed_manifest_byte_length"]
        expected_manifest_id = descriptor["manifest_sha256"]
        expected_epoch = descriptor["epoch_sequence"]
        assert isinstance(signed_id, bytes)
        assert isinstance(signed_length, int)
        assert isinstance(expected_manifest_id, bytes)
        assert isinstance(expected_epoch, int)

        signed_bytes = _load_verified(
            load_object,
            sha256=signed_id,
            byte_length=signed_length,
            label=f"signed Epoch Manifest {expected_epoch}",
        )

        try:
            manifest = verify_signed_epoch_manifest(signed_bytes)
        except CivicSignedManifestError as exc:
            raise CivicAuthorityStateError(
                f"signed Epoch Manifest {expected_epoch} failed verification"
            ) from exc

        actual_manifest_id = manifest_sha256(manifest)
        if actual_manifest_id != expected_manifest_id:
            raise CivicAuthorityStateError(
                f"Epoch Manifest {expected_epoch} payload identity mismatch"
            )
        if manifest["hoa_root_id"] != hoa_root_id:
            raise CivicAuthorityStateError(
                f"Epoch Manifest {expected_epoch} HOA root mismatch"
            )
        if manifest["epoch_sequence"] != expected_epoch:
            raise CivicAuthorityStateError(
                f"Epoch Manifest {expected_epoch} sequence mismatch"
            )
        if manifest["predecessor_manifest_sha256"] != previous_manifest_id:
            raise CivicAuthorityStateError(
                f"Epoch Manifest {expected_epoch} predecessor mismatch"
            )

        object_index = manifest["object_index"]
        governing_sources = manifest["governing_sources"]
        assert isinstance(object_index, list)
        assert isinstance(governing_sources, list)

        for raw_object in object_index:
            assert isinstance(raw_object, Mapping)
            digest = raw_object["sha256"]
            length = raw_object["byte_length"]
            inline = raw_object["inline"]
            assert isinstance(digest, bytes)
            assert isinstance(length, int)
            if inline is None:
                old = externally_required.get(digest)
                if old is not None and old != length:
                    raise CivicAuthorityStateError(
                        "authority object has conflicting byte lengths"
                    )
                externally_required[digest] = length
            else:
                old = inline_available.get(digest)
                if old is not None and old != length:
                    raise CivicAuthorityStateError(
                        "inline authority object has conflicting byte lengths"
                    )
                inline_available[digest] = length

        for raw_source in governing_sources:
            assert isinstance(raw_source, Mapping)
            digest = raw_source["sha256"]
            length = raw_source["byte_length"]
            assert isinstance(digest, bytes)
            assert isinstance(length, int)
            if digest not in inline_available:
                old = externally_required.get(digest)
                if old is not None and old != length:
                    raise CivicAuthorityStateError(
                        "governing source has conflicting byte lengths"
                    )
                externally_required[digest] = length

        verified_lineage.append(manifest)
        previous_manifest_id = actual_manifest_id

    if previous_manifest_id != current_manifest_id:
        raise CivicAuthorityStateError(
            "verified lineage does not end at current manifest identity"
        )

    declared_required: dict[bytes, int] = {}
    for raw_descriptor in required_descriptors:
        assert isinstance(raw_descriptor, Mapping)
        digest = raw_descriptor["sha256"]
        length = raw_descriptor["byte_length"]
        assert isinstance(digest, bytes)
        assert isinstance(length, int)
        declared_required[digest] = length

    for digest, length in externally_required.items():
        if digest in inline_available:
            continue
        if declared_required.get(digest) != length:
            raise CivicAuthorityStateError(
                "required_objects does not completely cover authority-required bytes"
            )

    for digest, length in declared_required.items():
        _load_verified(
            load_object,
            sha256=digest,
            byte_length=length,
            label=f"required authority object {digest.hex()}",
        )

    current_manifest = verified_lineage[-1]
    current_history = current_manifest["history"]
    assert isinstance(current_history, Mapping)

    manifest_head_fields = {
        "accepted": "accepted_history_head_sha256",
        "witness": "witness_head_sha256",
        "diagnostics": "diagnostics_head_sha256",
        "knowledge": "knowledge_head_sha256",
    }

    for stream in STREAMS:
        raw_stream = history_descriptors[stream]
        assert isinstance(raw_stream, Mapping)
        head = raw_stream["head_sha256"]
        sequence_id = raw_stream["sequence_sha256"]
        byte_length = raw_stream["byte_length"]

        expected_head = current_history[manifest_head_fields[stream]]
        if head != expected_head:
            raise CivicAuthorityStateError(
                f"{stream} replica history head does not match current Epoch Manifest"
            )

        if head is None:
            continue

        assert isinstance(head, bytes)
        assert isinstance(sequence_id, bytes)
        assert isinstance(byte_length, int)

        sequence_bytes = _load_verified(
            load_object,
            sha256=sequence_id,
            byte_length=byte_length,
            label=f"{stream} history sequence",
        )

        def authenticated_link_for_record(record: object) -> object:
            encoded = getattr(record, "encoded", None)
            sha256 = getattr(record, "sha256", None)
            if not isinstance(encoded, bytes) or not isinstance(sha256, bytes):
                raise CivicHistoryError(
                    "history sequence item does not expose exact record bytes"
                )

            try:
                verified = verify_signed_history_record(
                    encoded,
                    epoch_manifests=verified_lineage,
                )
            except CivicSignedHistoryRecordError as exc:
                raise CivicHistoryError(
                    "history record signed-envelope verification failed"
                ) from exc

            if verified.record_sha256 != sha256:
                raise CivicHistoryError(
                    "verified signed history record identity mismatch"
                )

            return verified.payload["history_link"]

        try:
            verify_linked_history_sequence(
                sequence_bytes,
                stream=stream,
                expected_head_sha256=head,
                authenticated_link_for_record=authenticated_link_for_record,
            )
        except CivicHistoryError as exc:
            raise CivicAuthorityStateError(
                f"{stream} signed history sequence verification failed"
            ) from exc

    return tuple(verified_lineage)
