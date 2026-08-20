#!/usr/bin/env python3
"""Regression tests for Kane Fabric v1 water LOD components."""

from __future__ import annotations

import hashlib
import importlib.util
import json
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
MODULE_PATH = ROOT / "substrate" / "tools" / "kane_fabric_water.py"
WRAPPER = ROOT / "substrate" / "kane-fabric-water.sh"

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


WATER = load_module("_kane_fabric_water_test", MODULE_PATH)


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


class WaterComponentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.database = self.root / "water.gpkg"
        self.output = self.root / "water-lod.kfs"
        fabric_db.init_database(self.database)
        self._record_water()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _descriptor(self, *, dataset_key, release_key, source, feature_count, digest):
        return {
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
                "description": "water component test",
                "data_kind": "water",
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
                    "byte_length": source.stat().st_size,
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

    def _record_water(self) -> None:
        fox_features = [
            {
                "type": "Feature",
                "properties": {"id": "fox-1"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-88.30, 41.72],
                        [-88.30, 41.96],
                        [-88.29, 41.96],
                        [-88.29, 41.72],
                        [-88.30, 41.72],
                    ]],
                },
            }
        ]
        creek_lengths = [0.010, 0.008, 0.006, 0.004, 0.002, 0.001]
        creek_features = []
        for index, length in enumerate(creek_lengths, start=1):
            x0 = -88.55 + index * 0.03
            y0 = 41.70 + index * 0.03
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

        fox_source = self.root / "fox.geojson"
        creek_source = self.root / "creeks.geojson"
        fox_source.write_bytes(
            canonical_bytes({"type": "FeatureCollection", "features": fox_features})
        )
        creek_source.write_bytes(
            canonical_bytes({"type": "FeatureCollection", "features": creek_features})
        )

        fox_digest = sha256(fox_source.read_bytes())
        creek_digest = sha256(creek_source.read_bytes())
        fox_descriptor = self.root / "fox-descriptor.json"
        creek_descriptor = self.root / "creek-descriptor.json"
        fox_descriptor.write_bytes(
            canonical_bytes(
                self._descriptor(
                    dataset_key="water-fox-river",
                    release_key="test-fox-release",
                    source=fox_source,
                    feature_count=len(fox_features),
                    digest=fox_digest,
                )
            )
        )
        creek_descriptor.write_bytes(
            canonical_bytes(
                self._descriptor(
                    dataset_key="water-creeks",
                    release_key="test-creeks-release",
                    source=creek_source,
                    feature_count=len(creek_features),
                    digest=creek_digest,
                )
            )
        )

        provenance.record_descriptor(self.database, fox_descriptor)
        provenance.record_descriptor(self.database, creek_descriptor)
        map_layers.import_map_layers(
            self.database,
            [
                ("test-fox-release", fox_source),
                ("test-creeks-release", creek_source),
            ],
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

    def test_build_is_deterministic_valid_and_read_only(self) -> None:
        before = sha256_file(self.database)
        first = WATER.build_component(self.database, self.output)
        first_bytes = self.output.read_bytes()
        second = WATER.build_component(self.database, self.output)
        info = WATER.validate_component(self.output)

        self.assertEqual(first, second)
        self.assertEqual(first_bytes, self.output.read_bytes())
        self.assertEqual(first["sha256"], sha256(first_bytes))
        self.assertTrue(info["valid"])
        self.assertEqual(7, info["feature_count"])
        self.assertEqual(before, sha256_file(self.database))

    def test_zlib_mismatch_fails_before_loading_or_output(self) -> None:
        with mock.patch.object(
            WATER.COMPRESSION,
            "require_accepted_zlib",
            side_effect=RuntimeError("simulated zlib mismatch"),
        ) as guard, mock.patch.object(WATER, "load_accepted_water") as loader:
            with self.assertRaisesRegex(RuntimeError, "simulated zlib mismatch"):
                WATER.build_component(self.database, self.output)

        guard.assert_called_once_with()
        loader.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_membership_matches_frozen_fox_creek_policy(self) -> None:
        WATER.build_component(self.database, self.output)
        overview = self._level_records("overview")
        context = self._level_records("context")
        detail = self._level_records("detail")

        overview_ids = {(item["dataset_key"], item["id"]) for item in overview}
        context_ids = {(item["dataset_key"], item["id"]) for item in context}
        detail_ids = {(item["dataset_key"], item["id"]) for item in detail}

        self.assertEqual({("water-fox-river", "fox-1")}, overview_ids)
        self.assertTrue(overview_ids < context_ids < detail_ids)
        self.assertEqual(7, len(detail_ids))
        self.assertEqual(
            6,
            len([item for item in detail if item["dataset_key"] == "water-creeks"]),
        )

        index, _payload_start, _data = self._read_index()
        counts = {
            level["key"]: level["creek_feature_count"] for level in index["levels"]
        }
        self.assertEqual(0, counts["overview"])
        self.assertGreater(counts["context"], 0)
        self.assertLess(counts["context"], 6)
        self.assertEqual(6, counts["detail"])
        self.assertEqual(
            {
                "context_creek_share_ppm": 600000,
                "fox_river_rule": "all-accepted-features-in-every-level",
                "key": "coordinated-fox-creek-v1",
                "score_scale": 10000000,
            },
            index["policy"]["membership"],
        )

    def test_detail_preserves_exact_accepted_geometry(self) -> None:
        WATER.build_component(self.database, self.output)
        detail = {
            (record["dataset_key"], record["id"]): record
            for record in self._level_records("detail")
        }

        fox = fabric_read.load_accepted_map_layer(
            self.database, "water-fox-river"
        ).features[0]
        creek = fabric_read.load_accepted_map_layer(
            self.database, "water-creeks"
        ).features[0]

        self.assertEqual(
            canonical_bytes(fox.coordinates),
            canonical_bytes(
                detail[("water-fox-river", fox.source_feature_id)]["geometry"][
                    "coordinates"
                ]
            ),
        )
        self.assertEqual(
            canonical_bytes(creek.coordinates),
            canonical_bytes(
                detail[("water-creeks", creek.source_feature_id)]["geometry"][
                    "coordinates"
                ]
            ),
        )

    def test_validator_rejects_payload_corruption(self) -> None:
        WATER.build_component(self.database, self.output)
        data = bytearray(self.output.read_bytes())
        data[-1] ^= 0x01
        self.output.write_bytes(data)
        with self.assertRaisesRegex(RuntimeError, "payload SHA-256|zlib"):
            WATER.validate_component(self.output)

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
        self.assertEqual(7, summary["feature_count"])

        validate = subprocess.run(
            ["bash", str(WRAPPER), "validate", str(self.output)],
            check=True,
            capture_output=True,
            text=True,
        )
        info = json.loads(validate.stdout)
        self.assertTrue(info["valid"])
        self.assertEqual(
            ["water-creeks", "water-fox-river"],
            [item["dataset_key"] for item in info["sources"]],
        )


if __name__ == "__main__":
    unittest.main()
