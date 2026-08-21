from __future__ import annotations

import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path

from ms4.tools.kane_fabric_partition import build_partition_descriptor, canonical_json_bytes
from ms4.tools.kane_fabric_scope import (
    administrative_scope,
    bounded_region_scope,
    bounds_intersect,
    composite_scope,
    normalize_coordinate,
    partition_includes_bounds,
    whole_jurisdiction_scope,
)
from ms4.tools.kane_fabric_selection import build_selection_manifest

JURISDICTION = {
    "country_code": "US",
    "state_code": "IL",
    "fips_code": "17089",
    "county_key": "kane-county-il",
    "name": "Kane County",
}


def write_component(path: Path, magic: bytes, role: str) -> tuple[int, str]:
    levels = [
        {
            "key": "orientation" if role == "roads" else "overview",
            "feature_count": 3,
            "chunks": [
                {
                    "bounds": [-88.6, 41.6, -88.4, 41.8],
                    "feature_count": 1,
                    "offset": 0,
                    "length": 4,
                    "uncompressed_length": 8,
                    "payload_sha256": "1" * 64,
                    "records_sha256": "2" * 64,
                },
                {
                    "bounds": [-88.4, 41.8, -88.2, 42.0],
                    "feature_count": 1,
                    "offset": 4,
                    "length": 4,
                    "uncompressed_length": 8,
                    "payload_sha256": "3" * 64,
                    "records_sha256": "4" * 64,
                },
                {
                    "bounds": [-88.1, 42.1, -88.0, 42.2],
                    "feature_count": 1,
                    "offset": 8,
                    "length": 4,
                    "uncompressed_length": 8,
                    "payload_sha256": "5" * 64,
                    "records_sha256": "6" * 64,
                },
            ],
        }
    ]
    index = {
        "format": f"kane-fabric-substrate-{role}",
        "version": 1,
        "srs_id": 4326,
        "compression": "zlib-deflate",
        "jurisdiction": JURISDICTION,
        "levels": levels,
    }
    index_bytes = canonical_json_bytes(index)
    data = magic + struct.pack(">Q", len(index_bytes)) + index_bytes + b"abcdefghijkl"
    path.write_bytes(data)
    return len(data), hashlib.sha256(data).hexdigest()


def write_package(root: Path) -> None:
    overview = canonical_json_bytes({"format": "proof-overview"})
    (root / "county-overview.json").write_bytes(overview)
    road_len, road_sha = write_component(root / "roads-lod.kfs", b"KFSR001\n", "roads")
    water_len, water_sha = write_component(root / "water-lod.kfs", b"KFSW001\n", "water")
    components = [
        {
            "role": "county_overview",
            "path": "county-overview.json",
            "format": "kane-fabric-substrate-overview",
            "version": 1,
            "byte_length": len(overview),
            "sha256": hashlib.sha256(overview).hexdigest(),
        },
        {
            "role": "roads",
            "path": "roads-lod.kfs",
            "format": "kane-fabric-substrate-roads",
            "version": 1,
            "byte_length": road_len,
            "sha256": road_sha,
        },
        {
            "role": "water",
            "path": "water-lod.kfs",
            "format": "kane-fabric-substrate-water",
            "version": 1,
            "byte_length": water_len,
            "sha256": water_sha,
        },
    ]
    manifest = {
        "format": "kane-fabric-substrate-manifest",
        "version": 1,
        "srs_id": 4326,
        "jurisdiction": JURISDICTION,
        "accepted_releases": [],
        "components": components,
        "substrate_content_sha256": "f" * 64,
    }
    (root / "substrate-manifest.json").write_bytes(canonical_json_bytes(manifest))


