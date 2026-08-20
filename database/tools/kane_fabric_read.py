#!/usr/bin/env python3
"""Reusable read-only access to accepted Kane Fabric geographic state.

This module is the read-side interface for compilers and other consumers. It
owns read-only SQLite connection mode, accepted-release selection, inventory
checks, geometry validation, and a compact authority summary so downstream
code and development sessions do not duplicate SQL or infer authority from
raw database facts.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

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


def authority_summary(database: Path) -> dict[str, object]:
    """Return a cheap read-only summary of geographic authority and its meaning.

    This deliberately does not perform full geometry validation. It is intended
    for session-start reasoning and other cheap checks. Call the existing Fabric
    validators, or the validated layer loaders below, before making stronger
    claims about stored geometry.
    """

    database = database.resolve()
    connection = _readonly(database)
    try:
        jurisdictions = [
            {
                "country_code": str(row["country_code"]),
                "state_code": str(row["state_code"]),
                "fips_code": str(row["fips_code"]),
                "county_key": str(row["county_key"]),
                "name": str(row["name"]),
            }
            for row in connection.execute(
                "SELECT county_key, name, state_code, country_code, fips_code "
                "FROM county ORDER BY county_key"
            )
        ]
        accepted_rows = connection.execute(
            "SELECT d.dataset_key, d.data_kind, sr.release_key, sr.content_sha256, "
            "sr.feature_count, sr.source_published_at, h.object_count "
            "FROM source_release sr "
            "JOIN dataset d ON d.dataset_id = sr.dataset_id "
            "JOIN harvest_run h ON h.harvest_run_id = sr.harvest_run_id "
            "WHERE sr.lifecycle_status = 'accepted' "
            "ORDER BY d.dataset_key"
        ).fetchall()
        candidate_rows = connection.execute(
            "SELECT d.dataset_key, COUNT(*) AS candidate_count "
            "FROM source_release sr "
            "JOIN dataset d ON d.dataset_id = sr.dataset_id "
            "WHERE sr.lifecycle_status = 'candidate' "
            "GROUP BY d.dataset_key ORDER BY d.dataset_key"
        ).fetchall()
    except sqlite3.Error as exc:
        raise RuntimeError(f"Unable to read Fabric authority state: {exc}") from exc
    finally:
        connection.close()

    if not accepted_rows:
        raise RuntimeError("Fabric database has no accepted geographic releases")

    candidate_counts = {
        str(row["dataset_key"]): int(row["candidate_count"])
        for row in candidate_rows
    }
    accepted_releases: list[dict[str, object]] = []
    for row in accepted_rows:
        feature_count = int(row["feature_count"])
        object_count = row["object_count"]
        if object_count is not None:
            object_count = int(object_count)
            if object_count < feature_count:
                raise RuntimeError(
                    f"Accepted {row['dataset_key']} harvest object_count is smaller "
                    "than accepted feature_count"
                )
            retained_delta: int | None = object_count - feature_count
        else:
            retained_delta = None

        if retained_delta is None:
            inventory_relation = "harvest_inventory_not_recorded"
        elif retained_delta == 0:
            inventory_relation = "matches_harvest_inventory"
        else:
            inventory_relation = "retains_fewer_features_than_harvest_inventory"

        accepted_releases.append(
            {
                "dataset_key": str(row["dataset_key"]),
                "data_kind": str(row["data_kind"]),
                "release_key": str(row["release_key"]),
                "content_sha256": str(row["content_sha256"]),
                "feature_count": feature_count,
                "harvest_object_count": object_count,
                "retained_feature_delta": retained_delta,
                "inventory_relation": inventory_relation,
                "source_published_at": row["source_published_at"],
                "candidate_release_count": candidate_counts.get(
                    str(row["dataset_key"]), 0
                ),
            }
        )

    return {
        "format": "kane-fabric-authority-summary",
        "version": 1,
        "mode": "read-only",
        "authority": "accepted-geographic-state",
        "validation_scope": "lifecycle-and-release-metadata-only",
        "database": str(database),
        "jurisdictions": jurisdictions,
        "accepted_release_count": len(accepted_releases),
        "accepted_releases": accepted_releases,
        "interpretation": {
            "accepted_release_rule": (
                "Only a source release with lifecycle_status=accepted is authoritative "
                "Kane Fabric geographic state."
            ),
            "candidate_rule": (
                "Candidate registration records staged provenance and does not change "
                "accepted geographic authority."
            ),
            "freshness_rule": (
                "A newer upstream response or candidate is not authoritative until an "
                "explicit validated promotion changes accepted state."
            ),
            "inventory_rule": (
                "A positive harvest-versus-retained feature delta can be deliberate "
                "source-contract behavior, such as rejected missing geometry; do not "
                "diagnose corruption from that delta alone. Check source profile/status."
            ),
            "compiler_rule": (
                "Substrate compilation reads accepted state and must not promote or "
                "otherwise mutate geographic authority."
            ),
            "validation_rule": (
                "This summary is intentionally cheap. Use Fabric validators or the "
                "validated feature loaders before claiming geometry/storage validity."
            ),
            "contradiction_rule": (
                "If this output contradicts the recorded current checkpoint, inspect only "
                "the contradicted area before any state-changing work."
            ),
        },
    }


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    authority = subparsers.add_parser(
        "authority",
        help="report accepted geographic authority and interpretation rules",
    )
    authority.add_argument("database", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "authority":
            result = authority_summary(args.database)
        else:
            raise RuntimeError(f"Unknown command: {args.command}")
    except (OSError, RuntimeError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
