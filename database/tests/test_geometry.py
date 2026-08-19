#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "kane_fabric_geometry.py"
SPEC = importlib.util.spec_from_file_location("kane_fabric_geometry", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load geometry module: {MODULE_PATH}")
geometry = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = geometry
SPEC.loader.exec_module(geometry)


class GeometryTests(unittest.TestCase):
    def test_polygon_round_trip(self) -> None:
        coordinates = [
            [
                (-88.50, 41.80),
                (-88.40, 41.80),
                (-88.40, 41.90),
                (-88.50, 41.90),
                (-88.50, 41.80),
            ]
        ]
        blob, wkb, bounds = geometry.encode_geopackage_polygon(
            "Polygon", coordinates
        )
        decoded = geometry.decode_geopackage_polygon(blob)
        self.assertEqual(decoded.geometry_type, "Polygon")
        self.assertEqual(decoded.coordinates, coordinates)
        self.assertEqual(decoded.srs_id, 4326)
        self.assertEqual(decoded.envelope, bounds)
        self.assertEqual(decoded.wkb, wkb)

    def test_multiline_round_trip(self) -> None:
        coordinates = [
            [(-88.50, 41.80), (-88.40, 41.90)],
            [(-88.30, 41.75), (-88.20, 41.85)],
        ]
        blob, wkb, bounds = geometry.encode_geopackage_geometry(
            "MultiLineString", coordinates
        )
        decoded = geometry.decode_geopackage_geometry(blob)
        self.assertEqual(decoded.geometry_type, "MultiLineString")
        self.assertEqual(decoded.coordinates, coordinates)
        self.assertEqual(decoded.envelope, bounds)
        self.assertEqual(decoded.wkb, wkb)

    def test_out_of_range_position_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "EPSG:4326"):
            geometry.normalize_position([181.0, 41.0])

    def test_degenerate_line_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "distinct positions"):
            geometry.normalize_line(
                [[-88.5, 41.8], [-88.5, 41.8]]
            )

    def test_polygon_wrapper_rejects_line(self) -> None:
        coordinates = [(-88.5, 41.8), (-88.4, 41.9)]
        blob, _, _ = geometry.encode_geopackage_geometry(
            "LineString", coordinates
        )
        with self.assertRaisesRegex(RuntimeError, "polygon geometry type"):
            geometry.decode_geopackage_polygon(blob)

    def test_trailing_wkb_bytes_are_rejected(self) -> None:
        coordinates = [(-88.5, 41.8), (-88.4, 41.9)]
        blob, _, _ = geometry.encode_geopackage_geometry(
            "LineString", coordinates
        )
        with self.assertRaisesRegex(RuntimeError, "trailing bytes"):
            geometry.decode_geopackage_geometry(blob + b"x")


if __name__ == "__main__":
    unittest.main()
