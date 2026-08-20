#!/usr/bin/env python3
"""Kane Fabric shared-substrate v1 wire-contract primitives.

This module defines generic Kane Fabric package identities. Kane County is the
reference deployment, but no county is implicit in these durable identifiers.
County/source-specific LOD policy belongs in the generators that use this
contract, not in the framing or content-identity rules here.
"""

from __future__ import annotations

import hashlib
import json
import re
import struct
from pathlib import PurePosixPath
from typing import Mapping, Sequence

VERSION = 1
SRS_ID = 4326

OVERVIEW_FORMAT = "kane-fabric-substrate-overview"
ROAD_FORMAT = "kane-fabric-substrate-roads"
WATER_FORMAT = "kane-fabric-substrate-water"
MANIFEST_FORMAT = "kane-fabric-substrate-manifest"

ROAD_MAGIC = b"KFSR001\n"
WATER_MAGIC = b"KFSW001\n"
PREFIX_LENGTH = 16

COMPONENT_ROLES = ("county_overview", "roads", "water")
COMPONENT_PATHS = {
    "county_overview": "county-overview.json",
    "roads": "roads-lod.kfs",
    "water": "water-lod.kfs",
}

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_FIPS_RE = re.compile(r"^[0-9]{5}$")
_COUNTRY_RE = re.compile(r"^[A-Z]{2}$")
_STATE_RE = re.compile(r"^[A-Z]{2}$")
_COUNTY_KEY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class SubstrateContractError(ValueError):
    """Raised when bytes or metadata violate the v1 substrate contract."""


def canonical_json_bytes(value: object) -> bytes:
    """Return the single JSON byte representation used by v1 artifacts."""

    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require_exact_keys(
    value: Mapping[str, object], keys: set[str], label: str
) -> None:
    actual = set(value)
    if actual != keys:
        missing = sorted(keys - actual)
        extra = sorted(actual - keys)
        raise SubstrateContractError(
            f"{label} keys mismatch: missing={missing!r} extra={extra!r}"
        )


def _require_sha256(value: object, label: str) -> str:
    text = str(value)
    if not _SHA256_RE.fullmatch(text):
        raise SubstrateContractError(
            f"{label} must be 64 lowercase hex characters"
        )
    return text


def validate_jurisdiction(value: Mapping[str, object]) -> dict[str, str]:
    """Validate the explicit jurisdiction identity carried across packages."""

    required = {"country_code", "state_code", "fips_code", "county_key", "name"}
    _require_exact_keys(value, required, "jurisdiction")

    country_code = str(value["country_code"])
    state_code = str(value["state_code"])
    fips_code = str(value["fips_code"])
    county_key = str(value["county_key"])
    name = str(value["name"]).strip()

    if not _COUNTRY_RE.fullmatch(country_code):
        raise SubstrateContractError(
            "jurisdiction country_code must be two uppercase ASCII letters"
        )
    if not _STATE_RE.fullmatch(state_code):
        raise SubstrateContractError(
            "jurisdiction state_code must be two uppercase ASCII letters"
        )
    if country_code == "US" and not _FIPS_RE.fullmatch(fips_code):
        raise SubstrateContractError(
            "U.S. jurisdiction fips_code must be exactly five digits"
        )
    if not _COUNTY_KEY_RE.fullmatch(county_key):
        raise SubstrateContractError(
            "jurisdiction county_key must be a lowercase hyphenated key"
        )
    if not name:
        raise SubstrateContractError("jurisdiction name must not be empty")

    return {
        "country_code": country_code,
        "state_code": state_code,
        "fips_code": fips_code,
        "county_key": county_key,
        "name": name,
    }


def validate_release_descriptor(
    value: Mapping[str, object],
) -> dict[str, object]:
    required = {"dataset_key", "release_key", "content_sha256", "feature_count"}
    _require_exact_keys(value, required, "accepted release")

    dataset_key = str(value["dataset_key"]).strip()
    release_key = str(value["release_key"]).strip()
    if not dataset_key or not release_key:
        raise SubstrateContractError("accepted release keys must not be empty")

    content_sha256 = _require_sha256(
        value["content_sha256"], "accepted release content_sha256"
    )
    feature_count = value["feature_count"]
    if (
        isinstance(feature_count, bool)
        or not isinstance(feature_count, int)
        or feature_count < 0
    ):
        raise SubstrateContractError(
            "accepted release feature_count must be a nonnegative integer"
        )

    return {
        "dataset_key": dataset_key,
        "release_key": release_key,
        "content_sha256": content_sha256,
        "feature_count": feature_count,
    }


