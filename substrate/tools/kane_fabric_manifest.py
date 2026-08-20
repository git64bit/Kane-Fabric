#!/usr/bin/env python3
"""Build and validate Kane Fabric v1 substrate manifests."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Mapping, Sequence

REQUIRED_DATASETS = (
    "county-boundary",
    "roads",
    "water-creeks",
    "water-fox-river",
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load support module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


TOOLS_DIR = Path(__file__).resolve().parent
ROOT = TOOLS_DIR.parents[1]
CONTRACT = _load_module(
    "_kane_fabric_manifest_contract",
    TOOLS_DIR / "kane_fabric_substrate.py",
)
ROADS_ENTRY = _load_module(
    "_kane_fabric_manifest_roads_entry",
    TOOLS_DIR / "kane_fabric_roads_entry.py",
)
ROADS = ROADS_ENTRY.ROADS
WATER = _load_module(
    "_kane_fabric_manifest_water",
    TOOLS_DIR / "kane_fabric_water.py",
)
FABRIC_READ = _load_module(
    "_kane_fabric_manifest_read",
    ROOT / "database" / "tools" / "kane_fabric_read.py",
)


def _sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_keys(value: object, keys: set[str], label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{label} must be a JSON object")
    actual = set(value)
    if actual != keys:
        raise RuntimeError(
            f"{label} keys mismatch: missing={sorted(keys - actual)!r} "
            f"extra={sorted(actual - keys)!r}"
        )
    return value


def _component_descriptor(role: str, path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return CONTRACT.validate_component_descriptor(
        {
            "role": role,
            "path": CONTRACT.COMPONENT_PATHS[role],
            "format": CONTRACT.COMPONENT_FORMATS[role],
            "version": CONTRACT.VERSION,
            "byte_length": len(data),
            "sha256": CONTRACT.sha256_bytes(data),
        }
    )


def _require_component_path(directory: Path, role: str) -> Path:
    path = directory / CONTRACT.COMPONENT_PATHS[role]
    if not path.is_file():
        raise RuntimeError(f"Required substrate component is missing: {role}: {path}")
    return path


def _inspect_overview(path: Path):
    data = path.read_bytes()
    try:
        document = json.loads(data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"County overview is invalid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise RuntimeError("County overview must be a JSON object")
    if CONTRACT.canonical_json_bytes(document) != data:
        raise RuntimeError("County overview is not canonical JSON")
    if document.get("format") != CONTRACT.OVERVIEW_FORMAT:
        raise RuntimeError("County overview format is unsupported")
    if document.get("version") != CONTRACT.VERSION:
        raise RuntimeError("County overview version is unsupported")
    if document.get("srs_id") != CONTRACT.SRS_ID:
        raise RuntimeError("County overview SRS is unsupported")
    jurisdiction = CONTRACT.validate_jurisdiction(document.get("jurisdiction", {}))
    source = document.get("source")
    if not isinstance(source, Mapping):
        raise RuntimeError("County overview source descriptor is missing")
    release = CONTRACT.validate_release_descriptor(
        {
            "dataset_key": source.get("dataset_key"),
            "release_key": source.get("release_key"),
            "content_sha256": source.get("content_sha256"),
            "feature_count": source.get("feature_count"),
        }
    )
    if release["dataset_key"] != "county-boundary":
        raise RuntimeError("County overview source dataset is not county-boundary")
    return _component_descriptor("county_overview", path), jurisdiction, [release]


def _inspect_roads(path: Path):
    info = ROADS.validate_component(path)
    descriptor = _component_descriptor("roads", path)
    if descriptor["sha256"] != info["sha256"] or descriptor["byte_length"] != info["byte_length"]:
        raise RuntimeError("Road component descriptor disagrees with validated bytes")
    jurisdiction = CONTRACT.validate_jurisdiction(info["jurisdiction"])
    source = CONTRACT.validate_release_descriptor(info["source"])
    if source["dataset_key"] != "roads":
        raise RuntimeError("Road component source dataset is not roads")
    return descriptor, jurisdiction, [source]


def _inspect_water(path: Path):
    info = WATER.validate_component(path)
    descriptor = _component_descriptor("water", path)
    if descriptor["sha256"] != info["sha256"] or descriptor["byte_length"] != info["byte_length"]:
        raise RuntimeError("Water component descriptor disagrees with validated bytes")
    jurisdiction = CONTRACT.validate_jurisdiction(info["jurisdiction"])
    sources = [CONTRACT.validate_release_descriptor(item) for item in info["sources"]]
    if sorted(item["dataset_key"] for item in sources) != ["water-creeks", "water-fox-river"]:
        raise RuntimeError("Water component must bind exactly the accepted creek and Fox River datasets")
    sources.sort(key=lambda item: str(item["dataset_key"]))
    return descriptor, jurisdiction, sources


def inspect_components(directory: Path):
    directory = directory.resolve()
    overview = _inspect_overview(_require_component_path(directory, "county_overview"))
    roads = _inspect_roads(_require_component_path(directory, "roads"))
    water = _inspect_water(_require_component_path(directory, "water"))

    inspections = (overview, roads, water)
    components = [item[0] for item in inspections]
    jurisdictions = [item[1] for item in inspections]
    if any(value != jurisdictions[0] for value in jurisdictions[1:]):
        raise RuntimeError("Substrate components do not belong to the same jurisdiction")

    releases = [release for item in inspections for release in item[2]]
    if len({item["dataset_key"] for item in releases}) != len(releases):
        raise RuntimeError("Substrate components contain duplicate accepted-release datasets")
    releases.sort(key=lambda item: str(item["dataset_key"]))
    if tuple(item["dataset_key"] for item in releases) != REQUIRED_DATASETS:
        raise RuntimeError(
            f"Substrate component releases must be exactly {REQUIRED_DATASETS!r}"
        )
    return jurisdictions[0], releases, components


def authoritative_state(database: Path):
    database = database.resolve()
    summary = FABRIC_READ.authority_summary(database)
    jurisdictions = summary.get("jurisdictions")
    if not isinstance(jurisdictions, list) or len(jurisdictions) != 1:
        count = len(jurisdictions) if isinstance(jurisdictions, list) else 0
        raise RuntimeError(f"Authoritative database jurisdiction count is {count}; expected 1")
    jurisdiction = CONTRACT.validate_jurisdiction(jurisdictions[0])

    by_dataset = {
        str(item["dataset_key"]): item
        for item in summary["accepted_releases"]
        if str(item["dataset_key"]) in REQUIRED_DATASETS
    }
    if tuple(sorted(by_dataset)) != REQUIRED_DATASETS:
        raise RuntimeError(
            f"Authoritative substrate releases must be exactly {REQUIRED_DATASETS!r}"
        )
    releases = [
        CONTRACT.validate_release_descriptor(
            {
                "dataset_key": by_dataset[key]["dataset_key"],
                "release_key": by_dataset[key]["release_key"],
                "content_sha256": by_dataset[key]["content_sha256"],
                "feature_count": by_dataset[key]["feature_count"],
            }
        )
        for key in REQUIRED_DATASETS
    ]
    audit = {
        "byte_length": database.stat().st_size,
        "sha256": _sha256_file(database),
    }
    return jurisdiction, releases, audit


def build_document(database: Path, directory: Path) -> dict[str, object]:
    jurisdiction, accepted_releases, database_audit = authoritative_state(database)
    component_jurisdiction, component_releases, components = inspect_components(directory)
    if component_jurisdiction != jurisdiction:
        raise RuntimeError("Substrate component jurisdiction disagrees with authoritative database")
    if component_releases != accepted_releases:
        raise RuntimeError("Substrate component release lineage disagrees with authoritative database")

    content_sha256 = CONTRACT.compute_substrate_content_sha256(
        jurisdiction,
        accepted_releases,
        components,
    )
    return {
        "accepted_releases": accepted_releases,
        "authoritative_database": database_audit,
        "components": components,
        "format": CONTRACT.MANIFEST_FORMAT,
        "jurisdiction": jurisdiction,
        "srs_id": CONTRACT.SRS_ID,
        "substrate_content_sha256": content_sha256,
        "version": CONTRACT.VERSION,
    }


def build_manifest(database: Path, directory: Path) -> dict[str, object]:
    database = database.resolve()
    directory = directory.resolve()
    if not database.is_file():
        raise RuntimeError(f"Authoritative database does not exist: {database}")
    directory.mkdir(parents=True, exist_ok=True)
    output = directory / CONTRACT.COMPONENT_PATHS.get("manifest", "substrate-manifest.json")
    if output == database:
        raise RuntimeError("Manifest output must not replace the authoritative database")

    document = build_document(database, directory)
    payload = CONTRACT.canonical_json_bytes(document)
    temporary = output.with_name(f".{output.name}.tmp")
    try:
        temporary.write_bytes(payload)
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    validate_manifest(output, database=database)
    return {
        "byte_length": len(payload),
        "output_file": str(output),
        "sha256": CONTRACT.sha256_bytes(payload),
        "substrate_content_sha256": document["substrate_content_sha256"],
    }


def _validate_database_audit(value: object) -> dict[str, object]:
    audit = _require_keys(value, {"byte_length", "sha256"}, "authoritative_database")
    byte_length = audit["byte_length"]
    if isinstance(byte_length, bool) or not isinstance(byte_length, int) or byte_length <= 0:
        raise RuntimeError("authoritative_database byte_length must be a positive integer")
    sha = str(audit["sha256"])
    if len(sha) != 64 or any(ch not in "0123456789abcdef" for ch in sha):
        raise RuntimeError("authoritative_database sha256 is invalid")
    return {"byte_length": byte_length, "sha256": sha}


def validate_manifest(path: Path, *, database: Path | None = None) -> dict[str, object]:
    path = path.resolve()
    if path.name != "substrate-manifest.json":
        raise RuntimeError("Substrate manifest filename must be substrate-manifest.json")
    data = path.read_bytes()
    try:
        document = json.loads(data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Substrate manifest is invalid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise RuntimeError("Substrate manifest must be a JSON object")
    if CONTRACT.canonical_json_bytes(document) != data:
        raise RuntimeError("Substrate manifest is not canonical JSON")
    _require_keys(
        document,
        {
            "accepted_releases",
            "authoritative_database",
            "components",
            "format",
            "jurisdiction",
            "srs_id",
            "substrate_content_sha256",
            "version",
        },
        "substrate manifest",
    )
    if document["format"] != CONTRACT.MANIFEST_FORMAT or document["version"] != CONTRACT.VERSION:
        raise RuntimeError("Substrate manifest format/version is unsupported")
    if document["srs_id"] != CONTRACT.SRS_ID:
        raise RuntimeError("Substrate manifest SRS is unsupported")

    jurisdiction = CONTRACT.validate_jurisdiction(document["jurisdiction"])
    raw_releases = document["accepted_releases"]
    if not isinstance(raw_releases, list):
        raise RuntimeError("Substrate manifest accepted_releases must be an array")
    releases = [CONTRACT.validate_release_descriptor(item) for item in raw_releases]
    if tuple(item["dataset_key"] for item in releases) != REQUIRED_DATASETS:
        raise RuntimeError(
            f"Substrate manifest releases must be exactly {REQUIRED_DATASETS!r}"
        )

    raw_components = document["components"]
    if not isinstance(raw_components, list):
        raise RuntimeError("Substrate manifest components must be an array")
    components = [CONTRACT.validate_component_descriptor(item) for item in raw_components]
    if tuple(item["role"] for item in components) != CONTRACT.COMPONENT_ROLES:
        raise RuntimeError(
            f"Substrate manifest component roles must be exactly {CONTRACT.COMPONENT_ROLES!r}"
        )

    database_audit = _validate_database_audit(document["authoritative_database"])
    expected_content = CONTRACT.compute_substrate_content_sha256(
        jurisdiction,
        releases,
        components,
    )
    if document["substrate_content_sha256"] != expected_content:
        raise RuntimeError("Substrate manifest content identity is invalid")

    component_jurisdiction, component_releases, actual_components = inspect_components(path.parent)
    if component_jurisdiction != jurisdiction:
        raise RuntimeError("Substrate manifest jurisdiction disagrees with component jurisdiction")
    if component_releases != releases:
        raise RuntimeError("Substrate manifest release lineage disagrees with component lineage")
    if actual_components != components:
        raise RuntimeError("Substrate manifest component descriptors disagree with component bytes")

    if database is not None:
        db_jurisdiction, db_releases, actual_audit = authoritative_state(database)
        if db_jurisdiction != jurisdiction:
            raise RuntimeError("Substrate manifest jurisdiction disagrees with authoritative database")
        if db_releases != releases:
            raise RuntimeError("Substrate manifest releases disagree with authoritative database")
        if actual_audit != database_audit:
            raise RuntimeError("Substrate manifest database audit identity is stale")

    return {
        "accepted_release_count": len(releases),
        "authoritative_database": database_audit,
        "byte_length": len(data),
        "components": components,
        "jurisdiction": jurisdiction,
        "path": str(path),
        "sha256": CONTRACT.sha256_bytes(data),
        "substrate_content_sha256": expected_content,
        "valid": True,
    }


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("database", type=Path)
    build.add_argument("directory", type=Path)
    validate = commands.add_parser("validate")
    validate.add_argument("manifest", type=Path)
    validate.add_argument("--database", type=Path)
    info = commands.add_parser("info")
    info.add_argument("manifest", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            result = build_manifest(args.database, args.directory)
        elif args.command == "validate":
            result = validate_manifest(args.manifest, database=args.database)
        elif args.command == "info":
            result = validate_manifest(args.manifest)
        else:
            raise RuntimeError(f"Unknown command: {args.command}")
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(CONTRACT.canonical_json_bytes(result).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
