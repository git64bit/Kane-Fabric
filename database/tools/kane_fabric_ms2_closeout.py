#!/usr/bin/env python3
"""Replay Milestone 1 Kane County evidence through the native Kane Fabric core."""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import kane_fabric_boundary_candidate as boundary_candidate
import kane_fabric_building_candidate as building_candidate
import kane_fabric_building_reconcile as reconcile
import kane_fabric_candidate_compare as compare
import kane_fabric_promotion as promotion
import kane_fabric_road_candidate as road_candidate
import kane_fabric_seed_import as seed_import
import kane_fabric_source_profiles as source_profiles
import kane_fabric_water_candidate as water_candidate

EXPECTED_SEED_SHA256 = "7fe2198b00b2d0dee9470eda3864b43b6f7b3b0ff3b236ce7c579ddc077f389a"
EXPECTED_ORACLE_SHA256 = "164200d4d7262874dcc03239c8258446a4d7bb81ce84daf46dc4937d6c97fe86"
EXPECTED_REGISTRY_SHA256 = "e95c9d0486f65035146cb0a2a9580e4148c853a78c4f9e44e2420f59ef654e12"
EXPECTED_COMPARISONS = {
    "buildings": "23916019e762740a4ebe773cdfab916ace4c4d505521407fd6c513b382108d28",
    "boundary": "6ffa83d940347e7ffeeb10e3c631625af75de7f12ef95729ab1ebb75b5879f95",
    "roads": "7b3bf1ddaef1a40948d57edf0c465199316216510e0a1a78cb2dc0a552f59d3b",
    "water": "a1b0ac3f1504e4e6de199e694f794c83643f02139ed37f9a38c0d65d638f88f3",
}
CANDIDATE_RELATIVE_PATHS = {
    "buildings": Path("staging/buildings/kane-buildings-candidate-20250730-608ac1b48564"),
    "roads": Path("staging/roads/kane-roads-candidate-20250730-c83a588170f3"),
    "water": Path("staging/water/kane-water-context-candidate-20250717-25d02c084002"),
    "boundary": Path("staging/boundary/kane-county-boundary-candidate-20230509-ecc3b0990d4c"),
}
EXPECTED_UNCHANGED = {
    "buildings": 208324,
    "county-boundary": 1,
    "roads": 27675,
    "water-creeks": 555,
    "water-fox-river": 1,
}
FORBIDDEN_RUNTIME_TOKENS = (
    "kane_fabric_compat",
    "load_donor(",
    "KANE_FABRIC_DONOR_TOOLS",
    "reconstruction-code/kane-condo",
)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _application_tables(database: Path) -> list[str]:
    connection = sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True)
    try:
        names = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    finally:
        connection.close()
    return sorted(
        names & {"building_classification_current", "building_classification_event"}
    )


def _assert_comparison(name: str, result: Mapping[str, Any]) -> None:
    expected_hash = EXPECTED_COMPARISONS[name]
    _assert(
        result.get("comparison_sha256") == expected_hash,
        f"{name} comparison hash mismatch: {result.get('comparison_sha256')}",
    )
    datasets = result.get("datasets")
    _assert(isinstance(datasets, list) and datasets, f"{name} comparison has no datasets")
    for dataset in datasets:
        key = str(dataset["dataset_key"])
        changes = dataset["feature_changes"]
        _assert(
            int(changes["unchanged"]["count"]) == EXPECTED_UNCHANGED[key],
            f"{key} unchanged count mismatch",
        )
        for category in (
            "added",
            "removed",
            "geometry_changed",
            "attributes_changed",
            "both_changed",
        ):
            _assert(
                int(changes[category]["count"]) == 0,
                f"{key} unexpectedly has {category} changes",
            )
        if key == "roads":
            _assert(
                int(dataset["candidate_exclusions"]["count"]) == 1,
                "roads must preserve exactly one declared candidate exclusion",
            )


def _runtime_dependency_scan() -> dict[str, list[str]]:
    tools = Path(__file__).resolve().parent
    hits: dict[str, list[str]] = {}
    for path in sorted(tools.glob("kane_fabric_*.py")):
        if path.name == Path(__file__).name:
            continue
        text = path.read_text(encoding="utf-8")
        matched = [token for token in FORBIDDEN_RUNTIME_TOKENS if token in text]
        if matched:
            hits[path.name] = matched
    return hits


