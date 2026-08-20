#!/usr/bin/env python3
"""Regression tests for Kane Fabric v1 substrate manifests."""

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
TOOLS = ROOT / "substrate" / "tools"
WRAPPER = ROOT / "substrate" / "kane-fabric-manifest.sh"

if str(DATABASE_TOOLS) not in sys.path:
    sys.path.insert(0, str(DATABASE_TOOLS))

import kane_fabric_boundary as boundary_store
import kane_fabric_db as fabric_db
import kane_fabric_map_layers as map_layers
import kane_fabric_provenance as provenance


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


OVERVIEW = load_module("_kane_fabric_manifest_test_overview", TOOLS / "kane_fabric_overview.py")
ROADS_ENTRY = load_module("_kane_fabric_manifest_test_roads_entry", TOOLS / "kane_fabric_roads_entry.py")
WATER = load_module("_kane_fabric_manifest_test_water", TOOLS / "kane_fabric_water.py")
MANIFEST = load_module("_kane_fabric_manifest_test", TOOLS / "kane_fabric_manifest.py")


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.database = self.root / "fabric.gpkg"
        self.package = self.root / "package"
        self.package.mkdir()
        fabric_db.init_database(self.database)
        self._record_sources()
        OVERVIEW.build_overview(self.database, self.package / "county-overview.json")
        ROADS_ENTRY.ROADS.build_component(self.database, self.package / "roads-lod.kfs")
        WATER.build_component(self.database, self.package / "water-lod.kfs")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _descriptor(
        self,
        *,
        dataset_key: str,
        data_kind: str,
        release_key: str,
        source: Path,
        feature_count: int,
    ) -> Path:
        raw = source.read_bytes()
        digest = sha256(raw)
        document = {
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
                "dataset_key": dataset_key,
                "name": dataset_key,
                "description": "substrate manifest test",
                "data_kind": data_kind,
                "source_uri": f"https://example.invalid/{dataset_key}",
            },
            "harvest": {
                "harvest_key": f"{dataset_key}-harvest",
                "started_at": "2026-08-20T12:00:00.000Z",
                "completed_at": "2026-08-20T12:00:01.000Z",
                "status": "succeeded",
                "source_metadata": {"id_property": "id"},
                "object_count": feature_count,
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
                "release_key": release_key,
                "lifecycle_status": "accepted",
                "source_published_at": "2026-08-20T11:00:00.000Z",
                "content_sha256": digest,
                "feature_count": feature_count,
                "metadata": {"id_property": "id"},
                "accepted_at": "2026-08-20T12:00:02.000Z",
            },
        }
        path = self.root / f"{dataset_key}-descriptor.json"
        path.write_bytes(canonical_bytes(document))
        provenance.record_descriptor(self.database, path)
        return path

    def _write_collection(self, name: str, features: list[dict[str, object]]) -> Path:
        path = self.root / name
        path.write_bytes(
            canonical_bytes({"type": "FeatureCollection", "features": features})
        )
        return path

    def _record_sources(self) -> None:
        boundary_source = self._write_collection(
            "boundary.geojson",
            [
                {
                    "type": "Feature",
                    "properties": {"id": "boundary-1"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [-88.0, 41.5],
                            [-87.7, 41.5],
                            [-87.7, 41.9],
                            [-88.0, 41.9],
                            [-88.0, 41.5],
                        ]],
                    },
                }
            ],
        )
        self._descriptor(
            dataset_key="county-boundary",
            data_kind="boundary",
            release_key="test-boundary-release",
            source=boundary_source,
            feature_count=1,
        )
        boundary_store.import_boundary(
            self.database, "test-boundary-release", boundary_source
        )

        road_features = []
        for index, length in enumerate((0.020, 0.012, 0.006), start=1):
            x0 = -87.98 + index * 0.03
            y0 = 41.55 + index * 0.04
            road_features.append(
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
        roads_source = self._write_collection("roads.geojson", road_features)
        self._descriptor(
            dataset_key="roads",
            data_kind="roads",
            release_key="test-roads-release",
            source=roads_source,
            feature_count=len(road_features),
        )

        fox_features = [
            {
                "type": "Feature",
                "properties": {"id": "fox-1"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-87.85, 41.52],
                        [-87.85, 41.88],
                        [-87.84, 41.88],
                        [-87.84, 41.52],
                        [-87.85, 41.52],
                    ]],
                },
            }
        ]
        fox_source = self._write_collection("fox.geojson", fox_features)
        self._descriptor(
            dataset_key="water-fox-river",
            data_kind="water",
            release_key="test-fox-release",
            source=fox_source,
            feature_count=1,
        )

        creek_features = []
        for index, length in enumerate((0.012, 0.008, 0.004), start=1):
            x0 = -87.95 + index * 0.04
            y0 = 41.58 + index * 0.05
            creek_features.append(
                {
                    "type": "Feature",
                    "properties": {"id": f"creek-{index}"},
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
        creeks_source = self._write_collection("creeks.geojson", creek_features)
        self._descriptor(
            dataset_key="water-creeks",
            data_kind="water",
            release_key="test-creeks-release",
            source=creeks_source,
            feature_count=len(creek_features),
        )

        map_layers.import_map_layers(
            self.database,
            [
                ("test-roads-release", roads_source),
                ("test-fox-release", fox_source),
                ("test-creeks-release", creeks_source),
            ],
        )

    def test_build_is_deterministic_canonical_and_read_only(self) -> None:
        before = sha256_file(self.database)
        first = MANIFEST.build_manifest(self.database, self.package)
        first_bytes = (self.package / "substrate-manifest.json").read_bytes()
        second = MANIFEST.build_manifest(self.database, self.package)
        info = MANIFEST.validate_manifest(
            self.package / "substrate-manifest.json", database=self.database
        )

        self.assertEqual(first, second)
        self.assertEqual(first_bytes, (self.package / "substrate-manifest.json").read_bytes())
        self.assertTrue(info["valid"])
        self.assertEqual(before, sha256_file(self.database))
        self.assertEqual(
            first_bytes,
            MANIFEST.CONTRACT.canonical_json_bytes(json.loads(first_bytes)),
        )

    def test_manifest_binds_frozen_roles_releases_and_content_identity(self) -> None:
        MANIFEST.build_manifest(self.database, self.package)
        document = json.loads((self.package / "substrate-manifest.json").read_bytes())
        self.assertEqual(
            ["county_overview", "roads", "water"],
            [item["role"] for item in document["components"]],
        )
        self.assertEqual(
            ["county-boundary", "roads", "water-creeks", "water-fox-river"],
            [item["dataset_key"] for item in document["accepted_releases"]],
        )
        self.assertEqual(
            document["substrate_content_sha256"],
            MANIFEST.CONTRACT.compute_substrate_content_sha256(
                document["jurisdiction"],
                document["accepted_releases"],
                document["components"],
            ),
        )
        self.assertNotIn("created_at", document)
        self.assertNotIn("path", document["authoritative_database"])

    def test_build_rejects_component_lineage_not_in_authoritative_state(self) -> None:
        path = self.package / "county-overview.json"
        document = json.loads(path.read_bytes())
        document["source"]["release_key"] = "not-authoritative"
        path.write_bytes(MANIFEST.CONTRACT.canonical_json_bytes(document))
        with self.assertRaisesRegex(RuntimeError, "release lineage disagrees"):
            MANIFEST.build_manifest(self.database, self.package)

    def test_validation_rejects_component_byte_corruption(self) -> None:
        MANIFEST.build_manifest(self.database, self.package)
        road = self.package / "roads-lod.kfs"
        data = bytearray(road.read_bytes())
        data[-1] ^= 0x01
        road.write_bytes(data)
        with self.assertRaisesRegex(RuntimeError, "payload SHA-256"):
            MANIFEST.validate_manifest(self.package / "substrate-manifest.json")

    def test_shell_entry_point_builds_and_validates(self) -> None:
        build = subprocess.run(
            ["bash", str(WRAPPER), "build", str(self.database), str(self.package)],
            check=True,
            capture_output=True,
            text=True,
        )
        summary = json.loads(build.stdout)
        self.assertEqual(
            str((self.package / "substrate-manifest.json").resolve()),
            summary["output_file"],
        )
        validate = subprocess.run(
            [
                "bash",
                str(WRAPPER),
                "validate",
                str(self.package / "substrate-manifest.json"),
                "--database",
                str(self.database),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertTrue(json.loads(validate.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()
