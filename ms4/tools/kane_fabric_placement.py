#!/usr/bin/env python3
"""MS4 logical edge-placement compatibility contract.

The logical identity binds content selected for placement. Physical node,
network, and storage metadata is deliberately carried outside that identity.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence

from ms4.tools.kane_fabric_partition import canonical_json_bytes

FORMAT = "kane-fabric-edge-placement-plan"
VERSION = 1
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PARTITION_KEY_RE = re.compile(r"^kfp1-[0-9a-f]{32}$")
_GENERATION_KEY_RE = re.compile(r"^kfsg1-[0-9a-f]{32}$")


class PlacementContractError(ValueError):
    pass


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PlacementContractError(f"{label} must be a nonempty string")
    return value.strip()


def _partition_key(value: object) -> str:
    text = str(value)
    if not _PARTITION_KEY_RE.fullmatch(text):
        raise PlacementContractError("partition_key is invalid")
    return text


def _substrate_sha(value: object) -> str:
    text = str(value)
    if not _SHA256_RE.fullmatch(text):
        raise PlacementContractError("substrate_content_sha256 is invalid")
    return text


def _generation_keys(values: Sequence[object]) -> list[str]:
    if isinstance(values, (str, bytes, bytearray)):
        raise PlacementContractError("subscription_generation_keys must be an array")
    result = sorted({str(value) for value in values})
    if any(not _GENERATION_KEY_RE.fullmatch(value) for value in result):
        raise PlacementContractError("subscription_generation_keys contain an invalid generation key")
    return result


def _physical(value: Mapping[str, object]) -> dict[str, object]:
    if not value:
        raise PlacementContractError("physical placement metadata must not be empty")
    result: dict[str, object] = {}
    for key, child in value.items():
        if not isinstance(key, str) or not key:
            raise PlacementContractError("physical placement keys must be nonempty strings")
        canonical_json_bytes(child)
        result[key] = child
    return result


def build_placement_plan(
    *,
    partition_key: str,
    substrate_content_sha256: str,
    subscription_generation_keys: Sequence[str],
    physical: Mapping[str, object],
) -> dict[str, object]:
    logical = {
        "partition_key": _partition_key(partition_key),
        "substrate_content_sha256": _substrate_sha(substrate_content_sha256),
        "subscription_generation_keys": _generation_keys(subscription_generation_keys),
    }
    logical_sha = hashlib.sha256(canonical_json_bytes(logical)).hexdigest()
    return {
        "format": FORMAT,
        "version": VERSION,
        "logical": logical,
        "logical_content_sha256": logical_sha,
        "physical": _physical(physical),
    }


def validate_placement_plan(value: Mapping[str, object]) -> None:
    if set(value) != {"format", "version", "logical", "logical_content_sha256", "physical"}:
        raise PlacementContractError("placement plan keys are invalid")
    if value["format"] != FORMAT or value["version"] != VERSION:
        raise PlacementContractError("placement plan format/version is unsupported")
    logical = value["logical"]
    physical = value["physical"]
    if not isinstance(logical, Mapping) or not isinstance(physical, Mapping):
        raise PlacementContractError("placement logical/physical sections must be objects")
    if set(logical) != {"partition_key", "substrate_content_sha256", "subscription_generation_keys"}:
        raise PlacementContractError("placement logical keys are invalid")
    generations = logical["subscription_generation_keys"]
    if not isinstance(generations, Sequence) or isinstance(generations, (str, bytes, bytearray)):
        raise PlacementContractError("subscription_generation_keys must be an array")
    normalized = {
        "partition_key": _partition_key(logical["partition_key"]),
        "substrate_content_sha256": _substrate_sha(logical["substrate_content_sha256"]),
        "subscription_generation_keys": _generation_keys(generations),
    }
    if dict(logical) != normalized:
        raise PlacementContractError("placement logical section is not normalized")
    _physical(physical)
    expected = hashlib.sha256(canonical_json_bytes(normalized)).hexdigest()
    if value["logical_content_sha256"] != expected:
        raise PlacementContractError("logical placement identity is invalid")
