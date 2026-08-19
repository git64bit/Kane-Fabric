from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Mapping

DATABASE = Path(__file__).resolve().parents[1]
TOOLS = DATABASE / "tools"

sys.path.insert(0, str(TOOLS))
import kane_fabric_building_candidate as CANDIDATE  # noqa: E402
import kane_fabric_buildings as BUILDINGS  # noqa: E402
import kane_fabric_candidate_compare as COMPARE  # noqa: E402
import kane_fabric_db as DB  # noqa: E402
import kane_fabric_provenance as PROVENANCE  # noqa: E402


class FakeArcGIS:
    def __init__(self) -> None:
        self.profile, _ = CANDIDATE.load_building_profile()
        self.object_ids = [2, 1]
        self.max_record_count = 2
        self.metadata: dict[str, Any] = {
            "type": "Feature Layer",
            "name": "Kane County Building Footprints",
            "geometryType": self.profile["geometry"]["arcgis_type"],
            "supportedQueryFormats": "JSON, geoJSON",
            "objectIdField": self.profile["query"]["object_id_field"],
            "fields": [
                {"name": name}
                for name in self.profile["query"]["out_fields"]
            ],
            "maxRecordCount": self.max_record_count,
            "editingInfo": {
                "lastEditDate": 1753889694870,
                "schemaLastEditDate": 1754339428959,
                "dataLastEditDate": 1753889694870,
            },
        }

    def feature(self, object_id: int) -> dict[str, Any]:
        base_x = -88.0 + object_id * 0.01
        base_y = 41.0 + object_id * 0.01
        properties = {
            name: None for name in self.profile["query"]["out_fields"]
        }
        properties["OBJECTID"] = object_id
        properties["FPId"] = f"fp-{object_id}"
        properties["CommonName"] = f"Building {object_id}"
        return {
            "type": "Feature",
            "properties": properties,
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [base_x, base_y],
                    [base_x + 0.001, base_y],
                    [base_x + 0.001, base_y + 0.001],
                    [base_x, base_y + 0.001],
                    [base_x, base_y],
                ]],
            },
        }

    def __call__(
        self,
        url: str,
        params: Mapping[str, str],
        *,
        timeout_seconds: float,
        byte_limit: int,
        post: bool,
    ) -> Any:
        if not url.endswith("/query"):
            return self.metadata
        if params.get("returnIdsOnly") == "true":
            return {
                "objectIdFieldName": self.profile["query"]["object_id_field"],
                "objectIds": list(self.object_ids),
            }
        requested = [int(value) for value in params["objectIds"].split(",")]
        return {
            "type": "FeatureCollection",
            "features": [self.feature(value) for value in reversed(requested)],
        }


class FabricCandidateComparisonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.database = self.root / "fabric.gpkg"
        self.staging = self.root / "staging"
        self.fake = FakeArcGIS()
        DB.init_database(self.database)
        self.create_accepted_buildings()

    def create_accepted_buildings(self) -> None:
        profile, _registry_sha = CANDIDATE.load_building_profile()
        accepted = {
            "type": "FeatureCollection",
            "features": [self.fake.feature(1)],
        }
        raw = CANDIDATE.canonical_bytes(accepted)
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
                "harvest_key": "fabric-buildings-accepted-fixture",
                "started_at": "2025-07-30T12:00:00.000Z",
                "completed_at": "2025-07-30T12:01:00.000Z",
                "status": "succeeded",
                "source_metadata": {
                    "id_property": "FPId",
                    "object_id_field": "OBJECTID",
                    "object_ids": [1],
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
                "release_key": "fabric-buildings-accepted-fixture",
                "lifecycle_status": "accepted",
                "source_published_at": "2025-07-30T10:30:00.000Z",
                "content_sha256": hashlib.sha256(raw).hexdigest(),
                "feature_count": 1,
                "metadata": {
                    "id_property": "FPId",
                    "object_id_field": "OBJECTID",
                    "object_ids": [1],
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
            "fabric-buildings-accepted-fixture",
            source,
        )

    def test_candidate_registration_and_comparison_are_deterministic(self) -> None:
        profile, registry_sha = CANDIDATE.load_building_profile()
        self.assertEqual("buildings", profile["dataset_key"])
        self.assertEqual(
            CANDIDATE.kane_source_profiles.APPROVED_REGISTRY_SHA256,
            registry_sha,
        )
        self.assertEqual(
            DATABASE / "source-profiles",
            CANDIDATE.kane_source_profiles.PROFILE_DIR,
        )
        self.assertEqual(
            DATABASE / "source-profiles",
            CANDIDATE.PROFILE_DIR,
        )

        harvested = CANDIDATE.harvest_candidate(
            self.staging,
            requester=self.fake,
            started_at="2026-08-19T12:30:00.000Z",
            completed_at="2026-08-19T12:31:00.000Z",
        )
        candidate_dir = Path(harvested["candidate_directory"])

        registered = CANDIDATE.register_candidate(self.database, candidate_dir)
        self.assertTrue(registered["registered"])
        self.assertTrue(registered["accepted_release_unchanged"])
        self.assertTrue(registered["protected_state_unchanged"])

        connection = sqlite3.connect(self.database)
        try:
            accepted = connection.execute(
                "SELECT release_key FROM source_release "
                "WHERE lifecycle_status = 'accepted' AND dataset_id = "
                "(SELECT dataset_id FROM dataset WHERE dataset_key = 'buildings')"
            ).fetchone()[0]
            candidate_count = connection.execute(
                "SELECT COUNT(*) FROM source_release "
                "WHERE lifecycle_status = 'candidate' AND dataset_id = "
                "(SELECT dataset_id FROM dataset WHERE dataset_key = 'buildings')"
            ).fetchone()[0]
        finally:
            connection.close()

        self.assertEqual("fabric-buildings-accepted-fixture", accepted)
        self.assertEqual(1, candidate_count)

        first = COMPARE.compare_candidate(self.database, candidate_dir)
        second = COMPARE.compare_candidate(self.database, candidate_dir)
        self.assertEqual(first, second)
        self.assertEqual(first["comparison_sha256"], second["comparison_sha256"])

        dataset = first["datasets"][0]
        self.assertEqual("buildings", dataset["dataset_key"])
        self.assertEqual(1, dataset["feature_changes"]["added"]["count"])
        self.assertEqual(1, dataset["feature_changes"]["unchanged"]["count"])
        self.assertEqual(0, dataset["feature_changes"]["removed"]["count"])


if __name__ == "__main__":
    unittest.main()
