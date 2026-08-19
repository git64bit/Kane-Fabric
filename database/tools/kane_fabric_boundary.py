#!/usr/bin/env python3
"""Kane Fabric county-boundary storage entry point."""

from __future__ import annotations

from typing import Sequence

from kane_fabric_compat import DB, FABRIC_GEOMETRY, load_donor, load_sibling

PROVENANCE = load_sibling("kane_fabric_provenance")
DONOR = load_donor("kane_boundary")

DONOR.kane_db = DB
DONOR.kane_provenance = PROVENANCE
DONOR.kane_geometry = FABRIC_GEOMETRY

BOUNDARY_TABLE = DONOR.BOUNDARY_TABLE
BOUNDARY_COLUMNS = DONOR.BOUNDARY_COLUMNS


def validate_schema(connection) -> list[str]:
    errors: list[str] = []
    if BOUNDARY_TABLE not in DB.table_names(connection):
        return [f"Missing county-boundary table: {BOUNDARY_TABLE}"]
    actual_columns = DONOR.table_columns(connection, BOUNDARY_TABLE)
    if actual_columns != BOUNDARY_COLUMNS:
        errors.append(
            f"Unexpected {BOUNDARY_TABLE} columns: expected {BOUNDARY_COLUMNS!r}, "
            f"found {actual_columns!r}"
        )
    registration = connection.execute(
        "SELECT data_type, identifier, srs_id FROM gpkg_contents WHERE table_name = ?",
        (BOUNDARY_TABLE,),
    ).fetchone()
    registration_tuple = tuple(registration) if registration is not None else None
    if registration_tuple != ("features", "Kane Fabric county boundary", 4326):
        errors.append(
            f"Unexpected {BOUNDARY_TABLE} gpkg_contents registration: {registration_tuple!r}"
        )
    geometry_registration = connection.execute(
        "SELECT column_name, geometry_type_name, srs_id, z, m "
        "FROM gpkg_geometry_columns WHERE table_name = ?",
        (BOUNDARY_TABLE,),
    ).fetchone()
    geometry_tuple = tuple(geometry_registration) if geometry_registration is not None else None
    if geometry_tuple != ("geometry", "GEOMETRY", 4326, 0, 0):
        errors.append(
            f"Unexpected {BOUNDARY_TABLE} geometry registration: {geometry_tuple!r}"
        )
    return errors


DONOR.validate_schema = validate_schema

sha256_bytes = DONOR.sha256_bytes
canonical_json = DONOR.canonical_json
validate_data = DONOR.validate_data
validate_foundation = DONOR.validate_foundation
validate_database = DONOR.validate_database
load_feature_collection = DONOR.load_feature_collection
normalize_feature = DONOR.normalize_feature
release_context = DONOR.release_context
matching_source_file = DONOR.matching_source_file
import_boundary = DONOR.import_boundary
boundary_info = DONOR.boundary_info
build_parser = DONOR.build_parser


def main(argv: Sequence[str] | None = None) -> int:
    return int(DONOR.main(argv))


if __name__ == "__main__":
    raise SystemExit(main())
