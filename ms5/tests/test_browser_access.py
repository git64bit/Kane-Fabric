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
from ms5.tools.kane_fabric_keys import build_key_provider

A = "a" * 64


class BrowserAccessContractTests(unittest.TestCase):
    def _edge(self, label: str = "node-a", browser_transport: str = "local-ap-https"):
        return build_edge_instance(
            logical_placement_sha256=A,
            platform_class="esp32-s3-class",
            instance_label=label,
            storage_backend="sd-card",
            browser_transport=browser_transport,
            management_transport="none",
        )

    def _provider(self, instance: str = "software-store", key_ref: str = "tls-key-1"):
        return build_key_provider(
            provider_class="software",
            provider_instance=instance,
            keys=[{"role": "browser-tls-server", "key_ref": key_ref}],
        )

    def _access(self):
        edge = self._edge()
        provider = self._provider()
        access = build_browser_access(
            edge_instance=edge,
            key_provider=provider,
            origin_host="edge.kane-fabric.test",
        )
        return edge, provider, access

    def test_build_and_validate(self):
        edge, provider, access = self._access()
        validate_browser_access(access, edge_instance=edge, key_provider=provider)
        self.assertEqual("https", access["origin"]["scheme"])
        self.assertEqual(RUNTIME_REQUIREMENTS, access["runtime_requirements"])
        self.assertEqual(LOCAL_NETWORK_REQUIREMENTS, access["local_network_requirements"])
        self.assertEqual(IDENTITY_BOUNDARY, access["identity_boundary"])

    def test_edge_transport_must_be_local_ap_https(self):
        with self.assertRaises(BrowserAccessContractError):
            build_browser_access(
                edge_instance=self._edge(browser_transport="local-ap-http"),
                key_provider=self._provider(),
                origin_host="edge.kane-fabric.test",
            )

    def test_http_origin_rejected(self):
        edge, provider, access = self._access()
        access["origin"] = dict(access["origin"])
        access["origin"]["scheme"] = "http"
        with self.assertRaises(BrowserAccessContractError):
            validate_browser_access(access, edge_instance=edge, key_provider=provider)

    def test_localhost_exception_cannot_stand_in_for_physical_edge_tls(self):
        with self.assertRaises(BrowserAccessContractError):
            build_browser_access(
                edge_instance=self._edge(),
                key_provider=self._provider(),
                origin_host="edge.localhost",
            )

    def test_profile_is_bound_to_actual_edge_instance(self):
        edge, provider, access = self._access()
        replacement = self._edge(label="replacement-node")
        with self.assertRaises(BrowserAccessContractError):
            validate_browser_access(access, edge_instance=replacement, key_provider=provider)

    def test_profile_is_bound_to_actual_tls_provider(self):
        edge, _, access = self._access()
        replacement_provider = self._provider(
            instance="replacement-store",
            key_ref="tls-key-2",
        )
        with self.assertRaises(BrowserAccessContractError):
            validate_browser_access(
                access,
                edge_instance=edge,
                key_provider=replacement_provider,
            )

    def test_geographic_identity_cannot_be_added_to_origin_boundary(self):
        edge, provider, access = self._access()
        access["identity_boundary"] = dict(access["identity_boundary"])
        access["identity_boundary"]["origin_contains_persistent_geographic_identity"] = True
        with self.assertRaises(BrowserAccessContractError):
            validate_browser_access(access, edge_instance=edge, key_provider=provider)

    def test_ap_sta_measurement_obligation_cannot_be_removed(self):
        edge, provider, access = self._access()
        access["local_network_requirements"] = dict(access["local_network_requirements"])
        access["local_network_requirements"][
            "runtime_resource_contention_measurement_required"
        ] = False
        with self.assertRaises(BrowserAccessContractError):
            validate_browser_access(access, edge_instance=edge, key_provider=provider)


if __name__ == "__main__":
    unittest.main(verbosity=2)
