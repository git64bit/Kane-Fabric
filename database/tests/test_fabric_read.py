from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

DATABASE = Path(__file__).resolve().parents[1]
TOOLS = DATABASE / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import kane_fabric_db as fabric_db
import kane_fabric_geometry as geometry
import kane_fabric_map_layers as map_layers
import kane_fabric_provenance as provenance
import kane_fabric_read as fabric_read


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class FabricReadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.database = self.root / "fabric.gpkg"
        fabric_db.init_database(self.database)
        self._record_roads()

    def _record_roads(self) -> None:
        coordinates = [
            [-88.4, 41.9],
            [-88.35, 41.900001],
            [-88.3, 42.0],
        ]
        document = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"id": "road-1"},
                    "geometry": {
                        "type": "LineString",
                        "coordinates": coordinates,
                    },
                }
            ],
        }
        source = self.root / "roads.geojson"
        source.write_bytes(canonical_bytes(document))
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
                "description": "read API test",
                "data_kind": "roads",
                "source_uri": "https://example.invalid/roads",
            },
            "harvest": {
                "harvest_key": "roads-harvest",
                "started_at": "2026-08-20T12:00:00.000Z",
                "completed_at": "2026-08-20T12:00:01.000Z",
                "status": "succeeded",
                "source_metadata": {"id_property": "id"},
                "object_count": 1,
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
                "feature_count": 1,
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

    def test_authority_summary_is_read_only_and_explains_authority(self) -> None:
        before = sha256_file(self.database)
        summary = fabric_read.authority_summary(self.database)
        after = sha256_file(self.database)

        self.assertEqual(before, after)
        self.assertEqual("read-only", summary["mode"])
        self.assertEqual("accepted-geographic-state", summary["authority"])
        self.assertEqual("lifecycle-and-release-metadata-only", summary["validation_scope"])
        self.assertEqual(1, summary["accepted_release_count"])
        release = summary["accepted_releases"][0]
        self.assertEqual("roads", release["dataset_key"])
        self.assertEqual("test-roads-release", release["release_key"])
        self.assertEqual(1, release["feature_count"])
        self.assertEqual(1, release["harvest_object_count"])
        self.assertEqual(0, release["retained_feature_delta"])
        self.assertEqual("matches_harvest_inventory", release["inventory_relation"])
        self.assertEqual(0, release["candidate_release_count"])
        self.assertIn("Only a source release", summary["interpretation"]["accepted_release_rule"])
        self.assertIn("does not change", summary["interpretation"]["candidate_rule"])
        self.assertIn("not authoritative", summary["interpretation"]["freshness_rule"])
        self.assertIn("do not diagnose corruption", summary["interpretation"]["inventory_rule"])

    def test_authority_summary_explains_retained_inventory_delta(self) -> None:
        connection = sqlite3.connect(self.database)
        try:
            connection.execute(
                "UPDATE harvest_run SET object_count = 2 WHERE harvest_key = 'roads-harvest'"
            )
            connection.commit()
        finally:
            connection.close()

        summary = fabric_read.authority_summary(self.database)
        release = summary["accepted_releases"][0]
        self.assertEqual(2, release["harvest_object_count"])
        self.assertEqual(1, release["retained_feature_delta"])
        self.assertEqual(
            "retains_fewer_features_than_harvest_inventory",
            release["inventory_relation"],
        )

    def test_authority_shell_entry_point_returns_same_contract(self) -> None:
        result = subprocess.run(
            [
                "bash",
                str(DATABASE / "kane-fabric-read.sh"),
                "authority",
                str(self.database),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        summary = json.loads(result.stdout)
        self.assertEqual("kane-fabric-authority-summary", summary["format"])
        self.assertEqual("accepted-geographic-state", summary["authority"])
        self.assertEqual("test-roads-release", summary["accepted_releases"][0]["release_key"])

    def test_load_accepted_map_layer_is_read_only_and_validated(self) -> None:
        before = sha256_file(self.database)
        layer = fabric_read.load_accepted_map_layer(self.database, "roads")
        after = sha256_file(self.database)

        self.assertEqual(before, after)
        self.assertEqual("roads", layer.release.dataset_key)
        self.assertEqual("roads", layer.release.data_kind)
        self.assertEqual("test-roads-release", layer.release.release_key)
        self.assertEqual(1, layer.release.feature_count)
        self.assertEqual("test-county", layer.release.jurisdiction["county_key"])
        self.assertEqual("17089", layer.release.jurisdiction["fips_code"])
        self.assertEqual(1, len(layer.features))
        self.assertEqual("road-1", layer.features[0].source_feature_id)
        self.assertEqual(1, layer.features[0].source_ordinal)

    def test_coordinates_are_the_decoded_database_geometry(self) -> None:
        connection = sqlite3.connect(f"file:{self.database.resolve()}?mode=ro", uri=True)
        try:
            blob = connection.execute(
                "SELECT geometry FROM source_map_feature WHERE source_feature_id = ?",
                ("road-1",),
            ).fetchone()[0]
        finally:
            connection.close()
        expected = geometry.decode_geopackage_geometry(blob)
        actual = fabric_read.load_accepted_map_layer(self.database, "roads").features[0]
        self.assertEqual(expected.geometry_type, actual.geometry_type)
        self.assertEqual(expected.coordinates, actual.coordinates)
        self.assertEqual(expected.envelope, actual.bounds)

    def test_rejects_non_map_dataset(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "release count is 0"):
            fabric_read.load_accepted_map_layer(self.database, "buildings")


if __name__ == "__main__":
    unittest.main()
