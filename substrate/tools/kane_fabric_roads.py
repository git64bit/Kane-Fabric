#!/usr/bin/env python3
"""Build and validate Kane Fabric v1 road LOD flat components."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import sqlite3
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

DATASET_KEY = "roads"
LEVEL_KEYS = ("orientation", "context", "detail")
SCORE_SCALE = 10_000_000
ORIENTATION_SHARE_PPM = 350_000
CONTEXT_SHARE_PPM = 750_000
MORTON_BITS = 16
CHUNK_FEATURES = 256
SIMPLIFICATION_DIVISORS = {"orientation": 2048, "context": 8192}


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load support module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CONTRACT = _load_module(
    "_kane_fabric_roads_contract",
    Path(__file__).resolve().with_name("kane_fabric_substrate.py"),
)
COMPRESSION = _load_module(
    "_kane_fabric_roads_compression",
    Path(__file__).resolve().with_name("kane_fabric_compression.py"),
)
GEOMETRY = _load_module(
    "_kane_fabric_roads_geometry",
    Path(__file__).resolve().parents[2]
    / "database"
    / "tools"
    / "kane_fabric_geometry.py",
)


@dataclass(frozen=True)
class RoadFeature:
    source_feature_id: str
    geometry_type: str
    coordinates: object
    bounds: tuple[float, float, float, float]
    score: int


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _segment_score(a: tuple[float, float], b: tuple[float, float]) -> int:
    ax = int(round(a[0] * SCORE_SCALE))
    ay = int(round(a[1] * SCORE_SCALE))
    bx = int(round(b[0] * SCORE_SCALE))
    by = int(round(b[1] * SCORE_SCALE))
    return math.isqrt((bx - ax) ** 2 + (by - ay) ** 2)


def coordinate_length_score(geometry_type: str, coordinates: object) -> int:
    if geometry_type == "LineString":
        lines = [coordinates]
    elif geometry_type == "MultiLineString":
        lines = coordinates
    else:
        raise RuntimeError(f"Road geometry must be linear, found {geometry_type}")
    total = 0
    for line in lines:
        for index in range(1, len(line)):
            total += _segment_score(line[index - 1], line[index])
    return total


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


def simplify_line(line: Sequence[tuple[float, float]], tolerance: float):
    if len(line) <= 2 or tolerance <= 0.0:
        return list(line)
    threshold = tolerance * tolerance
    keep = {0, len(line) - 1}
    stack = [(0, len(line) - 1)]
    while stack:
        first, last = stack.pop()
        best_index = -1
        best_distance = -1.0
        for index in range(first + 1, last):
            distance = _distance_sq(line[index], line[first], line[last])
            if distance > best_distance:
                best_distance = distance
                best_index = index
        if best_index >= 0 and best_distance > threshold:
            keep.add(best_index)
            stack.append((first, best_index))
            stack.append((best_index, last))
    result = [line[index] for index in sorted(keep)]
    if len(set(result)) < 2:
        return list(line)
    return result


def simplify_geometry(geometry_type: str, coordinates: object, tolerance: float):
    if geometry_type == "LineString":
        return simplify_line(coordinates, tolerance)
    if geometry_type == "MultiLineString":
        return [simplify_line(line, tolerance) for line in coordinates]
    raise RuntimeError(f"Road geometry must be linear, found {geometry_type}")


def _iter_positions(
    geometry_type: str, coordinates: object
) -> Iterable[tuple[float, float]]:
    if geometry_type == "LineString":
        yield from coordinates
    elif geometry_type == "MultiLineString":
        for line in coordinates:
            yield from line
    else:
        raise RuntimeError(f"Road geometry must be linear, found {geometry_type}")


def geometry_bounds(geometry_type: str, coordinates: object):
    positions = list(_iter_positions(geometry_type, coordinates))
    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    return min(xs), min(ys), max(xs), max(ys)


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
    qx = (
        0
        if max_x == min_x
        else int(round((cx - min_x) * max_value / (max_x - min_x)))
    )
    qy = (
        0
        if max_y == min_y
        else int(round((cy - min_y) * max_value / (max_y - min_y)))
    )
    qx = min(max(qx, 0), max_value)
    qy = min(max(qy, 0), max_value)
    return _morton_interleave(qx, qy)


def _accepted_road_release(connection: sqlite3.Connection) -> sqlite3.Row:
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        "SELECT c.county_key, c.name AS jurisdiction_name, c.state_code, "
        "c.country_code, c.fips_code, d.dataset_key, sr.source_release_id, "
        "sr.release_key, sr.content_sha256, sr.feature_count "
        "FROM source_release sr "
        "JOIN dataset d ON d.dataset_id = sr.dataset_id "
        "JOIN county c ON c.county_id = d.county_id "
        "WHERE d.dataset_key = ? AND sr.lifecycle_status = 'accepted'",
        (DATASET_KEY,),
    ).fetchall()
    if len(rows) != 1:
        raise RuntimeError(f"Accepted roads release count is {len(rows)}; expected 1")
    return rows[0]


def load_accepted_roads(database: Path):
    if not database.is_file():
        raise RuntimeError(f"Authoritative database does not exist: {database}")
    connection = sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    try:
        release = _accepted_road_release(connection)
        rows = connection.execute(
            "SELECT source_feature_id, geometry, geometry_type, geometry_sha256, "
            "min_x, min_y, max_x, max_y "
            "FROM source_map_feature WHERE source_release_id = ? "
            "ORDER BY source_feature_id",
            (release["source_release_id"],),
        ).fetchall()
    finally:
        connection.close()

    if len(rows) != int(release["feature_count"]):
        raise RuntimeError(
            f"Accepted roads release metadata says {release['feature_count']} features; "
            f"stored inventory has {len(rows)}"
        )
    if not rows:
        raise RuntimeError("Accepted roads release has no features")

    features = []
    for row in rows:
        decoded = GEOMETRY.decode_geopackage_geometry(row["geometry"])
        if decoded.geometry_type not in ("LineString", "MultiLineString"):
            raise RuntimeError(
                f"Road feature {row['source_feature_id']} is {decoded.geometry_type}, "
                "expected linear geometry"
            )
        stored_bounds = (row["min_x"], row["min_y"], row["max_x"], row["max_y"])
        if decoded.geometry_type != row["geometry_type"]:
            raise RuntimeError(
                f"Road feature {row['source_feature_id']} geometry type mismatch"
            )
        if decoded.envelope != stored_bounds:
            raise RuntimeError(
                f"Road feature {row['source_feature_id']} stored bounds mismatch"
            )
        if CONTRACT.sha256_bytes(decoded.wkb) != row["geometry_sha256"]:
            raise RuntimeError(
                f"Road feature {row['source_feature_id']} geometry SHA-256 mismatch"
            )
        features.append(
            RoadFeature(
                source_feature_id=str(row["source_feature_id"]),
                geometry_type=decoded.geometry_type,
                coordinates=decoded.coordinates,
                bounds=decoded.envelope,
                score=coordinate_length_score(
                    decoded.geometry_type, decoded.coordinates
                ),
            )
        )

    jurisdiction = CONTRACT.validate_jurisdiction(
        {
            "country_code": release["country_code"],
            "state_code": release["state_code"],
            "fips_code": release["fips_code"],
            "county_key": release["county_key"],
            "name": release["jurisdiction_name"],
        }
    )
    source = CONTRACT.validate_release_descriptor(
        {
            "dataset_key": release["dataset_key"],
            "release_key": release["release_key"],
            "content_sha256": release["content_sha256"],
            "feature_count": int(release["feature_count"]),
        }
    )
    extent = (
        min(f.bounds[0] for f in features),
        min(f.bounds[1] for f in features),
        max(f.bounds[2] for f in features),
        max(f.bounds[3] for f in features),
    )
    return jurisdiction, source, features, extent


def _prefix_for_share(features: Sequence[RoadFeature], share_ppm: int):
    ranked = sorted(features, key=lambda item: (-item.score, item.source_feature_id))
    total = sum(item.score for item in ranked)
    if total <= 0:
        raise RuntimeError("Accepted road coordinate-length score is zero")
    selected = []
    selected_score = 0
    for feature in ranked:
        selected.append(feature)
        selected_score += feature.score
        if selected_score * 1_000_000 >= total * share_ppm:
            break
    return selected, total, selected_score


def level_membership(features: Sequence[RoadFeature]):
    orientation, total, orientation_score = _prefix_for_share(
        features, ORIENTATION_SHARE_PPM
    )
    context, total2, context_score = _prefix_for_share(features, CONTEXT_SHARE_PPM)
    if total != total2:
        raise RuntimeError("Road score calculation is inconsistent")
    return {
        "orientation": (orientation, total, orientation_score),
        "context": (context, total, context_score),
        "detail": (list(features), total, total),
    }


def _record(feature: RoadFeature, tolerance: float):
    return {
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
        min(b[0] for b in bounds),
        min(b[1] for b in bounds),
        max(b[2] for b in bounds),
        max(b[3] for b in bounds),
    ]


def _build_level(key, selected, total_score, selected_score, extent, offset):
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
        key=lambda item: (morton_key(item.bounds, extent), item.source_feature_id),
    )
    payloads = []
    chunks = []
    for start in range(0, len(ordered), CHUNK_FEATURES):
        group = ordered[start : start + CHUNK_FEATURES]
        records = [_record(feature, tolerance) for feature in group]
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

    return (
        {
            "chunks": chunks,
            "feature_count": len(ordered),
            "key": key,
            "selected_coordinate_length_score": selected_score,
            "simplification": simplification,
            "source_coordinate_length_score": total_score,
        },
        payloads,
        offset,
    )


def _expected_policy():
    return {
        "chunking": {"key": "whole-features", "max_features": CHUNK_FEATURES},
        "membership": {
            "context_share_ppm": CONTEXT_SHARE_PPM,
            "key": "coordinate-length-share-v1",
            "orientation_share_ppm": ORIENTATION_SHARE_PPM,
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
            "Road component output must not replace the authoritative database"
        )
    jurisdiction, source, features, extent = load_accepted_roads(database)
    memberships = level_membership(features)

    levels = []
    payloads = []
    offset = 0
    for key in LEVEL_KEYS:
        selected, total_score, selected_score = memberships[key]
        level, level_payloads, offset = _build_level(
            key, selected, total_score, selected_score, extent, offset
        )
        levels.append(level)
        payloads.extend(level_payloads)

    index = {
        "compression": "zlib-deflate",
        "format": CONTRACT.ROAD_FORMAT,
        "jurisdiction": jurisdiction,
        "levels": levels,
        "policy": _expected_policy(),
        "source": source,
        "srs_id": CONTRACT.SRS_ID,
        "version": CONTRACT.VERSION,
    }
    component = CONTRACT.encode_container_prefix(CONTRACT.ROAD_MAGIC, index) + b"".join(
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
        "feature_count": source["feature_count"],
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
        expected_magic=CONTRACT.ROAD_MAGIC,
        expected_format=CONTRACT.ROAD_FORMAT,
    )
    _require_keys(
        index,
        {
            "compression",
            "format",
            "jurisdiction",
            "levels",
            "policy",
            "source",
            "srs_id",
            "version",
        },
        "road index",
    )
    if index["policy"] != _expected_policy():
        raise RuntimeError("Road component policy does not match v1 Kane road policy")
    source = CONTRACT.validate_release_descriptor(index["source"])
    if source["dataset_key"] != DATASET_KEY:
        raise RuntimeError("Road component source dataset_key is not roads")
    levels = index["levels"]
    if not isinstance(levels, list) or [level.get("key") for level in levels] != list(
        LEVEL_KEYS
    ):
        raise RuntimeError(f"Road component levels must be exactly {LEVEL_KEYS!r}")

    expected_offset = 0
    level_ids = {}
    total_chunks = 0
    source_score = None
    for level in levels:
        _require_keys(
            level,
            {
                "chunks",
                "feature_count",
                "key",
                "selected_coordinate_length_score",
                "simplification",
                "source_coordinate_length_score",
            },
            f"road level {level.get('key')}",
        )
        if source_score is None:
            source_score = level["source_coordinate_length_score"]
        elif level["source_coordinate_length_score"] != source_score:
            raise RuntimeError("Road levels disagree on source coordinate-length score")
        if (
            not isinstance(level["feature_count"], int)
            or isinstance(level["feature_count"], bool)
            or level["feature_count"] <= 0
        ):
            raise RuntimeError("Road level feature_count is invalid")
        if level["key"] == "detail":
            if level["simplification"] != {"key": "exact"}:
                raise RuntimeError("Road detail level must preserve exact geometry")
        else:
            divisor = SIMPLIFICATION_DIVISORS[level["key"]]
            simplification = level["simplification"]
            if (
                not isinstance(simplification, dict)
                or simplification.get("key") != f"extent-rdp-{divisor}"
                or simplification.get("divisor") != divisor
            ):
                raise RuntimeError("Road coarse-level simplification policy is invalid")

        chunks = level["chunks"]
        if not isinstance(chunks, list) or not chunks:
            raise RuntimeError(f"Road level {level['key']} has no chunks")
        ids = []
        observed_count = 0
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
                "road chunk",
            )
            _validate_bounds(chunk["bounds"], "road chunk")
            if chunk["offset"] != expected_offset:
                raise RuntimeError("Road chunk offsets are not contiguous")
            length = chunk["length"]
            if isinstance(length, bool) or not isinstance(length, int) or length <= 0:
                raise RuntimeError("Road chunk compressed length is invalid")
            start = payload_start + expected_offset
            end = start + length
            if end > len(data):
                raise RuntimeError("Road chunk payload is truncated")
            payload = data[start:end]
            if _sha256(payload) != chunk["payload_sha256"]:
                raise RuntimeError("Road chunk payload SHA-256 mismatch")
            try:
                records_bytes = zlib.decompress(payload)
            except zlib.error as exc:
                raise RuntimeError(f"Road chunk zlib payload is invalid: {exc}") from exc
            if len(records_bytes) != chunk["uncompressed_length"]:
                raise RuntimeError("Road chunk uncompressed length mismatch")
            if _sha256(records_bytes) != chunk["records_sha256"]:
                raise RuntimeError("Road chunk records SHA-256 mismatch")
            try:
                record_doc = json.loads(records_bytes.decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise RuntimeError(f"Road chunk records are invalid JSON: {exc}") from exc
            if CONTRACT.canonical_json_bytes(record_doc) != records_bytes:
                raise RuntimeError("Road chunk records are not canonical JSON")
            _require_keys(record_doc, {"features"}, "road chunk records")
            records = record_doc["features"]
            if not isinstance(records, list) or len(records) != chunk["feature_count"]:
                raise RuntimeError("Road chunk feature_count mismatch")
            if not records or len(records) > CHUNK_FEATURES:
                raise RuntimeError("Road chunk feature count violates chunking policy")
            calculated_bounds = []
            for record in records:
                _require_keys(record, {"geometry", "id"}, "road feature record")
                feature_id = record["id"]
                if not isinstance(feature_id, str) or not feature_id:
                    raise RuntimeError("Road feature record id is invalid")
                geometry = record["geometry"]
                _require_keys(
                    geometry, {"coordinates", "type"}, "road feature geometry"
                )
                geometry_type, coordinates = GEOMETRY.normalize_linear_geometry(
                    geometry
                )
                if geometry_type != geometry["type"]:
                    raise RuntimeError("Road feature geometry type is inconsistent")
                calculated_bounds.append(geometry_bounds(geometry_type, coordinates))
                ids.append(feature_id)
            actual_bounds = [
                min(b[0] for b in calculated_bounds),
                min(b[1] for b in calculated_bounds),
                max(b[2] for b in calculated_bounds),
                max(b[3] for b in calculated_bounds),
            ]
            if actual_bounds != [float(x) for x in chunk["bounds"]]:
                raise RuntimeError("Road chunk bounds mismatch")
            observed_count += len(records)
            expected_offset += length
            total_chunks += 1
        if observed_count != level["feature_count"]:
            raise RuntimeError(f"Road level {level['key']} feature_count mismatch")
        if len(ids) != len(set(ids)):
            raise RuntimeError(f"Road level {level['key']} contains duplicate feature ids")
        level_ids[level["key"]] = set(ids)

    if payload_start + expected_offset != len(data):
        raise RuntimeError("Road component has trailing or unindexed payload bytes")
    if not level_ids["orientation"].issubset(level_ids["context"]):
        raise RuntimeError("Road orientation membership is not a subset of context")
    if not level_ids["context"].issubset(level_ids["detail"]):
        raise RuntimeError("Road context membership is not a subset of detail")
    if len(level_ids["detail"]) != source["feature_count"]:
        raise RuntimeError(
            "Road detail membership does not match accepted source feature_count"
        )

    return {
        "byte_length": len(data),
        "chunk_count": total_chunks,
        "feature_count": source["feature_count"],
        "jurisdiction": CONTRACT.validate_jurisdiction(index["jurisdiction"]),
        "levels": [
            {"feature_count": level["feature_count"], "key": level["key"]}
            for level in levels
        ],
        "path": str(path),
        "sha256": _sha256(data),
        "source": source,
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
