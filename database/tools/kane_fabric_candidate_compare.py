#!/usr/bin/env python3
"""Kane Fabric deterministic candidate-comparison entry point."""

from __future__ import annotations

from typing import Sequence

from kane_fabric_compat import FABRIC_GEOMETRY, load_donor, load_sibling

SOURCE_STATUS = load_sibling("kane_fabric_source_status")
BUILDINGS = load_sibling("kane_fabric_buildings")
MAP_LAYERS = load_sibling("kane_fabric_map_layers")
BOUNDARY = load_sibling("kane_fabric_boundary")
BUILDING_CANDIDATE = load_sibling("kane_fabric_building_candidate")
ROAD_CANDIDATE = load_sibling("kane_fabric_road_candidate")
WATER_CANDIDATE = load_sibling("kane_fabric_water_candidate")
BOUNDARY_CANDIDATE = load_sibling("kane_fabric_boundary_candidate")
DONOR = load_donor("kane_candidate_compare")

DONOR.kane_geometry = FABRIC_GEOMETRY
DONOR.kane_source_status = SOURCE_STATUS
DONOR.kane_buildings = BUILDINGS
DONOR.kane_map_layers = MAP_LAYERS
DONOR.kane_boundary = BOUNDARY
DONOR.kane_building_candidate = BUILDING_CANDIDATE
DONOR.kane_road_candidate = ROAD_CANDIDATE
DONOR.kane_water_candidate = WATER_CANDIDATE
DONOR.kane_boundary_candidate = BOUNDARY_CANDIDATE

ComparisonError = DONOR.ComparisonError
compare_candidate = DONOR.compare_candidate
build_parser = DONOR.build_parser


def main(argv: Sequence[str] | None = None) -> int:
    return int(DONOR.main(argv))


if __name__ == "__main__":
    raise SystemExit(main())
