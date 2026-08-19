#!/usr/bin/env python3
"""Kane Fabric durable geographic building-identity entry point."""

from __future__ import annotations

from typing import Sequence

from kane_fabric_compat import DB, load_donor, load_sibling

BUILDINGS = load_sibling("kane_fabric_buildings")
DONOR = load_donor("kane_project_buildings")

DONOR.kane_db = DB
DONOR.kane_buildings = BUILDINGS

PROJECT_TABLE = DONOR.PROJECT_TABLE
MAPPING_TABLE = DONOR.MAPPING_TABLE
IDENTITY_ALGORITHM = DONOR.IDENTITY_ALGORITHM
BUILDING_KEY_PATTERN = DONOR.BUILDING_KEY_PATTERN
PROJECT_COLUMNS = DONOR.PROJECT_COLUMNS
MAPPING_COLUMNS = DONOR.MAPPING_COLUMNS


def validate_schema(connection) -> list[str]:
    errors: list[str] = []
    tables = DB.table_names(connection)
    for table, columns in (
        (PROJECT_TABLE, PROJECT_COLUMNS),
        (MAPPING_TABLE, MAPPING_COLUMNS),
    ):
        if table not in tables:
            errors.append(f"Missing geographic-building table: {table}")
            continue
        actual = DONOR.table_columns(connection, table)
        if actual != columns:
            errors.append(
                f"Unexpected {table} columns: expected {columns!r}, found {actual!r}"
            )

    expected = {
        PROJECT_TABLE: "Kane Fabric geographic buildings",
        MAPPING_TABLE: "Kane Fabric building mappings",
    }
    registrations = {
        str(row[0]): (str(row[1]), str(row[2]), row[3])
        for row in connection.execute(
            "SELECT table_name, data_type, identifier, srs_id FROM gpkg_contents "
            "WHERE table_name IN (?, ?)",
            (PROJECT_TABLE, MAPPING_TABLE),
        )
    }
    for table, identifier in expected.items():
        row = registrations.get(table)
        if row != ("attributes", identifier, None):
            errors.append(f"Unexpected {table} gpkg_contents registration: {row!r}")
    return errors


DONOR.validate_schema = validate_schema

canonical_json = DONOR.canonical_json
project_building_key = DONOR.project_building_key
validate_project_rows = DONOR.validate_project_rows
validate_mapping_rows = DONOR.validate_mapping_rows
validate_initial_mappings = DONOR.validate_initial_mappings
validate_accepted_release_coverage = DONOR.validate_accepted_release_coverage
validate_contents = DONOR.validate_contents
validate_data = DONOR.validate_data
validate_foundation = DONOR.validate_foundation
validate_database = DONOR.validate_database
accepted_release_context = DONOR.accepted_release_context
seed_project_buildings = DONOR.seed_project_buildings
build_parser = DONOR.build_parser


def main(argv: Sequence[str] | None = None) -> int:
    return int(DONOR.main(argv))


if __name__ == "__main__":
    raise SystemExit(main())
