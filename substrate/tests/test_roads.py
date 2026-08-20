#!/usr/bin/env python3
"""Regression tests for Kane Fabric v1 road LOD components."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sqlite3
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock

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


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ENTRY = load_module("_kane_fabric_roads_test_entry", ENTRY_PATH)
ROADS = ENTRY.ROADS


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


class RoadComponentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.database = self.root / "roads.gpkg"
        self.output = self.root / "roads-lod.kfs"
        fabric_db.init_database(self.database)
        self._record_roads()

    def tearDown(self) -> None:
        self.temp.cleanup()

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
        digest = sha256(raw)
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
                "description": "road component test",
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

    def _read_index(self):
        data = self.output.read_bytes()
        index_length = struct.unpack(">Q", data[8:16])[0]
        index_end = 16 + index_length
        return json.loads(data[16:index_end].decode("utf-8")), index_end, data

    def _level_records(self, key: str):
        index, payload_start, data = self._read_index()
        level = next(level for level in index["levels"] if level["key"] == key)
        records = []
        for chunk in level["chunks"]:
            start = payload_start + chunk["offset"]
            end = start + chunk["length"]
            document = json.loads(zlib.decompress(data[start:end]).decode("utf-8"))
            records.extend(document["features"])
        return records

    def _stored_feature(self, feature_id: str):
        accepted = fabric_read.load_accepted_map_layer(self.database, "roads")
        feature = next(
            (item for item in accepted.features if item.source_feature_id == feature_id),
            None,
        )
        self.assertIsNotNone(feature)
        return feature

    def test_build_is_deterministic_valid_and_read_only(self) -> None:
        before = sha256_file(self.database)
        first = ROADS.build_component(self.database, self.output)
        first_bytes = self.output.read_bytes()
        second = ROADS.build_component(self.database, self.output)
        info = ROADS.validate_component(self.output)

        self.assertEqual(first, second)
        self.assertEqual(first_bytes, self.output.read_bytes())
        self.assertEqual(first["sha256"], sha256(first_bytes))
        self.assertTrue(info["valid"])
        self.assertEqual(6, info["feature_count"])
        self.assertEqual(before, sha256_file(self.database))

    def test_zlib_mismatch_fails_before_loading_or_output(self) -> None:
        with mock.patch.object(
            ROADS.COMPRESSION,
            "require_accepted_zlib",
            side_effect=RuntimeError("simulated zlib mismatch"),
        ) as guard, mock.patch.object(ROADS, "load_accepted_roads") as loader:
            with self.assertRaisesRegex(RuntimeError, "simulated zlib mismatch"):
                ROADS.build_component(self.database, self.output)

        guard.assert_called_once_with()
        loader.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_membership_is_monotonic_and_uses_frozen_shares(self) -> None:
        ROADS.build_component(self.database, self.output)
        index, _payload_start, _data = self._read_index()
        counts = {
            level["key"]: level["feature_count"] for level in index["levels"]
        }
        self.assertEqual(
            {"orientation": 2, "context": 3, "detail": 6}, counts
        )
        orientation = {
            record["id"] for record in self._level_records("orientation")
        }
        context = {record["id"] for record in self._level_records("context")}
        detail = {record["id"] for record in self._level_records("detail")}
        self.assertTrue(orientation < context < detail)
        self.assertEqual(
            {
                "context_share_ppm": 750000,
                "key": "coordinate-length-share-v1",
                "orientation_share_ppm": 350000,
                "score_scale": 10000000,
            },
            index["policy"]["membership"],
        )

    def test_detail_preserves_exact_coordinates_and_coarse_level_simplifies(self) -> None:
        ROADS.build_component(self.database, self.output)
        detail = {
            record["id"]: record for record in self._level_records("detail")
        }
        orientation = {
            record["id"]: record for record in self._level_records("orientation")
        }

        stored = self._stored_feature("road-1")
        self.assertEqual(
            canonical_bytes(stored.coordinates),
            canonical_bytes(detail["road-1"]["geometry"]["coordinates"]),
        )
        self.assertEqual(
            stored.geometry_type,
            detail["road-1"]["geometry"]["type"],
        )
        self.assertEqual(
            2, len(orientation["road-1"]["geometry"]["coordinates"])
        )

    def test_validator_rejects_payload_corruption(self) -> None:
        ROADS.build_component(self.database, self.output)
        data = bytearray(self.output.read_bytes())
        data[-1] ^= 0x01
        self.output.write_bytes(data)
        with self.assertRaisesRegex(RuntimeError, "payload SHA-256"):
            ROADS.validate_component(self.output)

    def test_build_rejects_release_inventory_mismatch(self) -> None:
        connection = sqlite3.connect(self.database)
        connection.execute("UPDATE source_release SET feature_count = 7")
        connection.commit()
        connection.close()
        with self.assertRaisesRegex(RuntimeError, "stores 6 features; expected 7"):
            ROADS.build_component(self.database, self.output)

    def test_shell_entry_point_builds_and_validates(self) -> None:
        build = subprocess.run(
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
        summary = json.loads(build.stdout)
        self.assertEqual(str(self.output.resolve()), summary["output_file"])

        validate = subprocess.run(
            ["bash", str(WRAPPER), "validate", str(self.output)],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertTrue(json.loads(validate.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()
