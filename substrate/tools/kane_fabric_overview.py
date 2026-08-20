#!/usr/bin/env python3
"""Build the deterministic Kane Fabric v1 jurisdiction overview payload."""

from __future__ import annotations

import argparse
import importlib.util
import os
import sqlite3
import sys
from pathlib import Path
from typing import Sequence

SIMPLIFICATION_DIVISOR = 2048.0
SIMPLIFICATION_POLICY = "extent-rdp-2048"
DATASET_KEY = "county-boundary"

Position = tuple[float, float]
Ring = list[Position]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load support module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CONTRACT = _load_module(
    "_kane_fabric_substrate_overview_contract",
    Path(__file__).resolve().with_name("kane_fabric_substrate.py"),
)
GEOMETRY = _load_module(
    "_kane_fabric_substrate_overview_geometry",
    Path(__file__).resolve().parents[2]
    / "database"
    / "tools"
    / "kane_fabric_geometry.py",
)


def _distance_sq(point: Position, start: Position, end: Position) -> float:
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


def simplify_open(points: Sequence[Position], tolerance: float) -> list[Position]:
    if len(points) <= 2:
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


def simplify_closed_ring(ring: Sequence[Position], tolerance: float) -> Ring:
    if len(ring) < 4 or ring[0] != ring[-1]:
        raise RuntimeError("Jurisdiction overview source ring is not a valid closed ring")
    points = list(ring[:-1])
    if len(points) <= 4 or tolerance <= 0.0:
        return points + [points[0]]

    anchor_index = min(
        range(len(points)),
        key=lambda index: (points[index][0], points[index][1], index),
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


def exterior_rings(
    geometry_type: str, coordinates: object
) -> tuple[list[Ring], int]:
    if geometry_type == "Polygon":
        polygons = [coordinates]
    elif geometry_type == "MultiPolygon":
        polygons = coordinates
    else:
        raise RuntimeError(
            f"Accepted jurisdiction boundary has unsupported geometry type: {geometry_type}"
        )
    if not isinstance(polygons, list) or not polygons:
        raise RuntimeError("Accepted jurisdiction boundary contains no polygons")

    rings: list[Ring] = []
    interior_count = 0
    for polygon in polygons:
        if not isinstance(polygon, list) or not polygon:
            raise RuntimeError("Accepted jurisdiction boundary contains an empty polygon")
        exterior = polygon[0]
        rings.append([(float(x), float(y)) for x, y in exterior])
        interior_count += max(0, len(polygon) - 1)
    return rings, interior_count


def load_accepted_boundary(database: Path) -> dict[str, object]:
    """Read the exactly-one accepted boundary without mutating the Fabric DB."""

    if not database.is_file():
        raise RuntimeError(f"Authoritative database does not exist: {database}")

    connection = sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT c.county_key, c.name AS jurisdiction_name, c.state_code, "
            "c.country_code, c.fips_code, d.dataset_key, sr.release_key, "
            "sr.content_sha256 AS release_content_sha256, sr.feature_count, "
            "b.source_feature_id, b.geometry, b.geometry_type, b.geometry_sha256, "
            "b.min_x, b.min_y, b.max_x, b.max_y "
            "FROM source_release sr "
            "JOIN dataset d ON d.dataset_id = sr.dataset_id "
            "JOIN county c ON c.county_id = d.county_id "
            "JOIN source_county_boundary b ON b.source_release_id = sr.source_release_id "
            "WHERE d.dataset_key = ? AND sr.lifecycle_status = 'accepted' "
            "ORDER BY sr.source_release_id, b.source_boundary_id",
            (DATASET_KEY,),
        ).fetchall()
    except sqlite3.Error as exc:
        raise RuntimeError(f"Unable to read accepted jurisdiction boundary: {exc}") from exc
    finally:
        connection.close()

    if len(rows) != 1:
        raise RuntimeError(
            f"Accepted county-boundary feature count is {len(rows)}; expected 1"
        )
    row = rows[0]
    if int(row["feature_count"]) != 1:
        raise RuntimeError("Accepted county-boundary release feature_count is not 1")

    geometry = GEOMETRY.decode_geopackage_polygon(row["geometry"])
    stored_bounds = (
        row["min_x"],
        row["min_y"],
        row["max_x"],
        row["max_y"],
    )
    if geometry.geometry_type != row["geometry_type"]:
        raise RuntimeError("Accepted county-boundary geometry type is inconsistent")
    if geometry.envelope != stored_bounds:
        raise RuntimeError("Accepted county-boundary stored bounds are inconsistent")
    if CONTRACT.sha256_bytes(geometry.wkb) != row["geometry_sha256"]:
        raise RuntimeError("Accepted county-boundary geometry SHA-256 is invalid")

    jurisdiction = CONTRACT.validate_jurisdiction(
        {
            "country_code": row["country_code"],
            "state_code": row["state_code"],
            "fips_code": row["fips_code"],
            "county_key": row["county_key"],
            "name": row["jurisdiction_name"],
        }
    )

    return {
        "jurisdiction": jurisdiction,
        "dataset_key": row["dataset_key"],
        "release_key": row["release_key"],
        "release_content_sha256": row["release_content_sha256"],
        "feature_count": int(row["feature_count"]),
        "source_feature_id": row["source_feature_id"],
        "geometry_type": geometry.geometry_type,
        "geometry_sha256": row["geometry_sha256"],
        "coordinates": geometry.coordinates,
        "bounds": geometry.envelope,
    }


