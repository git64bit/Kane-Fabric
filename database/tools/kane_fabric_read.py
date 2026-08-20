#!/usr/bin/env python3
"""Reusable read-only access to accepted Kane Fabric geographic state.

This module is the read-side interface for compilers and other consumers. It
owns read-only SQLite connection mode, accepted-release selection, inventory
checks, and geometry validation so downstream code does not duplicate SQL or
schema knowledge.
"""

from __future__ import annotations

import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import kane_fabric_boundary as boundary_store
import kane_fabric_geometry as geometry
import kane_fabric_map_layers as map_store


@dataclass(frozen=True)
class AcceptedRelease:
    source_release_id: int
    dataset_key: str
    data_kind: str
    release_key: str
    content_sha256: str
    feature_count: int
    jurisdiction: Mapping[str, str]

    def descriptor(self) -> dict[str, object]:
        return {
            "dataset_key": self.dataset_key,
            "release_key": self.release_key,
            "content_sha256": self.content_sha256,
            "feature_count": self.feature_count,
        }


@dataclass(frozen=True)
class GeographicFeature:
    source_feature_id: str
    source_ordinal: int
    geometry_type: str
    coordinates: object
    bounds: tuple[float, float, float, float]
    geometry_sha256: str


@dataclass(frozen=True)
class AcceptedFeatureSet:
    release: AcceptedRelease
    features: tuple[GeographicFeature, ...]
    extent: tuple[float, float, float, float]


def _readonly(path: Path) -> sqlite3.Connection:
    path = path.resolve()
    if not path.is_file():
        raise RuntimeError(f"Authoritative database does not exist: {path}")
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def _accepted_release(
    connection: sqlite3.Connection,
    dataset_key: str,
    *,
    expected_data_kind: str | None = None,
) -> AcceptedRelease:
    rows = connection.execute(
        "SELECT c.county_key, c.name AS jurisdiction_name, c.state_code, "
        "c.country_code, c.fips_code, d.dataset_key, d.data_kind, "
        "sr.source_release_id, sr.release_key, sr.content_sha256, sr.feature_count "
        "FROM source_release sr "
        "JOIN dataset d ON d.dataset_id = sr.dataset_id "
        "JOIN county c ON c.county_id = d.county_id "
        "WHERE d.dataset_key = ? AND sr.lifecycle_status = ?",
        (dataset_key, "accepted"),
    ).fetchall()
    if len(rows) != 1:
        raise RuntimeError(
            f"Accepted {dataset_key} release count is {len(rows)}; expected 1"
        )
    row = rows[0]
    data_kind = str(row["data_kind"])
    if expected_data_kind is not None and data_kind != expected_data_kind:
        raise RuntimeError(
            f"Dataset {dataset_key} data_kind is {data_kind!r}; "
            f"expected {expected_data_kind!r}"
        )
    feature_count = int(row["feature_count"])
    if feature_count <= 0:
        raise RuntimeError(f"Accepted {dataset_key} release has no features")
    return AcceptedRelease(
        source_release_id=int(row["source_release_id"]),
        dataset_key=str(row["dataset_key"]),
        data_kind=data_kind,
        release_key=str(row["release_key"]),
        content_sha256=str(row["content_sha256"]),
        feature_count=feature_count,
        jurisdiction={
            "country_code": str(row["country_code"]),
            "state_code": str(row["state_code"]),
            "fips_code": str(row["fips_code"]),
            "county_key": str(row["county_key"]),
            "name": str(row["jurisdiction_name"]),
        },
    )


