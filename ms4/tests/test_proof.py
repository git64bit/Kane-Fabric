from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from ms4.tools.kane_fabric_proof import ProofError, select_authoritative_building

RELEASE = {
    "release_key": "kane-buildings-20250730-086f09eba5ad",
    "content_sha256": "086f09eba5ad5b21eea1b6c9a8158eaf8c509a258c53509d115eaf1d19a7f799",
}


class ProofCompilerTests(unittest.TestCase):
    def _database(self, path: Path, *, object_key: str = "kcb-proof") -> None:
        connection = sqlite3.connect(path)
        try:
            connection.executescript(
                """
                CREATE TABLE dataset(dataset_id INTEGER PRIMARY KEY, dataset_key TEXT NOT NULL);
                CREATE TABLE source_release(
                    source_release_id INTEGER PRIMARY KEY,
                    dataset_id INTEGER NOT NULL,
                    release_key TEXT NOT NULL,
                    content_sha256 TEXT NOT NULL,
                    lifecycle_status TEXT NOT NULL
                );
                CREATE TABLE source_building(
                    source_building_id INTEGER PRIMARY KEY,
                    source_release_id INTEGER NOT NULL,
                    source_feature_id TEXT NOT NULL,
                    min_x REAL, min_y REAL, max_x REAL, max_y REAL,
                    geometry_sha256 TEXT NOT NULL
                );
                CREATE TABLE project_building(
                    project_building_id INTEGER PRIMARY KEY,
                    building_key TEXT NOT NULL,
                    lifecycle_status TEXT NOT NULL,
                    created_from_source_building_id INTEGER NOT NULL
                );
                """
            )
            connection.execute("INSERT INTO dataset VALUES (1, 'buildings')")
            connection.execute(
                "INSERT INTO source_release VALUES (1, 1, ?, ?, 'accepted')",
                (RELEASE["release_key"], RELEASE["content_sha256"]),
            )
            connection.execute(
                "INSERT INTO source_building VALUES (1, 1, 'source-1', -88.301, 41.879, -88.299, 41.881, ?)",
                ("b" * 64,),
            )
            connection.execute(
                "INSERT INTO project_building VALUES (1, ?, 'active', 1)",
                (object_key,),
            )
            connection.commit()
        finally:
            connection.close()

    def test_proof_building_is_read_from_accepted_persistent_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "fabric.gpkg"
            self._database(path)
            building = select_authoritative_building(path, RELEASE)
            self.assertEqual(building["building_key"], "kcb-proof")
            self.assertEqual(building["source_feature_id"], "source-1")
            self.assertEqual(building["release_key"], RELEASE["release_key"])

    def test_proof_building_release_must_match_accepted_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "fabric.gpkg"
            self._database(path)
            with self.assertRaisesRegex(ProofError, "release_key disagrees"):
                select_authoritative_building(
                    path,
                    {"release_key": "different", "content_sha256": RELEASE["content_sha256"]},
                )


if __name__ == "__main__":
    unittest.main()
