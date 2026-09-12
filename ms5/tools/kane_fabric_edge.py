#!/usr/bin/env python3
"""MS5 physical-edge trust and replaceability contract.

The descriptor binds one replaceable physical instance to an already-defined
MS4 logical placement. Physical metadata may change without changing the
logical placement identity.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping

from ms5.tools.common import ContractError, canonical_json_bytes, nonempty_text, sha256_text

FORMAT = "kane-fabric-physical-edge-instance"
VERSION = 1

TRUST_BOUNDARY = {
    "accepted_geography_mutation": False,
    "candidate_promotion": False,
    "fabric_release_signing": False,
    "credential_issuing": False,
    "peer_authority": False,
    "physical_compromise_scope": "local-recoverable",
}

SECURITY_POSTURE = {
    "irreversible_efuse_required": False,
    "secure_element_required": False,
    "authoritative_private_keys_on_edge": False,
}

PHYSICAL_KEYS = {
    "platform_class",
    "instance_label",
    "storage_backend",
    "browser_transport",
    "management_transport",
}


class EdgeContractError(ContractError):
    pass


def _physical(value: Mapping[str, object]) -> dict[str, str]:
    if set(value) != PHYSICAL_KEYS:
        raise EdgeContractError("physical metadata keys are invalid")
    return {key: nonempty_text(value[key], f"physical.{key}") for key in sorted(PHYSICAL_KEYS)}


def build_edge_instance(
    *,
    logical_placement_sha256: str,
    platform_class: str,
    instance_label: str,
    storage_backend: str,
    browser_transport: str,
    management_transport: str,
) -> dict[str, object]:
    logical = {
        "logical_placement_sha256": sha256_text(
            logical_placement_sha256, "logical_placement_sha256"
        )
    }
    physical = _physical(
        {
            "platform_class": platform_class,
            "instance_label": instance_label,
            "storage_backend": storage_backend,
            "browser_transport": browser_transport,
            "management_transport": management_transport,
        }
    )
    body = {
        "logical": logical,
        "physical": physical,
        "trust_boundary": dict(TRUST_BOUNDARY),
        "security_posture": dict(SECURITY_POSTURE),
    }
    return {
        "format": FORMAT,
        "version": VERSION,
        **body,
        "physical_instance_sha256": hashlib.sha256(canonical_json_bytes(body)).hexdigest(),
    }


def validate_edge_instance(value: Mapping[str, object]) -> None:
    expected_keys = {
        "format",
        "version",
        "logical",
        "physical",
        "trust_boundary",
        "security_posture",
        "physical_instance_sha256",
    }
    if set(value) != expected_keys:
        raise EdgeContractError("edge instance keys are invalid")
    if value["format"] != FORMAT or value["version"] != VERSION:
        raise EdgeContractError("edge instance format/version is unsupported")

    logical = value["logical"]
    physical = value["physical"]
    if not isinstance(logical, Mapping) or set(logical) != {"logical_placement_sha256"}:
        raise EdgeContractError("logical section is invalid")
    normalized_logical = {
        "logical_placement_sha256": sha256_text(
            logical["logical_placement_sha256"], "logical.logical_placement_sha256"
        )
    }

    if not isinstance(physical, Mapping):
        raise EdgeContractError("physical section must be an object")
    normalized_physical = _physical(physical)
    if dict(physical) != normalized_physical:
        raise EdgeContractError("physical section is not normalized")

    if value["trust_boundary"] != TRUST_BOUNDARY:
        raise EdgeContractError("trust boundary is not the fixed MS5 trust boundary")
    if value["security_posture"] != SECURITY_POSTURE:
        raise EdgeContractError("security posture is not the fixed MS5 security posture")

    body = {
        "logical": normalized_logical,
        "physical": normalized_physical,
        "trust_boundary": dict(TRUST_BOUNDARY),
        "security_posture": dict(SECURITY_POSTURE),
    }
    expected = hashlib.sha256(canonical_json_bytes(body)).hexdigest()
    if value["physical_instance_sha256"] != expected:
        raise EdgeContractError("physical instance identity is invalid")
