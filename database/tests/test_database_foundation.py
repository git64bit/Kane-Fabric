from __future__ import annotations

import importlib.util
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
MODULE_PATH = TOOLS / "kane_fabric_db.py"
SPEC = importlib.util.spec_from_file_location("kane_fabric_db_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
DB = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = DB
SPEC.loader.exec_module(DB)


class DatabaseFoundationTests(unittest.TestCase):
    def make_database(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "fabric.gpkg"
        result = DB.init_database(path)
        self.assertTrue(result["valid"])
        return temporary, path

    def test_fresh_database_has_geographic_core_without_classification(self) -> None:
        temporary, path = self.make_database()
        self.addCleanup(temporary.cleanup)

        connection = sqlite3.connect(path)
        try:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            migration_count = connection.execute(
                "SELECT COUNT(*) FROM schema_migration"
            ).fetchone()[0]
        finally:
            connection.close()

        self.assertTrue(DB.REQUIRED_TABLES <= tables)
        self.assertFalse(DB.APPLICATION_TABLES & tables)
        self.assertEqual(migration_count, 7)

    def test_fresh_database_uses_fabric_geopackage_identifiers(self) -> None:
        temporary, path = self.make_database()
        self.addCleanup(temporary.cleanup)

        connection = sqlite3.connect(path)
        try:
            identifiers = dict(
                connection.execute(
                    "SELECT table_name, identifier FROM gpkg_contents"
                )
            )
        finally:
            connection.close()

        self.assertEqual(identifiers["schema_migration"], "Kane Fabric schema migrations")
        self.assertEqual(identifiers["project_building"], "Kane Fabric geographic buildings")
        self.assertEqual(
            identifiers["refresh_promotion_event"],
            "Kane Fabric refresh promotion history",
        )
        self.assertFalse(any("Kane Condo" in value for value in identifiers.values()))

    def test_application_tables_are_not_required_for_core_validation(self) -> None:
        temporary, path = self.make_database()
        self.addCleanup(temporary.cleanup)

        connection = sqlite3.connect(path)
        try:
            connection.execute(
                "CREATE TABLE application_private_state (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            connection.commit()
        finally:
            connection.close()

        result = DB.validate_database(path)
        self.assertTrue(result["valid"], result["errors"])
        info = DB.database_info(path)
        self.assertEqual(info["extra_tables"], ["application_private_state"])

    def test_migrate_is_idempotent_at_current_schema(self) -> None:
        temporary, path = self.make_database()
        self.addCleanup(temporary.cleanup)

        before = DB.database_info(path)
        after = DB.migrate_database(path)
        self.assertEqual(before["migration_count"], after["migration_count"])
        self.assertEqual(after["migration_count"], 7)
        self.assertTrue(after["valid"])

    def test_validation_detects_migration_identity_tampering(self) -> None:
        temporary, path = self.make_database()
        self.addCleanup(temporary.cleanup)

        connection = sqlite3.connect(path)
        try:
            connection.execute(
                "UPDATE schema_migration SET sha256 = ? WHERE migration_id = 1",
                ("0" * 64,),
            )
            connection.commit()
        finally:
            connection.close()

        result = DB.validate_database(path)
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("Migration SHA-256 mismatch" in error for error in result["errors"]),
            result["errors"],
        )

    def test_geopackage_header_is_1_4(self) -> None:
        temporary, path = self.make_database()
        self.addCleanup(temporary.cleanup)

        connection = sqlite3.connect(path)
        try:
            application_id = connection.execute("PRAGMA application_id").fetchone()[0]
            user_version = connection.execute("PRAGMA user_version").fetchone()[0]
        finally:
            connection.close()

        self.assertEqual(application_id, DB.GPKG_APPLICATION_ID)
        self.assertEqual(user_version, DB.GPKG_USER_VERSION)


if __name__ == "__main__":
    unittest.main()
