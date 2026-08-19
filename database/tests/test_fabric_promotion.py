from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
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

sys.path.insert(0, str(TOOLS))

import kane_fabric_boundary as BOUNDARY  # noqa: E402
import kane_fabric_buildings as BUILDINGS  # noqa: E402
import kane_fabric_db as DB  # noqa: E402
import kane_fabric_map_layers as MAP_LAYERS  # noqa: E402
import kane_fabric_project_buildings as PROJECT  # noqa: E402
import kane_fabric_promotion as PROMOTION  # noqa: E402
import kane_fabric_provenance as PROVENANCE  # noqa: E402


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


@unittest.skipUnless(DONOR.is_dir(), "frozen Kane Condo 0.4 donor is not available")
class FabricPromotionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.active = self.root / "active.gpkg"
        DB.init_database(self.active)
        self.previous_keys: dict[str, str] = {}
        self.candidate_keys: dict[str, str] = {}
        self._build_release_fixture()
        self.promotion_dir = self._build_promotion_artifact()

    def _geojson(self, filename: str, geometry: dict[str, object], feature_id: str) -> Path:
        path = self.root / filename
        path.write_bytes(
            canonical_bytes(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {"id": feature_id},
                            "geometry": geometry,
                        }
                    ],
                }
            )
        )
        return path

    def _record_release(
        self,
        *,
        dataset_key: str,
        data_kind: str,
        release_key: str,
        lifecycle: str,
        source: Path,
    ) -> None:
        raw = source.read_bytes()
        suffix = "old" if lifecycle == "accepted" else "new"
        descriptor = {
            "county": {
                "county_key": "fabric-test-county",
                "name": "Fabric Test County",
                "state_code": "IL",
                "country_code": "US",
                "fips_code": "17089",
            },
            "agency": {
                "agency_key": "fabric-test-agency",
                "name": "Fabric Test Agency",
                "jurisdiction": "Fabric Test County, Illinois",
                "homepage_uri": "https://example.invalid/",
            },
            "dataset": {
                "dataset_key": dataset_key,
                "name": dataset_key,
                "description": "Fabric atomic promotion fixture",
                "data_kind": data_kind,
                "source_uri": f"https://example.invalid/{dataset_key}",
            },
            "harvest": {
                "harvest_key": f"{dataset_key}-{suffix}-harvest",
                "started_at": "2026-08-19T15:00:00.000Z",
                "completed_at": "2026-08-19T15:00:01.000Z",
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
                "lifecycle_status": lifecycle,
                "source_published_at": (
                    "2026-08-18T10:00:00.000Z"
                    if lifecycle == "accepted"
                    else "2026-08-19T10:00:00.000Z"
                ),
                "content_sha256": hashlib.sha256(raw).hexdigest(),
                "feature_count": 1,
                "metadata": {"id_property": "id"},
                "accepted_at": (
                    "2026-08-18T12:00:00.000Z" if lifecycle == "accepted" else None
                ),
            },
        }
        descriptor_path = self.root / f"{release_key}.json"
        descriptor_path.write_bytes(canonical_bytes(descriptor))
        PROVENANCE.record_descriptor(self.active, descriptor_path)

    def _import_release(
        self,
        dataset_key: str,
        release_key: str,
        source: Path,
    ) -> None:
        if dataset_key == "buildings":
            BUILDINGS.import_buildings(self.active, release_key, source)
        elif dataset_key == "county-boundary":
            BOUNDARY.import_boundary(self.active, release_key, source)
        else:
            MAP_LAYERS.import_map_layers(self.active, [(release_key, source)])

    def _build_release_fixture(self) -> None:
        polygon_old = {
            "type": "Polygon",
            "coordinates": [[
                [-88.40, 41.90],
                [-88.39, 41.90],
                [-88.39, 41.91],
                [-88.40, 41.91],
                [-88.40, 41.90],
            ]],
        }
        polygon_new = {
            "type": "Polygon",
            "coordinates": [[
                [-88.40, 41.90],
                [-88.385, 41.90],
                [-88.385, 41.915],
                [-88.40, 41.915],
                [-88.40, 41.90],
            ]],
        }
        line_old = {
            "type": "LineString",
            "coordinates": [[-88.40, 41.90], [-88.30, 42.00]],
        }
        line_new = {
            "type": "LineString",
            "coordinates": [[-88.40, 41.90], [-88.29, 42.01]],
        }

        specifications = (
            ("county-boundary", "boundary", polygon_old, polygon_new, "boundary-1"),
            ("roads", "roads", line_old, line_new, "road-1"),
            ("water-creeks", "water", line_old, line_new, "creek-1"),
            ("water-fox-river", "water", polygon_old, polygon_new, "river-1"),
            ("buildings", "buildings", polygon_old, polygon_new, "building-1"),
        )

        old_sources: dict[str, Path] = {}
        new_sources: dict[str, Path] = {}
        data_kinds: dict[str, str] = {}

        for dataset_key, data_kind, old_geometry, new_geometry, feature_id in specifications:
            old_key = f"fabric-{dataset_key}-accepted"
            new_key = f"fabric-{dataset_key}-candidate"
            self.previous_keys[dataset_key] = old_key
            self.candidate_keys[dataset_key] = new_key
            data_kinds[dataset_key] = data_kind
            old_sources[dataset_key] = self._geojson(
                f"{dataset_key}-old.geojson", old_geometry, feature_id
            )
            new_sources[dataset_key] = self._geojson(
                f"{dataset_key}-new.geojson", new_geometry, feature_id
            )

        # Keep every intermediate database state valid. Each accepted release is
        # fully populated before another accepted release is introduced.
        for dataset_key, _data_kind, _old_geometry, _new_geometry, _feature_id in specifications:
            self._record_release(
                dataset_key=dataset_key,
                data_kind=data_kinds[dataset_key],
                release_key=self.previous_keys[dataset_key],
                lifecycle="accepted",
                source=old_sources[dataset_key],
            )
            self._import_release(
                dataset_key,
                self.previous_keys[dataset_key],
                old_sources[dataset_key],
            )

        # Candidate releases may exist without becoming authoritative, but store
        # their feature rows immediately so the completed fixture is fully valid.
        for dataset_key, _data_kind, _old_geometry, _new_geometry, _feature_id in specifications:
            self._record_release(
                dataset_key=dataset_key,
                data_kind=data_kinds[dataset_key],
                release_key=self.candidate_keys[dataset_key],
                lifecycle="candidate",
                source=new_sources[dataset_key],
            )
            self._import_release(
                dataset_key,
                self.candidate_keys[dataset_key],
                new_sources[dataset_key],
            )

        PROJECT.seed_project_buildings(self.active, self.previous_keys["buildings"])
        connection = sqlite3.connect(self.active)
        try:
            project_id = connection.execute(
                "SELECT project_building_id FROM project_building"
            ).fetchone()[0]
            candidate_source_id = connection.execute(
                "SELECT sb.source_building_id FROM source_building sb "
                "JOIN source_release sr ON sr.source_release_id = sb.source_release_id "
                "WHERE sr.release_key = ?",
                (self.candidate_keys["buildings"],),
            ).fetchone()[0]
            now = DB.utc_now()
            connection.execute(
                "INSERT INTO project_building_source_mapping ("
                "project_building_id, source_building_id, relationship_type, "
                "decision_method, mapping_status, created_at, reviewed_at"
                ") VALUES (?, ?, 'continuation', 'automatic', 'confirmed', ?, NULL)",
                (project_id, candidate_source_id, now),
            )
            connection.execute(
                "UPDATE gpkg_contents SET last_change = ? "
                "WHERE table_name = 'project_building_source_mapping'",
                (now,),
            )
            connection.commit()
        finally:
            connection.close()

        self.assertEqual([], PROJECT.validate_database(self.active))

    def _build_promotion_artifact(self) -> Path:
        previous_sha = PROMOTION.sha256_file(self.active)
        previous_state = PROMOTION._database_snapshot(self.active)
        transitions = {
            dataset_key: {
                "previous_release_key": self.previous_keys[dataset_key],
                "candidate_release_key": self.candidate_keys[dataset_key],
                "comparison_sha256": hashlib.sha256(dataset_key.encode()).hexdigest(),
            }
            for dataset_key in PROMOTION.DATASET_ORDER
        }
        core = {
            "promotion_schema": PROMOTION.PROMOTION_SCHEMA,
            "previous_database_sha256": previous_sha,
            "previous_state": previous_state,
            "reconciliation_key": "fabric-reconciliation-fixture",
            "reconciliation_sha256": "a" * 64,
            "release_transitions": transitions,
            "candidate_evidence": {"fixture": "atomic-promotion"},
            "authorization_kind": "explicit-command",
        }
        digest = PROMOTION.sha256_value(core)
        plan = {
            **core,
            "promotion_key": f"kane-fabric-promotion-{digest[:12]}",
            "promotion_plan_sha256": digest,
        }

        directory = self.root / "promotion" / plan["promotion_key"]
        directory.mkdir(parents=True)
        candidate_database = directory / PROMOTION.DATABASE_FILENAME
        shutil.copyfile(self.active, candidate_database)
        prepared_sha = PROMOTION.sha256_file(candidate_database)
        event_created = PROMOTION.DONOR._promote_release_rows(
            candidate_database, plan, prepared_sha
        )
        PROMOTION.DONOR._verify_promoted_state(
            candidate_database,
            {**plan, "prepared_candidate_sha256": prepared_sha},
        )
        promoted_state = PROMOTION._database_snapshot(candidate_database)
        database_info = {
            "filename": PROMOTION.DATABASE_FILENAME,
            "byte_length": candidate_database.stat().st_size,
            "sha256": PROMOTION.sha256_file(candidate_database),
        }
        manifest = {
            **plan,
            "prepared_candidate_sha256": prepared_sha,
            "promotion_event_created_at": event_created,
            "promoted_state": promoted_state,
            "final_candidate_database": database_info,
        }
        (directory / PROMOTION.MANIFEST_FILENAME).write_bytes(
            PROMOTION.canonical_bytes(manifest) + b"\n"
        )
        validated = PROMOTION.validate_promotion(directory)
        self.assertTrue(validated["valid"])
        return directory

    def _accepted_keys(self, database: Path) -> dict[str, str]:
        return PROMOTION.database_promotion_info(database)["accepted_release_keys"]

    def test_atomic_promotion_manual_and_automatic_rollback(self) -> None:
        validation = PROMOTION.validate_promotion(self.promotion_dir)
        self.assertTrue(validation["promotion_key"].startswith("kane-fabric-promotion-"))
        self.assertEqual(
            "kane-fabric-promoted.gpkg",
            PROMOTION.DATABASE_FILENAME,
        )

        live = self.root / "manual-live.gpkg"
        shutil.copyfile(self.active, live)
        previous_sha = PROMOTION.sha256_file(live)
        rollback_root = self.root / "manual-rollback"

        promoted = PROMOTION.promote_database(live, self.promotion_dir, rollback_root)
        self.assertTrue(promoted["promoted"])
        self.assertFalse(promoted["existing"])
        self.assertEqual(self.candidate_keys, self._accepted_keys(live))

        backup = Path(promoted["backup_database"])
        self.assertEqual(previous_sha, PROMOTION.sha256_file(backup))

        rolled_back = PROMOTION.rollback_database(
            live,
            self.promotion_dir,
            rollback_root,
            "Fabric promotion regression proof",
        )
        self.assertTrue(rolled_back["rolled_back"])
        self.assertEqual(self.previous_keys, self._accepted_keys(live))
        self.assertTrue(
            (
                rollback_root
                / validation["promotion_key"]
                / "promoted-before-rollback.gpkg"
            ).is_file()
        )

        connection = sqlite3.connect(live)
        try:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        finally:
            connection.close()
        self.assertNotIn("building_classification_current", tables)
        self.assertNotIn("building_classification_event", tables)

        automatic_live = self.root / "automatic-live.gpkg"
        shutil.copyfile(self.active, automatic_live)
        automatic_rollback = self.root / "automatic-rollback"

        def fail_post_verify(_database, _manifest):
            raise RuntimeError("injected post-verification failure")

        with self.assertRaisesRegex(
            RuntimeError,
            "prior accepted state was restored",
        ):
            PROMOTION.promote_database(
                automatic_live,
                self.promotion_dir,
                automatic_rollback,
                post_verify=fail_post_verify,
            )

        self.assertEqual(self.previous_keys, self._accepted_keys(automatic_live))
        activation = (
            automatic_rollback
            / validation["promotion_key"]
            / "activation.json"
        )
        receipt = json.loads(activation.read_text())
        self.assertFalse(receipt["promoted"])
        self.assertTrue(receipt["rolled_back"])


if __name__ == "__main__":
    unittest.main()
