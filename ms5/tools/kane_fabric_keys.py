#!/usr/bin/env python3
"""MS5 replaceable key-provider contract for device-local cryptographic roles."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence

from ms5.tools.common import ContractError, canonical_json_bytes, nonempty_text

FORMAT = "kane-fabric-edge-key-provider"
VERSION = 2

PROVIDER_CLASSES = {"software", "external"}
ALLOWED_PRIVATE_KEY_ROLES = {
    "management-transport-client",
}

FIXED_BOUNDARY = {
    "fabric_release_signing_private_key_present": False,
    "geographic_promotion_private_key_present": False,
    "ca_issuing_private_key_present": False,
    "irreversible_efuse_dependency": False,
}


class KeyProviderContractError(ContractError):
    pass


def _key(value: Mapping[str, object]) -> dict[str, str]:
    if set(value) != {"role", "key_ref"}:
        raise KeyProviderContractError("key entry fields are invalid")
    role = nonempty_text(value["role"], "key.role")
    if role not in ALLOWED_PRIVATE_KEY_ROLES:
        raise KeyProviderContractError(f"private-key role is not allowed on an edge: {role}")
    return {
        "role": role,
        "key_ref": nonempty_text(value["key_ref"], "key.key_ref"),
    }


def _keys(values: Sequence[Mapping[str, object]]) -> list[dict[str, str]]:
    if isinstance(values, (str, bytes, bytearray)):
        raise KeyProviderContractError("keys must be an array")
    result = [_key(value) for value in values]
    result.sort(key=lambda item: item["role"])
    roles = [item["role"] for item in result]
    refs = [item["key_ref"] for item in result]
    if len(roles) != len(set(roles)):
        raise KeyProviderContractError("private-key roles must be unique")
    if len(refs) != len(set(refs)):
        raise KeyProviderContractError("a private key reference may not be reused across roles")
    return result


def build_key_provider(
    *,
    provider_class: str,
    provider_instance: str,
    keys: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    provider_class = nonempty_text(provider_class, "provider_class")
    if provider_class not in PROVIDER_CLASSES:
        raise KeyProviderContractError("provider_class is unsupported")
    body = {
        "provider_class": provider_class,
        "provider_instance": nonempty_text(provider_instance, "provider_instance"),
        "keys": _keys(keys),
        "authority_boundary": dict(FIXED_BOUNDARY),
    }
    return {
        "format": FORMAT,
        "version": VERSION,
        **body,
        "provider_fingerprint_sha256": hashlib.sha256(canonical_json_bytes(body)).hexdigest(),
    }


def validate_key_provider(value: Mapping[str, object]) -> None:
    if set(value) != {
        "format",
        "version",
        "provider_class",
        "provider_instance",
        "keys",
        "authority_boundary",
        "provider_fingerprint_sha256",
    }:
        raise KeyProviderContractError("key-provider fields are invalid")
    if value["format"] != FORMAT or value["version"] != VERSION:
        raise KeyProviderContractError("key-provider format/version is unsupported")
    keys = value["keys"]
    if not isinstance(keys, Sequence) or isinstance(keys, (str, bytes, bytearray)):
        raise KeyProviderContractError("keys must be an array")
    provider_class = nonempty_text(value["provider_class"], "provider_class")
    if provider_class not in PROVIDER_CLASSES:
        raise KeyProviderContractError("provider_class is unsupported")
    body = {
        "provider_class": provider_class,
        "provider_instance": nonempty_text(value["provider_instance"], "provider_instance"),
        "keys": _keys(keys),
        "authority_boundary": dict(FIXED_BOUNDARY),
    }
    if list(keys) != body["keys"]:
        raise KeyProviderContractError("key entries are not normalized")
    if value["authority_boundary"] != FIXED_BOUNDARY:
        raise KeyProviderContractError("authority boundary is not the fixed MS5 boundary")
    expected = hashlib.sha256(canonical_json_bytes(body)).hexdigest()
    if value["provider_fingerprint_sha256"] != expected:
        raise KeyProviderContractError("provider fingerprint is invalid")
