#!/usr/bin/env python3
"""MS5-005 ESP-IDF/toolchain selection contract."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from ms5.tools.common import ContractError

FORMAT = "kane-fabric-ms5-toolchain-selection"
VERSION = 1
TARGET = "esp32s3"
REFERENCE_BUILD_HOST = {
    "os_family": "linux",
    "architecture": "x86_64",
    "profile": "linux-amd64",
}

EXPECTED_SDK = {
    "key": "esp-idf",
    "version": "6.0.3",
    "tag": "v6.0.3",
    "source_commit": "76f5dedd9950a3012fee8fb7d5586df21fc67802",
    "source_archive": "esp-idf-v6.0.3.zip",
    "source_sha256": "748b12484402d8a1cb58ba68b7545d2a1f96d36820ab0145e0332c8348ba5ab7",
    "source_uri": "https://github.com/espressif/esp-idf/releases/download/v6.0.3/esp-idf-v6.0.3.zip",
    "tools_manifest_git_blob_sha": "2cf625c4bdd3b8b9baa6c1566ff94c802ddbe0fd",
    "status": "selected-not-vendored",
}

EXPECTED_COMPILER = {
    "key": "xtensa-esp-elf",
    "version": "15.2.0_20251204",
    "archive": "xtensa-esp-elf-15.2.0_20251204-x86_64-linux-gnu.tar.xz",
    "source_sha256": "3d50f5cd5f173acfd524e07c1cd69bc99585731a415ca2e5bce879997fe602b8",
    "source_uri": "https://github.com/espressif/crosstool-NG/releases/download/esp-15.2.0_20251204/xtensa-esp-elf-15.2.0_20251204-x86_64-linux-gnu.tar.xz",
    "license": "GPL-3.0-with-GCC-exception",
    "status": "selected-not-vendored",
}

LICENSE_BOUNDARY = {
    "esp_idf_core_license": "Apache-2.0",
    "compiler_license": "GPL-3.0-with-GCC-exception",
    "kane_fabric_root_license_unchanged": True,
    "exact_release_third_party_notices_required": True,
}

DEPENDENCY_BOUNDARY = {
    "wireguard_status": "candidate-not-retained",
    "wireguard_selection_gate": "MS5-008",
    "package_manager_resolution_at_release": False,
}

OFFLINE_REPRODUCTION = {
    "esp_idf_submodule_complete_archive_required": True,
    "release_asset_mirror_required": True,
    "compiler_archive_mirror_required": True,
    "exact_python_build_environment_lock_required": True,
    "no_live_network_resolution_at_release": True,
    "large_archives_outside_git": True,
    "metadata_and_hashes_in_git": True,
}


class ToolchainContractError(ContractError):
    pass


def load_selection(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError) as exc:
        raise ToolchainContractError(f"cannot load toolchain selection: {exc}") from exc
    if not isinstance(value, dict):
        raise ToolchainContractError("toolchain selection must be an object")
    return value


def _require_exact(value: object, expected: object, label: str) -> None:
    if value != expected:
        raise ToolchainContractError(f"{label} does not match the accepted MS5-005 selection")


def validate_toolchain_selection(value: Mapping[str, object]) -> None:
    expected_keys = {
        "format",
        "schema_version",
        "target",
        "reference_build_host",
        "sdk",
        "compiler",
        "license_boundary",
        "dependency_boundary",
        "offline_reproduction",
    }
    if set(value) != expected_keys:
        raise ToolchainContractError("toolchain selection fields are invalid")
    if value["format"] != FORMAT or value["schema_version"] != VERSION:
        raise ToolchainContractError("toolchain selection format/version is unsupported")
    if value["target"] != TARGET:
        raise ToolchainContractError("reference firmware target must be esp32s3")

    _require_exact(value["reference_build_host"], REFERENCE_BUILD_HOST, "reference build host")
    _require_exact(value["sdk"], EXPECTED_SDK, "ESP-IDF pin")
    _require_exact(value["compiler"], EXPECTED_COMPILER, "Xtensa compiler pin")
    _require_exact(value["license_boundary"], LICENSE_BOUNDARY, "license boundary")
    _require_exact(value["dependency_boundary"], DEPENDENCY_BOUNDARY, "dependency boundary")
    _require_exact(value["offline_reproduction"], OFFLINE_REPRODUCTION, "offline reproduction policy")


def _entry(manifest: Mapping[str, object], key: str) -> Mapping[str, object]:
    entries = manifest.get("third_party")
    if not isinstance(entries, list):
        raise ToolchainContractError("third-party manifest inventory is invalid")
    matches = [item for item in entries if isinstance(item, Mapping) and item.get("key") == key]
    if len(matches) != 1:
        raise ToolchainContractError(f"third-party manifest must contain exactly one {key} entry")
    return matches[0]


def validate_manifest_binding(
    selection: Mapping[str, object], manifest: Mapping[str, object]
) -> None:
    validate_toolchain_selection(selection)

    sdk_entry = _entry(manifest, "esp-idf")
    sdk_pin = sdk_entry.get("pin")
    if not isinstance(sdk_pin, Mapping):
        raise ToolchainContractError("esp-idf manifest pin is invalid")
    for field in (
        "version",
        "tag",
        "source_commit",
        "source_archive",
        "source_sha256",
        "source_uri",
        "tools_manifest_git_blob_sha",
        "status",
    ):
        if sdk_pin.get(field) != EXPECTED_SDK[field]:
            raise ToolchainContractError(f"esp-idf manifest pin drifted at {field}")
    if sdk_pin.get("reference_target") != TARGET:
        raise ToolchainContractError("esp-idf manifest target must be esp32s3")
    if sdk_pin.get("reference_build_host") != REFERENCE_BUILD_HOST["profile"]:
        raise ToolchainContractError("esp-idf manifest build-host profile drifted")

    compiler_entry = _entry(manifest, "xtensa-esp-elf")
    compiler_pin = compiler_entry.get("pin")
    if not isinstance(compiler_pin, Mapping):
        raise ToolchainContractError("xtensa-esp-elf manifest pin is invalid")
    for field in ("version", "archive", "source_sha256", "source_uri", "status"):
        if compiler_pin.get(field) != EXPECTED_COMPILER[field]:
            raise ToolchainContractError(f"xtensa-esp-elf manifest pin drifted at {field}")
    if compiler_pin.get("reference_build_host") != REFERENCE_BUILD_HOST["profile"]:
        raise ToolchainContractError("compiler manifest build-host profile drifted")

    entries = manifest.get("third_party")
    assert isinstance(entries, list)
    retained_wireguard = [
        item
        for item in entries
        if isinstance(item, Mapping) and "wireguard" in str(item.get("key", "")).lower()
    ]
    if retained_wireguard:
        raise ToolchainContractError(
            "WireGuard implementation must remain unretained until the MS5-008 runtime proof"
        )
