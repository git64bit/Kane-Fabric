#!/usr/bin/env python3
"""Create, migrate, validate, and inspect Kane Fabric GeoPackages."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

GPKG_APPLICATION_ID = 0x47504B47
GPKG_USER_VERSION = 10400
GPKG_VERSION = "1.4.0"
MIGRATION_PATTERN = re.compile(r"^(?P<number>[0-9]{4})_[a-z0-9]+(?:_[a-z0-9]+)*\.sql$")
DATETIME_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z$")

REQUIRED_TABLES = {
    "county",
    "source_agency",
    "dataset",
    "harvest_run",
    "source_file",
    "source_release",
    "source_county_boundary",
    "source_map_feature",
    "source_building",
    "project_building",
    "project_building_source_mapping",
    "refresh_promotion_event",
    "schema_migration",
    "gpkg_spatial_ref_sys",
    "gpkg_contents",
    "gpkg_geometry_columns",
    "gpkg_extensions",
}

APPLICATION_TABLES = {
    "building_classification_event",
    "building_classification_current",
}

GEOMETRY_TABLES = {
    "source_county_boundary": 4326,
    "source_map_feature": 4326,
    "source_building": 4326,
}


@dataclass(frozen=True)
class Migration:
    number: int
    filename: str
    path: Path
    sha256: str


def migrations_directory() -> Path:
    return Path(__file__).resolve().parent.parent / "migrations"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    now = dt.datetime.now(dt.timezone.utc)
    return now.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def valid_datetime(value: object) -> bool:
    return isinstance(value, str) and DATETIME_PATTERN.fullmatch(value) is not None


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def discover_migrations() -> list[Migration]:
    root = migrations_directory()
    if not root.is_dir():
        raise RuntimeError(f"Migration directory is missing: {root}")

    migrations: list[Migration] = []
    for path in sorted(root.iterdir()):
        if not path.is_file():
            continue
        match = MIGRATION_PATTERN.fullmatch(path.name)
        if match is None:
            if path.suffix == ".sql":
                raise RuntimeError(f"Invalid migration filename: {path.name}")
            continue
        migrations.append(
            Migration(
                number=int(match.group("number")),
                filename=path.name,
                path=path,
                sha256=sha256_file(path),
            )
        )

    if not migrations:
        raise RuntimeError("No Kane Fabric migrations were found")

    expected = list(range(1, len(migrations) + 1))
    actual = [migration.number for migration in migrations]
    if actual != expected:
        raise RuntimeError(
            f"Migration sequence must be contiguous from 0001: expected {expected}, found {actual}"
        )

    return migrations


def table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
        if not str(row[0]).startswith("sqlite_")
    }


def _connect(path: Path, *, read_only: bool = False) -> sqlite3.Connection:
    if read_only:
        connection = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
        connection.execute("PRAGMA query_only = ON")
    else:
        connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _apply_migration(connection: sqlite3.Connection, migration: Migration) -> None:
    sql = migration.path.read_text(encoding="utf-8")
    if not sql.strip():
        raise RuntimeError(f"Migration is empty: {migration.filename}")
    created_at = utc_now()
    ledger = (
        "INSERT INTO schema_migration (migration_id, filename, sha256, applied_at) VALUES ("
        f"{migration.number}, {sql_literal(migration.filename)}, "
        f"{sql_literal(migration.sha256)}, {sql_literal(created_at)});"
    )
    script = "BEGIN IMMEDIATE;\n" + sql + "\n" + ledger + "\nCOMMIT;\n"
    connection.executescript(script)


def _set_geopackage_header(connection: sqlite3.Connection) -> None:
    connection.execute(f"PRAGMA application_id = {GPKG_APPLICATION_ID}")
    connection.execute(f"PRAGMA user_version = {GPKG_USER_VERSION}")
    connection.commit()


def init_database(path: Path) -> dict[str, object]:
    path = path.resolve()
    if path.exists():
        raise RuntimeError(f"Database already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)

    migrations = discover_migrations()
    connection = _connect(path)
    try:
        for migration in migrations:
            _apply_migration(connection, migration)
        _set_geopackage_header(connection)
    except Exception:
        connection.close()
        path.unlink(missing_ok=True)
        raise
    else:
        connection.close()

    result = validate_database(path)
    if not result["valid"]:
        path.unlink(missing_ok=True)
        raise RuntimeError("New Kane Fabric database failed validation: " + "; ".join(result["errors"]))
    return database_info(path)


def _ledger_rows(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    connection.row_factory = sqlite3.Row
    return connection.execute(
        "SELECT migration_id, filename, sha256, applied_at FROM schema_migration ORDER BY migration_id"
    ).fetchall()


def _validate_ledger(connection: sqlite3.Connection, migrations: Sequence[Migration]) -> list[str]:
    errors: list[str] = []
    try:
        rows = _ledger_rows(connection)
    except sqlite3.Error as exc:
        return [f"Unable to read migration ledger: {exc}"]

    if len(rows) > len(migrations):
        errors.append(
            f"Migration ledger has {len(rows)} entries but repository has only {len(migrations)}"
        )
        return errors

    for index, row in enumerate(rows):
        migration = migrations[index]
        if int(row["migration_id"]) != migration.number:
            errors.append(
                f"Migration ledger ID mismatch at position {index + 1}: {row['migration_id']}"
            )
        if str(row["filename"]) != migration.filename:
            errors.append(
                f"Migration filename mismatch for {migration.number:04d}: {row['filename']!r}"
            )
        if str(row["sha256"]) != migration.sha256:
            errors.append(f"Migration SHA-256 mismatch: {migration.filename}")
        if not valid_datetime(row["applied_at"]):
            errors.append(f"Migration applied_at is invalid: {migration.filename}")

    return errors


def migrate_database(path: Path) -> dict[str, object]:
    path = path.resolve()
    if not path.is_file():
        raise RuntimeError(f"Database does not exist: {path}")

    migrations = discover_migrations()
    connection = _connect(path)
    try:
        tables = table_names(connection)
        if "schema_migration" not in tables:
            raise RuntimeError("Existing database has no Kane Fabric migration ledger")

        ledger_errors = _validate_ledger(connection, migrations)
        if ledger_errors:
            raise RuntimeError("Existing migration ledger is incompatible: " + "; ".join(ledger_errors))

        applied = len(_ledger_rows(connection))
        for migration in migrations[applied:]:
            _apply_migration(connection, migration)
        _set_geopackage_header(connection)
    finally:
        connection.close()

    result = validate_database(path)
    if not result["valid"]:
        raise RuntimeError("Migrated database failed validation: " + "; ".join(result["errors"]))
    return database_info(path)


def validate_database(path: Path) -> dict[str, object]:
    path = path.resolve()
    errors: list[str] = []
    if not path.is_file():
        return {"valid": False, "path": str(path), "errors": ["Database does not exist"]}

    try:
        migrations = discover_migrations()
    except Exception as exc:
        return {"valid": False, "path": str(path), "errors": [str(exc)]}

    connection = _connect(path, read_only=True)
    try:
        application_id = int(connection.execute("PRAGMA application_id").fetchone()[0])
        user_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if application_id != GPKG_APPLICATION_ID:
            errors.append(
                f"GeoPackage application_id is {application_id}; expected {GPKG_APPLICATION_ID}"
            )
        if user_version != GPKG_USER_VERSION:
            errors.append(
                f"GeoPackage user_version is {user_version}; expected {GPKG_USER_VERSION}"
            )

        quick = [str(row[0]) for row in connection.execute("PRAGMA quick_check")]
        if quick != ["ok"]:
            errors.append("SQLite quick_check failed: " + "; ".join(quick))

        foreign_keys = list(connection.execute("PRAGMA foreign_key_check"))
        if foreign_keys:
            errors.append(f"SQLite foreign_key_check found {len(foreign_keys)} violation(s)")

        tables = table_names(connection)
        missing = sorted(REQUIRED_TABLES - tables)
        if missing:
            errors.append("Missing Kane Fabric core tables: " + ", ".join(missing))

        if "schema_migration" in tables:
            errors.extend(_validate_ledger(connection, migrations))
            rows = _ledger_rows(connection)
            if len(rows) != len(migrations):
                errors.append(
                    f"Database has {len(rows)} migrations; repository requires {len(migrations)}"
                )

        if "gpkg_geometry_columns" in tables:
            registrations = {
                str(row[0]): int(row[1])
                for row in connection.execute(
                    "SELECT table_name, srs_id FROM gpkg_geometry_columns"
                )
            }
            for table, srs_id in GEOMETRY_TABLES.items():
                if registrations.get(table) != srs_id:
                    errors.append(
                        f"Geometry registration for {table} is {registrations.get(table)!r}; expected SRS {srs_id}"
                    )

        trigger_names = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'trigger'"
            )
        }
        for trigger in (
            "tr_refresh_promotion_event_no_update",
            "tr_refresh_promotion_event_no_delete",
        ):
            if trigger not in trigger_names:
                errors.append(f"Missing promotion-history trigger: {trigger}")
    finally:
        connection.close()

    return {"valid": not errors, "path": str(path), "errors": errors}


def database_info(path: Path) -> dict[str, object]:
    path = path.resolve()
    validation = validate_database(path)
    if not validation["valid"]:
        raise RuntimeError("Database is invalid: " + "; ".join(validation["errors"]))

    connection = _connect(path, read_only=True)
    try:
        tables = table_names(connection)
        migration_count = int(connection.execute("SELECT COUNT(*) FROM schema_migration").fetchone()[0])
    finally:
        connection.close()

    return {
        "valid": True,
        "path": str(path),
        "byte_length": path.stat().st_size,
        "sha256": sha256_file(path),
        "geopackage_version": GPKG_VERSION,
        "migration_count": migration_count,
        "core_table_count": len(REQUIRED_TABLES),
        "application_tables_present": sorted(APPLICATION_TABLES & tables),
        "extra_tables": sorted(tables - REQUIRED_TABLES - APPLICATION_TABLES),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "migrate", "validate", "info"):
        command = commands.add_parser(name)
        command.add_argument("database", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            result = init_database(args.database)
        elif args.command == "migrate":
            result = migrate_database(args.database)
        elif args.command == "validate":
            result = validate_database(args.database)
        elif args.command == "info":
            result = database_info(args.database)
        else:
            raise RuntimeError(f"Unknown command: {args.command}")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("valid", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
