#!/usr/bin/env python3
"""MS5-009 firmware authenticity, update, rollback, and recovery contract."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence

from ms5.tools.common import ContractError, canonical_json_bytes, nonempty_text

FORMAT = "kane-fabric-ms5-firmware-lifecycle"
VERSION = 1
WORK_ITEM = "MS5-009"
STATUS = "contract-active-signing-inert"

REFERENCE_PLATFORM = {
    "device_family": "esp32-s3",
    "target": "esp32s3",
    "flash_size_bytes": 16 * 1024 * 1024,
    "current_partition_table": "ms5/esp32_reference/partitions.fabric-4m.csv",
    "current_app_model": "factory-only",
    "partition_migration_required": True,
}

AUTHORITY_BOUNDARY = {
    "release_manifest_format": "kane-fabric-firmware-release-manifest",
    "authorization_target": "manifest_sha256",
    "signer_provider_status": "selection-pending",
    "signature_envelope_status": "not-frozen",
    "hardware_backed_non_exportable_signer_required": True,
    "operator_presence_required_for_release_signing": True,
    "authority_container_private_key_file_allowed": False,
    "edge_private_release_signing_key_allowed": False,
    "build_authority_is_signing_authority": False,
    "distribution_is_signing_authority": False,
    "signing_activation_status": "not-activated",
}

UPDATE_BOUNDARY = {
    "transport_agnostic": True,
    "management_transport_required": False,
    "authorization_required_before_install": True,
    "firmware_digest_match_required": True,
    "release_sequence_monotonic": True,
    "rollback_floor_enforced_by_normal_update_path": True,
    "trial_boot_required": True,
    "confirm_only_after_health_check": True,
    "previous_valid_image_retained_until_confirmation": True,
    "failed_trial_must_rollback": True,
    "fabric_partition_rewritten_by_firmware_update": False,
    "nvs_erased_by_normal_firmware_update": False,
    "management_loss_invalidates_activated_publication": False,
    "irreversible_efuse_required": False,
}

PARTITION_PLAN = {
    "preserve": [
        {"name": "nvs", "offset": 0x9000, "size": 24 * 1024},
        {"name": "phy_init", "offset": 0xF000, "size": 4 * 1024},
        {"name": "factory", "offset": 0x10000, "size": 1 * 1024 * 1024},
        {"name": "fabric", "offset": 0x110000, "size": 4 * 1024 * 1024},
    ],
    "add": [
        {"name": "otadata", "type": "data", "subtype": "ota", "offset": 0x510000, "size": 8 * 1024},
        {"name": "ota_0", "type": "app", "subtype": "ota_0", "offset": 0x520000, "size": 1 * 1024 * 1024},
        {"name": "ota_1", "type": "app", "subtype": "ota_1", "offset": 0x620000, "size": 1 * 1024 * 1024},
    ],
    "first_unused_offset": 0x720000,
}

REQUIRED_EVIDENCE = (
    "canonical_release_manifest_for_exact_firmware",
    "hardware_backed_release_authorization",
    "device_public_verification_material_only",
    "authorized_update_acceptance",
    "firmware_digest_mismatch_rejection",
    "unauthorized_manifest_rejection",
    "lower_sequence_normal_update_rejection",
    "trial_boot_before_confirmation",
    "health_confirmation_of_new_image",
    "automatic_rollback_after_failed_trial",
    "recovery_from_interrupted_update",
    "recovery_when_management_transport_unavailable",
    "fabric_partition_preserved_across_firmware_update",
    "nvs_provisioning_preserved_across_normal_update",
    "last_valid_participant_publication_survives_update_failure",
    "authority_container_rebuild_without_private_key_clone",
)


class FirmwareLifecycleContractError(ContractError):
    pass


def _normalized_unique_strings(value: object, label: str) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise FirmwareLifecycleContractError(f"{label} must be an array")
    items = [nonempty_text(item, label) for item in value]
    if len(items) != len(set(items)):
        raise FirmwareLifecycleContractError(f"{label} entries must be unique")
    return items


def _partition_entries(value: object, label: str) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise FirmwareLifecycleContractError(f"{label} must be an array")
    result: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise FirmwareLifecycleContractError(f"{label} entries must be objects")
        entry = dict(item)
        required = {"name", "offset", "size"}
        optional = {"type", "subtype"}
        if not required.issubset(entry) or not set(entry).issubset(required | optional):
            raise FirmwareLifecycleContractError(f"{label} partition fields are invalid")
        if (
            not isinstance(entry["offset"], int)
            or not isinstance(entry["size"], int)
            or entry["offset"] < 0
            or entry["size"] <= 0
        ):
            raise FirmwareLifecycleContractError(f"{label} partition bounds are invalid")
        result.append(entry)
    return result


def _validate_partition_plan(plan: Mapping[str, object]) -> None:
    if set(plan) != {"preserve", "add", "first_unused_offset"}:
        raise FirmwareLifecycleContractError("partition plan fields are invalid")
    preserve = _partition_entries(plan["preserve"], "partition_plan.preserve")
    additions = _partition_entries(plan["add"], "partition_plan.add")
    if (
        preserve != PARTITION_PLAN["preserve"]
        or additions != PARTITION_PLAN["add"]
        or plan["first_unused_offset"] != PARTITION_PLAN["first_unused_offset"]
    ):
        raise FirmwareLifecycleContractError("partition migration plan drifted")
    intervals = sorted(
        (item["offset"], item["offset"] + item["size"], item["name"])
        for item in preserve + additions
    )
    if any(end > REFERENCE_PLATFORM["flash_size_bytes"] for _, end, _ in intervals):
        raise FirmwareLifecycleContractError("partition exceeds reference flash")
    for left, right in zip(intervals, intervals[1:]):
        if left[1] > right[0]:
            raise FirmwareLifecycleContractError(
                f"partitions overlap: {left[2]} and {right[2]}"
            )
    for item in additions:
        if item.get("type") == "app" and item["offset"] % 0x10000:
            raise FirmwareLifecycleContractError(
                "OTA application partition is not 64KiB aligned"
            )


def build_firmware_lifecycle_contract() -> dict[str, object]:
    body = {
        "work_item": WORK_ITEM,
        "status": STATUS,
        "reference_platform": dict(REFERENCE_PLATFORM),
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
        "update_boundary": dict(UPDATE_BOUNDARY),
        "partition_plan": {
            "preserve": [dict(item) for item in PARTITION_PLAN["preserve"]],
            "add": [dict(item) for item in PARTITION_PLAN["add"]],
            "first_unused_offset": PARTITION_PLAN["first_unused_offset"],
        },
        "required_evidence": list(REQUIRED_EVIDENCE),
    }
    return {
        "format": FORMAT,
        "version": VERSION,
        **body,
        "contract_sha256": hashlib.sha256(canonical_json_bytes(body)).hexdigest(),
    }


def validate_firmware_lifecycle_contract(value: Mapping[str, object]) -> None:
    expected_fields = {
        "format", "version", "work_item", "status", "reference_platform",
        "authority_boundary", "update_boundary", "partition_plan",
        "required_evidence", "contract_sha256",
    }
    if set(value) != expected_fields:
        raise FirmwareLifecycleContractError("MS5-009 contract fields are invalid")
    if value["format"] != FORMAT or value["version"] != VERSION:
        raise FirmwareLifecycleContractError("MS5-009 contract format/version is unsupported")
    if value["work_item"] != WORK_ITEM or value["status"] != STATUS:
        raise FirmwareLifecycleContractError("MS5-009 work item/status is invalid")
    if value["reference_platform"] != REFERENCE_PLATFORM:
        raise FirmwareLifecycleContractError("MS5-009 reference platform drifted")
    if value["authority_boundary"] != AUTHORITY_BOUNDARY:
        raise FirmwareLifecycleContractError("MS5-009 authority boundary drifted")
    if value["update_boundary"] != UPDATE_BOUNDARY:
        raise FirmwareLifecycleContractError("MS5-009 update boundary drifted")
    if not isinstance(value["partition_plan"], Mapping):
        raise FirmwareLifecycleContractError("MS5-009 partition plan must be an object")
    _validate_partition_plan(value["partition_plan"])
    evidence = _normalized_unique_strings(value["required_evidence"], "required_evidence")
    if evidence != list(REQUIRED_EVIDENCE):
        raise FirmwareLifecycleContractError("MS5-009 evidence set drifted")
    body = {
        "work_item": value["work_item"],
        "status": value["status"],
        "reference_platform": value["reference_platform"],
        "authority_boundary": value["authority_boundary"],
        "update_boundary": value["update_boundary"],
        "partition_plan": value["partition_plan"],
        "required_evidence": evidence,
    }
    expected_hash = hashlib.sha256(canonical_json_bytes(body)).hexdigest()
    if value["contract_sha256"] != expected_hash:
        raise FirmwareLifecycleContractError("MS5-009 contract identity is invalid")
