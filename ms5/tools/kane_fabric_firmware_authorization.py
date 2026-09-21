#!/usr/bin/env python3
"""MS5-009 firmware release-authorization envelope contract."""

from __future__ import annotations

import base64
import binascii
import hashlib
from collections.abc import Mapping

from ms5.tools.common import ContractError, sha256_text

FORMAT = "kane-fabric-firmware-authorization"
VERSION = 1
ALGORITHM = "ecdsa-p256-sha256"
SIGNATURE_ENCODING = "p1363-r-s-64"
PUBLIC_KEY_ENCODING = "sec1-uncompressed-p256-65"

P256_PUBLIC_KEY_BYTES = 65
P256_SIGNATURE_BYTES = 64


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


def build_authorization_envelope(
    *,
    manifest_sha256: str,
    key_id_sha256: str,
    signature: bytes,
) -> dict[str, object]:
    manifest_sha256 = sha256_text(manifest_sha256, "manifest_sha256")
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
        "manifest_sha256": manifest_sha256,
        "signature_base64": base64.b64encode(signature).decode("ascii"),
    }


def decode_authorization_signature(value: Mapping[str, object]) -> bytes:
    validate_authorization_envelope(value)
    try:
        decoded = base64.b64decode(
            str(value["signature_base64"]),
            validate=True,
        )
    except (binascii.Error, ValueError) as exc:
        raise FirmwareAuthorizationContractError(
            "signature_base64 is invalid"
        ) from exc
    return decoded


def validate_authorization_envelope(value: Mapping[str, object]) -> None:
    expected_fields = {
        "format",
        "version",
        "algorithm",
        "signature_encoding",
        "key_id_sha256",
        "manifest_sha256",
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
    sha256_text(value["manifest_sha256"], "manifest_sha256")

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
