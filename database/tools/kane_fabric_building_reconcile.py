#!/usr/bin/env python3
"""Kane Fabric building-identity reconciliation entry point."""

from __future__ import annotations

from typing import Sequence

from kane_fabric_compat import FABRIC_DB, load_donor, load_sibling

BUILDINGS = load_sibling("kane_fabric_buildings")
PROJECT = load_sibling("kane_fabric_project_buildings")
CANDIDATE = load_sibling("kane_fabric_building_candidate")
COMPARE = load_sibling("kane_fabric_candidate_compare")
DONOR = load_donor("kane_building_reconcile")

DONOR.kane_db = FABRIC_DB
DONOR.kane_buildings = BUILDINGS
DONOR.kane_project = PROJECT
DONOR.kane_candidate = CANDIDATE
DONOR.kane_compare = COMPARE


class GeographicCoreValidation:
    """Substitute Fabric geographic validation for Condo classification validation."""

    @staticmethod
    def validate_database(path):
        return PROJECT.validate_database(path)


DONOR.kane_classifications = GeographicCoreValidation()
DONOR.DATABASE_FILENAME = "kane-fabric-candidate.gpkg"
DONOR.REQUIRED_FILES = {DONOR.DATABASE_FILENAME, DONOR.REPORT_FILENAME}


def _empty_classification_snapshot(_connection):
    empty_sha = DONOR.sha256_value([])
    return {
        "current_count": 0,
        "event_count": 0,
        "current_sha256": empty_sha,
        "event_sha256": empty_sha,
    }


def _no_classifications(_connection):
    return {}


# Classification is application-owned state. Fabric reconciliation preserves an
# explicit empty application-state snapshot rather than requiring Condo tables.
DONOR._classification_snapshot = _empty_classification_snapshot
DONOR._classification_by_project = _no_classifications

RECONCILIATION_SCHEMA = DONOR.RECONCILIATION_SCHEMA
RECONCILIATION_DIRNAME = DONOR.RECONCILIATION_DIRNAME
DATABASE_FILENAME = DONOR.DATABASE_FILENAME
REPORT_FILENAME = DONOR.REPORT_FILENAME
REQUIRED_FILES = set(DONOR.REQUIRED_FILES)

canonical_bytes = DONOR.canonical_bytes
sha256_bytes = DONOR.sha256_bytes
sha256_file = DONOR.sha256_file
sha256_value = DONOR.sha256_value
build_plan = DONOR.build_plan
prepare_reconciliation = DONOR.prepare_reconciliation
validate_reconciliation = DONOR.validate_reconciliation
build_parser = DONOR.build_parser


def main(argv: Sequence[str] | None = None) -> int:
    return int(DONOR.main(argv))


if __name__ == "__main__":
    raise SystemExit(main())
