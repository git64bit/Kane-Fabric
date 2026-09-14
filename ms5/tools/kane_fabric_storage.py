#!/usr/bin/env python3
"""MS5 immutable storage inventory and activation-state contract."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath

from ms5.tools.common import ContractError, canonical_json_bytes, nonempty_text, sha256_text
from ms5.tools.kane_fabric_edge import validate_edge_instance

INVENTORY_FORMAT = "kane-fabric-edge-storage-inventory"
ACTIVATION_FORMAT = "kane-fabric-edge-activation-state"
VERSION = 1


class StorageContractError(ContractError):
    pass


def _logical_path(value: object) -> str:
    text = nonempty_text(value, "artifact.path")
    path = PurePosixPath(text)
    if (
        "\\" in text
        or path.is_absolute()
        or text.startswith("/")
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        raise StorageContractError("artifact.path must be a normalized relative POSIX path")
    normalized = path.as_posix()
    if normalized != text:
        raise StorageContractError("artifact.path is not normalized")
    return normalized


def _artifact(value: Mapping[str, object]) -> dict[str, object]:
    if set(value) != {"artifact_key", "path", "byte_length", "sha256"}:
        raise StorageContractError("artifact keys are invalid")
    key = nonempty_text(value["artifact_key"], "artifact.artifact_key")
    length = value["byte_length"]
    if isinstance(length, bool) or not isinstance(length, int) or length < 0:
        raise StorageContractError("artifact.byte_length must be a nonnegative integer")
    return {
        "artifact_key": key,
        "path": _logical_path(value["path"]),
        "byte_length": length,
        "sha256": sha256_text(value["sha256"], "artifact.sha256"),
    }


def _artifacts(values: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    if isinstance(values, (str, bytes, bytearray)):
        raise StorageContractError("artifacts must be an array")
    normalized = [_artifact(value) for value in values]
    normalized.sort(key=lambda item: item["artifact_key"])
    keys = [item["artifact_key"] for item in normalized]
    paths = [item["path"] for item in normalized]
    if len(keys) != len(set(keys)):
        raise StorageContractError("artifact_key values must be unique")
    if len(paths) != len(set(paths)):
        raise StorageContractError("artifact paths must be unique")
    if not normalized:
        raise StorageContractError("inventory must contain at least one artifact")
    return normalized


def build_inventory(
    *,
    logical_placement_sha256: str,
    artifacts: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    body = {
        "logical_placement_sha256": sha256_text(
            logical_placement_sha256, "logical_placement_sha256"
        ),
        "artifacts": _artifacts(artifacts),
    }
    return {
        "format": INVENTORY_FORMAT,
        "version": VERSION,
        **body,
        "inventory_sha256": hashlib.sha256(canonical_json_bytes(body)).hexdigest(),
    }


def validate_inventory(value: Mapping[str, object]) -> None:
    if set(value) != {
        "format",
        "version",
        "logical_placement_sha256",
        "artifacts",
        "inventory_sha256",
    }:
        raise StorageContractError("inventory keys are invalid")
    if value["format"] != INVENTORY_FORMAT or value["version"] != VERSION:
        raise StorageContractError("inventory format/version is unsupported")
    artifacts = value["artifacts"]
    if not isinstance(artifacts, Sequence) or isinstance(artifacts, (str, bytes, bytearray)):
        raise StorageContractError("artifacts must be an array")
    normalized = {
        "logical_placement_sha256": sha256_text(
            value["logical_placement_sha256"], "logical_placement_sha256"
        ),
        "artifacts": _artifacts(artifacts),
    }
    if list(artifacts) != normalized["artifacts"]:
        raise StorageContractError("inventory artifacts are not normalized")
    expected = hashlib.sha256(canonical_json_bytes(normalized)).hexdigest()
    if value["inventory_sha256"] != expected:
        raise StorageContractError("inventory identity is invalid")


def verify_inventory_files(value: Mapping[str, object], root: Path) -> None:
    validate_inventory(value)
    root = root.resolve()
    for artifact in value["artifacts"]:
        path = (root / str(artifact["path"])).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise StorageContractError("artifact escaped storage root") from exc
        if not path.is_file():
            raise StorageContractError(f"artifact is missing: {artifact['path']}")
        if path.stat().st_size != artifact["byte_length"]:
            raise StorageContractError(f"artifact byte length mismatch: {artifact['path']}")
        digest_state = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(64 * 1024), b""):
                digest_state.update(chunk)
        digest = digest_state.hexdigest()
        if digest != artifact["sha256"]:
            raise StorageContractError(f"artifact SHA-256 mismatch: {artifact['path']}")


def build_activation_state(
    *, active_inventory_sha256: str | None, rollback_inventory_sha256: str | None
) -> dict[str, object]:
    if active_inventory_sha256 is not None:
        active_inventory_sha256 = sha256_text(
            active_inventory_sha256, "active_inventory_sha256"
        )
    if rollback_inventory_sha256 is not None:
        rollback_inventory_sha256 = sha256_text(
            rollback_inventory_sha256, "rollback_inventory_sha256"
        )
    if active_inventory_sha256 is None and rollback_inventory_sha256 is not None:
        raise StorageContractError("rollback inventory requires an active inventory")
    if active_inventory_sha256 is not None and active_inventory_sha256 == rollback_inventory_sha256:
        raise StorageContractError("active and rollback inventories must differ")
    return {
        "format": ACTIVATION_FORMAT,
        "version": VERSION,
        "active_inventory_sha256": active_inventory_sha256,
        "rollback_inventory_sha256": rollback_inventory_sha256,
    }


def validate_activation_state(value: Mapping[str, object]) -> None:
    if set(value) != {
        "format",
        "version",
        "active_inventory_sha256",
        "rollback_inventory_sha256",
    }:
        raise StorageContractError("activation-state keys are invalid")
    if value["format"] != ACTIVATION_FORMAT or value["version"] != VERSION:
        raise StorageContractError("activation-state format/version is unsupported")
    normalized = build_activation_state(
        active_inventory_sha256=value["active_inventory_sha256"],
        rollback_inventory_sha256=value["rollback_inventory_sha256"],
    )
    if dict(value) != normalized:
        raise StorageContractError("activation state is not normalized")


def activate_inventory(
    state: Mapping[str, object],
    candidate: Mapping[str, object],
    *,
    edge_instance: Mapping[str, object],
    verified_inventory_sha256: str,
) -> dict[str, object]:
    validate_activation_state(state)
    validate_inventory(candidate)
    validate_edge_instance(edge_instance)

    edge_logical = edge_instance["logical"]
    expected_placement = edge_logical["logical_placement_sha256"]
    if candidate["logical_placement_sha256"] != expected_placement:
        raise StorageContractError(
            "candidate inventory logical placement does not match edge logical placement"
        )

    candidate_sha = str(candidate["inventory_sha256"])
    verified_sha = sha256_text(
        verified_inventory_sha256, "verified_inventory_sha256"
    )
    if verified_sha != candidate_sha:
        raise StorageContractError(
            "verified inventory identity does not match activation candidate"
        )
    active = state["active_inventory_sha256"]
    if active == candidate_sha:
        return dict(state)
    return build_activation_state(
        active_inventory_sha256=candidate_sha,
        rollback_inventory_sha256=active,
    )


def rollback_activation(state: Mapping[str, object]) -> dict[str, object]:
    validate_activation_state(state)
    rollback = state["rollback_inventory_sha256"]
    if rollback is None:
        raise StorageContractError("no rollback inventory is available")
    return build_activation_state(
        active_inventory_sha256=rollback,
        rollback_inventory_sha256=state["active_inventory_sha256"],
    )


def recover_activation(
    state: Mapping[str, object],
    verified_inventory_sha256: set[str],
) -> dict[str, object]:
    validate_activation_state(state)
    verified = {
        sha256_text(value, "verified_inventory_sha256")
        for value in verified_inventory_sha256
    }
    active = state["active_inventory_sha256"]
    rollback = state["rollback_inventory_sha256"]
    if active is not None and active in verified:
        return dict(state)
    if rollback is not None and rollback in verified:
        return build_activation_state(
            active_inventory_sha256=rollback,
            rollback_inventory_sha256=None,
        )
    raise StorageContractError("neither active nor rollback inventory is verified")
