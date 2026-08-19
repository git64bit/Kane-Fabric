#!/usr/bin/env python3
"""Prepare, atomically promote, verify, and roll back Kane Fabric source refreshes."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Mapping, Sequence

from kane_fabric_compat import FABRIC_DB, load_donor, load_sibling

PROVENANCE = load_sibling("kane_fabric_provenance")
BOUNDARY = load_sibling("kane_fabric_boundary")
MAP_LAYERS = load_sibling("kane_fabric_map_layers")
BUILDINGS = load_sibling("kane_fabric_buildings")
PROJECT = load_sibling("kane_fabric_project_buildings")
RECONCILE = load_sibling("kane_fabric_building_reconcile")
COMPARE = load_sibling("kane_fabric_candidate_compare")
ROAD_CANDIDATE = load_sibling("kane_fabric_road_candidate")
WATER_CANDIDATE = load_sibling("kane_fabric_water_candidate")
BOUNDARY_CANDIDATE = load_sibling("kane_fabric_boundary_candidate")
DONOR = load_donor("kane_promotion")

DONOR.kane_db = FABRIC_DB
DONOR.kane_provenance = PROVENANCE
DONOR.kane_boundary = BOUNDARY
DONOR.kane_map_layers = MAP_LAYERS
DONOR.kane_buildings = BUILDINGS
DONOR.kane_project = PROJECT
DONOR.kane_reconcile = RECONCILE
DONOR.kane_compare = COMPARE
DONOR.kane_road_candidate = ROAD_CANDIDATE
DONOR.kane_water_candidate = WATER_CANDIDATE
DONOR.kane_boundary_candidate = BOUNDARY_CANDIDATE

DONOR.DATABASE_FILENAME = "kane-fabric-promoted.gpkg"
DONOR.REQUIRED_FILES = {DONOR.DATABASE_FILENAME, DONOR.MANIFEST_FILENAME}


def _empty_application_snapshot() -> dict[str, Any]:
    empty_sha = DONOR.sha256_value([])
    return {
        "current_count": 0,
        "event_count": 0,
        "current_sha256": empty_sha,
        "history_sha256": empty_sha,
    }


def _database_snapshot(database: Path) -> dict[str, Any]:
    """Snapshot Fabric-authoritative state without requiring application tables."""
    connection = sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        accepted = {
            str(row["dataset_key"]): {
                "release_key": str(row["release_key"]),
                "content_sha256": str(row["content_sha256"]),
                "feature_count": int(row["feature_count"]),
            }
            for row in connection.execute(
                "SELECT d.dataset_key, sr.release_key, sr.content_sha256, sr.feature_count "
                "FROM dataset d JOIN source_release sr ON sr.dataset_id = d.dataset_id "
                "WHERE sr.lifecycle_status = 'accepted' AND d.dataset_key IN "
                "('buildings','county-boundary','roads','water-creeks','water-fox-river') "
                "ORDER BY d.dataset_key"
            )
        }
        if set(accepted) != set(DONOR.DATASET_ORDER):
            raise RuntimeError(
                f"Accepted source-release set is incomplete: {sorted(accepted)}"
            )
        project = {
            "count": int(
                connection.execute("SELECT COUNT(*) FROM project_building").fetchone()[0]
            ),
            "active_count": int(
                connection.execute(
                    "SELECT COUNT(*) FROM project_building WHERE lifecycle_status = 'active'"
                ).fetchone()[0]
            ),
            "mapping_count": int(
                connection.execute(
                    "SELECT COUNT(*) FROM project_building_source_mapping"
                ).fetchone()[0]
            ),
        }
        return {
            "accepted_releases": accepted,
            # Retain the manifest field during behavior-preserving extraction, but
            # application classification state is explicitly absent from Fabric.
            "classifications": _empty_application_snapshot(),
            "project": project,
        }
    finally:
        connection.close()


def _validate_full_database(database: Path) -> None:
    validators = (
        PROVENANCE.validate_database,
        BOUNDARY.validate_database,
        MAP_LAYERS.validate_database,
        BUILDINGS.validate_database,
        PROJECT.validate_database,
    )
    for validator in validators:
        errors = list(validator(database))
        if errors:
            raise RuntimeError(
                f"Database failed {validator.__module__} validation:\n- "
                + "\n- ".join(errors)
            )
    DONOR._validate_promotion_history(database)


_ORIGINAL_PLAN_BODY = DONOR._plan_body


def _plan_body(*args, **kwargs) -> dict[str, Any]:
    result = dict(_ORIGINAL_PLAN_BODY(*args, **kwargs))
    result["promotion_key"] = (
        f"kane-fabric-promotion-{result['promotion_plan_sha256'][:12]}"
    )
    return result


def validate_promotion(directory: Path) -> dict[str, Any]:
    directory = directory.resolve()
    DONOR._validate_artifact_layout(directory)
    manifest_path = directory / DONOR.MANIFEST_FILENAME
    manifest_raw = manifest_path.read_bytes()
    manifest = DONOR._mapping(DONOR.load_json(manifest_path), "Promotion manifest")
    if manifest_raw != DONOR.canonical_bytes(manifest) + b"\n":
        raise RuntimeError("Promotion manifest is not canonical JSON")
    required = {
        "promotion_schema",
        "previous_database_sha256",
        "previous_state",
        "reconciliation_key",
        "reconciliation_sha256",
        "release_transitions",
        "candidate_evidence",
        "authorization_kind",
        "promotion_key",
        "promotion_plan_sha256",
        "prepared_candidate_sha256",
        "promotion_event_created_at",
        "promoted_state",
        "final_candidate_database",
    }
    if set(manifest) != required:
        raise RuntimeError("Promotion manifest has an unexpected key set")
    if manifest["promotion_schema"] != DONOR.PROMOTION_SCHEMA:
        raise RuntimeError(f"promotion_schema must be {DONOR.PROMOTION_SCHEMA}")
    plan = {
        key: manifest[key]
        for key in (
            "promotion_schema",
            "previous_database_sha256",
            "previous_state",
            "reconciliation_key",
            "reconciliation_sha256",
            "release_transitions",
            "candidate_evidence",
            "authorization_kind",
        )
    }
    if manifest["promotion_plan_sha256"] != DONOR.sha256_value(plan):
        raise RuntimeError("Promotion plan SHA-256 is invalid")
    if manifest["promotion_key"] != (
        f"kane-fabric-promotion-{manifest['promotion_plan_sha256'][:12]}"
    ):
        raise RuntimeError("Promotion key is invalid")
    if set(manifest["release_transitions"]) != set(DONOR.DATASET_ORDER):
        raise RuntimeError("Promotion release transition set is incomplete")
    if manifest["authorization_kind"] != "explicit-command":
        raise RuntimeError("Promotion authorization kind is invalid")
    if not FABRIC_DB.valid_datetime(manifest["promotion_event_created_at"]):
        raise RuntimeError("Promotion event timestamp is invalid")
    database_info = DONOR._mapping(
        manifest["final_candidate_database"], "final_candidate_database"
    )
    if set(database_info) != {"filename", "byte_length", "sha256"}:
        raise RuntimeError("final_candidate_database has an unexpected key set")
    if database_info["filename"] != DONOR.DATABASE_FILENAME:
        raise RuntimeError("Promotion database filename is invalid")
    database = directory / DONOR.DATABASE_FILENAME
    if database.stat().st_size != database_info["byte_length"]:
        raise RuntimeError("Promotion database byte length is invalid")
    if DONOR.sha256_file(database) != database_info["sha256"]:
        raise RuntimeError("Promotion database SHA-256 is invalid")
    DONOR._verify_promoted_state(database, manifest)
    if _database_snapshot(database) != manifest["promoted_state"]:
        raise RuntimeError(
            "Promotion manifest promoted_state does not match candidate database"
        )
    return {
        "valid": True,
        "promotion_key": manifest["promotion_key"],
        "promotion_plan_sha256": manifest["promotion_plan_sha256"],
        "previous_database_sha256": manifest["previous_database_sha256"],
        "prepared_candidate_sha256": manifest["prepared_candidate_sha256"],
        "promoted_database_sha256": database_info["sha256"],
        "manifest_sha256": DONOR.sha256_bytes(manifest_raw),
        "release_transitions": manifest["release_transitions"],
        "reconciliation_key": manifest["reconciliation_key"],
    }


DONOR._database_snapshot = _database_snapshot
DONOR._validate_full_database = _validate_full_database
DONOR._plan_body = _plan_body
DONOR.validate_promotion = validate_promotion

PROMOTION_SCHEMA = DONOR.PROMOTION_SCHEMA
ARTIFACT_DIRNAME = DONOR.ARTIFACT_DIRNAME
DATABASE_FILENAME = DONOR.DATABASE_FILENAME
MANIFEST_FILENAME = DONOR.MANIFEST_FILENAME
REQUIRED_FILES = DONOR.REQUIRED_FILES
DATASET_ORDER = DONOR.DATASET_ORDER

canonical_bytes = DONOR.canonical_bytes
sha256_bytes = DONOR.sha256_bytes
sha256_value = DONOR.sha256_value
sha256_file = DONOR.sha256_file
prepare_promotion = DONOR.prepare_promotion
promotion_info = DONOR.promotion_info
promote_database = DONOR.promote_database
rollback_database = DONOR.rollback_database
database_promotion_info = DONOR.database_promotion_info
build_parser = DONOR.build_parser


def main(argv: Sequence[str] | None = None) -> int:
    return int(DONOR.main(argv))


if __name__ == "__main__":
    raise SystemExit(main())
