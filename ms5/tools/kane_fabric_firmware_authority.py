#!/usr/bin/env python3
"""MS5 firmware authority and release-manifest contracts.

This module deliberately contains no private-key generation or signing code.
MS5-009 must activate a hardware-backed signer through a later accepted
provider-specific boundary.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping

from ms5.tools.common import ContractError, canonical_json_bytes, nonempty_text, sha256_text

AUTHORITY_STATE_FORMAT = "kane-fabric-firmware-authority-state"
AUTHORITY_STATE_VERSION = 1
MANIFEST_FORMAT = "kane-fabric-firmware-release-manifest"
MANIFEST_VERSION = 1

DEPLOYMENT_CLASS = "unprivileged-lxc-lxd-container"
ACCEPTANCE_GATE = "MS5-009"

FIXED_AUTHORITY_BOUNDARY = {
    "build_authority_is_signing_authority": False,
    "distribution_is_signing_authority": False,
    "edge_private_signing_key_present": False,
    "container_private_signing_key_file_present": False,
    "hardware_backed_signer_required_for_activation": True,
    "operator_presence_required_for_release_signing": True,
}


class FirmwareAuthorityContractError(ContractError):
    pass


def _uint(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise FirmwareAuthorityContractError(f"{label} must be a non-negative integer")
    return value


def _positive_uint(value: object, label: str) -> int:
    value = _uint(value, label)
    if value < 1:
        raise FirmwareAuthorityContractError(f"{label} must be greater than zero")
    return value


def build_authority_state(*, enabled_device_families: list[str]) -> dict[str, object]:
    families = sorted({nonempty_text(item, "device_family") for item in enabled_device_families})
    if not families:
        raise FirmwareAuthorityContractError("at least one device family must be enabled")
    return {
        "format": AUTHORITY_STATE_FORMAT,
        "version": AUTHORITY_STATE_VERSION,
        "role": "firmware-authority",
        "deployment_class": DEPLOYMENT_CLASS,
        "container_name": "firmware-authority",
        "network_identity": None,
        "enabled_device_families": families,
        "private_signing_key_created": False,
        "signing_enabled": False,
        "acceptance_gate": ACCEPTANCE_GATE,
        "authority_boundary": dict(FIXED_AUTHORITY_BOUNDARY),
    }


def validate_authority_state(value: Mapping[str, object]) -> None:
    expected_fields = {
        "format",
        "version",
        "role",
        "deployment_class",
        "container_name",
        "network_identity",
        "enabled_device_families",
        "private_signing_key_created",
        "signing_enabled",
        "acceptance_gate",
        "authority_boundary",
    }
    if set(value) != expected_fields:
        raise FirmwareAuthorityContractError("authority-state fields are invalid")
    if value["format"] != AUTHORITY_STATE_FORMAT or value["version"] != AUTHORITY_STATE_VERSION:
        raise FirmwareAuthorityContractError("authority-state format/version is unsupported")
    if value["role"] != "firmware-authority":
        raise FirmwareAuthorityContractError("authority role is invalid")
    if value["deployment_class"] != DEPLOYMENT_CLASS:
        raise FirmwareAuthorityContractError("deployment class is not the frozen reference class")
    if value["container_name"] != "firmware-authority":
        raise FirmwareAuthorityContractError("container name is not the frozen reference name")
    if value["network_identity"] is not None:
        raise FirmwareAuthorityContractError("network identity is not assigned in the architectural placeholder state")
    families = value["enabled_device_families"]
    if not isinstance(families, list) or not families:
        raise FirmwareAuthorityContractError("enabled_device_families must be a non-empty array")
    normalized = sorted({nonempty_text(item, "device_family") for item in families})
    if families != normalized:
        raise FirmwareAuthorityContractError("device families are not normalized")
    if value["private_signing_key_created"] is not False or value["signing_enabled"] is not False:
        raise FirmwareAuthorityContractError("placeholder authority must not contain or activate a private signing key")
    if value["acceptance_gate"] != ACCEPTANCE_GATE:
        raise FirmwareAuthorityContractError("authority acceptance gate must remain MS5-009")
    if value["authority_boundary"] != FIXED_AUTHORITY_BOUNDARY:
        raise FirmwareAuthorityContractError("authority boundary is not the fixed MS5 boundary")


def _manifest_body(
    *,
    device_family: str,
    target: str,
    release_version: str,
    release_sequence: int,
    firmware_name: str,
    firmware_sha256: str,
    firmware_byte_length: int,
    source_repository: str,
    source_commit: str,
    toolchain_record: str,
    toolchain_record_sha256: str,
    build_identity: str,
    rollback_floor_sequence: int,
    recovery_compatible: bool,
) -> dict[str, object]:
    release_sequence = _positive_uint(release_sequence, "release_sequence")
    rollback_floor_sequence = _uint(rollback_floor_sequence, "rollback_floor_sequence")
    if rollback_floor_sequence > release_sequence:
        raise FirmwareAuthorityContractError("rollback floor cannot exceed release sequence")
    if not isinstance(recovery_compatible, bool):
        raise FirmwareAuthorityContractError("recovery_compatible must be boolean")
    source_commit = nonempty_text(source_commit, "source_commit")
    if len(source_commit) != 40 or any(ch not in "0123456789abcdef" for ch in source_commit):
        raise FirmwareAuthorityContractError("source_commit must be a lowercase 40-character Git commit id")
    return {
        "release": {
            "device_family": nonempty_text(device_family, "device_family"),
            "target": nonempty_text(target, "target"),
            "version": nonempty_text(release_version, "release_version"),
            "sequence": release_sequence,
        },
        "firmware": {
            "name": nonempty_text(firmware_name, "firmware_name"),
            "sha256": sha256_text(firmware_sha256, "firmware_sha256"),
            "byte_length": _positive_uint(firmware_byte_length, "firmware_byte_length"),
        },
        "source": {
            "repository": nonempty_text(source_repository, "source_repository"),
            "commit": source_commit,
        },
        "build": {
            "toolchain_record": nonempty_text(toolchain_record, "toolchain_record"),
            "toolchain_record_sha256": sha256_text(toolchain_record_sha256, "toolchain_record_sha256"),
            "build_identity": nonempty_text(build_identity, "build_identity"),
        },
        "recovery": {
            "rollback_floor_sequence": rollback_floor_sequence,
            "recovery_compatible": recovery_compatible,
        },
    }


def build_release_manifest(**kwargs: object) -> dict[str, object]:
    body = _manifest_body(**kwargs)  # type: ignore[arg-type]
    return {
        "format": MANIFEST_FORMAT,
        "version": MANIFEST_VERSION,
        **body,
        "manifest_sha256": hashlib.sha256(canonical_json_bytes(body)).hexdigest(),
    }


def validate_release_manifest(value: Mapping[str, object]) -> None:
    expected_fields = {
        "format",
        "version",
        "release",
        "firmware",
        "source",
        "build",
        "recovery",
        "manifest_sha256",
    }
    if set(value) != expected_fields:
        raise FirmwareAuthorityContractError("release-manifest fields are invalid")
    if value["format"] != MANIFEST_FORMAT or value["version"] != MANIFEST_VERSION:
        raise FirmwareAuthorityContractError("release-manifest format/version is unsupported")
    for name in ("release", "firmware", "source", "build", "recovery"):
        if not isinstance(value[name], Mapping):
            raise FirmwareAuthorityContractError(f"{name} must be an object")

    release = value["release"]
    firmware = value["firmware"]
    source = value["source"]
    build = value["build"]
    recovery = value["recovery"]

    if set(release) != {"device_family", "target", "version", "sequence"}:
        raise FirmwareAuthorityContractError("release fields are invalid")
    if set(firmware) != {"name", "sha256", "byte_length"}:
        raise FirmwareAuthorityContractError("firmware fields are invalid")
    if set(source) != {"repository", "commit"}:
        raise FirmwareAuthorityContractError("source fields are invalid")
    if set(build) != {"toolchain_record", "toolchain_record_sha256", "build_identity"}:
        raise FirmwareAuthorityContractError("build fields are invalid")
    if set(recovery) != {"rollback_floor_sequence", "recovery_compatible"}:
        raise FirmwareAuthorityContractError("recovery fields are invalid")

    body = _manifest_body(
        device_family=release["device_family"],
        target=release["target"],
        release_version=release["version"],
        release_sequence=release["sequence"],
        firmware_name=firmware["name"],
        firmware_sha256=firmware["sha256"],
        firmware_byte_length=firmware["byte_length"],
        source_repository=source["repository"],
        source_commit=source["commit"],
        toolchain_record=build["toolchain_record"],
        toolchain_record_sha256=build["toolchain_record_sha256"],
        build_identity=build["build_identity"],
        rollback_floor_sequence=recovery["rollback_floor_sequence"],
        recovery_compatible=recovery["recovery_compatible"],
    )
    for key in ("release", "firmware", "source", "build", "recovery"):
        if value[key] != body[key]:
            raise FirmwareAuthorityContractError(f"{key} is not normalized")
    expected = hashlib.sha256(canonical_json_bytes(body)).hexdigest()
    if value["manifest_sha256"] != expected:
        raise FirmwareAuthorityContractError("manifest identity is invalid")
