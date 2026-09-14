from __future__ import annotations

import unittest

from ms5.tools.kane_fabric_browser_access import (
    BrowserAccessContractError,
    IDENTITY_BOUNDARY,
    LOCAL_NETWORK_REQUIREMENTS,
    RUNTIME_REQUIREMENTS,
    build_browser_access,
    validate_browser_access,
)
from ms5.tools.kane_fabric_edge import build_edge_instance

A = "a" * 64


class BrowserAccessContractTests(unittest.TestCase):
    def _edge(self, label: str = "node-a", browser_transport: str = "wiregate-hub-proxy"):
        return build_edge_instance(
            logical_placement_sha256=A,
            platform_class="esp32-s3-class",
            instance_label=label,
            storage_backend="sd-card",
            browser_transport=browser_transport,
            management_transport="none",
        )

    def _access(self):
        edge = self._edge()
        access = build_browser_access(
            edge_instance=edge,
            origin_host="fabric.kane-fabric.test",
        )
        return edge, access

    def test_build_and_validate(self):
        edge, access = self._access()
        validate_browser_access(access, edge_instance=edge)
        self.assertEqual("https", access["browser_origin"]["scheme"])
        self.assertEqual("wiregate-hub", access["browser_origin"]["tls_termination"])
        self.assertEqual("http", access["edge_transport"]["scheme"])
        self.assertFalse(access["edge_transport"]["tls_required"])
        self.assertFalse(access["edge_transport"]["direct_browser_access"])
        self.assertEqual(RUNTIME_REQUIREMENTS, access["runtime_requirements"])
        self.assertEqual(LOCAL_NETWORK_REQUIREMENTS, access["local_network_requirements"])
        self.assertEqual(IDENTITY_BOUNDARY, access["identity_boundary"])

    def test_edge_transport_must_be_wiregate_hub_proxy(self):
        with self.assertRaises(BrowserAccessContractError):
            build_browser_access(
                edge_instance=self._edge(browser_transport="local-ap-http"),
                origin_host="fabric.kane-fabric.test",
            )

    def test_browser_origin_must_remain_https(self):
        edge, access = self._access()
        access["browser_origin"] = dict(access["browser_origin"])
        access["browser_origin"]["scheme"] = "http"
        with self.assertRaises(BrowserAccessContractError):
            validate_browser_access(access, edge_instance=edge)

    def test_edge_transport_must_remain_plain_http(self):
        edge, access = self._access()
        access["edge_transport"] = dict(access["edge_transport"])
        access["edge_transport"]["scheme"] = "https"
        access["edge_transport"]["tls_required"] = True
        with self.assertRaises(BrowserAccessContractError):
            validate_browser_access(access, edge_instance=edge)

    def test_wiregate_may_not_use_localhost_secure_context_exception(self):
        with self.assertRaises(BrowserAccessContractError):
            build_browser_access(
                edge_instance=self._edge(),
                origin_host="fabric.localhost",
            )

    def test_profile_is_bound_to_actual_edge_instance(self):
        edge, access = self._access()
        replacement = self._edge(label="replacement-node")
        with self.assertRaises(BrowserAccessContractError):
            validate_browser_access(access, edge_instance=replacement)

    def test_geographic_identity_cannot_be_added_to_origin_boundary(self):
        edge, access = self._access()
        access["identity_boundary"] = dict(access["identity_boundary"])
        access["identity_boundary"]["origin_contains_persistent_geographic_identity"] = True
        with self.assertRaises(BrowserAccessContractError):
            validate_browser_access(access, edge_instance=edge)

    def test_wireguard_is_not_required_for_browser_path(self):
        edge, access = self._access()
        access["local_network_requirements"] = dict(access["local_network_requirements"])
        access["local_network_requirements"]["wireguard_required_for_browser_path"] = True
        with self.assertRaises(BrowserAccessContractError):
            validate_browser_access(access, edge_instance=edge)

    def test_esp32_hosted_ap_is_not_required(self):
        edge, access = self._access()
        self.assertFalse(access["local_network_requirements"]["esp32_hosted_ap_required"])
        validate_browser_access(access, edge_instance=edge)


if __name__ == "__main__":
    unittest.main(verbosity=2)
