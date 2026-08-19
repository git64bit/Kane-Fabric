#!/usr/bin/env python3
"""Load, validate, inspect, and hash Kane Fabric source profiles."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote, urlsplit

PROFILE_DIR = Path(__file__).resolve().parent.parent / "source-profiles"
REGISTRY_SCHEMA = 1
PROFILE_SCHEMA = 1
APPROVED_REGISTRY_SHA256 = "e95c9d0486f65035146cb0a2a9580e4148c853a78c4f9e44e2420f59ef654e12"
ARC_GIS_HOST = "services1.arcgis.com"
ARC_GIS_ACCOUNT = "oRKmdBXD6EbdmVgJ"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

PROFILE_FILENAMES = (
    "kane-county-boundary.json",
    "kane-county-buildings.json",
    "kane-county-creeks.json",
    "kane-county-fox-river.json",
    "kane-county-roads.json",
)
ALLOWED_DIRECTORY_ENTRIES = frozenset((*PROFILE_FILENAMES, "README.md"))

TOP_REQUIRED = frozenset(
    (
        "registry_profile_schema",
        "profile_key",
        "agency_key",
        "dataset_key",
        "donor",
        "source",
        "query",
        "geometry",
        "pagination",
        "validation",
        "copyright_text",
    )
)
TOP_OPTIONAL = frozenset(("expected_feature_count", "update_group"))
OBJECT_KEYS = {
    "donor": frozenset(("repository", "commit", "path", "file_sha256", "profile_schema")),
    "source": frozenset(("layer_url", "service_name", "layer_id")),
    "query": frozenset(
        ("where", "object_id_field", "identity_field", "out_srs", "page_size", "out_fields")
    ),
    "geometry": frozenset(
        (
            "arcgis_type",
            "geojson_types",
            "missing_geometry_policy",
            "missing_geometry_policy_origin",
        )
    ),
    "pagination": frozenset(
        (
            "mode",
            "inventory_query",
            "ordering",
            "respect_service_max_record_count",
            "offset_pagination",
            "require_exact_requested_ids",
        )
    ),
    "validation": frozenset(("identity", "schema", "geometry", "response")),
}
PAGINATION_CONTRACT = {
    "mode": "exact-object-id-groups",
    "inventory_query": "returnIdsOnly",
    "ordering": "ascending-numeric",
    "respect_service_max_record_count": True,
    "offset_pagination": False,
    "require_exact_requested_ids": True,
}
VALIDATION_CONTRACT = {
    "identity": "required-unique",
    "schema": "requested-fields-present",
    "geometry": "declared-types-only",
    "response": "geojson-feature-collection",
}


class DuplicateKeyError(ValueError):
    """Raised when JSON contains a duplicate object key."""


def _pairs_to_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate object key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number {value!r}")


def _path_text(path: tuple[str | int, ...]) -> str:
    text = "profile"
    for part in path:
        text += f"[{part}]" if isinstance(part, int) else f".{part}"
    return text


def _scan_value(value: Any, path: tuple[str | int, ...], errors: list[str]) -> None:
    label = _path_text(path)
    if value is None:
        errors.append(f"{label}: null is not permitted")
    elif isinstance(value, str):
        if not value:
            errors.append(f"{label}: empty strings are not permitted")
        elif value != value.strip():
            errors.append(f"{label}: leading or trailing whitespace is not permitted")
    elif isinstance(value, list):
        fingerprints: set[str] = set()
        for index, item in enumerate(value):
            fingerprint = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            if fingerprint in fingerprints:
                errors.append(f"{label}: duplicate array entry at index {index}")
            fingerprints.add(fingerprint)
            _scan_value(item, (*path, index), errors)
    elif isinstance(value, dict):
        for key, item in value.items():
            _scan_value(item, (*path, key), errors)


def _check_keys(
    value: Any,
    label: str,
    required: frozenset[str],
    optional: frozenset[str],
    errors: list[str],
) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label}: expected an object")
        return False
    keys = set(value)
    for key in sorted(required - keys):
        errors.append(f"{label}: missing required key {key!r}")
    for key in sorted(keys - required - optional):
        errors.append(f"{label}: unknown key {key!r}")
    return required <= keys and keys <= required | optional


def _validate_endpoint(profile: dict[str, Any], filename: str, errors: list[str]) -> None:
    source = profile.get("source")
    if not isinstance(source, dict):
        return
    url = source.get("layer_url")
    service = source.get("service_name")
    layer_id = source.get("layer_id")
    if not isinstance(url, str):
        errors.append(f"{filename}: source.layer_url must be a string")
        return
    try:
        parsed = urlsplit(url)
    except ValueError as exc:
        errors.append(f"{filename}: invalid source.layer_url: {exc}")
        return
    if parsed.scheme != "https":
        errors.append(f"{filename}: source.layer_url must use HTTPS")
    if parsed.hostname != ARC_GIS_HOST:
        errors.append(f"{filename}: source.layer_url has an unapproved hostname")
    try:
        port = parsed.port
    except ValueError:
        port = -1
    if port is not None:
        errors.append(f"{filename}: source.layer_url must not declare a port")
    if parsed.username is not None or parsed.password is not None:
        errors.append(f"{filename}: source.layer_url must not contain credentials")
    if parsed.query or parsed.fragment:
        errors.append(f"{filename}: source.layer_url must not contain query or fragment data")
    if url.endswith("/"):
        errors.append(f"{filename}: source.layer_url must not end with a slash")
    if not isinstance(service, str):
        errors.append(f"{filename}: source.service_name must be a string")
        return
    if "%" in service or unquote(service) != service:
        errors.append(f"{filename}: source.service_name must not be percent encoded")
    if type(layer_id) is not int or layer_id < 0:
        errors.append(f"{filename}: source.layer_id must be a nonnegative integer")
        return
    expected_path = f"/{ARC_GIS_ACCOUNT}/ArcGIS/rest/services/{service}/FeatureServer/{layer_id}"
    if parsed.path != expected_path or f"https://{ARC_GIS_HOST}{expected_path}" != url:
        errors.append(f"{filename}: source endpoint and service/layer declaration disagree")


def _parse_profile(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    raw = path.read_bytes()
    if not raw:
        return None, [f"{path.name}: empty profile file"]
    if raw.startswith(b"\xef\xbb\xbf"):
        return None, [f"{path.name}: UTF-8 BOM is not permitted"]
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs_to_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, DuplicateKeyError, json.JSONDecodeError, ValueError) as exc:
        return None, [f"{path.name}: invalid JSON: {exc}"]
    if not isinstance(value, dict):
        return None, [f"{path.name}: top-level JSON value must be an object"]
    _scan_value(value, (), errors)
    return value, errors


def _validate_profile(profile: dict[str, Any], filename: str) -> list[str]:
    errors: list[str] = []
    _check_keys(profile, filename, TOP_REQUIRED, TOP_OPTIONAL, errors)
    for name, keys in OBJECT_KEYS.items():
        if name in profile:
            _check_keys(profile[name], f"{filename}.{name}", keys, frozenset(), errors)
    _validate_endpoint(profile, filename, errors)

    if profile.get("registry_profile_schema") != PROFILE_SCHEMA:
        errors.append(f"{filename}: registry_profile_schema must equal {PROFILE_SCHEMA}")
    if profile.get("agency_key") != "kane-county-gis":
        errors.append(f"{filename}: agency_key must equal 'kane-county-gis'")

    donor = profile.get("donor")
    if isinstance(donor, dict):
        digest = donor.get("file_sha256")
        if not isinstance(digest, str) or SHA256_PATTERN.fullmatch(digest) is None:
            errors.append(f"{filename}: donor.file_sha256 must be lowercase SHA-256")

    query = profile.get("query")
    if isinstance(query, dict):
        out_fields = query.get("out_fields")
        if not isinstance(out_fields, list) or not out_fields:
            errors.append(f"{filename}: query.out_fields must be a nonempty array")
        elif any(not isinstance(field, str) for field in out_fields):
            errors.append(f"{filename}: query.out_fields entries must be strings")
        else:
            if "*" in out_fields:
                errors.append(f"{filename}: wildcard field requests are not permitted")
            if any("," in field for field in out_fields):
                errors.append(f"{filename}: comma-combined requested fields are not permitted")
            identity = query.get("identity_field")
            if isinstance(identity, str) and identity not in out_fields:
                errors.append(f"{filename}: identity_field is absent from out_fields")
            if "OBJECTID" not in out_fields:
                errors.append(f"{filename}: OBJECTID is absent from out_fields")
        if query.get("where") != "1=1":
            errors.append(f"{filename}: query.where must equal '1=1'")
        if query.get("object_id_field") != "OBJECTID":
            errors.append(f"{filename}: query.object_id_field must equal 'OBJECTID'")
        for key, expected in (("out_srs", 4326), ("page_size", 2000)):
            value = query.get(key)
            if type(value) is not int or value != expected:
                errors.append(f"{filename}: query.{key} must equal {expected}")

    if profile.get("pagination") != PAGINATION_CONTRACT:
        errors.append(f"{filename}: pagination contract does not match the approved contract")
    if profile.get("validation") != VALIDATION_CONTRACT:
        errors.append(f"{filename}: validation contract does not match the approved contract")
    if profile.get("copyright_text") != "Kane County, GIS":
        errors.append(f"{filename}: copyright_text does not match the approved attribution")
    return errors


def _directory_errors(directory: Path) -> tuple[list[str], list[Path]]:
    if not directory.is_dir():
        return [f"registry directory does not exist: {directory}"], []
    errors: list[str] = []
    profiles: list[Path] = []
    entries = sorted(directory.iterdir(), key=lambda item: item.name)
    names = {entry.name for entry in entries}
    for entry in entries:
        if entry.is_symlink():
            errors.append(f"registry directory contains a symlink: {entry.name}")
            continue
        if entry.is_dir():
            errors.append(f"registry directory contains a subdirectory: {entry.name}")
            continue
        if entry.name not in ALLOWED_DIRECTORY_ENTRIES:
            errors.append(f"registry directory contains an additional file: {entry.name}")
        elif entry.name.endswith(".json"):
            profiles.append(entry)
    for name in sorted(ALLOWED_DIRECTORY_ENTRIES - names):
        errors.append(f"registry directory is missing required file: {name}")
    return errors, profiles


def _cross_profile_errors(profiles: list[tuple[str, dict[str, Any]]]) -> list[str]:
    errors: list[str] = []
    if len(profiles) != 5:
        errors.append(f"registry must contain exactly five profiles; found {len(profiles)}")

    def values(getter: Callable[[dict[str, Any]], Any]) -> list[Any]:
        return [getter(profile) for _, profile in profiles]

    for label, items in {
        "profile_key": values(lambda p: p.get("profile_key")),
        "dataset_key": values(lambda p: p.get("dataset_key")),
        "donor path": values(
            lambda p: p.get("donor", {}).get("path") if isinstance(p.get("donor"), dict) else None
        ),
    }.items():
        if len(items) != len(set(json.dumps(item, sort_keys=True) for item in items)):
            errors.append(f"registry contains duplicate {label} values")

    groups = {
        profile.get("profile_key"): profile.get("update_group")
        for _, profile in profiles
        if "update_group" in profile
    }
    if groups != {
        "kane-county-creeks": "water-context",
        "kane-county-fox-river": "water-context",
    }:
        errors.append("Fox River and creeks must be the only water-context update-group members")

    expected_counts = [profile for _, profile in profiles if "expected_feature_count" in profile]
    if len(expected_counts) != 1 or expected_counts[0].get("profile_key") != "kane-county-boundary":
        errors.append("exactly the county boundary must declare expected_feature_count")
    return errors


def canonical_registry_bytes(registry: dict[str, Any]) -> bytes:
    return json.dumps(
        registry,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def inspect_registry(directory: Path = PROFILE_DIR) -> dict[str, Any]:
    directory = Path(directory)
    errors, paths = _directory_errors(directory)
    parsed: list[tuple[str, dict[str, Any]]] = []
    for path in sorted(paths, key=lambda item: item.name):
        try:
            profile, parse_errors = _parse_profile(path)
        except OSError as exc:
            errors.append(f"cannot read {path}: {exc}")
            continue
        errors.extend(parse_errors)
        if profile is not None:
            errors.extend(_validate_profile(profile, path.name))
            parsed.append((path.name, profile))
    errors.extend(_cross_profile_errors(parsed))

    normalized_profiles: list[dict[str, Any]] = []
    if not errors:
        for filename, profile in sorted(parsed, key=lambda item: item[1]["profile_key"]):
            normalized = dict(profile)
            normalized["registry_filename"] = filename
            normalized_profiles.append(normalized)
        registry = {"registry_schema": REGISTRY_SCHEMA, "profiles": normalized_profiles}
        digest = hashlib.sha256(canonical_registry_bytes(registry)).hexdigest()
        if digest != APPROVED_REGISTRY_SHA256:
            errors.append(
                "registry semantic identity differs from the approved Kane County source-profile contract"
            )
    else:
        registry = None
        digest = None

    errors = sorted(set(errors))
    if errors:
        return {
            "valid": False,
            "errors": errors,
            "profile_count": len(paths),
            "registry": None,
            "registry_sha256": None,
        }
    return {
        "valid": True,
        "errors": [],
        "profile_count": len(normalized_profiles),
        "registry": registry,
        "registry_sha256": digest,
    }


def _emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=PROFILE_DIR)
    parser.add_argument("command", choices=("validate", "info", "hash"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = inspect_registry(args.directory)
    if args.command == "validate":
        _emit(
            {
                "errors": result["errors"],
                "profile_count": result["profile_count"],
                "registry_sha256": result["registry_sha256"],
                "valid": result["valid"],
            }
        )
    elif args.command == "hash":
        _emit(
            {"registry_sha256": result["registry_sha256"], "valid": result["valid"]}
            if result["valid"]
            else {
                "errors": result["errors"],
                "profile_count": result["profile_count"],
                "registry_sha256": None,
                "valid": False,
            }
        )
    else:
        _emit(
            {
                "profile_count": result["profile_count"],
                "profiles": result["registry"]["profiles"],
                "registry_schema": result["registry"]["registry_schema"],
                "registry_sha256": result["registry_sha256"],
                "valid": True,
            }
            if result["valid"]
            else {
                "errors": result["errors"],
                "profile_count": result["profile_count"],
                "registry_sha256": None,
                "valid": False,
            }
        )
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
