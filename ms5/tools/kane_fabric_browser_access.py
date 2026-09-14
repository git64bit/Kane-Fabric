#!/usr/bin/env python3
"""MS5 browser secure-origin, Wiregate hub, and edge HTTP access contract."""

from __future__ import annotations

import hashlib
import ipaddress
import re
from collections.abc import Mapping

from ms5.tools.common import ContractError, canonical_json_bytes, nonempty_text
from ms5.tools.kane_fabric_edge import validate_edge_instance

FORMAT = "kane-fabric-browser-access"
VERSION = 2
REQUIRED_BROWSER_TRANSPORT = "wiregate-hub-proxy"

DNS_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")

RUNTIME_REQUIREMENTS = {
    "window_is_secure_context_required": True,
    "webcrypto_sha256_required": True,
    "browser_certificate_errors_permitted": False,
}

LOCAL_NETWORK_REQUIREMENTS = {
    "wiregate_hub_required": True,
    "browser_to_hub_https_required": True,
    "hub_to_edge_http_required": True,
    "direct_browser_to_edge_http_is_reference_path": False,
    "esp32_hosted_ap_required": False,
    "wireguard_required_for_browser_path": False,
}

IDENTITY_BOUNDARY = {
    "browser_origin_scope": "wiregate-hub-serving-only",
    "hub_tls_identity_is_fabric_identity": False,
    "edge_http_endpoint_is_fabric_identity": False,
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


def _origin_host(value: object) -> str:
    try:
        host = nonempty_text(value, "origin_host").lower()
    except ContractError as exc:
        raise BrowserAccessContractError(str(exc)) from exc
    if any(char in host for char in "/?#@") or any(char.isspace() for char in host):
        raise BrowserAccessContractError("origin_host must contain only a host, not a URL")
    if host == "localhost" or host.endswith(".localhost"):
        raise BrowserAccessContractError(
            "the Wiregate hub may not rely on the browser localhost secure-context exception"
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


def _port(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 65535:
        raise BrowserAccessContractError(f"{label} must be an integer from 1 through 65535")
    return value


def build_browser_access(
    *,
    edge_instance: Mapping[str, object],
    origin_host: str,
    origin_port: int = 443,
    edge_http_port: int = 80,
) -> dict[str, object]:
    _validated_edge(edge_instance)

    body = {
        "bindings": {
            "edge_physical_instance_sha256": edge_instance["physical_instance_sha256"],
        },
        "browser_origin": {
            "scheme": "https",
            "host": _origin_host(origin_host),
            "port": _port(origin_port, "origin_port"),
            "tls_termination": "wiregate-hub",
            "tls_trust_requirement": "browser-trusted-certificate",
        },
        "edge_transport": {
            "scheme": "http",
            "port": _port(edge_http_port, "edge_http_port"),
            "tls_required": False,
            "direct_browser_access": False,
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
) -> None:
    expected_keys = {
        "format",
        "version",
        "bindings",
        "browser_origin",
        "edge_transport",
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

    expected_bindings = {
        "edge_physical_instance_sha256": edge_instance["physical_instance_sha256"],
    }
    if value["bindings"] != expected_bindings:
        raise BrowserAccessContractError(
            "browser access is not bound to the supplied physical edge"
        )

    origin = value["browser_origin"]
    if not isinstance(origin, Mapping) or set(origin) != {
        "scheme",
        "host",
        "port",
        "tls_termination",
        "tls_trust_requirement",
    }:
        raise BrowserAccessContractError("browser origin section is invalid")
    normalized_origin = {
        "scheme": "https",
        "host": _origin_host(origin["host"]),
        "port": _port(origin["port"], "browser_origin.port"),
        "tls_termination": "wiregate-hub",
        "tls_trust_requirement": "browser-trusted-certificate",
    }
    if dict(origin) != normalized_origin:
        raise BrowserAccessContractError(
            "browser origin is not the fixed Wiregate HTTPS contract"
        )

    edge_transport = value["edge_transport"]
    if not isinstance(edge_transport, Mapping) or set(edge_transport) != {
        "scheme",
        "port",
        "tls_required",
        "direct_browser_access",
    }:
        raise BrowserAccessContractError("edge transport section is invalid")
    normalized_edge_transport = {
        "scheme": "http",
        "port": _port(edge_transport["port"], "edge_transport.port"),
        "tls_required": False,
        "direct_browser_access": False,
    }
    if dict(edge_transport) != normalized_edge_transport:
        raise BrowserAccessContractError(
            "physical edge transport must be plain HTTP behind the Wiregate hub"
        )

    if value["runtime_requirements"] != RUNTIME_REQUIREMENTS:
        raise BrowserAccessContractError(
            "browser runtime requirements are not the fixed MS5 contract"
        )
    if value["local_network_requirements"] != LOCAL_NETWORK_REQUIREMENTS:
        raise BrowserAccessContractError(
            "Wiregate/edge network requirements are not the fixed MS5 contract"
        )
    if value["identity_boundary"] != IDENTITY_BOUNDARY:
        raise BrowserAccessContractError(
            "browser identity boundary is not the fixed MS5 contract"
        )

    body = {
        "bindings": expected_bindings,
        "browser_origin": normalized_origin,
        "edge_transport": normalized_edge_transport,
        "runtime_requirements": dict(RUNTIME_REQUIREMENTS),
        "local_network_requirements": dict(LOCAL_NETWORK_REQUIREMENTS),
        "identity_boundary": dict(IDENTITY_BOUNDARY),
    }
    expected = hashlib.sha256(canonical_json_bytes(body)).hexdigest()
    if value["browser_access_sha256"] != expected:
        raise BrowserAccessContractError("browser access identity is invalid")
