from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

DATABASE = Path(__file__).resolve().parents[1]
TOOLS = DATABASE / "tools"
DONOR = Path(
    os.environ.get(
        "KANE_FABRIC_DONOR_TOOLS",
        "/var/lib/kane-fabric/reconstruction-code/kane-condo-0.4/database/tools",
    )
)

SPEC = importlib.util.spec_from_file_location(
    "kane_fabric_db_storage_test", TOOLS / "kane_fabric_db.py"
)
assert SPEC is not None and SPEC.loader is not None
DB = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = DB
SPEC.loader.exec_module(DB)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


@unittest.skipUnless(DONOR.is_dir(), "frozen Kane Condo 0.4 donor is not available")
class FabricStorageEntrypointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.database = self.root / "fabric.gpkg"
        DB.init_database(self.database)

    def command(self, script: str, *arguments: object) -> dict[str, object]:
        env = dict(os.environ)
        env["KANE_FABRIC_DONOR_TOOLS"] = str(DONOR)
        result = subprocess.run(
            ["bash", str(DATABASE / script), *(str(value) for value in arguments)],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            self.fail(
                f"{script} failed with {result.returncode}\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        return json.loads(result.stdout)

    def write_geojson(self, name: str, feature: dict[str, object]) -> Path:
        path = self.root / name
        document = {"type": "FeatureCollection", "features": [feature]}
        path.write_bytes(canonical_bytes(document))
        return path

    def record_release(
        self,
        *,
        dataset_key: str,
        data_kind: str,
        release_key: str,
        source: Path,
    ) -> None:
        raw = source.read_bytes()
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
                "dataset_key": dataset_key,
                "name": dataset_key,
                "description": "Kane Fabric extraction test",
                "data_kind": data_kind,
                "source_uri": f"https://example.invalid/{dataset_key}",
            },
            "harvest": {
                "harvest_key": f"{dataset_key}-harvest",
                "started_at": "2026-08-19T12:00:00.000Z",
                "completed_at": "2026-08-19T12:00:01.000Z",
                "status": "succeeded",
                "source_metadata": {"id_property": "id"},
                "object_count": 1,
            },
            "files": [
                {
                    "file_role": "source",
                    "relative_path": source.name,
                    "byte_length": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "media_type": "application/geo+json",
                }
            ],
            "release": {
                "release_key": release_key,
                "lifecycle_status": "accepted",
                "source_published_at": "2026-08-19T11:00:00.000Z",
                "content_sha256": hashlib.sha256(raw).hexdigest(),
                "feature_count": 1,
                "metadata": {"id_property": "id"},
                "accepted_at": "2026-08-19T12:00:02.000Z",
            },
        }
        path = self.root / f"{dataset_key}-descriptor.json"
        path.write_bytes(canonical_bytes(descriptor))
        result = self.command(
            "kane-fabric-provenance.sh", "record", self.database, path
        )
        self.assertTrue(result["valid"])

    def test_provenance_boundary_map_and_building_storage(self) -> None:
        boundary = self.write_geojson(
            "boundary.geojson",
            {
                "type": "Feature",
                "properties": {"id": "boundary-1"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-88.5, 41.8], [-88.2, 41.8], [-88.2, 42.1],
                        [-88.5, 42.1], [-88.5, 41.8],
                    ]],
                },
            },
        )
        self.record_release(
            dataset_key="county-boundary",
            data_kind="boundary",
            release_key="test-boundary-release",
            source=boundary,
        )
        self.assertTrue(
            self.command(
                "kane-fabric-boundary.sh",
                "import",
                self.database,
                "test-boundary-release",
                boundary,
            )["valid"]
        )

        roads = self.write_geojson(
            "roads.geojson",
            {
                "type": "Feature",
                "properties": {"id": "road-1"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[-88.4, 41.9], [-88.3, 42.0]],
                },
            },
        )
        self.record_release(
            dataset_key="roads",
            data_kind="roads",
            release_key="test-roads-release",
            source=roads,
        )
        self.assertTrue(
            self.command(
                "kane-fabric-map-layers.sh",
                "import",
                self.database,
                "test-roads-release",
                roads,
            )["valid"]
        )

        water = self.write_geojson(
            "water.geojson",
            {
                "type": "Feature",
                "properties": {"id": "water-1"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-88.4, 41.9], [-88.35, 41.9], [-88.35, 41.95],
                        [-88.4, 41.95], [-88.4, 41.9],
                    ]],
                },
            },
        )
        self.record_release(
            dataset_key="water-test",
            data_kind="water",
            release_key="test-water-release",
            source=water,
        )
        self.assertTrue(
            self.command(
                "kane-fabric-map-layers.sh",
                "import",
                self.database,
                "test-water-release",
                water,
            )["valid"]
        )

        buildings = self.write_geojson(
            "buildings.geojson",
            {
                "type": "Feature",
                "properties": {"id": "building-1"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-88.31, 41.91], [-88.30, 41.91], [-88.30, 41.92],
                        [-88.31, 41.92], [-88.31, 41.91],
                    ]],
                },
            },
        )
        self.record_release(
            dataset_key="buildings",
            data_kind="buildings",
            release_key="test-buildings-release",
            source=buildings,
        )
        self.assertTrue(
            self.command(
                "kane-fabric-buildings.sh",
                "import",
                self.database,
                "test-buildings-release",
                buildings,
            )["valid"]
        )

        for script in (
            "kane-fabric-provenance.sh",
            "kane-fabric-boundary.sh",
            "kane-fabric-map-layers.sh",
            "kane-fabric-buildings.sh",
        ):
            result = self.command(script, "validate", self.database)
            self.assertTrue(result["valid"], result)

        connection = __import__("sqlite3").connect(self.database)
        try:
            counts = {
                "source_county_boundary": connection.execute(
                    "SELECT COUNT(*) FROM source_county_boundary"
                ).fetchone()[0],
                "source_map_feature": connection.execute(
                    "SELECT COUNT(*) FROM source_map_feature"
                ).fetchone()[0],
                "source_building": connection.execute(
                    "SELECT COUNT(*) FROM source_building"
                ).fetchone()[0],
            }
        finally:
            connection.close()
        self.assertEqual(counts["source_county_boundary"], 1)
        self.assertEqual(counts["source_map_feature"], 2)
        self.assertEqual(counts["source_building"], 1)


if __name__ == "__main__":
    unittest.main()
