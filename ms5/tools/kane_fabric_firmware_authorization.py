#!/usr/bin/env python3
"""MS5-009 firmware release-authorization payload and envelope contract."""

from __future__ import annotations

import base64
import binascii
import hashlib
import struct
from collections.abc import Mapping

from ms5.tools.common import ContractError, sha256_text

FORMAT = "kane-fabric-firmware-authorization"
VERSION = 1
ALGORITHM = "ecdsa-p256-sha256"
SIGNATURE_ENCODING = "p1363-r-s-64"
PUBLIC_KEY_ENCODING = "sec1-uncompressed-p256-65"
PAYLOAD_ENCODING = "kane-fabric-fw-auth-v1-fixed-binary"

P256_PUBLIC_KEY_BYTES = 65
P256_SIGNATURE_BYTES = 64
PAYLOAD_BYTES = 152

_DOMAIN = b"kane-fabric-firmware-auth-v1" + b"\x00" * 4


class FirmwareAuthorizationContractError(ContractError):
    pass


def derive_key_id_sha256(public_key: bytes) -> str:
    if (
        not isinstance(public_key, bytes)
        or len(public_key) != P256_PUBLIC_KEY_BYTES
        or public_key[0] != 0x04
    ):
        raise FirmwareAuthorizationContractError(
            "public key must be a 65-byte uncompressed P-256 SEC1 point"
        )
    return hashlib.sha256(public_key).hexdigest()


def _fixed_text(value: object, label: str, width: int) -> bytes:
    if not isinstance(value, str) or not value:
        raise FirmwareAuthorizationContractError(
            f"{label} must be a nonempty string"
        )
    encoded = value.encode("ascii")
    if len(encoded) > width:
        raise FirmwareAuthorizationContractError(
            f"{label} exceeds fixed authorization width"
        )
    return encoded + b"\x00" * (width - len(encoded))


def _u64(value: object, label: str, *, positive: bool = False) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < (1 if positive else 0)
        or value > 0xFFFFFFFFFFFFFFFF
    ):
        qualifier = "positive " if positive else ""
        raise FirmwareAuthorizationContractError(
            f"{label} must be a {qualifier}uint64"
        )
    return value


def build_authorization_payload(
    *,
    device_family: str,
    target: str,
    manifest_sha256: str,
    firmware_sha256: str,
    firmware_byte_length: int,
    release_sequence: int,
    rollback_floor_sequence: int,
) -> bytes:
    manifest_sha256 = sha256_text(manifest_sha256, "manifest_sha256")
    firmware_sha256 = sha256_text(firmware_sha256, "firmware_sha256")
    firmware_byte_length = _u64(
        firmware_byte_length,
        "firmware_byte_length",
        positive=True,
    )
    release_sequence = _u64(
        release_sequence,
        "release_sequence",
        positive=True,
    )
    rollback_floor_sequence = _u64(
        rollback_floor_sequence,
        "rollback_floor_sequence",
    )
    if rollback_floor_sequence > release_sequence:
        raise FirmwareAuthorizationContractError(
            "rollback floor cannot exceed release sequence"
        )

    payload = b"".join(
        (
            _DOMAIN,
            _fixed_text(device_family, "device_family", 16),
            _fixed_text(target, "target", 16),
            bytes.fromhex(manifest_sha256),
            bytes.fromhex(firmware_sha256),
            struct.pack(
                ">QQQ",
                firmware_byte_length,
                release_sequence,
                rollback_floor_sequence,
            ),
        )
    )
    if len(payload) != PAYLOAD_BYTES:
        raise FirmwareAuthorizationContractError(
            "authorization payload length drifted"
        )
    return payload


def authorization_payload_sha256(**kwargs: object) -> str:
    return hashlib.sha256(build_authorization_payload(**kwargs)).hexdigest()


def build_authorization_envelope(
    *,
    authorization_payload_sha256: str,
    key_id_sha256: str,
    signature: bytes,
) -> dict[str, object]:
    authorization_payload_sha256 = sha256_text(
        authorization_payload_sha256,
        "authorization_payload_sha256",
    )
    key_id_sha256 = sha256_text(key_id_sha256, "key_id_sha256")
    if not isinstance(signature, bytes) or len(signature) != P256_SIGNATURE_BYTES:
        raise FirmwareAuthorizationContractError(
            "signature must be exactly 64 P1363 r||s bytes"
        )
    return {
        "format": FORMAT,
        "version": VERSION,
        "algorithm": ALGORITHM,
        "signature_encoding": SIGNATURE_ENCODING,
        "key_id_sha256": key_id_sha256,
        "authorization_payload_sha256": authorization_payload_sha256,
        "signature_base64": base64.b64encode(signature).decode("ascii"),
    }


def decode_authorization_signature(value: Mapping[str, object]) -> bytes:
    validate_authorization_envelope(value)
    try:
        return base64.b64decode(
            str(value["signature_base64"]),
            validate=True,
        )
    except (binascii.Error, ValueError) as exc:
        raise FirmwareAuthorizationContractError(
            "signature_base64 is invalid"
        ) from exc


def validate_authorization_envelope(value: Mapping[str, object]) -> None:
    expected_fields = {
        "format",
        "version",
        "algorithm",
        "signature_encoding",
        "key_id_sha256",
        "authorization_payload_sha256",
        "signature_base64",
    }
    if set(value) != expected_fields:
        raise FirmwareAuthorizationContractError(
            "authorization envelope fields are invalid"
        )
    if value["format"] != FORMAT or value["version"] != VERSION:
        raise FirmwareAuthorizationContractError(
            "authorization envelope format/version is unsupported"
        )
    if value["algorithm"] != ALGORITHM:
        raise FirmwareAuthorizationContractError(
            "authorization algorithm is unsupported"
        )
    if value["signature_encoding"] != SIGNATURE_ENCODING:
        raise FirmwareAuthorizationContractError(
            "authorization signature encoding is unsupported"
        )
    sha256_text(value["key_id_sha256"], "key_id_sha256")
    sha256_text(
        value["authorization_payload_sha256"],
        "authorization_payload_sha256",
    )

    signature_text = value["signature_base64"]
    if not isinstance(signature_text, str) or not signature_text:
        raise FirmwareAuthorizationContractError(
            "signature_base64 must be a nonempty string"
        )
    try:
        decoded = base64.b64decode(signature_text, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise FirmwareAuthorizationContractError(
            "signature_base64 is invalid"
        ) from exc
    if len(decoded) != P256_SIGNATURE_BYTES:
        raise FirmwareAuthorizationContractError(
            "signature must decode to exactly 64 P1363 r||s bytes"
        )
