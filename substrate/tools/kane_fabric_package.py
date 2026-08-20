#!/usr/bin/env python3
"""Build, validate, compare, and activate complete Kane Fabric v1 substrate packages."""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Mapping, Sequence

PACKAGE_FILES = (
    "county-overview.json",
    "roads-lod.kfs",
    "water-lod.kfs",
    "substrate-manifest.json",
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load support module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


TOOLS = Path(__file__).resolve().parent
CONTRACT = _load_module(
    "_kane_fabric_package_contract",
    TOOLS / "kane_fabric_substrate.py",
)
COMPRESSION = _load_module(
    "_kane_fabric_package_compression",
    TOOLS / "kane_fabric_compression.py",
)
OVERVIEW = _load_module(
    "_kane_fabric_package_overview",
    TOOLS / "kane_fabric_overview.py",
)
ROADS_ENTRY = _load_module(
    "_kane_fabric_package_roads_entry",
    TOOLS / "kane_fabric_roads_entry.py",
)
ROADS = ROADS_ENTRY.ROADS
WATER = _load_module(
    "_kane_fabric_package_water",
    TOOLS / "kane_fabric_water.py",
)
MANIFEST = _load_module(
    "_kane_fabric_package_manifest",
    TOOLS / "kane_fabric_manifest.py",
)


def _sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_paths(package_dir: Path) -> dict[str, Path]:
    root = package_dir.resolve()
    return {
        "county_overview": root / "county-overview.json",
        "roads": root / "roads-lod.kfs",
        "water": root / "water-lod.kfs",
        "manifest": root / "substrate-manifest.json",
    }


def _require_package_directory(package_dir: Path) -> Path:
    package_dir = package_dir.resolve()
    if package_dir.is_symlink():
        raise RuntimeError(f"Substrate package directory must not be a symlink: {package_dir}")
    if not package_dir.is_dir():
        raise RuntimeError(f"Substrate package directory does not exist: {package_dir}")
    expected = set(PACKAGE_FILES)
    actual = {path.name for path in package_dir.iterdir()}
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        details = []
        if missing:
            details.append(f"missing={missing!r}")
        if extra:
            details.append(f"extra={extra!r}")
        raise RuntimeError(
            "Substrate package file inventory is invalid: " + ", ".join(details)
        )
    for filename in PACKAGE_FILES:
        path = package_dir / filename
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"Substrate package component is not a regular file: {path}")
    return package_dir


def _component_hashes(manifest_info: Mapping[str, object]) -> dict[str, str]:
    components = manifest_info.get("components")
    if not isinstance(components, list):
        raise RuntimeError("Substrate manifest component inventory is invalid")
    result = {}
    for item in components:
        if not isinstance(item, Mapping):
            raise RuntimeError("Substrate manifest component descriptor is invalid")
        role = str(item.get("role"))
        digest = str(item.get("sha256"))
        result[role] = digest
    if tuple(result) != CONTRACT.COMPONENT_ROLES:
        raise RuntimeError("Substrate manifest component role order is invalid")
    return result


def validate_package(database: Path, package_dir: Path) -> dict[str, object]:
    database = database.resolve()
    package_dir = _require_package_directory(package_dir)
    if not database.is_file():
        raise RuntimeError(f"Authoritative database does not exist: {database}")
    paths = package_paths(package_dir)
    manifest_info = MANIFEST.validate_manifest(paths["manifest"], database=database)
    return {
        "component_sha256": _component_hashes(manifest_info),
        "manifest_sha256": manifest_info["sha256"],
        "package_directory": str(package_dir),
        "status": "valid",
        "substrate_content_sha256": manifest_info["substrate_content_sha256"],
    }


def inspect_package(package_dir: Path) -> dict[str, object]:
    package_dir = _require_package_directory(package_dir)
    manifest_info = MANIFEST.validate_manifest(
        package_paths(package_dir)["manifest"],
        database=None,
    )
    return {
        "component_sha256": _component_hashes(manifest_info),
        "manifest_sha256": manifest_info["sha256"],
        "package_directory": str(package_dir),
        "status": "valid-without-authority-check",
        "substrate_content_sha256": manifest_info["substrate_content_sha256"],
    }


