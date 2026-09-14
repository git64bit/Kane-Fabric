#!/usr/bin/env python3
"""MS5 browser secure-origin and local AP/STA access contract."""

from __future__ import annotations

import hashlib
import ipaddress
import re
from collections.abc import Mapping

from ms5.tools.common import ContractError, canonical_json_bytes, nonempty_text
from ms5.tools.kane_fabric_edge import validate_edge_instance
from ms5.tools.kane_fabric_keys import validate_key_provider

FORMAT = "kane-fabric-browser-access"
VERSION = 1
REQUIRED_BROWSER_TRANSPORT = "local-ap-https"

DNS_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")

RUNTIME_REQUIREMENTS = {
    "window_is_secure_context_required": True,
    "webcrypto_sha256_required": True,
    "browser_certificate_errors_permitted": False,
}

LOCAL_NETWORK_REQUIREMENTS = {
    "esp32_hosted_ap_required": True,
    "deterministic_local_reachability_required": True,
    "sta_coexistence_supported": True,
    "ap_sta_shared_radio": True,
    "ap_sta_channel_coupled": True,
    "runtime_channel_behavior_measurement_required": True,
    "runtime_resource_contention_measurement_required": True,
}

IDENTITY_BOUNDARY = {
    "tls_identity_scope": "device-serving-only",
    "origin_is_fabric_identity": False,
    "tls_identity_is_fabric_identity": False,
    "origin_contains_persistent_geographic_identity": False,
    "origin_contains_delivery_point_identity": False,
}


class BrowserAccessContractError(ContractError):
    pass


def _validated_edge(value: Mapping[str, object]) -> None:
    try:
        validate_edge_instance(value)
    except ContractError as exc:
        raise BrowserAccessContractError(f"edge instance is invalid: {exc}") from exc
    physical = value["physical"]
    if physical["browser_transport"] != REQUIRED_BROWSER_TRANSPORT:
        raise BrowserAccessContractError(
            f"edge browser transport must be {REQUIRED_BROWSER_TRANSPORT}"
        )


def _validated_provider(value: Mapping[str, object]) -> str:
    try:
        validate_key_provider(value)
    except ContractError as exc:
        raise BrowserAccessContractError(f"key provider is invalid: {exc}") from exc
    keys = value["keys"]
    for key in keys:
        if key["role"] == "browser-tls-server":
            return key["key_ref"]
    raise BrowserAccessContractError("browser-tls-server key role is missing")


def _origin_host(value: object) -> str:
    try:
        host = nonempty_text(value, "origin_host").lower()
    except ContractError as exc:
        raise BrowserAccessContractError(str(exc)) from exc
    if any(char in host for char in "/?#@") or any(char.isspace() for char in host):
        raise BrowserAccessContractError("origin_host must contain only a host, not a URL")
    if host == "localhost" or host.endswith(".localhost"):
        raise BrowserAccessContractError(
            "a physical edge may not rely on the browser localhost secure-context exception"
        )
    try:
        ipaddress.IPv4Address(host)
        return host
    except ipaddress.AddressValueError:
        pass
    if len(host) > 253:
        raise BrowserAccessContractError("origin_host DNS name is too long")
    labels = host.rstrip(".").split(".")
    if not labels or any(not DNS_LABEL_RE.fullmatch(label) for label in labels):
        raise BrowserAccessContractError(
            "origin_host must be an IPv4 literal or normalized DNS name"
        )
    return host.rstrip(".")


def _origin_port(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 65535:
        raise BrowserAccessContractError("origin_port must be an integer from 1 through 65535")
    return value


def build_browser_access(
    *,
    edge_instance: Mapping[str, object],
    key_provider: Mapping[str, object],
    origin_host: str,
    origin_port: int = 443,
) -> dict[str, object]:
    _validated_edge(edge_instance)
    tls_key_ref = _validated_provider(key_provider)

    body = {
        "bindings": {
            "edge_physical_instance_sha256": edge_instance["physical_instance_sha256"],
            "key_provider_fingerprint_sha256": key_provider["provider_fingerprint_sha256"],
        },
        "origin": {
            "scheme": "https",
            "host": _origin_host(origin_host),
            "port": _origin_port(origin_port),
            "tls_trust_requirement": "browser-trusted-certificate",
            "tls_key_ref": tls_key_ref,
        },
        "runtime_requirements": dict(RUNTIME_REQUIREMENTS),
        "local_network_requirements": dict(LOCAL_NETWORK_REQUIREMENTS),
        "identity_boundary": dict(IDENTITY_BOUNDARY),
    }
    return {
        "format": FORMAT,
        "version": VERSION,
        **body,
        "browser_access_sha256": hashlib.sha256(canonical_json_bytes(body)).hexdigest(),
    }


def validate_browser_access(
    value: Mapping[str, object],
    *,
    edge_instance: Mapping[str, object],
    key_provider: Mapping[str, object],
) -> None:
    expected_keys = {
        "format",
        "version",
        "bindings",
        "origin",
        "runtime_requirements",
        "local_network_requirements",
        "identity_boundary",
        "browser_access_sha256",
    }
    if set(value) != expected_keys:
        raise BrowserAccessContractError("browser access fields are invalid")
    if value["format"] != FORMAT or value["version"] != VERSION:
        raise BrowserAccessContractError("browser access format/version is unsupported")

    _validated_edge(edge_instance)
    tls_key_ref = _validated_provider(key_provider)

    expected_bindings = {
        "edge_physical_instance_sha256": edge_instance["physical_instance_sha256"],
        "key_provider_fingerprint_sha256": key_provider["provider_fingerprint_sha256"],
    }
    if value["bindings"] != expected_bindings:
        raise BrowserAccessContractError(
            "browser access is not bound to the supplied edge/provider"
        )

    origin = value["origin"]
    if not isinstance(origin, Mapping) or set(origin) != {
        "scheme",
        "host",
        "port",
        "tls_trust_requirement",
        "tls_key_ref",
    }:
        raise BrowserAccessContractError("browser origin section is invalid")
    normalized_origin = {
        "scheme": "https",
        "host": _origin_host(origin["host"]),
        "port": _origin_port(origin["port"]),
        "tls_trust_requirement": "browser-trusted-certificate",
        "tls_key_ref": tls_key_ref,
    }
    if dict(origin) != normalized_origin:
        raise BrowserAccessContractError(
            "browser origin is not the fixed secure-origin contract"
        )

    if value["runtime_requirements"] != RUNTIME_REQUIREMENTS:
        raise BrowserAccessContractError(
            "browser runtime requirements are not the fixed MS5 contract"
        )
    if value["local_network_requirements"] != LOCAL_NETWORK_REQUIREMENTS:
        raise BrowserAccessContractError(
            "local AP/STA requirements are not the fixed MS5 contract"
        )
    if value["identity_boundary"] != IDENTITY_BOUNDARY:
        raise BrowserAccessContractError(
            "browser identity boundary is not the fixed MS5 contract"
        )

    body = {
        "bindings": expected_bindings,
        "origin": normalized_origin,
        "runtime_requirements": dict(RUNTIME_REQUIREMENTS),
        "local_network_requirements": dict(LOCAL_NETWORK_REQUIREMENTS),
        "identity_boundary": dict(IDENTITY_BOUNDARY),
    }
    expected = hashlib.sha256(canonical_json_bytes(body)).hexdigest()
    if value["browser_access_sha256"] != expected:
        raise BrowserAccessContractError("browser access identity is invalid")
