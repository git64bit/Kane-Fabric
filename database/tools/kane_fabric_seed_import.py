#!/usr/bin/env python3
"""Build and validate a clean Kane Fabric county database from an approved seed GeoPackage."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

import kane_fabric_boundary as kane_boundary
import kane_fabric_buildings as kane_buildings
import kane_fabric_db as kane_db
import kane_fabric_map_layers as kane_map_layers
import kane_fabric_project_buildings as kane_project_buildings
import kane_fabric_provenance as kane_provenance

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
DEFAULT_CONTRACT = (
    Path(__file__).resolve().parent.parent
    / "seed"
    / "kane-offline-map-0911eeef.json"
)
DONOR_REQUIRED_TABLES = {
    "county",
    "source_agency",
    "dataset",
    "harvest_run",
    "source_file",
    "source_release",
    "source_county_boundary",
    "source_map_feature",
    "source_building",
}
FEATURE_TABLES = {
    "boundary": ("source_county_boundary", "source_boundary_id"),
    "roads": ("source_map_feature", "source_map_feature_id"),
    "water": ("source_map_feature", "source_map_feature_id"),
    "buildings": ("source_building", "source_building_id"),
}
APPLICATION_TABLES = {
    "building_classification_current",
    "building_classification_event",
}


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def remove_sqlite_files(path: Path) -> None:
    for candidate in (
        path,
        Path(str(path) + "-wal"),
        Path(str(path) + "-shm"),
        Path(str(path) + "-journal"),
    ):
        candidate.unlink(missing_ok=True)


def load_json_object(path: Path, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to read {label} {path}: {exc}") from exc
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{label} must be a JSON object")
    return value


def normalize_datetime(value: object, fallback: str | None = None) -> str | None:
    if value is None or value == "":
        return fallback
    if not isinstance(value, str):
        raise RuntimeError(f"Invalid donor datetime value: {value!r}")
    text = value.strip()
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeError(f"Invalid donor datetime value: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    parsed = parsed.astimezone(dt.timezone.utc)
    return parsed.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def validate_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    key = contract.get("contract_key")
    donor = contract.get("donor")
    releases = contract.get("expected_releases")
    totals = contract.get("expected_totals")
    excluded = contract.get("excluded_donor_tables")
    if not isinstance(key, str) or not key.strip():
        raise RuntimeError("Seed contract contract_key is invalid")
    if not isinstance(donor, Mapping):
        raise RuntimeError("Seed contract donor must be an object")
    donor_sha = donor.get("sha256")
    donor_bytes = donor.get("byte_length")
    source_commit = donor.get("source_commit")
    if not isinstance(donor_sha, str) or SHA256_PATTERN.fullmatch(donor_sha) is None:
        raise RuntimeError("Seed contract donor.sha256 is invalid")
    if not isinstance(donor_bytes, int) or isinstance(donor_bytes, bool) or donor_bytes <= 0:
        raise RuntimeError("Seed contract donor.byte_length is invalid")
    if not isinstance(source_commit, str) or not source_commit.strip():
        raise RuntimeError("Seed contract donor.source_commit is invalid")
    if not isinstance(releases, list) or not releases:
        raise RuntimeError("Seed contract expected_releases must be a non-empty array")

    normalized_releases: list[dict[str, str]] = []
    seen_datasets: set[str] = set()
    seen_releases: set[str] = set()
    for index, item in enumerate(releases):
        if not isinstance(item, Mapping):
            raise RuntimeError(f"Seed contract expected_releases[{index}] is invalid")
        normalized: dict[str, str] = {}
        for field in (
            "dataset_key",
            "release_key",
            "data_kind",
            "id_property",
            "content_sha256",
        ):
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                raise RuntimeError(
                    f"Seed contract expected_releases[{index}].{field} is invalid"
                )
            normalized[field] = value.strip()
        if SHA256_PATTERN.fullmatch(normalized["content_sha256"]) is None:
            raise RuntimeError(
                f"Seed contract expected_releases[{index}].content_sha256 is invalid"
            )
        if normalized["data_kind"] not in FEATURE_TABLES:
            raise RuntimeError(
                f"Seed contract expected_releases[{index}].data_kind is unsupported"
            )
        if normalized["dataset_key"] in seen_datasets:
            raise RuntimeError("Seed contract dataset keys must be unique")
        if normalized["release_key"] in seen_releases:
            raise RuntimeError("Seed contract release keys must be unique")
        seen_datasets.add(normalized["dataset_key"])
        seen_releases.add(normalized["release_key"])
        normalized_releases.append(normalized)

    if not isinstance(totals, Mapping):
        raise RuntimeError("Seed contract expected_totals must be an object")
    normalized_totals: dict[str, int] = {}
    for kind in FEATURE_TABLES:
        count = totals.get(kind)
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise RuntimeError(f"Seed contract expected_totals.{kind} is invalid")
        normalized_totals[kind] = count
    if not isinstance(excluded, list) or not all(
        isinstance(value, str) and value for value in excluded
    ):
        raise RuntimeError("Seed contract excluded_donor_tables is invalid")

    return {
        "contract_key": key.strip(),
        "donor": {
            "sha256": donor_sha,
            "byte_length": donor_bytes,
            "source_commit": source_commit.strip(),
        },
        "expected_releases": normalized_releases,
        "expected_totals": normalized_totals,
        "excluded_donor_tables": sorted(set(excluded)),
    }


def table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )
    }


def donor_release_rows(
    connection: sqlite3.Connection, contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        "SELECT r.*, d.dataset_key, d.dataset_name, d.description, d.feature_class, "
        "d.source_id_policy, a.agency_key, a.agency_name, a.jurisdiction, "
        "a.homepage_uri, a.created_at AS agency_created_at, c.county_name, "
        "c.state_name, c.state_code, c.fips_code, c.created_at AS county_created_at, "
        "d.created_at AS dataset_created_at "
        "FROM source_release r JOIN dataset d ON d.dataset_id = r.dataset_id "
        "JOIN county c ON c.county_id = d.county_id "
        "JOIN source_agency a ON a.agency_id = d.agency_id "
        "WHERE r.status = 'accepted' ORDER BY d.dataset_key"
    ).fetchall()
    expected = {
        item["dataset_key"]: item for item in contract["expected_releases"]
    }
    actual_keys = {str(row["dataset_key"]) for row in rows}
    if actual_keys != set(expected):
        raise RuntimeError(
            "Accepted donor dataset set differs from the seed contract: "
            f"expected {sorted(expected)}, found {sorted(actual_keys)}"
        )

    output: list[dict[str, Any]] = []
    totals = {kind: 0 for kind in FEATURE_TABLES}
    for row in rows:
        dataset_key = str(row["dataset_key"])
        specification = expected[dataset_key]
        if row["release_key"] != specification["release_key"]:
            raise RuntimeError(
                f"Donor release mismatch for {dataset_key}: {row['release_key']}"
            )
        if row["content_sha256"] != specification["content_sha256"]:
            raise RuntimeError(f"Donor content SHA-256 mismatch for {dataset_key}")
        table, _identity = FEATURE_TABLES[specification["data_kind"]]
        count = int(
            connection.execute(
                f"SELECT COUNT(*) FROM {table} WHERE release_id = ?",
                (row["release_id"],),
            ).fetchone()[0]
        )
        if count <= 0:
            raise RuntimeError(f"Accepted donor release has no features: {row['release_key']}")
        totals[specification["data_kind"]] += count
        files = connection.execute(
            "SELECT * FROM source_file WHERE release_id = ? ORDER BY source_file_id",
            (row["release_id"],),
        ).fetchall()
        source_candidates = [
            item
            for item in files
            if str(item["media_type"] or "").lower() == "application/geo+json"
            or (
                str(item["relative_path"]).lower().endswith(".geojson")
                and "manifest" not in str(item["relative_path"]).lower()
            )
        ]
        if len(source_candidates) != 1:
            raise RuntimeError(
                f"Donor release {row['release_key']} does not have exactly one source GeoJSON file"
            )
        run = connection.execute(
            "SELECT * FROM harvest_run WHERE candidate_release_id = ? "
            "ORDER BY run_id DESC LIMIT 1",
            (row["release_id"],),
        ).fetchone()
        output.append(
            {
                "release": dict(row),
                "specification": specification,
                "feature_count": count,
                "files": [dict(item) for item in files],
                "source_file_id": int(source_candidates[0]["source_file_id"]),
                "harvest": dict(run) if run is not None else None,
            }
        )

    expected_totals = dict(contract["expected_totals"])
    if totals != expected_totals:
        raise RuntimeError(
            f"Donor feature totals differ from the seed contract: expected "
            f"{expected_totals}, found {totals}"
        )
    return output


def inspect_donor(donor: Path, contract: Mapping[str, Any]) -> dict[str, Any]:
    if not donor.is_file():
        raise RuntimeError(f"Donor database does not exist: {donor}")
    actual_bytes = donor.stat().st_size
    actual_sha = sha256_file(donor)
    expected = contract["donor"]
    if actual_bytes != expected["byte_length"]:
        raise RuntimeError(
            f"Donor byte length is {actual_bytes}; expected {expected['byte_length']}"
        )
    if actual_sha != expected["sha256"]:
        raise RuntimeError(f"Donor SHA-256 is {actual_sha}; expected {expected['sha256']}")
    connection = sqlite3.connect(f"file:{donor.resolve()}?mode=ro", uri=True)
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchall()
        if integrity != [("ok",)]:
            raise RuntimeError(f"Donor SQLite integrity_check failed: {integrity!r}")
        missing = sorted(DONOR_REQUIRED_TABLES - table_names(connection))
        if missing:
            raise RuntimeError("Donor database is missing tables: " + ", ".join(missing))
        releases = donor_release_rows(connection, contract)
        donor_tables = table_names(connection)
    finally:
        connection.close()
    return {
        "path": str(donor.resolve()),
        "byte_length": actual_bytes,
        "sha256": actual_sha,
        "source_commit": expected["source_commit"],
        "releases": releases,
        "donor_tables": sorted(donor_tables),
    }


def file_role(file_row: Mapping[str, Any], source_file_id: int) -> str:
    if int(file_row["source_file_id"]) == source_file_id:
        return "source"
    path = str(file_row["relative_path"]).lower()
    if "manifest" in path:
        return "manifest"
    if "metadata" in path:
        return "metadata"
    if "inventory" in path:
        return "inventory"
    if "exclusion" in path:
        return "exclusions"
    return "other"


def insert_administration(
    target: sqlite3.Connection,
    donor_info: Mapping[str, Any],
) -> list[dict[str, Any]]:
    releases = donor_info["releases"]
    first = releases[0]["release"]
    seed_time = kane_db.utc_now()
    county_created = normalize_datetime(first["county_created_at"], seed_time) or seed_time
    target.execute(
        "INSERT INTO county (county_key, name, state_code, country_code, fips_code, created_at) "
        "VALUES ('kane-county-il', ?, ?, 'US', ?, ?)",
        (first["county_name"], first["state_code"], first["fips_code"], county_created),
    )
    county_id = int(target.execute("SELECT last_insert_rowid()").fetchone()[0])
    agency_ids: dict[str, int] = {}
    imported: list[dict[str, Any]] = []

    for item in releases:
        release = item["release"]
        specification = item["specification"]
        agency_key = str(release["agency_key"])
        if agency_key not in agency_ids:
            agency_created = normalize_datetime(release["agency_created_at"], seed_time) or seed_time
            target.execute(
                "INSERT INTO source_agency (agency_key, name, jurisdiction, homepage_uri, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    agency_key,
                    release["agency_name"],
                    release["jurisdiction"] or "Kane County, Illinois",
                    release["homepage_uri"],
                    agency_created,
                ),
            )
            agency_ids[agency_key] = int(
                target.execute("SELECT last_insert_rowid()").fetchone()[0]
            )

        source_uri = str(release["source_uri"] or "").strip()
        if not source_uri:
            raise RuntimeError(f"Donor release {release['release_key']} has no source URI")
        created_at = normalize_datetime(release["harvested_at"], seed_time) or seed_time
        target.execute(
            "INSERT INTO dataset (dataset_key, county_id, source_agency_id, name, "
            "description, data_kind, source_uri, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                specification["dataset_key"],
                county_id,
                agency_ids[agency_key],
                release["dataset_name"],
                release["description"] or "",
                specification["data_kind"],
                source_uri,
                created_at,
            ),
        )
        dataset_id = int(target.execute("SELECT last_insert_rowid()").fetchone()[0])
        donor_run = item["harvest"] or {}
        started_at = normalize_datetime(
            donor_run.get("started_at"),
            normalize_datetime(release["harvested_at"], created_at),
        ) or created_at
        completed_at = normalize_datetime(
            donor_run.get("completed_at"),
            normalize_datetime(release["accepted_at"], created_at),
        ) or created_at
        harvest_key = "seed-" + specification["release_key"]
        source_metadata = canonical_json(
            {
                "donor_release_id": release["release_id"],
                "donor_run_id": donor_run.get("run_id"),
                "donor_tool_version": donor_run.get("tool_version"),
                "id_property": specification["id_property"],
                "seed_contract": donor_info["contract_key"],
            }
        )
        target.execute(
            "INSERT INTO harvest_run (harvest_key, dataset_id, started_at, completed_at, "
            "status, source_metadata_json, object_count, error_message, created_at) "
            "VALUES (?, ?, ?, ?, 'succeeded', ?, ?, NULL, ?)",
            (
                harvest_key,
                dataset_id,
                started_at,
                completed_at,
                source_metadata,
                item["feature_count"],
                created_at,
            ),
        )
        harvest_id = int(target.execute("SELECT last_insert_rowid()").fetchone()[0])
        source_file_target_id: int | None = None
        for donor_file in item["files"]:
            role = file_role(donor_file, item["source_file_id"])
            file_created = normalize_datetime(donor_file["preserved_at"], created_at) or created_at
            target.execute(
                "INSERT INTO source_file (harvest_run_id, file_role, relative_path, "
                "byte_length, sha256, media_type, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    harvest_id,
                    role,
                    donor_file["relative_path"],
                    donor_file["byte_length"],
                    donor_file["sha256"],
                    donor_file["media_type"] or "application/octet-stream",
                    file_created,
                ),
            )
            inserted_file_id = int(target.execute("SELECT last_insert_rowid()").fetchone()[0])
            if role == "source":
                source_file_target_id = inserted_file_id
        if source_file_target_id is None:
            raise RuntimeError(f"No source file imported for {release['release_key']}")

        accepted_at = normalize_datetime(release["accepted_at"], completed_at) or completed_at
        source_published_at = normalize_datetime(release["source_published_at"], None)
        release_metadata = canonical_json(
            {
                "donor_release_id": release["release_id"],
                "donor_source_id_policy": release["source_id_policy"],
                "donor_source_version": release["source_version"],
                "id_property": specification["id_property"],
                "seed_contract": donor_info["contract_key"],
            }
        )
        target.execute(
            "INSERT INTO source_release (release_key, dataset_id, harvest_run_id, "
            "lifecycle_status, source_published_at, content_sha256, feature_count, "
            "metadata_json, accepted_at, superseded_by_release_id, created_at) "
            "VALUES (?, ?, ?, 'accepted', ?, ?, ?, ?, ?, NULL, ?)",
            (
                specification["release_key"],
                dataset_id,
                harvest_id,
                source_published_at,
                specification["content_sha256"],
                item["feature_count"],
                release_metadata,
                accepted_at,
                created_at,
            ),
        )
        target_release_id = int(target.execute("SELECT last_insert_rowid()").fetchone()[0])
        imported.append(
            dict(
                item,
                target_release_id=target_release_id,
                target_source_file_id=source_file_target_id,
                created_at=created_at,
            )
        )

    changed_at = kane_db.utc_now()
    target.execute(
        "UPDATE gpkg_contents SET last_change = ? WHERE table_name IN "
        "('county','source_agency','dataset','harvest_run','source_file','source_release')",
        (changed_at,),
    )
    return imported


def copy_features(
    donor: sqlite3.Connection,
    target: sqlite3.Connection,
    releases: Sequence[Mapping[str, Any]],
) -> None:
    for item in releases:
        kind = item["specification"]["data_kind"]
        donor_release_id = item["release"]["release_id"]
        target_release_id = item["target_release_id"]
        source_file_id = item["target_source_file_id"]
        created_at = item["created_at"]
        if kind == "boundary":
            table = "source_county_boundary"
        elif kind in {"roads", "water"}:
            table = "source_map_feature"
        else:
            table = "source_building"
        rows = donor.execute(
            "SELECT source_feature_id, source_ordinal, geometry, geometry_type, "
            "geometry_sha256, attributes_json, attributes_sha256, content_sha256, "
            f"min_x, min_y, max_x, max_y FROM {table} "
            "WHERE release_id = ? ORDER BY source_ordinal",
            (donor_release_id,),
        )
        target.executemany(
            f"INSERT INTO {table} (source_release_id, source_file_id, "
            "source_feature_id, source_ordinal, geometry, geometry_type, geometry_sha256, "
            "attributes_json, attributes_sha256, content_sha256, min_x, min_y, max_x, "
            "max_y, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                (target_release_id, source_file_id, *row, created_at)
                for row in rows
            ),
        )


def update_extents(connection: sqlite3.Connection) -> None:
    now = kane_db.utc_now()
    for table in ("source_county_boundary", "source_map_feature", "source_building"):
        bounds = connection.execute(
            f"SELECT MIN(min_x), MIN(min_y), MAX(max_x), MAX(max_y) FROM {table}"
        ).fetchone()
        connection.execute(
            "UPDATE gpkg_contents SET last_change = ?, min_x = ?, min_y = ?, "
            "max_x = ?, max_y = ? WHERE table_name = ?",
            (now, *bounds, table),
        )


def validate_target(path: Path) -> list[str]:
    errors: list[str] = []
    core = kane_db.validate_database(path)
    errors.extend(str(value) for value in core.get("errors", []))
    for validator in (
        kane_provenance.validate_database,
        kane_boundary.validate_database,
        kane_map_layers.validate_database,
        kane_buildings.validate_database,
        kane_project_buildings.validate_database,
    ):
        errors.extend(str(value) for value in validator(path))
    return list(dict.fromkeys(errors))


def _application_tables_present(database: Path) -> list[str]:
    connection = sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True)
    try:
        return sorted(APPLICATION_TABLES & table_names(connection))
    finally:
        connection.close()


def audit_report(
    contract: Mapping[str, Any],
    contract_path: Path,
    donor_info: Mapping[str, Any],
    target: Path,
) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{target.resolve()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        releases = [
            dict(row)
            for row in connection.execute(
                "SELECT d.dataset_key, d.data_kind, sr.release_key, sr.content_sha256, "
                "sr.feature_count, sr.lifecycle_status FROM source_release sr "
                "JOIN dataset d ON d.dataset_id = sr.dataset_id ORDER BY d.dataset_key"
            )
        ]
        totals = {
            str(key): int(value)
            for key, value in connection.execute(
                "SELECT d.data_kind, SUM(sr.feature_count) FROM source_release sr "
                "JOIN dataset d ON d.dataset_id = sr.dataset_id "
                "WHERE sr.lifecycle_status = 'accepted' GROUP BY d.data_kind"
            )
        }
        project_count = int(connection.execute("SELECT COUNT(*) FROM project_building").fetchone()[0])
        mapping_count = int(
            connection.execute("SELECT COUNT(*) FROM project_building_source_mapping").fetchone()[0]
        )
        migration_count = int(connection.execute("SELECT COUNT(*) FROM schema_migration").fetchone()[0])
        target_tables = table_names(connection)
    finally:
        connection.close()
    excluded = contract["excluded_donor_tables"]
    return {
        "valid": True,
        "contract": {
            "contract_key": contract["contract_key"],
            "path": str(contract_path.resolve()),
            "sha256": sha256_file(contract_path),
        },
        "donor_database": {
            "path": donor_info["path"],
            "byte_length": donor_info["byte_length"],
            "sha256": donor_info["sha256"],
            "source_commit": donor_info["source_commit"],
        },
        "target_database": {
            "path": str(target.resolve()),
            "byte_length": target.stat().st_size,
            "sha256": sha256_file(target),
            "migration_count": migration_count,
        },
        "accepted_releases": releases,
        "feature_totals": totals,
        "geographic_buildings": {
            "count": project_count,
            "confirmed_initial_mappings": mapping_count,
        },
        "application_tables": {
            "required": False,
            "present": sorted(APPLICATION_TABLES & target_tables),
        },
        "excluded_donor_tables": {
            "present_in_donor": [
                table for table in excluded if table in donor_info["donor_tables"]
            ],
            "absent_from_target": [table for table in excluded if table not in target_tables],
        },
        "validation": {"errors": []},
    }


def write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".candidate", dir=path.parent
    )
    os.close(handle)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def import_seed(
    donor: Path,
    output: Path,
    audit: Path,
    contract_path: Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    donor = donor.resolve()
    output = output.resolve()
    audit = audit.resolve()
    contract_path = contract_path.resolve()
    if output.exists():
        raise RuntimeError(f"Output already exists: {output}")
    if audit.exists():
        raise RuntimeError(f"Audit report already exists: {audit}")

    contract = validate_contract(load_json_object(contract_path, "seed contract"))
    donor_info = inspect_donor(donor, contract)
    donor_info["contract_key"] = contract["contract_key"]
    output.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{output.stem}.seed.", suffix=".gpkg", dir=output.parent
    )
    os.close(handle)
    candidate = Path(temporary_name)
    candidate.unlink()
    donor_before = donor_info["sha256"]

    try:
        kane_db.init_database(candidate)
        donor_connection = sqlite3.connect(f"file:{donor}?mode=ro", uri=True)
        donor_connection.row_factory = sqlite3.Row
        target_connection = sqlite3.connect(candidate)
        target_connection.row_factory = sqlite3.Row
        try:
            target_connection.execute("PRAGMA foreign_keys = ON")
            target_connection.execute("BEGIN IMMEDIATE")
            imported = insert_administration(target_connection, donor_info)
            copy_features(donor_connection, target_connection, imported)
            update_extents(target_connection)
            target_connection.commit()
        except Exception:
            target_connection.rollback()
            raise
        finally:
            target_connection.close()
            donor_connection.close()

        building_release = next(
            item["release_key"]
            for item in contract["expected_releases"]
            if item["data_kind"] == "buildings"
        )
        kane_project_buildings.seed_project_buildings(candidate, building_release)
        errors = validate_target(candidate)
        if errors:
            raise RuntimeError(
                "Candidate seed database failed validation:\n- " + "\n- ".join(errors)
            )
        application_tables = _application_tables_present(candidate)
        if application_tables:
            raise RuntimeError(
                "Seed database unexpectedly contains application tables: "
                + ", ".join(application_tables)
            )
        if sha256_file(donor) != donor_before:
            raise RuntimeError("Donor database changed during seed import")

        os.replace(candidate, output)
        report = audit_report(contract, contract_path, donor_info, output)
        try:
            write_json_atomic(audit, report)
        except Exception:
            remove_sqlite_files(output)
            raise
        return report
    finally:
        remove_sqlite_files(candidate)


def validate_seed(database: Path) -> dict[str, Any]:
    database = database.resolve()
    errors = validate_target(database)
    application_tables = _application_tables_present(database) if database.is_file() else []
    if application_tables:
        errors.append(
            "Seed database unexpectedly contains application tables: "
            + ", ".join(application_tables)
        )
    return {
        "valid": not errors,
        "path": str(database),
        "errors": errors,
        "application_tables_present": application_tables,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    import_parser = subparsers.add_parser(
        "import", help="build a clean Kane Fabric database from an approved seed donor"
    )
    import_parser.add_argument("donor", type=Path)
    import_parser.add_argument("output", type=Path)
    import_parser.add_argument("audit", type=Path)
    import_parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    validate = subparsers.add_parser("validate", help="validate an imported Fabric seed database")
    validate.add_argument("database", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "import":
            result = import_seed(args.donor, args.output, args.audit, args.contract)
        else:
            result = validate_seed(args.database)
    except (OSError, RuntimeError, sqlite3.Error, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("valid") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
