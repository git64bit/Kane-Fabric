#!/usr/bin/env python3
"""MS5-008 management-transport candidate/evaluation contract."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from ms5.tools.common import ContractError

FORMAT = "kane-fabric-ms5-management-transport-candidate"
VERSION = 1
WORK_ITEM = "MS5-008"
STATUS = "candidate-evaluation-only-not-retained"
TRANSPORT = "wireguard"
TARGET = "esp32s3"

REFERENCE_SDK = {
    "name": "esp-idf",
    "version": "6.0.3",
    "tag": "v6.0.3",
    "source_commit": "76f5dedd9950a3012fee8fb7d5586df21fc67802",
}

EXPECTED_CANDIDATE = {
    "implementation": "esphome-libs/wireguard",
    "repository": "https://github.com/esphome-libs/wireguard",
    "component": "esphome/wireguard",
    "version": "0.4.6",
    "tag": "v0.4.6",
    "source_commit": "cddaa4eab4e633847bf846723ac0449a34c3d2f7",
    "release_published": "2026-08-17",
    "release_immutable": True,
    "license": "BSD-3-Clause",
    "declared_dependency": {
        "component": "esphome/libsodium",
        "constraint": "^1.10021.1",
    },
    "evaluation_dependency_pin": {
        "implementation": "esphome-libs/libsodium",
        "repository": "https://github.com/esphome-libs/libsodium",
        "component": "esphome/libsodium",
        "version": "1.10021.11",
        "tag": "1.10021.11",
        "source_commit": "40c22448d6e8f42be56c45f739b52a5c8d21c8ca",
        "release_asset": "libsodium-1.10021.11.tar.gz",
        "source_sha256": "72696259f15278f146b700854798f639aa5ab193e0068f2f1f56d6d3cbe9692f",
        "release_immutable": False,
        "license": "MIT",
    },
}

EXPECTED_BOUNDARIES = {
    "browser_path_prerequisite": False,
    "firmware_v1_requirement": False,
    "retained_dependency": False,
    "third_party_manifest_entry_allowed_before_retain_decision": False,
    "live_package_resolution_allowed_during_evaluation": False,
    "participant_router_administration_required": False,
    "inbound_port_forwarding_required": False,
    "dhcp_reservation_required": False,
    "static_participant_lan_address_required": False,
    "management_identity_is_fabric_identity": False,
    "transport_locator_is_fabric_identity": False,
    "wireguard_key_is_fabric_identity": False,
}

REQUIRED_EVIDENCE = (
    "exact_pinned_esp32s3_build",
    "outbound_transport_from_ordinary_participant_nat",
    "no_inbound_port_forwarding",
    "no_participant_router_reservation",
    "authenticated_wireguard_handshake_to_controlled_hub",
    "routed_management_traffic",
    "persistent_keepalive_nat_behavior",
    "wifi_interruption_and_reconnect",
    "repeated_disconnect_reconnect",
    "flash_cost",
    "ram_cost",
    "task_cost",
    "socket_cost",
    "cpu_cost",
    "coexistence_with_plain_http_artifact_serving",
    "coexistence_with_storage_operations",
    "coexistence_with_update_operations",
    "management_loss_does_not_invalidate_activated_publication",
)

EXPECTED_DECISION = {
    "allowed_results": ["retain", "reject", "defer"],
    "state_before_runtime_evidence": "defer",
    "retain_requires_all_required_evidence": True,
    "retain_requires_dependency_policy_followup": True,
}


class ManagementTransportContractError(ContractError):
    pass


def load_candidate(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError) as exc:
        raise ManagementTransportContractError(
            f"cannot load MS5-008 candidate record: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise ManagementTransportContractError("MS5-008 candidate record must be an object")
    return value


def _require_exact(value: object, expected: object, label: str) -> None:
    if value != expected:
        raise ManagementTransportContractError(f"{label} drifted from the MS5-008 evaluation contract")


def validate_candidate(value: Mapping[str, object]) -> None:
    expected_keys = {
        "format",
        "schema_version",
        "work_item",
        "status",
        "transport",
        "observed_date",
        "reference_target",
        "reference_sdk",
        "candidate",
        "boundaries",
        "required_evidence",
        "decision",
    }
    if set(value) != expected_keys:
        raise ManagementTransportContractError("MS5-008 candidate fields are invalid")
    if value["format"] != FORMAT or value["schema_version"] != VERSION:
        raise ManagementTransportContractError("MS5-008 candidate format/version is unsupported")
    if value["work_item"] != WORK_ITEM:
        raise ManagementTransportContractError("candidate must belong to MS5-008")
    if value["status"] != STATUS:
        raise ManagementTransportContractError("WireGuard must remain evaluation-only and unretained")
    if value["transport"] != TRANSPORT:
        raise ManagementTransportContractError("MS5-008 candidate transport must be WireGuard")
    if value["reference_target"] != TARGET:
        raise ManagementTransportContractError("MS5-008 reference target must be esp32s3")

    _require_exact(value["reference_sdk"], REFERENCE_SDK, "reference ESP-IDF pin")
    _require_exact(value["candidate"], EXPECTED_CANDIDATE, "WireGuard candidate")
    _require_exact(value["boundaries"], EXPECTED_BOUNDARIES, "MS5-008 architecture boundaries")
    _require_exact(tuple(value["required_evidence"]), REQUIRED_EVIDENCE, "required runtime evidence")
    _require_exact(value["decision"], EXPECTED_DECISION, "retain/reject/defer decision contract")


def validate_repository_binding(
    candidate: Mapping[str, object],
    toolchain_selection: Mapping[str, object],
    manifest: Mapping[str, object],
) -> None:
    validate_candidate(candidate)

    if toolchain_selection.get("target") != TARGET:
        raise ManagementTransportContractError("toolchain target drifted from esp32s3")

    sdk = toolchain_selection.get("sdk")
    if not isinstance(sdk, Mapping):
        raise ManagementTransportContractError("toolchain ESP-IDF selection is invalid")
    for field, expected in (
        ("version", REFERENCE_SDK["version"]),
        ("tag", REFERENCE_SDK["tag"]),
        ("source_commit", REFERENCE_SDK["source_commit"]),
    ):
        if sdk.get(field) != expected:
            raise ManagementTransportContractError(
                f"MS5-008 reference ESP-IDF pin drifted at {field}"
            )

    dependency_boundary = toolchain_selection.get("dependency_boundary")
    if not isinstance(dependency_boundary, Mapping):
        raise ManagementTransportContractError("toolchain dependency boundary is invalid")
    if dependency_boundary.get("wireguard_status") != "candidate-not-retained":
        raise ManagementTransportContractError("WireGuard was retained before MS5-008 decision")
    if dependency_boundary.get("wireguard_selection_gate") != WORK_ITEM:
        raise ManagementTransportContractError("WireGuard selection gate must remain MS5-008")

    entries = manifest.get("third_party")
    if not isinstance(entries, list):
        raise ManagementTransportContractError("third-party manifest inventory is invalid")

    wireguard_entries = [
        item
        for item in entries
        if isinstance(item, Mapping)
        and "wireguard" in str(item.get("key", "")).lower()
    ]
    if wireguard_entries:
        raise ManagementTransportContractError(
            "third_party/manifest.json must not retain WireGuard before a retain decision"
        )