def validate_component_descriptor(
    value: Mapping[str, object],
) -> dict[str, object]:
    required = {"role", "path", "format", "version", "byte_length", "sha256"}
    _require_exact_keys(value, required, "component")

    role = str(value["role"])
    if role not in COMPONENT_ROLES:
        raise SubstrateContractError(f"unsupported component role: {role}")

    path = str(value["path"])
    if path != COMPONENT_PATHS[role]:
        raise SubstrateContractError(
            f"component path does not match role {role}"
        )
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts:
        raise SubstrateContractError("component path must be a safe relative path")

    format_key = str(value["format"])
    version = value["version"]
    byte_length = value["byte_length"]
    if version != VERSION:
        raise SubstrateContractError("component version is unsupported")
    if (
        isinstance(byte_length, bool)
        or not isinstance(byte_length, int)
        or byte_length < 0
    ):
        raise SubstrateContractError(
            "component byte_length must be a nonnegative integer"
        )
    digest = _require_sha256(value["sha256"], "component sha256")

    return {
        "role": role,
        "path": path,
        "format": format_key,
        "version": version,
        "byte_length": byte_length,
        "sha256": digest,
    }


def content_identity_document(
    jurisdiction: Mapping[str, object],
    accepted_releases: Sequence[Mapping[str, object]],
    components: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Build the deterministic document hashed as substrate content identity."""

    jurisdiction_doc = validate_jurisdiction(jurisdiction)

    releases = [validate_release_descriptor(item) for item in accepted_releases]
    if len({item["dataset_key"] for item in releases}) != len(releases):
        raise SubstrateContractError(
            "accepted release inventory contains duplicate dataset_key"
        )
    releases.sort(key=lambda item: str(item["dataset_key"]))

    component_docs = [validate_component_descriptor(item) for item in components]
    roles = tuple(item["role"] for item in component_docs)
    if roles != COMPONENT_ROLES:
        raise SubstrateContractError(
            f"component roles must be exactly {COMPONENT_ROLES!r} in that order"
        )

    return {
        "accepted_releases": releases,
        "components": component_docs,
        "jurisdiction": jurisdiction_doc,
    }


def compute_substrate_content_sha256(
    jurisdiction: Mapping[str, object],
    accepted_releases: Sequence[Mapping[str, object]],
    components: Sequence[Mapping[str, object]],
) -> str:
    return sha256_bytes(
        canonical_json_bytes(
            content_identity_document(
                jurisdiction,
                accepted_releases,
                components,
            )
        )
    )


def encode_container_prefix(
    magic: bytes, index: Mapping[str, object]
) -> bytes:
    """Encode the fixed prefix plus canonical index for a v1 flat component."""

    if magic not in (ROAD_MAGIC, WATER_MAGIC):
        raise SubstrateContractError("unsupported substrate component magic")
    index_bytes = canonical_json_bytes(index)
    return magic + struct.pack(">Q", len(index_bytes)) + index_bytes


def decode_container_index(
    data: bytes,
    *,
    expected_magic: bytes,
    expected_format: str,
) -> tuple[dict[str, object], int]:
    """Validate and decode a complete prefix+index byte sequence.

    `data` may contain payload bytes after the index. The returned integer is the
    absolute byte offset at which the payload area begins. This small operation
    is intentionally separable from payload loading so browser and ESP32-S3
    readers do not need whole-component RAM residency.
    """

    if expected_magic not in (ROAD_MAGIC, WATER_MAGIC):
        raise SubstrateContractError("unsupported expected magic")
    if len(data) < PREFIX_LENGTH:
        raise SubstrateContractError("substrate component prefix is truncated")
    if data[:8] != expected_magic:
        raise SubstrateContractError(
            "substrate component magic/version is invalid"
        )

    index_length = struct.unpack(">Q", data[8:16])[0]
    index_end = PREFIX_LENGTH + index_length
    if index_end > len(data):
        raise SubstrateContractError("substrate component index is truncated")

    index_bytes = data[PREFIX_LENGTH:index_end]
    try:
        index = json.loads(index_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SubstrateContractError(
            f"substrate component index is invalid JSON: {exc}"
        ) from exc

    if not isinstance(index, dict):
        raise SubstrateContractError(
            "substrate component index must be a JSON object"
        )
    if canonical_json_bytes(index) != index_bytes:
        raise SubstrateContractError(
            "substrate component index is not canonical JSON"
        )
    if index.get("format") != expected_format or index.get("version") != VERSION:
        raise SubstrateContractError(
            "substrate component format/version is unsupported"
        )
    if index.get("srs_id") != SRS_ID:
        raise SubstrateContractError("substrate component SRS is unsupported")
    if index.get("compression") != "zlib-deflate":
        raise SubstrateContractError(
            "substrate component compression is unsupported"
        )
    if not isinstance(index.get("jurisdiction"), dict):
        raise SubstrateContractError(
            "substrate component jurisdiction is missing"
        )
    validate_jurisdiction(index["jurisdiction"])

    return index, index_end
