#!/usr/bin/env python3
"""Build and validate Kane Fabric v1 water LOD flat components."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

FOX_DATASET_KEY = "water-fox-river"
CREEK_DATASET_KEY = "water-creeks"
LEVEL_KEYS = ("overview", "context", "detail")
SCORE_SCALE = 10_000_000
CONTEXT_CREEK_SHARE_PPM = 600_000
MORTON_BITS = 16
CHUNK_FEATURES = 256
SIMPLIFICATION_DIVISORS = {"overview": 2048, "context": 8192}


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load support module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = _load_module(
    "_kane_fabric_water_contract",
    Path(__file__).resolve().with_name("kane_fabric_substrate.py"),
)
COMPRESSION = _load_module(
    "_kane_fabric_water_compression",
    Path(__file__).resolve().with_name("kane_fabric_compression.py"),
)
FABRIC_READ = _load_module(
    "_kane_fabric_water_read",
    ROOT / "database" / "tools" / "kane_fabric_read.py",
)


@dataclass(frozen=True)
class WaterFeature:
    dataset_key: str
    source_feature_id: str
    geometry_type: str
    coordinates: object
    bounds: tuple[float, float, float, float]
    score: int
    source_vertex_count: int


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def geometry_lines(geometry_type: str, coordinates: object):
    if geometry_type == "LineString":
        values = [coordinates]
    elif geometry_type == "MultiLineString":
        values = coordinates
    else:
        raise RuntimeError(f"Water line has unsupported geometry type: {geometry_type}")
    if not isinstance(values, (list, tuple)) or not values:
        raise RuntimeError("Water line geometry contains no components")
    result = []
    for line in values:
        if not isinstance(line, (list, tuple)) or len(line) < 2:
            raise RuntimeError("Water line component contains fewer than two positions")
        result.append([(float(x), float(y)) for x, y in line])
    return result


def geometry_polygons(geometry_type: str, coordinates: object):
    if geometry_type == "Polygon":
        values = [coordinates]
    elif geometry_type == "MultiPolygon":
        values = coordinates
    else:
        raise RuntimeError(f"Water polygon has unsupported geometry type: {geometry_type}")
    if not isinstance(values, (list, tuple)) or not values:
        raise RuntimeError("Water polygon geometry contains no polygons")
    polygons = []
    for polygon in values:
        if not isinstance(polygon, (list, tuple)) or not polygon:
            raise RuntimeError("Water polygon contains no rings")
        rings = []
        for ring in polygon:
            if not isinstance(ring, (list, tuple)) or len(ring) < 4:
                raise RuntimeError("Water polygon ring contains fewer than four positions")
            normalized = [(float(x), float(y)) for x, y in ring]
            if normalized[0] != normalized[-1]:
                raise RuntimeError("Water polygon ring is not closed")
            if len(set(normalized[:-1])) < 3:
                raise RuntimeError("Water polygon ring contains fewer than three unique positions")
            rings.append(normalized)
        polygons.append(rings)
    return polygons


def iter_positions(geometry_type: str, coordinates: object) -> Iterable[tuple[float, float]]:
    if geometry_type in ("LineString", "MultiLineString"):
        for line in geometry_lines(geometry_type, coordinates):
            yield from line
        return
    if geometry_type in ("Polygon", "MultiPolygon"):
        for polygon in geometry_polygons(geometry_type, coordinates):
            for ring in polygon:
                yield from ring
        return
    raise RuntimeError(f"Water geometry has unsupported type: {geometry_type}")


def geometry_bounds(geometry_type: str, coordinates: object):
    positions = list(iter_positions(geometry_type, coordinates))
    if not positions:
        raise RuntimeError("Water geometry contains no positions")
    xs = [point[0] for point in positions]
    ys = [point[1] for point in positions]
    return min(xs), min(ys), max(xs), max(ys)


def geometry_vertex_count(geometry_type: str, coordinates: object) -> int:
    return sum(1 for _ in iter_positions(geometry_type, coordinates))


def _distance_sq(point, start, end) -> float:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    if dx == 0.0 and dy == 0.0:
        px = point[0] - start[0]
        py = point[1] - start[1]
        return px * px + py * py
    t = ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / (
        dx * dx + dy * dy
    )
    t = min(1.0, max(0.0, t))
    qx = start[0] + t * dx
    qy = start[1] + t * dy
    px = point[0] - qx
    py = point[1] - qy
    return px * px + py * py


def simplify_open(points: Sequence[tuple[float, float]], tolerance: float):
    if len(points) <= 2 or tolerance <= 0.0:
        return list(points)
    threshold = tolerance * tolerance
    keep = {0, len(points) - 1}
    stack = [(0, len(points) - 1)]
    while stack:
        first, last = stack.pop()
        best_index = -1
        best_distance = -1.0
        for index in range(first + 1, last):
            distance = _distance_sq(points[index], points[first], points[last])
            if distance > best_distance:
                best_distance = distance
                best_index = index
        if best_index >= 0 and best_distance > threshold:
            keep.add(best_index)
            stack.append((first, best_index))
            stack.append((best_index, last))
    return [points[index] for index in sorted(keep)]


def simplify_line(points: Sequence[tuple[float, float]], tolerance: float):
    simplified = simplify_open(points, tolerance)
    if len(set(simplified)) < 2:
        return [points[0], points[-1]]
    return simplified


def simplify_ring(ring: Sequence[tuple[float, float]], tolerance: float):
    if len(ring) < 4 or ring[0] != ring[-1]:
        raise RuntimeError("Accepted water polygon ring is not a valid closed ring")
    points = list(ring[:-1])
    if tolerance <= 0.0 or len(points) <= 3:
        return points + [points[0]]

    anchor_index = min(
        range(len(points)), key=lambda index: (points[index][0], points[index][1], index)
    )
    rotated = points[anchor_index:] + points[:anchor_index]
    anchor = rotated[0]
    split_index = max(
        range(1, len(rotated)),
        key=lambda index: (_distance_sq(rotated[index], anchor, anchor), -index),
    )
    first = simplify_open(rotated[: split_index + 1], tolerance)
    second = simplify_open(rotated[split_index:] + [anchor], tolerance)
    simplified = first[:-1] + second[:-1]
    if len(set(simplified)) < 3:
        return points + [points[0]]
    return simplified + [simplified[0]]


def simplify_geometry(geometry_type: str, coordinates: object, tolerance: float):
    if geometry_type in ("LineString", "MultiLineString"):
        lines = [
            simplify_line(line, tolerance)
            for line in geometry_lines(geometry_type, coordinates)
        ]
        return lines[0] if geometry_type == "LineString" else lines
    if geometry_type in ("Polygon", "MultiPolygon"):
        polygons = [
            [simplify_ring(ring, tolerance) for ring in polygon]
            for polygon in geometry_polygons(geometry_type, coordinates)
        ]
        return polygons[0] if geometry_type == "Polygon" else polygons
    raise RuntimeError(f"Water geometry has unsupported type: {geometry_type}")


def coordinate_length_score(geometry_type: str, coordinates: object) -> int:
    if geometry_type not in ("LineString", "MultiLineString"):
        raise RuntimeError("Coordinate-length score is only defined for creek linework")
    score = 0
    for line in geometry_lines(geometry_type, coordinates):
        for start, end in zip(line, line[1:]):
            dx = round((end[0] - start[0]) * SCORE_SCALE)
            dy = round((end[1] - start[1]) * SCORE_SCALE)
            score += math.isqrt(dx * dx + dy * dy)
    return max(1, score)


def _feature_from_read(item, dataset_key: str) -> WaterFeature:
    geometry_type = item.geometry_type
    if dataset_key == FOX_DATASET_KEY:
        if geometry_type not in ("Polygon", "MultiPolygon"):
            raise RuntimeError(
                f"Fox River feature {item.source_feature_id} is {geometry_type}; "
                "expected polygon geometry"
            )
        score = 0
    elif dataset_key == CREEK_DATASET_KEY:
        if geometry_type not in ("LineString", "MultiLineString"):
            raise RuntimeError(
                f"Creek feature {item.source_feature_id} is {geometry_type}; "
                "expected linear geometry"
            )
        score = coordinate_length_score(geometry_type, item.coordinates)
    else:
        raise RuntimeError(f"Unsupported water dataset: {dataset_key}")
    return WaterFeature(
        dataset_key=dataset_key,
        source_feature_id=item.source_feature_id,
        geometry_type=geometry_type,
        coordinates=item.coordinates,
        bounds=item.bounds,
        score=score,
        source_vertex_count=geometry_vertex_count(geometry_type, item.coordinates),
    )


def load_accepted_water(database: Path):
    fox = FABRIC_READ.load_accepted_map_layer(database, FOX_DATASET_KEY)
    creeks = FABRIC_READ.load_accepted_map_layer(database, CREEK_DATASET_KEY)

    fox_jurisdiction = CONTRACT.validate_jurisdiction(fox.release.jurisdiction)
    creek_jurisdiction = CONTRACT.validate_jurisdiction(creeks.release.jurisdiction)
    if fox_jurisdiction != creek_jurisdiction:
        raise RuntimeError(
            "Accepted Fox River and creek releases do not belong to the same jurisdiction"
        )

    sources = [
        CONTRACT.validate_release_descriptor(creeks.release.descriptor()),
        CONTRACT.validate_release_descriptor(fox.release.descriptor()),
    ]
    sources.sort(key=lambda item: str(item["dataset_key"]))

    fox_features = [
        _feature_from_read(item, FOX_DATASET_KEY) for item in fox.features
    ]
    creek_features = [
        _feature_from_read(item, CREEK_DATASET_KEY) for item in creeks.features
    ]
    all_features = fox_features + creek_features
    extent = (
        min(item.bounds[0] for item in all_features),
        min(item.bounds[1] for item in all_features),
        max(item.bounds[2] for item in all_features),
        max(item.bounds[3] for item in all_features),
    )
    return fox_jurisdiction, sources, fox_features, creek_features, extent


def _prefix_for_share(features: Sequence[WaterFeature], share_ppm: int):
    ranked = sorted(features, key=lambda item: (-item.score, item.source_feature_id))
    total = sum(item.score for item in ranked)
    if total <= 0:
        raise RuntimeError("Accepted creek coordinate-length score is zero")
    selected = []
    selected_score = 0
    for feature in ranked:
        selected.append(feature)
        selected_score += feature.score
        if selected_score * 1_000_000 >= total * share_ppm:
            break
    return selected, total, selected_score


def level_membership(
    fox_features: Sequence[WaterFeature],
    creek_features: Sequence[WaterFeature],
):
    context_creeks, total_score, context_score = _prefix_for_share(
        creek_features, CONTEXT_CREEK_SHARE_PPM
    )
    return {
        "overview": (list(fox_features), 0, total_score, 0),
        "context": (
            list(fox_features) + context_creeks,
            len(context_creeks),
            total_score,
            context_score,
        ),
        "detail": (
            list(fox_features) + list(creek_features),
            len(creek_features),
            total_score,
            total_score,
        ),
    }


def _morton_interleave(x: int, y: int) -> int:
    value = 0
    for bit in range(MORTON_BITS):
        value |= ((x >> bit) & 1) << (2 * bit)
        value |= ((y >> bit) & 1) << (2 * bit + 1)
    return value


def morton_key(bounds, extent) -> int:
    min_x, min_y, max_x, max_y = extent
    cx = (bounds[0] + bounds[2]) / 2.0
    cy = (bounds[1] + bounds[3]) / 2.0
    max_value = (1 << MORTON_BITS) - 1
    qx = 0 if max_x == min_x else int(round((cx - min_x) * max_value / (max_x - min_x)))
    qy = 0 if max_y == min_y else int(round((cy - min_y) * max_value / (max_y - min_y)))
    qx = min(max(qx, 0), max_value)
    qy = min(max(qy, 0), max_value)
    return _morton_interleave(qx, qy)


def _record(feature: WaterFeature, tolerance: float):
    return {
        "dataset_key": feature.dataset_key,
        "geometry": {
            "coordinates": simplify_geometry(
                feature.geometry_type, feature.coordinates, tolerance
            ),
            "type": feature.geometry_type,
        },
        "id": feature.source_feature_id,
    }


def _chunk_bounds(records: Sequence[Mapping[str, object]]):
    bounds = [
        geometry_bounds(
            str(record["geometry"]["type"]),
            record["geometry"]["coordinates"],
        )
        for record in records
    ]
    return [
        min(item[0] for item in bounds),
        min(item[1] for item in bounds),
        max(item[2] for item in bounds),
        max(item[3] for item in bounds),
    ]


def _build_level(
    key: str,
    selected: Sequence[WaterFeature],
    fox_count: int,
    creek_count: int,
    total_score: int,
    selected_score: int,
    extent,
    offset: int,
):
    if key == "detail":
        tolerance = 0.0
        simplification = {"key": "exact"}
    else:
        divisor = SIMPLIFICATION_DIVISORS[key]
        tolerance = max(extent[2] - extent[0], extent[3] - extent[1]) / divisor
        simplification = {
            "divisor": divisor,
            "key": f"extent-rdp-{divisor}",
            "tolerance_degrees": tolerance,
        }

    ordered = sorted(
        selected,
        key=lambda item: (
            morton_key(item.bounds, extent),
            item.dataset_key,
            item.source_feature_id,
        ),
    )
    payloads = []
    chunks = []
    source_vertex_count = sum(item.source_vertex_count for item in ordered)
    output_vertex_count = 0
    for start in range(0, len(ordered), CHUNK_FEATURES):
        group = ordered[start : start + CHUNK_FEATURES]
        records = [_record(feature, tolerance) for feature in group]
        output_vertex_count += sum(
            geometry_vertex_count(
                str(record["geometry"]["type"]),
                record["geometry"]["coordinates"],
            )
            for record in records
        )
        records_bytes = CONTRACT.canonical_json_bytes({"features": records})
        compressed = zlib.compress(records_bytes, level=9)
        chunks.append(
            {
                "bounds": _chunk_bounds(records),
                "feature_count": len(records),
                "length": len(compressed),
                "offset": offset,
                "payload_sha256": _sha256(compressed),
                "records_sha256": _sha256(records_bytes),
                "uncompressed_length": len(records_bytes),
            }
        )
        payloads.append(compressed)
        offset += len(compressed)

    if tolerance == 0.0 and output_vertex_count != source_vertex_count:
        raise RuntimeError("Exact water LOD changed source vertex count")
    if output_vertex_count > source_vertex_count:
        raise RuntimeError("Water LOD simplification increased vertex count")

    return (
        {
            "chunks": chunks,
            "creek_feature_count": creek_count,
            "feature_count": len(ordered),
            "fox_river_feature_count": fox_count,
            "key": key,
            "selected_creek_coordinate_length_score": selected_score,
            "simplification": simplification,
            "source_creek_coordinate_length_score": total_score,
            "source_vertex_count": source_vertex_count,
            "vertex_count": output_vertex_count,
        },
        payloads,
        offset,
    )


def _expected_policy():
    return {
        "chunking": {"key": "whole-features", "max_features": CHUNK_FEATURES},
        "membership": {
            "context_creek_share_ppm": CONTEXT_CREEK_SHARE_PPM,
            "fox_river_rule": "all-accepted-features-in-every-level",
            "key": "coordinated-fox-creek-v1",
            "score_scale": SCORE_SCALE,
        },
        "ordering": {"bits": MORTON_BITS, "key": "morton-center"},
    }


def build_component(database: Path, output: Path):
    COMPRESSION.require_accepted_zlib()
    database = database.resolve()
    output = output.resolve()
    if database == output:
        raise RuntimeError(
            "Water component output must not replace the authoritative database"
        )

    jurisdiction, sources, fox_features, creek_features, extent = load_accepted_water(
        database
    )
    memberships = level_membership(fox_features, creek_features)

    levels = []
    payloads = []
    offset = 0
    for key in LEVEL_KEYS:
        selected, creek_count, total_score, selected_score = memberships[key]
        level, level_payloads, offset = _build_level(
            key,
            selected,
            len(fox_features),
            creek_count,
            total_score,
            selected_score,
            extent,
            offset,
        )
        levels.append(level)
        payloads.extend(level_payloads)

    index = {
        "compression": "zlib-deflate",
        "format": CONTRACT.WATER_FORMAT,
        "jurisdiction": jurisdiction,
        "levels": levels,
        "policy": _expected_policy(),
        "sources": sources,
        "srs_id": CONTRACT.SRS_ID,
        "version": CONTRACT.VERSION,
    }
    component = CONTRACT.encode_container_prefix(CONTRACT.WATER_MAGIC, index) + b"".join(
        payloads
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp")
    try:
        temporary.write_bytes(component)
        validate_component(temporary)
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)

    return {
        "byte_length": len(component),
        "feature_count": len(fox_features) + len(creek_features),
        "output_file": str(output),
        "sha256": _sha256(component),
    }


def _require_keys(value: Mapping[str, object], keys: set[str], label: str):
    if set(value) != keys:
        raise RuntimeError(
            f"{label} keys mismatch: missing={sorted(keys - set(value))} "
            f"extra={sorted(set(value) - keys)}"
        )


def _validate_bounds(value, label):
    if not isinstance(value, list) or len(value) != 4:
        raise RuntimeError(f"{label} bounds must contain four numbers")
    vals = []
    for item in value:
        if (
            isinstance(item, bool)
            or not isinstance(item, (int, float))
            or not math.isfinite(item)
        ):
            raise RuntimeError(f"{label} bounds contain a non-finite number")
        vals.append(float(item))
    if vals[0] > vals[2] or vals[1] > vals[3]:
        raise RuntimeError(f"{label} bounds are invalid")
    return vals


def validate_component(path: Path):
    path = path.resolve()
    data = path.read_bytes()
    index, payload_start = CONTRACT.decode_container_index(
        data,
        expected_magic=CONTRACT.WATER_MAGIC,
        expected_format=CONTRACT.WATER_FORMAT,
    )
    _require_keys(
        index,
        {
            "compression",
            "format",
            "jurisdiction",
            "levels",
            "policy",
            "sources",
            "srs_id",
            "version",
        },
        "water index",
    )
    if index["policy"] != _expected_policy():
        raise RuntimeError("Water component policy does not match v1 Kane water policy")

    sources_raw = index["sources"]
    if not isinstance(sources_raw, list) or len(sources_raw) != 2:
        raise RuntimeError("Water component must carry exactly two accepted sources")
    sources = [CONTRACT.validate_release_descriptor(item) for item in sources_raw]
    if [item["dataset_key"] for item in sources] != [
        CREEK_DATASET_KEY,
        FOX_DATASET_KEY,
    ]:
        raise RuntimeError(
            "Water component accepted sources must be water-creeks and water-fox-river"
        )
    source_by_key = {item["dataset_key"]: item for item in sources}

    levels = index["levels"]
    if not isinstance(levels, list) or [level.get("key") for level in levels] != list(
        LEVEL_KEYS
    ):
        raise RuntimeError(f"Water component levels must be exactly {LEVEL_KEYS!r}")

    expected_offset = 0
    total_chunks = 0
    identities_by_level = {}
    creek_scores = None

    for level in levels:
        _require_keys(
            level,
            {
                "chunks",
                "creek_feature_count",
                "feature_count",
                "fox_river_feature_count",
                "key",
                "selected_creek_coordinate_length_score",
                "simplification",
                "source_creek_coordinate_length_score",
                "source_vertex_count",
                "vertex_count",
            },
            f"water level {level.get('key')}",
        )
        key = level["key"]
        if level["fox_river_feature_count"] != source_by_key[FOX_DATASET_KEY]["feature_count"]:
            raise RuntimeError("Water level Fox River feature count mismatch")
        if creek_scores is None:
            creek_scores = level["source_creek_coordinate_length_score"]
        elif level["source_creek_coordinate_length_score"] != creek_scores:
            raise RuntimeError("Water levels disagree on creek coordinate-length score")

        if key == "detail":
            if level["simplification"] != {"key": "exact"}:
                raise RuntimeError("Water detail level must preserve exact geometry")
        else:
            divisor = SIMPLIFICATION_DIVISORS[key]
            simplification = level["simplification"]
            if (
                not isinstance(simplification, dict)
                or simplification.get("key") != f"extent-rdp-{divisor}"
                or simplification.get("divisor") != divisor
            ):
                raise RuntimeError("Water coarse-level simplification policy is invalid")

        chunks = level["chunks"]
        if not isinstance(chunks, list) or not chunks:
            raise RuntimeError(f"Water level {key} has no chunks")
        identities = []
        observed_count = 0
        observed_fox = 0
        observed_creeks = 0
        observed_vertices = 0

        for chunk in chunks:
            _require_keys(
                chunk,
                {
                    "bounds",
                    "feature_count",
                    "length",
                    "offset",
                    "payload_sha256",
                    "records_sha256",
                    "uncompressed_length",
                },
                "water chunk",
            )
            _validate_bounds(chunk["bounds"], "water chunk")
            if chunk["offset"] != expected_offset:
                raise RuntimeError("Water chunk offsets are not contiguous")
            length = chunk["length"]
            if isinstance(length, bool) or not isinstance(length, int) or length <= 0:
                raise RuntimeError("Water chunk compressed length is invalid")
            start = payload_start + expected_offset
            end = start + length
            if end > len(data):
                raise RuntimeError("Water chunk payload is truncated")
            payload = data[start:end]
            if _sha256(payload) != chunk["payload_sha256"]:
                raise RuntimeError("Water chunk payload SHA-256 mismatch")
            try:
                records_bytes = zlib.decompress(payload)
            except zlib.error as exc:
                raise RuntimeError(f"Water chunk zlib payload is invalid: {exc}") from exc
            if len(records_bytes) != chunk["uncompressed_length"]:
                raise RuntimeError("Water chunk uncompressed length mismatch")
            if _sha256(records_bytes) != chunk["records_sha256"]:
                raise RuntimeError("Water chunk records SHA-256 mismatch")
            try:
                record_doc = json.loads(records_bytes.decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise RuntimeError(f"Water chunk records are invalid JSON: {exc}") from exc
            if CONTRACT.canonical_json_bytes(record_doc) != records_bytes:
                raise RuntimeError("Water chunk records are not canonical JSON")
            _require_keys(record_doc, {"features"}, "water chunk records")
            records = record_doc["features"]
            if not isinstance(records, list) or len(records) != chunk["feature_count"]:
                raise RuntimeError("Water chunk feature_count mismatch")
            if not records or len(records) > CHUNK_FEATURES:
                raise RuntimeError("Water chunk feature count violates chunking policy")

            calculated_bounds = []
            for record in records:
                _require_keys(
                    record, {"dataset_key", "geometry", "id"}, "water feature record"
                )
                dataset_key = record["dataset_key"]
                feature_id = record["id"]
                if dataset_key not in (FOX_DATASET_KEY, CREEK_DATASET_KEY):
                    raise RuntimeError("Water feature dataset_key is invalid")
                if not isinstance(feature_id, str) or not feature_id:
                    raise RuntimeError("Water feature id is invalid")
                geometry = record["geometry"]
                _require_keys(
                    geometry, {"coordinates", "type"}, "water feature geometry"
                )
                geometry_type = geometry["type"]
                coordinates = geometry["coordinates"]
                if dataset_key == FOX_DATASET_KEY:
                    geometry_polygons(str(geometry_type), coordinates)
                    observed_fox += 1
                else:
                    geometry_lines(str(geometry_type), coordinates)
                    observed_creeks += 1
                calculated_bounds.append(
                    geometry_bounds(str(geometry_type), coordinates)
                )
                observed_vertices += geometry_vertex_count(
                    str(geometry_type), coordinates
                )
                identities.append((dataset_key, feature_id))

            actual_bounds = [
                min(item[0] for item in calculated_bounds),
                min(item[1] for item in calculated_bounds),
                max(item[2] for item in calculated_bounds),
                max(item[3] for item in calculated_bounds),
            ]
            if actual_bounds != [float(item) for item in chunk["bounds"]]:
                raise RuntimeError("Water chunk bounds mismatch")
            observed_count += len(records)
            expected_offset += length
            total_chunks += 1

        if observed_count != level["feature_count"]:
            raise RuntimeError(f"Water level {key} feature_count mismatch")
        if observed_fox != level["fox_river_feature_count"]:
            raise RuntimeError(f"Water level {key} Fox River count mismatch")
        if observed_creeks != level["creek_feature_count"]:
            raise RuntimeError(f"Water level {key} creek count mismatch")
        if observed_vertices != level["vertex_count"]:
            raise RuntimeError(f"Water level {key} vertex count mismatch")
        if level["vertex_count"] > level["source_vertex_count"]:
            raise RuntimeError(f"Water level {key} simplification increased vertex count")
        if len(identities) != len(set(identities)):
            raise RuntimeError(f"Water level {key} contains duplicate feature identities")
        identities_by_level[key] = set(identities)

    if payload_start + expected_offset != len(data):
        raise RuntimeError("Water component has trailing or unindexed payload bytes")

    overview = identities_by_level["overview"]
    context = identities_by_level["context"]
    detail = identities_by_level["detail"]
    fox_detail = {
        identity for identity in detail if identity[0] == FOX_DATASET_KEY
    }
    creek_detail = {
        identity for identity in detail if identity[0] == CREEK_DATASET_KEY
    }
    if overview != fox_detail:
        raise RuntimeError("Water overview must contain all Fox River features and no creeks")
    if not overview.issubset(context) or not context.issubset(detail):
        raise RuntimeError("Water level membership is not monotonic")
    if len(fox_detail) != source_by_key[FOX_DATASET_KEY]["feature_count"]:
        raise RuntimeError("Water detail Fox River membership count mismatch")
    if len(creek_detail) != source_by_key[CREEK_DATASET_KEY]["feature_count"]:
        raise RuntimeError("Water detail creek membership count mismatch")

    context_creeks = {
        identity for identity in context if identity[0] == CREEK_DATASET_KEY
    }
    if len(context_creeks) != levels[1]["creek_feature_count"]:
        raise RuntimeError("Water context creek membership count mismatch")
    if levels[0]["creek_feature_count"] != 0:
        raise RuntimeError("Water overview must contain zero creeks")
    if levels[2]["creek_feature_count"] != source_by_key[CREEK_DATASET_KEY]["feature_count"]:
        raise RuntimeError("Water detail must contain all accepted creeks")

    return {
        "byte_length": len(data),
        "chunk_count": total_chunks,
        "feature_count": len(detail),
        "jurisdiction": CONTRACT.validate_jurisdiction(index["jurisdiction"]),
        "levels": [
            {"feature_count": level["feature_count"], "key": level["key"]}
            for level in levels
        ],
        "path": str(path),
        "sha256": _sha256(data),
        "sources": sources,
        "valid": True,
    }


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("database", type=Path)
    build.add_argument("output", type=Path)
    validate = commands.add_parser("validate")
    validate.add_argument("component", type=Path)
    info = commands.add_parser("info")
    info.add_argument("component", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            result = build_component(args.database, args.output)
        elif args.command in ("validate", "info"):
            result = validate_component(args.component)
        else:
            raise RuntimeError(f"Unknown command: {args.command}")
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(CONTRACT.canonical_json_bytes(result).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
