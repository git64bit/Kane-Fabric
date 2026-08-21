#!/usr/bin/env python3
"""MS4 normalized geographic scope and inclusion semantics."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN

from ms4.tools.kane_fabric_partition import (
    PartitionContractError,
    _require_exact_keys,
    build_partition_descriptor,
    canonical_json_bytes,
    validate_partition_descriptor,
)

COORDINATE_PLACES = Decimal("0.0000001")
_SUPPORTED_SCOPE_CLASSES = frozenset({"whole-jurisdiction", "bounded-region", "administrative", "composite"})


def normalize_coordinate(value: object, *, latitude: bool = False) -> str:
    if isinstance(value, bool):
        raise PartitionContractError("coordinate must be numeric")
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise PartitionContractError("coordinate must be numeric") from exc
    if not decimal.is_finite():
        raise PartitionContractError("coordinate must be finite")
    limit = Decimal("90") if latitude else Decimal("180")
    if decimal < -limit or decimal > limit:
        raise PartitionContractError("coordinate is outside WGS84 range")
    quantized = decimal.quantize(COORDINATE_PLACES, rounding=ROUND_HALF_EVEN)
    if quantized == 0:
        quantized = abs(quantized)
    return f"{quantized:.7f}"


def normalize_bounds(bounds: Sequence[object]) -> list[str]:
    if len(bounds) != 4:
        raise PartitionContractError("bounds must contain four coordinates")
    result = [
        normalize_coordinate(bounds[0]),
        normalize_coordinate(bounds[1], latitude=True),
        normalize_coordinate(bounds[2]),
        normalize_coordinate(bounds[3], latitude=True),
    ]
    min_x, min_y, max_x, max_y = map(Decimal, result)
    if min_x >= max_x or min_y >= max_y:
        raise PartitionContractError("bounds must have positive width and height")
    return result


def whole_jurisdiction_scope() -> dict[str, object]:
    return {"scope_class": "whole-jurisdiction", "definition": {"jurisdiction": True}}


def bounded_region_scope(bounds: Sequence[object]) -> dict[str, object]:
    return {"scope_class": "bounded-region", "definition": {"bounds": normalize_bounds(bounds), "srs_id": 4326}}


def _text(value: object, label: str) -> str:
    text = str(value).strip()
    if not text:
        raise PartitionContractError(f"{label} must be nonempty")
    return text


def _sha(value: object, label: str) -> str:
    text = str(value)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise PartitionContractError(f"{label} must be 64 lowercase hex characters")
    return text


def administrative_scope(*, administrative_kind: str, name: str, bounds: Sequence[object], boundary_lineage: Mapping[str, object]) -> dict[str, object]:
    if administrative_kind not in {"municipality", "township-or-equivalent"}:
        raise PartitionContractError("administrative_kind is unsupported")
    _require_exact_keys(boundary_lineage, {"dataset_key", "release_key", "content_sha256", "feature_id", "geometry_sha256"}, "administrative boundary lineage")
    boundary = {
        "dataset_key": _text(boundary_lineage["dataset_key"], "boundary dataset_key"),
        "release_key": _text(boundary_lineage["release_key"], "boundary release_key"),
        "content_sha256": _sha(boundary_lineage["content_sha256"], "boundary content_sha256"),
        "feature_id": _text(boundary_lineage["feature_id"], "boundary feature_id"),
        "geometry_sha256": _sha(boundary_lineage["geometry_sha256"], "boundary geometry_sha256"),
    }
    return {
        "scope_class": "administrative",
        "definition": {
            "administrative_kind": administrative_kind,
            "name": _text(name, "administrative name"),
            "bounds": normalize_bounds(bounds),
            "boundary": boundary,
            "srs_id": 4326,
        },
    }


def partition_bounds(partition: Mapping[str, object]) -> list[str] | None:
    descriptor = validate_partition_descriptor(partition)
    scope = descriptor["scope"]
    scope_class = scope["scope_class"]
    if scope_class not in _SUPPORTED_SCOPE_CLASSES:
        raise PartitionContractError(f"scope_class {scope_class!r} has no v1 inclusion semantics")
    if scope_class == "whole-jurisdiction":
        return None
    bounds = scope["definition"].get("bounds")
    if bounds is None:
        return None
    if not isinstance(bounds, Sequence) or isinstance(bounds, (str, bytes, bytearray)):
        raise PartitionContractError("scope bounds are invalid")
    normalized = normalize_bounds(bounds)
    if list(bounds) != normalized:
        raise PartitionContractError("scope bounds are not normalized")
    return normalized


def composite_scope(partitions: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if len(partitions) < 2:
        raise PartitionContractError("composite scope requires at least two partitions")
    validated = [validate_partition_descriptor(item) for item in partitions]
    if len({canonical_json_bytes(item["jurisdiction"]) for item in validated}) != 1:
        raise PartitionContractError("composite partitions must share one jurisdiction")
    keys = sorted(str(item["partition_key"]) for item in validated)
    if len(set(keys)) != len(keys):
        raise PartitionContractError("composite partitions must be unique")
    member_bounds = [partition_bounds(item) for item in validated]
    if any(item is None for item in member_bounds):
        bounds = None
    else:
        values = [tuple(map(Decimal, item)) for item in member_bounds if item is not None]
        bounds = [
            normalize_coordinate(min(item[0] for item in values)),
            normalize_coordinate(min(item[1] for item in values), latitude=True),
            normalize_coordinate(max(item[2] for item in values)),
            normalize_coordinate(max(item[3] for item in values), latitude=True),
        ]
    return {"scope_class": "composite", "definition": {"members": keys, "bounds": bounds, "operation": "union", "srs_id": 4326}}


def bounds_intersect(first: Sequence[object], second: Sequence[object]) -> bool:
    a = tuple(map(Decimal, normalize_bounds(first)))
    b = tuple(map(Decimal, normalize_bounds(second)))
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


def partition_includes_bounds(partition: Mapping[str, object], candidate_bounds: Sequence[object]) -> bool:
    bounds = partition_bounds(partition)
    return True if bounds is None else bounds_intersect(bounds, candidate_bounds)
