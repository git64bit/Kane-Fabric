#!/usr/bin/env python3
"""Kane Fabric official-building storage entry point."""

from __future__ import annotations

from typing import Sequence

from kane_fabric_compat import DB, FABRIC_GEOMETRY, load_donor, load_sibling

PROVENANCE = load_sibling("kane_fabric_provenance")
BOUNDARY = load_sibling("kane_fabric_boundary")
MAP_LAYERS = load_sibling("kane_fabric_map_layers")
DONOR = load_donor("kane_buildings")

DONOR.kane_db = DB
DONOR.kane_provenance = PROVENANCE
DONOR.kane_boundary = BOUNDARY
DONOR.kane_map_layers = MAP_LAYERS
DONOR.kane_geometry = FABRIC_GEOMETRY

BUILDING_TABLE = DONOR.BUILDING_TABLE
BUILDING_COLUMNS = DONOR.BUILDING_COLUMNS
ALLOWED_GEOMETRY_TYPES = DONOR.ALLOWED_GEOMETRY_TYPES


def validate_schema(connection) -> list[str]:
    errors: list[str] = []
    if BUILDING_TABLE not in DB.table_names(connection):
        return [f"Missing official-building table: {BUILDING_TABLE}"]
    actual_columns = DONOR.table_columns(connection, BUILDING_TABLE)
    if actual_columns != BUILDING_COLUMNS:
        errors.append(
            f"Unexpected {BUILDING_TABLE} columns: expected {BUILDING_COLUMNS!r}, "
            f"found {actual_columns!r}"
        )
    registration = connection.execute(
        "SELECT data_type, identifier, srs_id FROM gpkg_contents WHERE table_name = ?",
        (BUILDING_TABLE,),
    ).fetchone()
    registration_tuple = tuple(registration) if registration is not None else None
    if registration_tuple != ("features", "Kane Fabric official buildings", 4326):
        errors.append(
            f"Unexpected {BUILDING_TABLE} gpkg_contents registration: {registration_tuple!r}"
        )
    geometry_registration = connection.execute(
        "SELECT column_name, geometry_type_name, srs_id, z, m "
        "FROM gpkg_geometry_columns WHERE table_name = ?",
        (BUILDING_TABLE,),
    ).fetchone()
    geometry_tuple = tuple(geometry_registration) if geometry_registration is not None else None
    if geometry_tuple != ("geometry", "GEOMETRY", 4326, 0, 0):
        errors.append(
            f"Unexpected {BUILDING_TABLE} geometry registration: {geometry_tuple!r}"
        )
    return errors


DONOR.validate_schema = validate_schema

sha256_bytes = DONOR.sha256_bytes
canonical_json = DONOR.canonical_json
validate_feature_rows = DONOR.validate_feature_rows
validate_release_groups = DONOR.validate_release_groups
validate_contents = DONOR.validate_contents
validate_data = DONOR.validate_data
validate_foundation = DONOR.validate_foundation
validate_database = DONOR.validate_database
release_context = DONOR.release_context
load_feature_collection = DONOR.load_feature_collection
normalize_features = DONOR.normalize_features
matching_source_file = DONOR.matching_source_file
import_buildings = DONOR.import_buildings
building_info = DONOR.building_info
build_parser = DONOR.build_parser


def main(argv: Sequence[str] | None = None) -> int:
    return int(DONOR.main(argv))


if __name__ == "__main__":
    raise SystemExit(main())