def closeout(
    seed: Path,
    evidence_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    seed = seed.resolve()
    evidence_root = evidence_root.resolve()
    output_root = output_root.resolve()
    if output_root.exists():
        raise RuntimeError(f"Closeout output already exists: {output_root}")
    output_root.mkdir(parents=True)

    oracle = evidence_root / "database" / "kane-condo.gpkg"
    candidate_dirs = {
        key: evidence_root / relative
        for key, relative in CANDIDATE_RELATIVE_PATHS.items()
    }
    for label, path in {"seed": seed, "historical oracle": oracle, **candidate_dirs}.items():
        if not path.exists():
            raise RuntimeError(f"Missing {label}: {path}")

    seed_before = seed_import.sha256_file(seed)
    oracle_before = seed_import.sha256_file(oracle)
    _assert(seed_before == EXPECTED_SEED_SHA256, "Immutable seed SHA-256 mismatch")
    _assert(oracle_before == EXPECTED_ORACLE_SHA256, "Historical promoted oracle SHA-256 mismatch")

    registry = source_profiles.inspect_registry(source_profiles.PROFILE_DIR)
    _assert(registry.get("valid") is True, f"Fabric source profile registry is invalid: {registry}")
    _assert(
        registry.get("registry_sha256") == EXPECTED_REGISTRY_SHA256,
        "Fabric source profile registry hash does not match MS-1 evidence",
    )

    runtime_hits = _runtime_dependency_scan()
    _assert(not runtime_hits, f"Frozen donor runtime references remain: {runtime_hits}")

    database_dir = output_root / "database"
    database_dir.mkdir()
    database = database_dir / "kane-county-fabric.gpkg"
    seed_audit = output_root / "seed-import.json"
    seed_report = seed_import.import_seed(seed, database, seed_audit)
    _assert(seed_report.get("valid") is True, "Fabric seed bootstrap failed")
    _assert(not _application_tables(database), "Fabric seed unexpectedly contains application tables")

    registrations = {
        "buildings": building_candidate.register_candidate(database, candidate_dirs["buildings"]),
        "roads": road_candidate.register_candidate(database, candidate_dirs["roads"]),
        "water": water_candidate.register_candidate(database, candidate_dirs["water"]),
        "boundary": boundary_candidate.register_candidate(database, candidate_dirs["boundary"]),
    }
    for name, result in registrations.items():
        _assert(result.get("valid") is True and result.get("registered") is True, f"{name} registration failed")

    comparison_results = {
        "buildings": compare.compare_candidate(database, candidate_dirs["buildings"]),
        "boundary": compare.compare_candidate(database, candidate_dirs["boundary"]),
        "roads": compare.compare_candidate(database, candidate_dirs["roads"]),
        "water": compare.compare_candidate(database, candidate_dirs["water"]),
    }
    comparison_dir = output_root / "comparisons"
    for name, result in comparison_results.items():
        _assert_comparison(name, result)
        _write_json(comparison_dir / f"{name}.json", result)

    reconciliation_result = reconcile.prepare_reconciliation(
        database, candidate_dirs["buildings"], output_root
    )
    reconciliation_dir = Path(reconciliation_result["reconciliation_directory"])
    reconciliation_info = reconcile.reconciliation_info(reconciliation_dir)
    _assert(reconciliation_info["valid"] is True, "Fabric reconciliation is invalid")
    _assert(reconciliation_info["ready_for_promotion"] is True, "Fabric reconciliation is not promotion-ready")
    _assert(int(reconciliation_info["ambiguity_count"]) == 0, "Fabric reconciliation has ambiguities")
    _assert(int(reconciliation_info["mapped_source_count"]) == 208324, "Fabric reconciliation mapped count mismatch")
    _assert(int(reconciliation_info["unmapped_source_count"]) == 0, "Fabric reconciliation has unmapped sources")
    automatic = reconciliation_info["automatic_summary"]
    expected_summary = {
        "continuation_mapping_count": 208324,
        "geometry_redraw_mapping_count": 0,
        "replacement_mapping_count": 0,
        "addition_count": 0,
        "disappearance_count": 0,
    }
    for key, expected in expected_summary.items():
        _assert(int(automatic[key]) == expected, f"Fabric reconciliation {key} mismatch")
    _assert(
        int(reconciliation_info["project_state"]["new_project_building_count"]) == 0,
        "Fabric reconciliation created unexpected geographic building identities",
    )
    _assert(
        reconciliation_info["classification_preservation"]["before"]
        == reconciliation_info["classification_preservation"]["after"],
        "Fabric reconciliation application-state placeholder changed",
    )

    promotion_result = promotion.prepare_promotion(
        database,
        reconciliation_dir,
        candidate_dirs["roads"],
        candidate_dirs["water"],
        candidate_dirs["boundary"],
        output_root,
    )
    promotion_dir = Path(promotion_result["promotion_directory"])
    promotion_validation = promotion.validate_promotion(promotion_dir)
    _assert(promotion_validation["valid"] is True, "Fabric promotion artifact is invalid")

    live = database_dir / "kane-county-live.gpkg"
    shutil.copyfile(database, live)
    rollback_root = output_root / "rollback"
    promoted = promotion.promote_database(live, promotion_dir, rollback_root)
    _assert(promoted["valid"] is True and promoted["promoted"] is True, "Fabric promotion failed")
    transitions = promotion_validation["release_transitions"]
    expected_promoted = {
        key: str(transitions[key]["candidate_release_key"])
        for key in promotion.DATASET_ORDER
    }
    promoted_info = promotion.database_promotion_info(live)
    _assert(
        promoted_info["accepted_release_keys"] == expected_promoted,
        "Promoted Fabric accepted release set is wrong",
    )

    rolled_back = promotion.rollback_database(
        live,
        promotion_dir,
        rollback_root,
        "MS-2 historical closeout rollback proof",
    )
    _assert(rolled_back["valid"] is True and rolled_back["rolled_back"] is True, "Fabric rollback failed")
    expected_previous = {
        key: str(transitions[key]["previous_release_key"])
        for key in promotion.DATASET_ORDER
    }
    rollback_info = promotion.database_promotion_info(live)
    _assert(
        rollback_info["accepted_release_keys"] == expected_previous,
        "Rollback did not restore the prior accepted release set",
    )
    _assert(not _application_tables(live), "Rolled-back Fabric database contains application tables")

    seed_after = seed_import.sha256_file(seed)
    oracle_after = seed_import.sha256_file(oracle)
    _assert(seed_after == seed_before, "Immutable seed changed during closeout")
    _assert(oracle_after == oracle_before, "Historical promoted oracle changed during closeout")

    report_body = {
        "closeout_schema": 1,
        "valid": True,
        "seed": {
            "path": str(seed),
            "sha256_before": seed_before,
            "sha256_after": seed_after,
            "unchanged": True,
        },
        "historical_promoted_oracle": {
            "path": str(oracle),
            "sha256_before": oracle_before,
            "sha256_after": oracle_after,
            "unchanged": True,
        },
        "source_profile_registry_sha256": registry["registry_sha256"],
        "runtime_dependency_scan": {"forbidden_hits": runtime_hits},
        "fabric_seed": {
            "path": str(database),
            "sha256": seed_import.sha256_file(database),
            "feature_totals": seed_report["feature_totals"],
            "geographic_buildings": seed_report["geographic_buildings"],
            "application_tables": seed_report["application_tables"],
        },
        "comparison_sha256": {
            key: value["comparison_sha256"] for key, value in comparison_results.items()
        },
        "reconciliation": {
            "reconciliation_key": reconciliation_info["reconciliation_key"],
            "reconciliation_sha256": reconciliation_info["reconciliation_sha256"],
            "candidate_database_sha256": reconciliation_info["candidate_database_sha256"],
            "mapped_source_count": reconciliation_info["mapped_source_count"],
            "unmapped_source_count": reconciliation_info["unmapped_source_count"],
            "ambiguity_count": reconciliation_info["ambiguity_count"],
            "ready_for_promotion": reconciliation_info["ready_for_promotion"],
            "automatic_summary": automatic,
        },
        "promotion": {
            "promotion_key": promotion_validation["promotion_key"],
            "promotion_plan_sha256": promotion_validation["promotion_plan_sha256"],
            "promoted_database_sha256": promotion_validation["promoted_database_sha256"],
            "promoted_release_keys": expected_promoted,
            "rollback_restored_release_keys": expected_previous,
            "manual_rollback_proved": True,
        },
    }
    report_body["closeout_sha256"] = promotion.sha256_value(report_body)
    report_path = output_root / "ms2-closeout.json"
    _write_json(report_path, report_body)
    return {**report_body, "report_path": str(report_path)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("seed", type=Path)
    parser.add_argument("historical_evidence_root", type=Path)
    parser.add_argument("output_root", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = closeout(args.seed, args.historical_evidence_root, args.output_root)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