def _build_staged_package(database: Path, stage_dir: Path) -> dict[str, object]:
    COMPRESSION.require_accepted_zlib()
    paths = package_paths(stage_dir)
    OVERVIEW.build_overview(database, paths["county_overview"])
    ROADS.build_component(database, paths["roads"])
    WATER.build_component(database, paths["water"])
    MANIFEST.build_manifest(database, stage_dir)
    return validate_package(database, stage_dir)


def compare_packages(database: Path, first: Path, second: Path) -> dict[str, object]:
    first = _require_package_directory(first)
    second = _require_package_directory(second)
    first_info = validate_package(database, first)
    second_info = validate_package(database, second)

    for filename in PACKAGE_FILES:
        if (first / filename).read_bytes() != (second / filename).read_bytes():
            raise RuntimeError(
                f"Substrate package reproducibility mismatch: {filename}"
            )
    if first_info["substrate_content_sha256"] != second_info["substrate_content_sha256"]:
        raise RuntimeError("Substrate package content identity mismatch")
    if first_info["component_sha256"] != second_info["component_sha256"]:
        raise RuntimeError("Substrate package component identity mismatch")
    if first_info["manifest_sha256"] != second_info["manifest_sha256"]:
        raise RuntimeError("Substrate package manifest identity mismatch")

    return {
        "component_sha256": first_info["component_sha256"],
        "manifest_sha256": first_info["manifest_sha256"],
        "status": "reproducible",
        "substrate_content_sha256": first_info["substrate_content_sha256"],
    }


def _staging_prefix(package_dir: Path) -> str:
    return f".{package_dir.name}.stage-"


def _backup_path(package_dir: Path) -> Path:
    return package_dir.with_name(f".{package_dir.name}.previous")