def build_document(database: Path) -> dict[str, object]:
    source = load_accepted_boundary(database)
    bounds = tuple(float(value) for value in source["bounds"])
    min_x, min_y, max_x, max_y = bounds
    width = max_x - min_x
    height = max_y - min_y
    if width <= 0.0 or height <= 0.0:
        raise RuntimeError("Accepted county-boundary bounds are degenerate")

    tolerance = max(width, height) / SIMPLIFICATION_DIVISOR
    rings, interior_count = exterior_rings(
        str(source["geometry_type"]),
        source["coordinates"],
    )
    simplified = [simplify_closed_ring(ring, tolerance) for ring in rings]
    source_vertex_count = sum(len(ring) for ring in rings)
    output_vertex_count = sum(len(ring) for ring in simplified)
    if output_vertex_count > source_vertex_count:
        raise RuntimeError("Jurisdiction overview simplification increased vertex count")

    return {
        "format": CONTRACT.OVERVIEW_FORMAT,
        "version": CONTRACT.VERSION,
        "srs_id": CONTRACT.SRS_ID,
        "jurisdiction": source["jurisdiction"],
        "source": {
            "dataset_key": source["dataset_key"],
            "release_key": source["release_key"],
            "content_sha256": source["release_content_sha256"],
            "feature_count": source["feature_count"],
            "source_feature_id": source["source_feature_id"],
            "geometry_type": source["geometry_type"],
            "geometry_sha256": source["geometry_sha256"],
        },
        "fit": {
            "bounds": [min_x, min_y, max_x, max_y],
            "center": [(min_x + max_x) / 2.0, (min_y + max_y) / 2.0],
            "width": width,
            "height": height,
        },
        "outline": {
            "kind": "exterior-rings",
            "rings": [[[x, y] for x, y in ring] for ring in simplified],
            "ring_count": len(simplified),
            "source_interior_ring_count": interior_count,
            "source_vertex_count": source_vertex_count,
            "vertex_count": output_vertex_count,
            "simplification_policy": {
                "key": SIMPLIFICATION_POLICY,
                "divisor": int(SIMPLIFICATION_DIVISOR),
                "tolerance_degrees": tolerance,
            },
        },
    }


def build_overview(database: Path, output: Path) -> dict[str, object]:
    database = database.resolve()
    output = output.resolve()
    if output == database:
        raise RuntimeError(
            "Overview output path must not replace the authoritative database"
        )

    document = build_document(database)
    payload = CONTRACT.canonical_json_bytes(document)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp")
    try:
        temporary.write_bytes(payload)
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)

    return {
        "output_file": str(output),
        "byte_length": len(payload),
        "sha256": CONTRACT.sha256_bytes(payload),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser(
        "build",
        help="build deterministic jurisdiction overview payload",
    )
    build.add_argument("database", type=Path)
    build.add_argument("output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = build_overview(args.database, args.output)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(CONTRACT.canonical_json_bytes(result).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
