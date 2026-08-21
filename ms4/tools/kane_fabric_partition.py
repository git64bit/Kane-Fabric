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
from decimal import Decimal, InvalidOperation

PARTITION_FORMAT = "kane-fabric-partition"
PARTITION_IDENTITY_FORMAT = "kane-fabric-partition-definition"
VERSION = 1
PARTITION_KEY_PREFIX = "kfp1-"

SUPPORTED_SCOPE_CLASSES = frozenset(
    {"whole-jurisdiction", "bounded-region", "administrative", "composite"}
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PARTITION_KEY_RE = re.compile(r"^kfp1-[0-9a-f]{32}$")
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_COUNTRY_RE = re.compile(r"^[A-Z]{2}$")
_STATE_RE = re.compile(r"^[A-Z]{2}$")
_FIPS_RE = re.compile(r"^[0-9]{5}$")
_COORDINATE_RE = re.compile(r"^-?(?:0|[1-9][0-9]*)\.[0-9]{7}$")


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


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PartitionContractError(f"{label} must be a nonempty string")
    return value.strip()


def _require_sha256(value: object, label: str) -> str:
    text = str(value)
    if not _SHA256_RE.fullmatch(text):
        raise PartitionContractError(f"{label} must be 64 lowercase hex characters")
    return text


def _require_partition_key(value: object, label: str = "partition_key") -> str:
    text = str(value)
    if not _PARTITION_KEY_RE.fullmatch(text):
        raise PartitionContractError(f"{label} must match kfp1- followed by 32 lowercase hex characters")
    return text


def _normalize_coordinate_text(value: object, *, latitude: bool, label: str) -> str:
    if not isinstance(value, str) or not _COORDINATE_RE.fullmatch(value):
        raise PartitionContractError(
            f"{label} must be normalized fixed-decimal coordinate text with seven decimal places"
        )
    try:
        decimal = Decimal(value)
    except InvalidOperation as exc:
        raise PartitionContractError(f"{label} must be valid coordinate text") from exc
    limit = Decimal("90") if latitude else Decimal("180")
    if not decimal.is_finite() or decimal < -limit or decimal > limit:
        raise PartitionContractError(f"{label} is outside WGS84 range")
    if decimal == 0 and value.startswith("-"):
        raise PartitionContractError(f"{label} negative zero is not normalized")
    return value


def _normalize_bounds_identity(value: object, label: str = "scope.definition.bounds") -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise PartitionContractError(f"{label} must be an array")
    if len(value) != 4:
        raise PartitionContractError(f"{label} must contain four coordinates")
    result = [
        _normalize_coordinate_text(value[0], latitude=False, label=f"{label}[0]"),
        _normalize_coordinate_text(value[1], latitude=True, label=f"{label}[1]"),
        _normalize_coordinate_text(value[2], latitude=False, label=f"{label}[2]"),
        _normalize_coordinate_text(value[3], latitude=True, label=f"{label}[3]"),
    ]
    min_x, min_y, max_x, max_y = map(Decimal, result)
    if min_x >= max_x or min_y >= max_y:
        raise PartitionContractError(f"{label} must have positive width and height")
    return result


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
    """Validate exactly one supported v1 scope shape.

    The v1 identity contract is closed: unsupported scope classes and unknown
    definition fields are rejected rather than admitted through a vocabulary
    blacklist.
    """

    _require_exact_keys(value, {"scope_class", "definition"}, "scope")
    scope_class = str(value["scope_class"])
    if scope_class not in SUPPORTED_SCOPE_CLASSES:
        raise PartitionContractError(f"scope_class {scope_class!r} is unsupported by v1")
    definition = value["definition"]
    if not isinstance(definition, Mapping):
        raise PartitionContractError("scope.definition must be an object")

    if scope_class == "whole-jurisdiction":
        _require_exact_keys(definition, {"jurisdiction"}, "whole-jurisdiction definition")
        if definition["jurisdiction"] is not True:
            raise PartitionContractError("whole-jurisdiction definition.jurisdiction must be true")
        normalized_definition: dict[str, object] = {"jurisdiction": True}

    elif scope_class == "bounded-region":
        _require_exact_keys(definition, {"bounds", "srs_id"}, "bounded-region definition")
        if definition["srs_id"] != 4326:
            raise PartitionContractError("bounded-region definition.srs_id must be 4326")
        normalized_definition = {
            "bounds": _normalize_bounds_identity(definition["bounds"]),
            "srs_id": 4326,
        }

    elif scope_class == "administrative":
        _require_exact_keys(
            definition,
            {"administrative_kind", "name", "bounds", "boundary", "srs_id"},
            "administrative definition",
        )
        administrative_kind = str(definition["administrative_kind"])
        if administrative_kind not in {"municipality", "township-or-equivalent"}:
            raise PartitionContractError("administrative_kind is unsupported")
        if definition["srs_id"] != 4326:
            raise PartitionContractError("administrative definition.srs_id must be 4326")
        boundary = definition["boundary"]
        if not isinstance(boundary, Mapping):
            raise PartitionContractError("administrative definition.boundary must be an object")
        _require_exact_keys(
            boundary,
            {
                "dataset_key",
                "release_key",
                "content_sha256",
                "feature_id",
                "geometry_sha256",
            },
            "administrative boundary",
        )
        normalized_boundary = {
            "dataset_key": _require_text(boundary["dataset_key"], "administrative boundary dataset_key"),
            "release_key": _require_text(boundary["release_key"], "administrative boundary release_key"),
            "content_sha256": _require_sha256(boundary["content_sha256"], "administrative boundary content_sha256"),
            "feature_id": _require_text(boundary["feature_id"], "administrative boundary feature_id"),
            "geometry_sha256": _require_sha256(boundary["geometry_sha256"], "administrative boundary geometry_sha256"),
        }
        normalized_definition = {
            "administrative_kind": administrative_kind,
            "name": _require_text(definition["name"], "administrative name"),
            "bounds": _normalize_bounds_identity(definition["bounds"]),
            "boundary": normalized_boundary,
            "srs_id": 4326,
        }

    else:
        _require_exact_keys(definition, {"members", "operation", "srs_id"}, "composite definition")
        if definition["operation"] != "union":
            raise PartitionContractError("composite definition.operation must be 'union'")
        if definition["srs_id"] != 4326:
            raise PartitionContractError("composite definition.srs_id must be 4326")
        members = definition["members"]
        if not isinstance(members, Sequence) or isinstance(members, (str, bytes, bytearray)):
            raise PartitionContractError("composite definition.members must be an array")
        if len(members) < 2:
            raise PartitionContractError("composite scope requires at least two members")
        normalized_members: list[dict[str, object]] = []
        for index, member in enumerate(members):
            if not isinstance(member, Mapping):
                raise PartitionContractError(f"composite member {index} must be an object")
            _require_exact_keys(member, {"partition_key", "scope"}, f"composite member {index}")
            member_scope = member["scope"]
            if not isinstance(member_scope, Mapping):
                raise PartitionContractError(f"composite member {index}.scope must be an object")
            normalized_members.append(
                {
                    "partition_key": _require_partition_key(
                        member["partition_key"], f"composite member {index}.partition_key"
                    ),
                    "scope": normalize_scope(member_scope),
                }
            )
        normalized_members.sort(key=lambda item: str(item["partition_key"]))
        keys = [str(item["partition_key"]) for item in normalized_members]
        if len(set(keys)) != len(keys):
            raise PartitionContractError("composite members must have unique partition keys")
        normalized_definition = {
            "members": normalized_members,
            "operation": "union",
            "srs_id": 4326,
        }

    return {
        "scope_class": scope_class,
        "definition": normalized_definition,
    }


def _scope_identity_sha256(
    jurisdiction: Mapping[str, object], normalized_scope: Mapping[str, object]
) -> str:
    identity = {
        "format": PARTITION_IDENTITY_FORMAT,
        "version": VERSION,
        "jurisdiction": dict(jurisdiction),
        "scope": dict(normalized_scope),
    }
    return sha256_bytes(canonical_json_bytes(identity))


def _validate_composite_member_identities(
    jurisdiction: Mapping[str, object], normalized_scope: Mapping[str, object]
) -> None:
    if normalized_scope["scope_class"] != "composite":
        return
    definition = normalized_scope["definition"]
    assert isinstance(definition, Mapping)
    members = definition["members"]
    assert isinstance(members, list)
    for member in members:
        assert isinstance(member, Mapping)
        member_scope = member["scope"]
        assert isinstance(member_scope, Mapping)
        expected_sha = _scope_identity_sha256(jurisdiction, member_scope)
        expected_key = partition_key_from_sha256(expected_sha)
        if member["partition_key"] != expected_key:
            raise PartitionContractError(
                "composite member partition_key does not match its embedded logical scope identity"
            )
        _validate_composite_member_identities(jurisdiction, member_scope)


def partition_identity_document(
    jurisdiction: Mapping[str, object], scope: Mapping[str, object]
) -> dict[str, object]:
    normalized_jurisdiction = normalize_jurisdiction(jurisdiction)
    normalized_scope = normalize_scope(scope)
    _validate_composite_member_identities(normalized_jurisdiction, normalized_scope)
    return {
        "format": PARTITION_IDENTITY_FORMAT,
        "version": VERSION,
        "jurisdiction": normalized_jurisdiction,
        "scope": normalized_scope,
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

    identity = partition_identity_document(value["jurisdiction"], value["scope"])
    normalized_jurisdiction = identity["jurisdiction"]
    normalized_scope = identity["scope"]
    expected_sha256 = sha256_bytes(canonical_json_bytes(identity))
    definition_sha256 = str(value["definition_sha256"])
    if definition_sha256 != expected_sha256:
        raise PartitionContractError("partition definition_sha256 does not match descriptor identity")

    partition_key = _require_partition_key(value["partition_key"])
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
