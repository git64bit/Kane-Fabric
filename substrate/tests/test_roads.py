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

ROOT = Path(__file__).resolve().parents[2]
ROADS_PATH = ROOT / "substrate/tools/kane_fabric_roads.py"
GEOMETRY_PATH = ROOT / "database/tools/kane_fabric_geometry.py"
WRAPPER = ROOT / "substrate/kane-fabric-roads.sh"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ROADS = load_module("_kane_fabric_roads_test", ROADS_PATH)
GEOMETRY = load_module("_kane_fabric_roads_geometry_test", GEOMETRY_PATH)


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
        self._create_database()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _create_database(self) -> None:
        connection = sqlite3.connect(self.database)
        connection.executescript(
            """
            CREATE TABLE county (
                county_id INTEGER PRIMARY KEY,
                county_key TEXT NOT NULL,
                name TEXT NOT NULL,
                state_code TEXT NOT NULL,
                country_code TEXT NOT NULL,
                fips_code TEXT NOT NULL
            );
            CREATE TABLE dataset (
                dataset_id INTEGER PRIMARY KEY,
                dataset_key TEXT NOT NULL,
                county_id INTEGER NOT NULL
            );
            CREATE TABLE source_release (
                source_release_id INTEGER PRIMARY KEY,
                dataset_id INTEGER NOT NULL,
                release_key TEXT NOT NULL,
                lifecycle_status TEXT NOT NULL,
                content_sha256 TEXT NOT NULL,
                feature_count INTEGER NOT NULL
            );
            CREATE TABLE source_map_feature (
                source_map_feature_id INTEGER PRIMARY KEY,
                source_release_id INTEGER NOT NULL,
                source_feature_id TEXT NOT NULL,
                geometry BLOB NOT NULL,
                geometry_type TEXT NOT NULL,
                geometry_sha256 TEXT NOT NULL,
                min_x REAL NOT NULL,
                min_y REAL NOT NULL,
                max_x REAL NOT NULL,
                max_y REAL NOT NULL
            );
            """
        )
        connection.execute(
            "INSERT INTO county VALUES "
            "(1, 'kane-county-il', 'Kane County', 'IL', 'US', '17089')"
        )
        connection.execute("INSERT INTO dataset VALUES (1, 'roads', 1)")
        connection.execute(
            "INSERT INTO source_release VALUES "
            "(1, 1, 'kane-roads-test', 'accepted', ?, 6)",
            ("a" * 64,),
        )

        lengths = [0.010, 0.008, 0.006, 0.004, 0.002, 0.001]
        for index, length in enumerate(lengths, start=1):
            x0 = -88.0 + index * 0.02
            y0 = 41.5 + index * 0.01
            coordinates = [
                [x0, y0],
                [x0 + length / 2.0, y0 + 0.000001],
                [x0 + length, y0],
            ]
            blob, wkb, bounds = GEOMETRY.encode_geopackage_geometry(
                "LineString", coordinates
            )
            connection.execute(
                "INSERT INTO source_map_feature VALUES "
                "(?, 1, ?, ?, 'LineString', ?, ?, ?, ?, ?)",
                (index, f"road-{index}", blob, sha256(wkb), *bounds),
            )
        connection.commit()
        connection.close()

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

        self.assertEqual(
            [[-87.98, 41.51], [-87.975, 41.510001], [-87.97, 41.51]],
            detail["road-1"]["geometry"]["coordinates"],
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
        with self.assertRaisesRegex(RuntimeError, "stored inventory has 6"):
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
