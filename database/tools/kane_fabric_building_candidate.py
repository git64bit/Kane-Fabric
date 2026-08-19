#!/usr/bin/env python3
"""Kane Fabric building-candidate entry point."""

from __future__ import annotations

from typing import Sequence

from kane_fabric_compat import FABRIC_GEOMETRY, load_donor, load_sibling

SOURCE_PROFILES = load_sibling("kane_fabric_source_profiles")
PROVENANCE = load_sibling("kane_fabric_provenance")
BUILDINGS = load_sibling("kane_fabric_buildings")
DONOR = load_donor("kane_building_candidate")

DONOR.PROFILE_DIR = SOURCE_PROFILES.PROFILE_DIR
DONOR.kane_source_profiles = SOURCE_PROFILES
DONOR.kane_geometry = FABRIC_GEOMETRY
DONOR.kane_provenance = PROVENANCE
DONOR.kane_buildings = BUILDINGS
DONOR.PROTECTED_TABLES = tuple(
    table for table in DONOR.PROTECTED_TABLES
    if not table.startswith("building_classification_")
)

HarvestUnavailableError = DONOR.HarvestUnavailableError
HarvestContractError = DONOR.HarvestContractError
harvest_candidate = DONOR.harvest_candidate
validate_candidate = DONOR.validate_candidate
register_candidate = DONOR.register_candidate
candidate_info = DONOR.candidate_info
load_building_profile = DONOR.load_building_profile
canonical_bytes = DONOR.canonical_bytes
build_parser = DONOR.build_parser


def main(argv: Sequence[str] | None = None) -> int:
    return int(DONOR.main(argv))


if __name__ == "__main__":
    raise SystemExit(main())
