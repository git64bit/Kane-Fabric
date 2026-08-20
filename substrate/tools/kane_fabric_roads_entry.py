#!/usr/bin/env python3
"""Public road-compiler entry point using the Fabric accepted-state read boundary.

The road LOD/container implementation owns road scoring, simplification,
chunking, framing, and validation. It does not own authoritative database SQL.
This entry point injects validated accepted roads from kane_fabric_read before
any build command runs.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load support module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[1]

ROADS = _load_module(
    "_kane_fabric_roads_implementation",
    TOOLS / "kane_fabric_roads.py",
)
FABRIC_READ = _load_module(
    "_kane_fabric_roads_fabric_read",
    ROOT / "database" / "tools" / "kane_fabric_read.py",
)


def load_accepted_roads(database: Path):
    """Adapt validated Fabric accepted roads to the road compiler model."""

    layer = FABRIC_READ.load_accepted_map_layer(database, ROADS.DATASET_KEY)
    jurisdiction = ROADS.CONTRACT.validate_jurisdiction(layer.release.jurisdiction)
    source = ROADS.CONTRACT.validate_release_descriptor(layer.release.descriptor())
    features = [
        ROADS.RoadFeature(
            source_feature_id=feature.source_feature_id,
            geometry_type=feature.geometry_type,
            coordinates=feature.coordinates,
            bounds=feature.bounds,
            score=ROADS.coordinate_length_score(
                feature.geometry_type,
                feature.coordinates,
            ),
        )
        for feature in layer.features
    ]
    return jurisdiction, source, features, layer.extent


# build_component resolves this name from the implementation module at runtime.
# Replacing it here makes the public command incapable of using the older
# compiler-local SQLite loader while preserving the already-written road
# algorithm for bounded review.
ROADS.load_accepted_roads = load_accepted_roads


def main() -> int:
    return int(ROADS.main())


if __name__ == "__main__":
    raise SystemExit(main())
