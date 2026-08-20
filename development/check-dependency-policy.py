#!/usr/bin/env python3
"""Enforce Kane Fabric Unlicense and dependency/vendoring policy invariants."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "third_party" / "manifest.json"
PROHIBITED_PACKAGE_KEYS = {
    "dependencies",
    "devDependencies",
    "optionalDependencies",
    "peerDependencies",
    "bundledDependencies",
    "bundleDependencies",
}
PROHIBITED_RESOLUTION_FILES = {
    "package-lock.json",
    "npm-shrinkwrap.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "Pipfile.lock",
    "poetry.lock",
    "uv.lock",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest() -> dict[str, object]:
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise RuntimeError("third-party manifest schema is unsupported")
    return value


def iter_project_package_json() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("package.json")
        if "vendor" not in path.relative_to(ROOT).parts
    )


def validate(mode: str) -> dict[str, object]:
    errors: list[str] = []
    manifest = load_manifest()

    root_license = manifest.get("root_license")
    if not isinstance(root_license, dict):
        errors.append("third-party manifest root_license is missing")
    else:
        license_path = ROOT / str(root_license.get("path", ""))
        expected = str(root_license.get("sha256", ""))
        if not license_path.is_file():
            errors.append("root Unlicense file is missing")
        elif sha256_file(license_path) != expected:
            errors.append("root Unlicense changed; dependency policy forbids this")

    third_party = manifest.get("third_party")
    if not isinstance(third_party, list) or not third_party:
        errors.append("third-party inventory is empty or invalid")
    else:
        keys: set[str] = set()
        for item in third_party:
            if not isinstance(item, dict):
                errors.append("third-party inventory contains a non-object entry")
                continue
            key = str(item.get("key", ""))
            if not key:
                errors.append("third-party inventory entry has no key")
                continue
            if key in keys:
                errors.append(f"duplicate third-party key: {key}")
            keys.add(key)
            impact = str(item.get("license_impact", ""))
            if not impact.startswith("does-not-relicense-kane-fabric"):
                errors.append(f"{key}: license impact is not approved for Kane Fabric")
            if not item.get("license"):
                errors.append(f"{key}: license disposition is missing")
            requirement = str(item.get("vendoring_requirement", ""))
            if not requirement:
                errors.append(f"{key}: vendoring requirement is missing")
            pin = item.get("pin")
            if not isinstance(pin, dict) or not pin.get("status"):
                errors.append(f"{key}: pin status is missing")
            elif mode == "release" and requirement.startswith("required"):
                if pin.get("status") != "vendored":
                    errors.append(f"{key}: release gate requires vendored status")
                for field in ("version", "source_sha256", "vendor_path"):
                    if not pin.get(field):
                        errors.append(f"{key}: release gate missing pin.{field}")

    for package_path in iter_project_package_json():
        try:
            document = json.loads(package_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid package.json {package_path.relative_to(ROOT)}: {exc}")
            continue
        if not isinstance(document, dict):
            errors.append(f"package.json is not an object: {package_path.relative_to(ROOT)}")
            continue
        present = sorted(PROHIBITED_PACKAGE_KEYS & set(document))
        if present:
            errors.append(
                f"unapproved npm dependency graph in {package_path.relative_to(ROOT)}: {present}"
            )

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if "vendor" in relative.parts:
            continue
        if path.name in PROHIBITED_RESOLUTION_FILES:
            errors.append(f"unapproved external dependency lockfile: {relative}")

    return {
        "mode": mode,
        "root_license_sha256": sha256_file(ROOT / "LICENSE"),
        "third_party_entry_count": len(third_party) if isinstance(third_party, list) else 0,
        "valid": not errors,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", action="store_true", help="require all final vendoring pins")
    args = parser.parse_args()
    result = validate("release" if args.release else "development")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
