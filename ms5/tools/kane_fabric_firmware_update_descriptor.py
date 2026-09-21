#!/usr/bin/env python3
"""MS5-009 normalized ESP32 firmware update descriptor."""

from __future__ import annotations

from collections.abc import Mapping

from ms5.tools.common import ContractError, sha256_text
from ms5.tools.kane_fabric_firmware_authority import validate_release_manifest
from ms5.tools.kane_fabric_firmware_authorization import (
    ALGORITHM,
    SIGNATURE_ENCODING,
    validate_authorization_envelope,
)

FORMAT = "kane-fabric-esp32-firmware-update-descriptor"
VERSION = 1


class FirmwareUpdateDescriptorError(ContractError):
    pass


def build_update_descriptor(
    manifest: Mapping[str, object],
    authorization: Mapping[str, object],
) -> dict[str, object]:
    validate_release_manifest(manifest)
    validate_authorization_envelope(authorization)

    if authorization["manifest_sha256"] != manifest["manifest_sha256"]:
        raise FirmwareUpdateDescriptorError(
            "authorization does not bind this release manifest"
        )

    release = manifest["release"]
    firmware = manifest["firmware"]
    recovery = manifest["recovery"]

    if release["device_family"] != "esp32-s3" or release["target"] != "esp32s3":
        raise FirmwareUpdateDescriptorError(
            "release manifest is not for the ESP32-S3 reference family"
        )

    descriptor = {
        "format": FORMAT,
        "version": VERSION,
        "device_family": "esp32-s3",
        "target": "esp32s3",
        "manifest_sha256": manifest["manifest_sha256"],
        "key_id_sha256": authorization["key_id_sha256"],
        "authorization_algorithm": ALGORITHM,
        "signature_encoding": SIGNATURE_ENCODING,
        "signature_base64": authorization["signature_base64"],
        "release_sequence": release["sequence"],
        "rollback_floor_sequence": recovery["rollback_floor_sequence"],
        "firmware_byte_length": firmware["byte_length"],
        "firmware_sha256": firmware["sha256"],
    }
    validate_update_descriptor(descriptor)
    return descriptor


def validate_update_descriptor(value: Mapping[str, object]) -> None:
    expected_fields = {
        "format",
        "version",
        "device_family",
        "target",
        "manifest_sha256",
        "key_id_sha256",
        "authorization_algorithm",
        "signature_encoding",
        "signature_base64",
        "release_sequence",
        "rollback_floor_sequence",
        "firmware_byte_length",
        "firmware_sha256",
    }
    if set(value) != expected_fields:
        raise FirmwareUpdateDescriptorError(
            "update descriptor fields are invalid"
        )
    if value["format"] != FORMAT or value["version"] != VERSION:
        raise FirmwareUpdateDescriptorError(
            "update descriptor format/version is unsupported"
        )
    if value["device_family"] != "esp32-s3" or value["target"] != "esp32s3":
        raise FirmwareUpdateDescriptorError(
            "update descriptor target is unsupported"
        )
    if value["authorization_algorithm"] != ALGORITHM:
        raise FirmwareUpdateDescriptorError(
            "update descriptor algorithm drifted"
        )
    if value["signature_encoding"] != SIGNATURE_ENCODING:
        raise FirmwareUpdateDescriptorError(
            "update descriptor signature encoding drifted"
        )

    sha256_text(value["manifest_sha256"], "manifest_sha256")
    sha256_text(value["key_id_sha256"], "key_id_sha256")
    sha256_text(value["firmware_sha256"], "firmware_sha256")

    for name in (
        "release_sequence",
        "rollback_floor_sequence",
        "firmware_byte_length",
    ):
        item = value[name]
        if not isinstance(item, int) or isinstance(item, bool) or item < 0:
            raise FirmwareUpdateDescriptorError(
                f"{name} must be a non-negative integer"
            )

    if value["release_sequence"] < 1:
        raise FirmwareUpdateDescriptorError(
            "release_sequence must be positive"
        )
    if value["firmware_byte_length"] < 1:
        raise FirmwareUpdateDescriptorError(
            "firmware_byte_length must be positive"
        )
    if value["rollback_floor_sequence"] > value["release_sequence"]:
        raise FirmwareUpdateDescriptorError(
            "rollback floor cannot exceed release sequence"
        )

    signature = value["signature_base64"]
    if not isinstance(signature, str) or not signature:
        raise FirmwareUpdateDescriptorError(
            "signature_base64 must be a nonempty string"
        )
