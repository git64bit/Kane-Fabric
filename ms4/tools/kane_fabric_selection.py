#!/usr/bin/env python3
"""MS4 substrate partition-selection manifest compiler."""

from __future__ import annotations

import hashlib
import json
import struct
from collections.abc import Mapping
from pathlib import Path

from ms4.tools.kane_fabric_partition import canonical_json_bytes, validate_partition_descriptor
from ms4.tools.kane_fabric_scope import normalize_bounds, partition_bounds, partition_includes_bounds

FORMAT = "kane-fabric-substrate-partition-selection"
VERSION = 1
_MAGIC = {"roads": b"KFSR001\n", "water": b"KFSW001\n"}
_ROLE_PATH = {
    "county_overview": "county-overview.json",
    "roads": "roads-lod.kfs",
    "water": "water-lod.kfs",
}


class SelectionContractError(ValueError):
    pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_canonical_json(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SelectionContractError(f"{path.name} is invalid JSON: {exc}") from exc
    if not isinstance(value, dict) or canonical_json_bytes(value) != data:
        raise SelectionContractError(f"{path.name} is not canonical JSON")
    return value


def _component_by_role(manifest: Mapping[str, object], role: str) -> dict[str, object]:
    components = manifest.get("components")
    if not isinstance(components, list):
        raise SelectionContractError("substrate manifest components are invalid")
    matches = [item for item in components if isinstance(item, dict) and item.get("role") == role]
    if len(matches) != 1:
        raise SelectionContractError(f"substrate manifest must contain one {role} component")
    return matches[0]


def _read_flat_index(path: Path, role: str) -> tuple[dict[str, object], int]:
    with path.open("rb") as stream:
        prefix = stream.read(16)
        if len(prefix) != 16 or prefix[:8] != _MAGIC[role]:
            raise SelectionContractError(f"{role} component prefix is invalid")
        index_length = struct.unpack(">Q", prefix[8:16])[0]
        index_bytes = stream.read(index_length)
    if len(index_bytes) != index_length:
        raise SelectionContractError(f"{role} component index is truncated")
    try:
        index = json.loads(index_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SelectionContractError(f"{role} component index is invalid JSON") from exc
    if not isinstance(index, dict) or canonical_json_bytes(index) != index_bytes:
        raise SelectionContractError(f"{role} component index is not canonical JSON")
    return index, 16 + index_length


def build_selection_manifest(
    package_dir: Path,
    partition: Mapping[str, object],
    *,
    road_level: str = "orientation",
    water_level: str = "overview",
) -> dict[str, object]:
    """Select exact canonical substrate chunks intersecting a logical partition."""

    descriptor = validate_partition_descriptor(partition)
    package_dir = package_dir.resolve()
    manifest_path = package_dir / "substrate-manifest.json"
    manifest = _read_canonical_json(manifest_path)
    if manifest.get("format") != "kane-fabric-substrate-manifest" or manifest.get("version") != 1:
        raise SelectionContractError("substrate manifest format/version is unsupported")
    if canonical_json_bytes(manifest.get("jurisdiction")) != canonical_json_bytes(descriptor["jurisdiction"]):
        raise SelectionContractError("partition and substrate jurisdictions differ")
    substrate_identity = manifest.get("substrate_content_sha256")
    if not isinstance(substrate_identity, str) or len(substrate_identity) != 64:
        raise SelectionContractError("substrate content identity is invalid")

    selections: list[dict[str, object]] = []
    overview = _component_by_role(manifest, "county_overview")
    overview_path = package_dir / str(overview.get("path"))
    if overview_path.name != _ROLE_PATH["county_overview"]:
        raise SelectionContractError("county overview path violates v1 contract")
    if overview_path.stat().st_size != overview.get("byte_length") or _sha256_file(overview_path) != overview.get("sha256"):
        raise SelectionContractError("county overview bytes disagree with substrate manifest")
    selections.append(
        {
            "role": "county_overview",
            "path": overview_path.name,
            "component_byte_length": overview["byte_length"],
            "component_sha256": overview["sha256"],
            "selection": "whole-component-reference",
        }
    )

    for role, level_key in (("roads", road_level), ("water", water_level)):
        component = _component_by_role(manifest, role)
        path = package_dir / str(component.get("path"))
        if path.name != _ROLE_PATH[role]:
            raise SelectionContractError(f"{role} path violates v1 contract")
        if path.stat().st_size != component.get("byte_length") or _sha256_file(path) != component.get("sha256"):
            raise SelectionContractError(f"{role} bytes disagree with substrate manifest")
        index, payload_start = _read_flat_index(path, role)
        levels = index.get("levels")
        if not isinstance(levels, list):
            raise SelectionContractError(f"{role} levels are invalid")
        matches = [item for item in levels if isinstance(item, dict) and item.get("key") == level_key]
        if len(matches) != 1 or not isinstance(matches[0].get("chunks"), list):
            raise SelectionContractError(f"{role} level {level_key!r} is unavailable")
        selected_chunks: list[dict[str, object]] = []
        for ordinal, chunk in enumerate(matches[0]["chunks"]):
            if not isinstance(chunk, dict) or not isinstance(chunk.get("bounds"), list):
                raise SelectionContractError(f"{role} chunk metadata is invalid")
            if not partition_includes_bounds(descriptor, chunk["bounds"]):
                continue
            selected_chunks.append(
                {
                    "ordinal": ordinal,
                    "bounds": normalize_bounds(chunk["bounds"]),
                    "offset": int(chunk["offset"]),
                    "length": int(chunk["length"]),
                    "absolute_start": payload_start + int(chunk["offset"]),
                    "payload_sha256": str(chunk["payload_sha256"]),
                    "records_sha256": str(chunk["records_sha256"]),
                    "feature_count": int(chunk["feature_count"]),
                }
            )
        selections.append(
            {
                "role": role,
                "path": path.name,
                "component_byte_length": component["byte_length"],
                "component_sha256": component["sha256"],
                "index_byte_length": payload_start - 16,
                "level": level_key,
                "selected_chunks": selected_chunks,
            }
        )

    body = {
        "format": FORMAT,
        "version": VERSION,
        "jurisdiction": descriptor["jurisdiction"],
        "partition_key": descriptor["partition_key"],
        "partition_definition_sha256": descriptor["definition_sha256"],
        "partition_bounds": partition_bounds(descriptor),
        "substrate_content_sha256": substrate_identity,
        "components": selections,
    }
    return {**body, "selection_sha256": hashlib.sha256(canonical_json_bytes(body)).hexdigest()}