class ScopeNormalizationTests(unittest.TestCase):
    def test_coordinate_normalization_is_fixed_decimal(self) -> None:
        self.assertEqual(normalize_coordinate(-88.5), "-88.5000000")
        self.assertEqual(
            normalize_coordinate("41.70000004", latitude=True), "41.7000000"
        )
        self.assertEqual(normalize_coordinate("-0", latitude=True), "0.0000000")

    def test_boundary_touching_is_included(self) -> None:
        partition = build_partition_descriptor(
            JURISDICTION,
            bounded_region_scope([-88.5, 41.7, -88.4, 41.8]),
        )
        self.assertTrue(
            partition_includes_bounds(partition, [-88.4, 41.75, -88.3, 41.9])
        )
        self.assertTrue(
            bounds_intersect(
                [-88.5, 41.7, -88.4, 41.8],
                [-88.4, 41.8, -88.3, 41.9],
            )
        )
        self.assertFalse(
            partition_includes_bounds(partition, [-88.39, 41.81, -88.3, 41.9])
        )

    def test_administrative_lineage_changes_identity(self) -> None:
        lineage = {
            "dataset_key": "municipal-boundaries",
            "release_key": "release-a",
            "content_sha256": "a" * 64,
            "feature_id": "aurora",
            "geometry_sha256": "b" * 64,
        }
        first = build_partition_descriptor(
            JURISDICTION,
            administrative_scope(
                administrative_kind="municipality",
                name="Aurora",
                bounds=[-88.5, 41.7, -88.2, 42.0],
                boundary_lineage=lineage,
            ),
        )
        lineage["geometry_sha256"] = "c" * 64
        second = build_partition_descriptor(
            JURISDICTION,
            administrative_scope(
                administrative_kind="municipality",
                name="Aurora",
                bounds=[-88.5, 41.7, -88.2, 42.0],
                boundary_lineage=lineage,
            ),
        )
        self.assertNotEqual(first["partition_key"], second["partition_key"])

    def test_composite_identity_is_member_order_independent(self) -> None:
        a = build_partition_descriptor(
            JURISDICTION,
            bounded_region_scope([-88.6, 41.6, -88.4, 41.8]),
        )
        b = build_partition_descriptor(
            JURISDICTION,
            bounded_region_scope([-88.4, 41.8, -88.2, 42.0]),
        )
        first = build_partition_descriptor(
            JURISDICTION, composite_scope([a, b])
        )
        second = build_partition_descriptor(
            JURISDICTION, composite_scope([b, a])
        )
        self.assertEqual(first["partition_key"], second["partition_key"])

    def test_composite_union_excludes_gap_between_disjoint_members(self) -> None:
        west = build_partition_descriptor(
            JURISDICTION,
            bounded_region_scope([-88.60, 41.60, -88.41, 41.79]),
        )
        east = build_partition_descriptor(
            JURISDICTION,
            bounded_region_scope([-88.09, 42.11, -88.01, 42.19]),
        )
        composite = build_partition_descriptor(
            JURISDICTION, composite_scope([west, east])
        )
        self.assertTrue(
            partition_includes_bounds(composite, [-88.59, 41.61, -88.58, 41.62])
        )
        self.assertTrue(
            partition_includes_bounds(composite, [-88.08, 42.12, -88.02, 42.18])
        )
        self.assertFalse(
            partition_includes_bounds(composite, [-88.35, 41.85, -88.30, 41.90])
        )

    def test_whole_jurisdiction_includes_any_valid_bounds(self) -> None:
        partition = build_partition_descriptor(
            JURISDICTION,
            whole_jurisdiction_scope(),
        )
        self.assertTrue(
            partition_includes_bounds(partition, [-180, -90, 180, 90])
        )


class SelectionManifestTests(unittest.TestCase):
    def test_selection_references_only_intersecting_chunks_and_binds_substrate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_package(root)
            partition = build_partition_descriptor(
                JURISDICTION,
                bounded_region_scope([-88.5, 41.7, -88.4, 41.8]),
            )
            selection = build_selection_manifest(root, partition)
            self.assertEqual(selection["substrate_content_sha256"], "f" * 64)
            self.assertEqual(
                selection["partition_key"], partition["partition_key"]
            )
            self.assertEqual(selection["partition_scope"], partition["scope"])
            roads = next(
                item
                for item in selection["components"]
                if item["role"] == "roads"
            )
            self.assertEqual(
                [chunk["ordinal"] for chunk in roads["selected_chunks"]],
                [0, 1],
            )
            self.assertEqual(
                roads["selected_chunks"][0]["absolute_start"],
                16 + roads["index_byte_length"],
            )

    def test_composite_selection_does_not_select_gap_chunk(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_package(root)
            west = build_partition_descriptor(
                JURISDICTION,
                bounded_region_scope([-88.59, 41.61, -88.41, 41.79]),
            )
            east = build_partition_descriptor(
                JURISDICTION,
                bounded_region_scope([-88.09, 42.11, -88.01, 42.19]),
            )
            composite = build_partition_descriptor(
                JURISDICTION, composite_scope([west, east])
            )
            selection = build_selection_manifest(root, composite)
            roads = next(
                item
                for item in selection["components"]
                if item["role"] == "roads"
            )
            self.assertEqual(
                [chunk["ordinal"] for chunk in roads["selected_chunks"]],
                [0, 2],
            )


if __name__ == "__main__":
    unittest.main()