def load_accepted_map_layer(database: Path, dataset_key: str) -> AcceptedFeatureSet:
    """Return one validated accepted roads/water layer from a Fabric database."""

    database = database.resolve()
    errors = map_store.validate_database(database)
    if errors:
        raise RuntimeError(
            "Database failed roads-and-water validation:\n- " + "\n- ".join(errors)
        )

    connection = _readonly(database)
    try:
        release = _accepted_release(connection, dataset_key)
        allowed = map_store.ALLOWED_GEOMETRY_TYPES.get(release.data_kind)
        if allowed is None:
            raise RuntimeError(
                f"Dataset {dataset_key} is not a roads or water dataset"
            )
        rows = connection.execute(
            "SELECT source_feature_id, source_ordinal, geometry, geometry_type, "
            "geometry_sha256, min_x, min_y, max_x, max_y "
            "FROM source_map_feature WHERE source_release_id = ? "
            "ORDER BY source_ordinal",
            (release.source_release_id,),
        ).fetchall()
    finally:
        connection.close()

    if len(rows) != release.feature_count:
        raise RuntimeError(
            f"Accepted {dataset_key} release metadata says {release.feature_count} "
            f"features; stored inventory has {len(rows)}"
        )

    features: list[GeographicFeature] = []
    for row in rows:
        decoded = geometry.decode_geopackage_geometry(row["geometry"])
        feature_id = str(row["source_feature_id"])
        if decoded.geometry_type != row["geometry_type"]:
            raise RuntimeError(f"Feature {feature_id} geometry type mismatch")
        if decoded.geometry_type not in allowed:
            raise RuntimeError(
                f"Feature {feature_id} geometry is {decoded.geometry_type}; "
                f"expected {' or '.join(allowed)}"
            )
        if map_store.sha256_bytes(decoded.wkb) != row["geometry_sha256"]:
            raise RuntimeError(f"Feature {feature_id} geometry SHA-256 mismatch")
        stored_bounds = (
            float(row["min_x"]),
            float(row["min_y"]),
            float(row["max_x"]),
            float(row["max_y"]),
        )
        if decoded.envelope != stored_bounds:
            raise RuntimeError(f"Feature {feature_id} stored bounds mismatch")
        features.append(
            GeographicFeature(
                source_feature_id=feature_id,
                source_ordinal=int(row["source_ordinal"]),
                geometry_type=decoded.geometry_type,
                coordinates=decoded.coordinates,
                bounds=decoded.envelope,
                geometry_sha256=str(row["geometry_sha256"]),
            )
        )

    extent = (
        min(feature.bounds[0] for feature in features),
        min(feature.bounds[1] for feature in features),
        max(feature.bounds[2] for feature in features),
        max(feature.bounds[3] for feature in features),
    )
    return AcceptedFeatureSet(release=release, features=tuple(features), extent=extent)


def load_accepted_boundary(database: Path, dataset_key: str = "county-boundary") -> AcceptedFeatureSet:
    """Return the exactly-one validated accepted county boundary."""

    database = database.resolve()
    errors = boundary_store.validate_database(database)
    if errors:
        raise RuntimeError(
            "Database failed county-boundary validation:\n- " + "\n- ".join(errors)
        )

    connection = _readonly(database)
    try:
        release = _accepted_release(
            connection, dataset_key, expected_data_kind="boundary"
        )
        rows = connection.execute(
            "SELECT source_feature_id, source_ordinal, geometry, geometry_type, "
            "geometry_sha256, min_x, min_y, max_x, max_y "
            "FROM source_county_boundary WHERE source_release_id = ? "
            "ORDER BY source_ordinal",
            (release.source_release_id,),
        ).fetchall()
    finally:
        connection.close()

    if release.feature_count != 1 or len(rows) != 1:
        raise RuntimeError(
            f"Accepted county-boundary feature count is {len(rows)}; expected 1"
        )
    row = rows[0]
    decoded = geometry.decode_geopackage_polygon(row["geometry"])
    feature_id = str(row["source_feature_id"])
    if decoded.geometry_type != row["geometry_type"]:
        raise RuntimeError(f"Boundary feature {feature_id} geometry type mismatch")
    if boundary_store.sha256_bytes(decoded.wkb) != row["geometry_sha256"]:
        raise RuntimeError(f"Boundary feature {feature_id} geometry SHA-256 mismatch")
    stored_bounds = (
        float(row["min_x"]),
        float(row["min_y"]),
        float(row["max_x"]),
        float(row["max_y"]),
    )
    if decoded.envelope != stored_bounds:
        raise RuntimeError(f"Boundary feature {feature_id} stored bounds mismatch")

    feature = GeographicFeature(
        source_feature_id=feature_id,
        source_ordinal=int(row["source_ordinal"]),
        geometry_type=decoded.geometry_type,
        coordinates=decoded.coordinates,
        bounds=decoded.envelope,
        geometry_sha256=str(row["geometry_sha256"]),
    )
    return AcceptedFeatureSet(
        release=release,
        features=(feature,),
        extent=feature.bounds,
    )
