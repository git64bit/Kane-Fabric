#!/usr/bin/env python3
"""Regression tests for the MS3 road compiler's Fabric read boundary."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATABASE_TOOLS = ROOT / "database" / "tools"
ENTRY_PATH = ROOT / "substrate" / "tools" / "kane_fabric_roads_entry.py"
WRAPPER = ROOT / "substrate" / "kane-fabric-roads.sh"

if str(DATABASE_TOOLS) not in sys.path:
    sys.path.insert(0, str(DATABASE_TOOLS))

import kane_fabric_db as fabric_db
import kane_fabric_map_layers as map_layers
import kane_fabric_provenance as provenance
import kane_fabric_read as fabric_read


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ENTRY = _load_module("_kane_fabric_roads_read_boundary_test", ENTRY_PATH)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class RoadReadBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.database = self.root / "fabric.gpkg"
        self.output = self.root / "roads-lod.kfs"
        fabric_db.init_database(self.database)
        self._record_roads()

    def _record_roads(self) -> None:
        lengths = [0.010, 0.008, 0.006, 0.004, 0.002, 0.001]
        features = []
        for index, length in enumerate(lengths, start=1):
            x0 = -88.0 + index * 0.02
            y0 = 41.5 + index * 0.01
            features.append(
                {
                    "type": "Feature",
                    "properties": {"id": f"road-{index}"},
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [x0, y0],
                            [x0 + length / 2.0, y0 + 0.000001],
                            [x0 + length, y0],
                        ],
                    },
                }
            )

        source = self.root / "roads.geojson"
        source.write_bytes(
            canonical_bytes({"type": "FeatureCollection", "features": features})
        )
        raw = source.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        descriptor = {
            "county": {
                "county_key": "test-county",
                "name": "Test County",
                "state_code": "IL",
                "country_code": "US",
                "fips_code": "17089",
            },
            "agency": {
                "agency_key": "test-agency",
                "name": "Test Agency",
                "jurisdiction": "Test County, Illinois",
                "homepage_uri": "https://example.invalid/",
            },
            "dataset": {
                "dataset_key": "roads",
                "name": "roads",
                "description": "road read-boundary test",
                "data_kind": "roads",
                "source_uri": "https://example.invalid/roads",
            },
            "harvest": {
                "harvest_key": "roads-harvest",
                "started_at": "2026-08-20T12:00:00.000Z",
                "completed_at": "2026-08-20T12:00:01.000Z",
                "status": "succeeded",
                "source_metadata": {"id_property": "id"},
                "object_count": len(features),
            },
            "files": [
                {
                    "file_role": "source",
                    "relative_path": source.name,
                    "byte_length": len(raw),
                    "sha256": digest,
                    "media_type": "application/geo+json",
                }
            ],
            "release": {
                "release_key": "test-roads-release",
                "lifecycle_status": "accepted",
                "source_published_at": "2026-08-20T11:00:00.000Z",
                "content_sha256": digest,
                "feature_count": len(features),
                "metadata": {"id_property": "id"},
                "accepted_at": "2026-08-20T12:00:02.000Z",
            },
        }
        descriptor_path = self.root / "roads-descriptor.json"
        descriptor_path.write_bytes(canonical_bytes(descriptor))
        provenance.record_descriptor(self.database, descriptor_path)
        map_layers.import_map_layers(
            self.database,
            [("test-roads-release", source)],
        )

    def test_entry_replaces_compiler_local_database_loader(self) -> None:
        self.assertIs(ENTRY.ROADS.load_accepted_roads, ENTRY.load_accepted_roads)

    def test_build_uses_validated_fabric_read_state_and_is_read_only(self) -> None:
        before = sha256_file(self.database)
        accepted = fabric_read.load_accepted_map_layer(self.database, "roads")
        result = ENTRY.ROADS.build_component(self.database, self.output)
        after = sha256_file(self.database)

        self.assertEqual(before, after)
        self.assertEqual(accepted.release.feature_count, result["feature_count"])
        self.assertEqual(6, len(accepted.features))
        self.assertTrue(self.output.is_file())

        validation = ENTRY.ROADS.validate_component(self.output)
        self.assertTrue(validation["valid"])
        self.assertEqual(accepted.release.descriptor(), validation["source"])
        self.assertEqual(accepted.release.jurisdiction, validation["jurisdiction"])

    def test_public_shell_entry_point_uses_same_boundary(self) -> None:
        before = sha256_file(self.database)
        result = subprocess.run(
            [
                "bash",
                str(WRAPPER),
                "build",
                str(self.database),
                str(self.output),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        after = sha256_file(self.database)

        summary = json.loads(result.stdout)
        self.assertEqual(6, summary["feature_count"])
        self.assertEqual(before, after)
        self.assertTrue(self.output.is_file())


if __name__ == "__main__":
    unittest.main()
