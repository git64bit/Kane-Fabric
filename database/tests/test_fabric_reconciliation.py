from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

DATABASE = Path(__file__).resolve().parents[1]
TOOLS = DATABASE / "tools"
TESTS = DATABASE / "tests"
DONOR = Path(
    os.environ.get(
        "KANE_FABRIC_DONOR_TOOLS",
        "/var/lib/kane-fabric/reconstruction-code/kane-condo-0.4/database/tools",
    )
)

sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TESTS))

import kane_fabric_building_candidate as CANDIDATE  # noqa: E402
import kane_fabric_building_reconcile as RECONCILE  # noqa: E402
import kane_fabric_buildings as BUILDINGS  # noqa: E402
import kane_fabric_db as DB  # noqa: E402
import kane_fabric_project_buildings as PROJECT  # noqa: E402
import kane_fabric_provenance as PROVENANCE  # noqa: E402
from test_fabric_candidate_compare import FakeArcGIS  # noqa: E402


@unittest.skipUnless(DONOR.is_dir(), "frozen Kane Condo 0.4 donor is not available")
class FabricReconciliationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.database = self.root / "fabric.gpkg"
        self.staging = self.root / "staging"
        self.output = self.root / "output"
        self.fake = FakeArcGIS()
        DB.init_database(self.database)
        self._create_accepted_buildings()

    def _create_accepted_buildings(self) -> None:
        profile, _registry_sha = CANDIDATE.load_building_profile()
        document = {
            "type": "FeatureCollection",
            "features": [self.fake.feature(1)],
        }
        raw = CANDIDATE.canonical_bytes(document)
        source = self.root / "accepted-buildings.geojson"
        source.write_bytes(raw)

        descriptor = {
            "county": {
                "county_key": "kane-county-il",
                "name": "Kane County",
                "state_code": "IL",
                "country_code": "US",
                "fips_code": "17089",
            },
            "agency": {
                "agency_key": profile["agency_key"],
                "name": "Kane County GIS-Technologies",
                "jurisdiction": "Kane County, Illinois",
                "homepage_uri": "https://www.kanecountyil.gov/",
            },
            "dataset": {
                "dataset_key": "buildings",
                "name": "Kane County Building Footprints",
                "description": "Official building footprint geometry",
                "data_kind": "buildings",
                "source_uri": profile["source"]["layer_url"],
            },
            "harvest": {
                "harvest_key": "fabric-buildings-accepted-reconcile-fixture",
                "started_at": "2025-07-30T12:00:00.000Z",
                "completed_at": "2025-07-30T12:01:00.000Z",
                "status": "succeeded",
                "source_metadata": {
                    "id_property": "FPId",
                    "object_id_field": "OBJECTID",
                },
                "object_count": 1,
            },
            "files": [{
                "file_role": "source",
                "relative_path": source.name,
                "byte_length": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "media_type": "application/geo+json",
            }],
            "release": {
                "release_key": "fabric-buildings-accepted-reconcile-fixture",
                "lifecycle_status": "accepted",
                "source_published_at": "2025-07-30T10:30:00.000Z",
                "content_sha256": hashlib.sha256(raw).hexdigest(),
                "feature_count": 1,
                "metadata": {
                    "id_property": "FPId",
                    "object_id_field": "OBJECTID",
                },
                "accepted_at": "2025-07-30T13:00:00.000Z",
            },
        }
        descriptor_path = self.root / "accepted-buildings.json"
        descriptor_path.write_bytes(
            (json.dumps(descriptor, sort_keys=True, separators=(",", ":")) + "\n").encode()
        )
        PROVENANCE.record_descriptor(self.database, descriptor_path)
        BUILDINGS.import_buildings(
            self.database,
            descriptor["release"]["release_key"],
            source,
        )

    def test_identity_seed_and_reconciliation_without_classification_tables(self) -> None:
        seeded = PROJECT.seed_project_buildings(
            self.database,
            "fabric-buildings-accepted-reconcile-fixture",
        )
        self.assertEqual(1, seeded["project_building_count"])
        self.assertEqual(1, seeded["mapping_count"])

        connection = sqlite3.connect(self.database)
        try:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            building_key = connection.execute(
                "SELECT building_key FROM project_building"
            ).fetchone()[0]
        finally:
            connection.close()

        self.assertTrue(building_key.startswith("kcb-"))
        self.assertNotIn("building_classification_current", tables)
        self.assertNotIn("building_classification_event", tables)
        self.assertEqual([], PROJECT.validate_database(self.database))

        harvested = CANDIDATE.harvest_candidate(
            self.staging,
            requester=self.fake,
            started_at="2026-08-19T13:00:00.000Z",
            completed_at="2026-08-19T13:01:00.000Z",
        )
        candidate_dir = Path(harvested["candidate_directory"])
        registered = CANDIDATE.register_candidate(self.database, candidate_dir)
        self.assertTrue(registered["registered"])
        self.assertTrue(registered["accepted_release_unchanged"])

        prepared = RECONCILE.prepare_reconciliation(
            self.database,
            candidate_dir,
            self.output,
        )
        self.assertTrue(prepared["valid"])
        self.assertTrue(prepared["ready_for_promotion"])
        self.assertEqual(0, prepared["ambiguity_count"])

        reconciliation_dir = Path(prepared["reconciliation_directory"])
        self.assertEqual(
            "kane-fabric-candidate.gpkg",
            RECONCILE.DATABASE_FILENAME,
        )
        self.assertTrue((reconciliation_dir / RECONCILE.DATABASE_FILENAME).is_file())

        validated = RECONCILE.validate_reconciliation(reconciliation_dir)
        self.assertTrue(validated["valid"])
        self.assertTrue(validated["ready_for_promotion"])
        self.assertEqual(0, validated["ambiguity_count"])
        self.assertEqual(2, validated["mapped_source_count"])
        self.assertEqual(0, validated["unmapped_source_count"])

        candidate_db = reconciliation_dir / RECONCILE.DATABASE_FILENAME
        connection = sqlite3.connect(candidate_db)
        try:
            project_count = connection.execute(
                "SELECT COUNT(*) FROM project_building"
            ).fetchone()[0]
            mapping_count = connection.execute(
                "SELECT COUNT(*) FROM project_building_source_mapping"
            ).fetchone()[0]
            candidate_tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        finally:
            connection.close()

        self.assertEqual(2, project_count)
        self.assertEqual(3, mapping_count)
        self.assertNotIn("building_classification_current", candidate_tables)
        self.assertNotIn("building_classification_event", candidate_tables)


if __name__ == "__main__":
    unittest.main()
