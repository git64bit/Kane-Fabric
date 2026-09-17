#!/usr/bin/env python3
"""Executable mirror of the frozen Kane Fabric ESP32-S3 v1 firmware role.

Normative prose remains in docs/MILESTONE_5_DESIGN.md. This module makes the
first-release responsibility boundary machine-checkable so later implementation
work cannot silently turn candidate or administrative capabilities into firmware
requirements.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence

from ms5.tools.common import ContractError, canonical_json_bytes

FORMAT = "kane-fabric-esp32-firmware-v1-role"
VERSION = 1

CORE_RUNTIME_REQUIRED = (
    "firmware-build-identity-diagnostics",
    "deployment-provided-ip-network-client-attachment",
    "read-only-artifact-storage-mount",
    "active-inventory-verification-before-serving",
    "plain-http-artifact-serving",
    "exact-closed-byte-range-serving",
    "serial-operational-diagnostics",
    "fail-closed-on-invalid-active-generation",
    "continue-last-valid-generation-without-management-connectivity",
)

LIFECYCLE_REQUIRED = (
    "firmware-source-tracked-in-repository",
    "exact-pinned-toolchain-build",
    "identifiable-firmware-artifact",
    "reproducible-flash-and-reprovision",
    "firmware-authenticity-update-recovery-proof",
    "physical-replacement-preserves-logical-identity",
    "device-acceptance-evidence",
)

CANDIDATE_ONLY = (
    "wireguard-management-transport",
    "managed-artifact-synchronization",
    "automatic-update-transport",
    "external-secure-element",
    "remote-fleet-telemetry",
    "richer-network-discovery",
)

EXPLICITLY_NOT_V1_RESPONSIBILITIES = (
    "browser-https-termination",
    "browser-certificate-lifecycle",
    "browser-authentication",
    "esp32-hosted-browser-access-point",
    "fabric-geographic-authority",
    "fabric-release-signing-authority",
    "county-database-mutation",
    "official-source-acquisition",
    "candidate-promotion",
    "county-wide-substrate-replication",
    "county-web-map-hosting",
    "category-and-publication-contract-administration",
    "browser-rendering-or-gis-processing",
    "application-membership-or-person-identity",
    "fleet-orchestration",
)

FIXED_BOUNDARY = {
    "browser_tls_on_edge": False,
    "browser_certificate_lifecycle_on_edge": False,
    "esp32_hosted_ap_required": False,
    "wireguard_required_for_v1": False,
    "management_connectivity_required_to_serve_activated_data": False,
    "fabric_geographic_authority_on_edge": False,
    "fabric_release_signing_authority_on_edge": False,
    "county_database_mutation_on_edge": False,
    "county_wide_substrate_required_on_edge": False,
    "county_web_map_on_edge": False,
    "category_contract_administration_on_edge": False,
    "edge_publication_scope": "bounded-participant-publication",
}

ACCEPTANCE_LAYERS = {
    "repository": (
        "role-contract-and-source-tracked",
        "host-contract-tests-pass",
        "pinned-toolchain-selection-recorded",
    ),
    "device": (
        "pinned-esp-idf-build-pass",
        "flash-and-boot-pass",
        "serial-firmware-identity-visible",
        "read-only-storage-mount-pass",
        "active-inventory-verification-pass",
        "plain-http-get-and-range-pass",
        "invalid-generation-fails-closed",
    ),
    "ms5_integration": (
        "wiregate-focused-participant-publication-integration-pass",
        "management-loss-preserves-local-serving",
        "firmware-update-rollback-recovery-pass",
        "physical-replacement-identity-preservation-pass",
        "constrained-resource-coexistence-pass",
    ),
}


class FirmwareV1RoleContractError(ContractError):
    pass


def _normalized_sequence(value: object, label: str) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise FirmwareV1RoleContractError(f"{label} must be an array")
    items = list(value)
    if not all(isinstance(item, str) and item for item in items):
        raise FirmwareV1RoleContractError(f"{label} entries must be non-empty strings")
    if len(items) != len(set(items)):
        raise FirmwareV1RoleContractError(f"{label} entries must be unique")
    return items


def _body() -> dict[str, object]:
    return {
        "core_runtime_required": list(CORE_RUNTIME_REQUIRED),
        "lifecycle_required": list(LIFECYCLE_REQUIRED),
        "candidate_only": list(CANDIDATE_ONLY),
        "explicitly_not_v1_responsibilities": list(EXPLICITLY_NOT_V1_RESPONSIBILITIES),
        "fixed_boundary": dict(FIXED_BOUNDARY),
        "acceptance_layers": {
            key: list(values) for key, values in ACCEPTANCE_LAYERS.items()
        },
    }


def build_firmware_v1_role() -> dict[str, object]:
    body = _body()
    return {
        "format": FORMAT,
        "version": VERSION,
        **body,
        "role_sha256": hashlib.sha256(canonical_json_bytes(body)).hexdigest(),
    }


def validate_firmware_v1_role(value: Mapping[str, object]) -> None:
    expected_keys = {
        "format",
        "version",
        "core_runtime_required",
        "lifecycle_required",
        "candidate_only",
        "explicitly_not_v1_responsibilities",
        "fixed_boundary",
        "acceptance_layers",
        "role_sha256",
    }
    if set(value) != expected_keys:
        raise FirmwareV1RoleContractError("firmware-v1 role fields are invalid")
    if value["format"] != FORMAT or value["version"] != VERSION:
        raise FirmwareV1RoleContractError("firmware-v1 role format/version is unsupported")

    expected = _body()

    for key in (
        "core_runtime_required",
        "lifecycle_required",
        "candidate_only",
        "explicitly_not_v1_responsibilities",
    ):
        actual = _normalized_sequence(value[key], key)
        if actual != expected[key]:
            raise FirmwareV1RoleContractError(f"{key} is not the frozen v1 responsibility set")

    boundary = value["fixed_boundary"]
    if not isinstance(boundary, Mapping) or dict(boundary) != FIXED_BOUNDARY:
        raise FirmwareV1RoleContractError("fixed boundary is not the frozen v1 boundary")

    layers = value["acceptance_layers"]
    if not isinstance(layers, Mapping) or set(layers) != set(ACCEPTANCE_LAYERS):
        raise FirmwareV1RoleContractError("acceptance layers are invalid")
    normalized_layers = {
        key: _normalized_sequence(layers[key], f"acceptance_layers.{key}")
        for key in ACCEPTANCE_LAYERS
    }
    if normalized_layers != expected["acceptance_layers"]:
        raise FirmwareV1RoleContractError("acceptance layers are not the frozen v1 contract")

    required = set(CORE_RUNTIME_REQUIRED) | set(LIFECYCLE_REQUIRED)
    candidate = set(CANDIDATE_ONLY)
    excluded = set(EXPLICITLY_NOT_V1_RESPONSIBILITIES)
    if required & candidate or required & excluded or candidate & excluded:
        raise FirmwareV1RoleContractError("firmware-v1 responsibility classes overlap")

    expected_hash = hashlib.sha256(canonical_json_bytes(expected)).hexdigest()
    if value["role_sha256"] != expected_hash:
        raise FirmwareV1RoleContractError("firmware-v1 role identity is invalid")