def _remove_directory(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        raise RuntimeError(f"Substrate package temporary path is invalid: {path}")
    shutil.rmtree(path)


def recover_interrupted_activation(package_dir: Path) -> None:
    """Restore the prior complete package whenever an unfinalized backup exists."""

    package_dir = package_dir.resolve()
    parent = package_dir.parent
    backup = _backup_path(package_dir)
    if backup.exists():
        if backup.is_symlink() or not backup.is_dir():
            raise RuntimeError(f"Substrate package recovery path is invalid: {backup}")
        if package_dir.exists():
            if package_dir.is_symlink() or not package_dir.is_dir():
                raise RuntimeError(
                    f"Substrate package destination is invalid during recovery: {package_dir}"
                )
            shutil.rmtree(package_dir)
        os.replace(backup, package_dir)

    if not parent.is_dir():
        return
    prefix = _staging_prefix(package_dir)
    for path in parent.iterdir():
        if path.name.startswith(prefix):
            _remove_directory(path)


def _begin_activation(stage_dir: Path, package_dir: Path) -> bool:
    stage_dir = stage_dir.resolve()
    package_dir = package_dir.resolve()
    if stage_dir.parent != package_dir.parent:
        raise RuntimeError(
            "Substrate package staging and destination must share a parent directory"
        )
    if stage_dir.is_symlink() or not stage_dir.is_dir():
        raise RuntimeError(f"Substrate package staging directory is invalid: {stage_dir}")
    if package_dir.is_symlink():
        raise RuntimeError("Substrate package destination must not be a symlink")
    backup = _backup_path(package_dir)
    if backup.exists():
        raise RuntimeError(f"Substrate package activation backup already exists: {backup}")

    moved_old = False
    if package_dir.exists():
        if not package_dir.is_dir():
            raise RuntimeError(
                f"Substrate package destination is not a directory: {package_dir}"
            )
        os.replace(package_dir, backup)
        moved_old = True
    try:
        os.replace(stage_dir, package_dir)
    except BaseException:
        if moved_old and backup.exists() and not package_dir.exists():
            os.replace(backup, package_dir)
        raise
    return moved_old


def _finalize_activation(package_dir: Path) -> None:
    backup = _backup_path(package_dir.resolve())
    if backup.exists():
        _remove_directory(backup)


def _rollback_activation(package_dir: Path, *, had_previous: bool) -> None:
    package_dir = package_dir.resolve()
    backup = _backup_path(package_dir)
    if package_dir.exists():
        if package_dir.is_symlink() or not package_dir.is_dir():
            raise RuntimeError(
                f"Substrate package destination is invalid during rollback: {package_dir}"
            )
        shutil.rmtree(package_dir)
    if had_previous:
        if backup.is_symlink() or not backup.is_dir():
            raise RuntimeError("Substrate package rollback backup is missing or invalid")
        os.replace(backup, package_dir)
    elif backup.exists():
        _remove_directory(backup)


def build_package(database: Path, package_dir: Path) -> dict[str, object]:
    COMPRESSION.require_accepted_zlib()
    database = database.resolve()
    package_dir = package_dir.resolve()
    if not database.is_file():
        raise RuntimeError(f"Authoritative database does not exist: {database}")
    if package_dir == database or package_dir in database.parents:
        raise RuntimeError(
            "Substrate package destination must not replace or contain the authoritative database"
        )

    package_dir.parent.mkdir(parents=True, exist_ok=True)
    recover_interrupted_activation(package_dir)
    database_sha_before = _sha256_file(database)

    first_stage = Path(
        tempfile.mkdtemp(prefix=_staging_prefix(package_dir), dir=str(package_dir.parent))
    ).resolve()
    second_stage = Path(
        tempfile.mkdtemp(prefix=_staging_prefix(package_dir), dir=str(package_dir.parent))
    ).resolve()
    activated = False
    had_previous = False
    try:
        first_info = _build_staged_package(database, first_stage)
        _build_staged_package(database, second_stage)
        reproducibility = compare_packages(database, first_stage, second_stage)
        _remove_directory(second_stage)

        database_sha_after_build = _sha256_file(database)
        if database_sha_after_build != database_sha_before:
            raise RuntimeError(
                "Authoritative database changed during substrate compilation"
            )

        had_previous = _begin_activation(first_stage, package_dir)
        activated = True
        try:
            final_info = validate_package(database, package_dir)
            database_sha_after_activation = _sha256_file(database)
            if database_sha_after_activation != database_sha_before:
                raise RuntimeError(
                    "Authoritative database changed during substrate activation validation"
                )
        except BaseException:
            _rollback_activation(package_dir, had_previous=had_previous)
            activated = False
            raise
        _finalize_activation(package_dir)
        activated = False
    finally:
        if first_stage.exists():
            _remove_directory(first_stage)
        if second_stage.exists():
            _remove_directory(second_stage)
        if activated:
            _rollback_activation(package_dir, had_previous=had_previous)

    return {
        "component_sha256": final_info["component_sha256"],
        "database_sha256": database_sha_before,
        "manifest_sha256": final_info["manifest_sha256"],
        "package_directory": str(package_dir),
        "reproducibility": reproducibility["status"],
        "status": "built-and-activated",
        "substrate_content_sha256": final_info["substrate_content_sha256"],
    }


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    build = commands.add_parser(
        "build",
        help="build twice, prove reproducibility, and activate one complete package",
    )
    build.add_argument("database", type=Path)
    build.add_argument("package_dir", type=Path)

    validate = commands.add_parser("validate", help="validate a complete active package")
    validate.add_argument("database", type=Path)
    validate.add_argument("package_dir", type=Path)

    inspect = commands.add_parser(
        "inspect", help="validate exact package inventory without a database authority check"
    )
    inspect.add_argument("package_dir", type=Path)

    compare = commands.add_parser(
        "compare", help="validate and byte-compare two complete packages"
    )
    compare.add_argument("database", type=Path)
    compare.add_argument("first", type=Path)
    compare.add_argument("second", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            result = build_package(args.database, args.package_dir)
        elif args.command == "validate":
            result = validate_package(args.database, args.package_dir)
        elif args.command == "inspect":
            result = inspect_package(args.package_dir)
        elif args.command == "compare":
            result = compare_packages(args.database, args.first, args.second)
        else:
            raise RuntimeError(f"Unknown command: {args.command}")
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(CONTRACT.canonical_json_bytes(result).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
