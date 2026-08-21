#!/usr/bin/env python3
"""Kane Fabric Milestone 4 geographic partition identity contract.

Partition identity is logical distribution identity. It is intentionally
independent of edge-device, network, and storage placement.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence

PARTITION_FORMAT = "kane-fabric-partition"
PARTITION_IDENTITY_FORMAT = "kane-fabric-partition-definition"
VERSION = 1
PARTITION_KEY_PREFIX = "kfp1-"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_COUNTRY_RE = re.compile(r"^[A-Z]{2}$")
_STATE_RE = re.compile(r"^[A-Z]{2}$")
_FIPS_RE = re.compile(r"^[0-9]{5}$")

_PHYSICAL_IDENTITY_KEYS = frozenset(
    {
        "device",
        "device_id",
        "esp32_serial",
        "hostname",
        "ip",
        "ip_address",
        "network_address",
        "serial_number",
        "ssid",
        "storage_path",
    }
)


class PartitionContractError(ValueError):
    """Raised when a partition descriptor violates the v1 contract."""


def canonical_json_bytes(value: object) -> bytes:
    """Return the canonical JSON representation used for MS4 identities."""

    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require_exact_keys(value: Mapping[str, object], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise PartitionContractError(
            f"{label} keys mismatch: missing={missing!r} extra={extra!r}"
        )


def _normalize_json_identity(value: object, path: str = "scope.definition") -> object:
    """Validate JSON identity data and reject non-normalized floating point values."""

    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        raise PartitionContractError(
            f"{path} contains a floating-point value; scope normalization must encode coordinates deterministically"
        )
    if isinstance(value, Mapping):
        normalized: dict[str, object] = {}
        for key, child in value.items():
            if not isinstance(key, str) or not key:
                raise PartitionContractError(f"{path} object keys must be nonempty strings")
            if key in _PHYSICAL_IDENTITY_KEYS:
                raise PartitionContractError(
                    f"{path}.{key} is physical placement metadata and cannot participate in partition identity"
                )
            normalized[key] = _normalize_json_identity(child, f"{path}.{key}")
        return normalized
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return [
            _normalize_json_identity(child, f"{path}[{index}]")
            for index, child in enumerate(value)
        ]
    raise PartitionContractError(f"{path} contains unsupported identity value {type(value).__name__}")


def normalize_jurisdiction(value: Mapping[str, object]) -> dict[str, str]:
    required = {"country_code", "state_code", "fips_code", "county_key", "name"}
    _require_exact_keys(value, required, "jurisdiction")

    country_code = str(value["country_code"])
    state_code = str(value["state_code"])
    fips_code = str(value["fips_code"])
    county_key = str(value["county_key"])
    name = str(value["name"]).strip()

    if not _COUNTRY_RE.fullmatch(country_code):
        raise PartitionContractError("jurisdiction country_code must be two uppercase ASCII letters")
    if not _STATE_RE.fullmatch(state_code):
        raise PartitionContractError("jurisdiction state_code must be two uppercase ASCII letters")
    if country_code == "US" and not _FIPS_RE.fullmatch(fips_code):
        raise PartitionContractError("U.S. jurisdiction fips_code must be exactly five digits")
    if not _SLUG_RE.fullmatch(county_key):
        raise PartitionContractError("jurisdiction county_key must be a lowercase hyphenated key")
    if not name:
        raise PartitionContractError("jurisdiction name must not be empty")

    return {
        "country_code": country_code,
        "state_code": state_code,
        "fips_code": fips_code,
        "county_key": county_key,
        "name": name,
    }


def normalize_scope(value: Mapping[str, object]) -> dict[str, object]:
    """Validate a normalized scope envelope without defining class-specific semantics."""

    _require_exact_keys(value, {"scope_class", "definition"}, "scope")
    scope_class = str(value["scope_class"])
    if not _SLUG_RE.fullmatch(scope_class):
        raise PartitionContractError("scope_class must be a lowercase hyphenated key")
    definition = value["definition"]
    if not isinstance(definition, Mapping):
        raise PartitionContractError("scope.definition must be an object")
    return {
        "scope_class": scope_class,
        "definition": _normalize_json_identity(definition),
    }


def partition_identity_document(
    jurisdiction: Mapping[str, object], scope: Mapping[str, object]
) -> dict[str, object]:
    return {
        "format": PARTITION_IDENTITY_FORMAT,
        "version": VERSION,
        "jurisdiction": normalize_jurisdiction(jurisdiction),
        "scope": normalize_scope(scope),
    }


def compute_partition_definition_sha256(
    jurisdiction: Mapping[str, object], scope: Mapping[str, object]
) -> str:
    return sha256_bytes(canonical_json_bytes(partition_identity_document(jurisdiction, scope)))


def partition_key_from_sha256(definition_sha256: str) -> str:
    if not _SHA256_RE.fullmatch(definition_sha256):
        raise PartitionContractError("definition_sha256 must be 64 lowercase hex characters")
    return PARTITION_KEY_PREFIX + definition_sha256[:32]


def build_partition_descriptor(
    jurisdiction: Mapping[str, object],
    scope: Mapping[str, object],
    *,
    label: str | None = None,
) -> dict[str, object]:
    identity = partition_identity_document(jurisdiction, scope)
    definition_sha256 = sha256_bytes(canonical_json_bytes(identity))
    if label is not None:
        label = label.strip()
        if not label:
            raise PartitionContractError("partition label must not be empty when present")
    return {
        "format": PARTITION_FORMAT,
        "version": VERSION,
        "jurisdiction": identity["jurisdiction"],
        "scope": identity["scope"],
        "definition_sha256": definition_sha256,
        "partition_key": partition_key_from_sha256(definition_sha256),
        "label": label,
    }


def validate_partition_descriptor(value: Mapping[str, object]) -> dict[str, object]:
    required = {
        "format",
        "version",
        "jurisdiction",
        "scope",
        "definition_sha256",
        "partition_key",
        "label",
    }
    _require_exact_keys(value, required, "partition descriptor")
    if value["format"] != PARTITION_FORMAT or value["version"] != VERSION:
        raise PartitionContractError("partition format/version is unsupported")
    if not isinstance(value["jurisdiction"], Mapping):
        raise PartitionContractError("partition jurisdiction must be an object")
    if not isinstance(value["scope"], Mapping):
        raise PartitionContractError("partition scope must be an object")

    normalized_jurisdiction = normalize_jurisdiction(value["jurisdiction"])
    normalized_scope = normalize_scope(value["scope"])
    expected_sha256 = compute_partition_definition_sha256(
        normalized_jurisdiction, normalized_scope
    )
    definition_sha256 = str(value["definition_sha256"])
    if definition_sha256 != expected_sha256:
        raise PartitionContractError("partition definition_sha256 does not match descriptor identity")

    partition_key = str(value["partition_key"])
    if partition_key != partition_key_from_sha256(definition_sha256):
        raise PartitionContractError("partition_key does not match definition_sha256")

    label_value = value["label"]
    if label_value is not None:
        if not isinstance(label_value, str) or not label_value.strip():
            raise PartitionContractError("partition label must be null or a nonempty string")
        label_value = label_value.strip()

    return {
        "format": PARTITION_FORMAT,
        "version": VERSION,
        "jurisdiction": normalized_jurisdiction,
        "scope": normalized_scope,
        "definition_sha256": definition_sha256,
        "partition_key": partition_key,
        "label": label_value,
    }
