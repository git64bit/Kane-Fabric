from __future__ import annotations

import unittest
from pathlib import Path

from ms5.tools.kane_fabric_firmware_v1 import (
    CANDIDATE_ONLY,
    CORE_RUNTIME_REQUIRED,
    EXPLICITLY_NOT_V1_RESPONSIBILITIES,
    FIXED_BOUNDARY,
    LIFECYCLE_REQUIRED,
    FirmwareV1RoleContractError,
    build_firmware_v1_role,
    validate_firmware_v1_role,
)


REPO = Path(__file__).resolve().parents[2]


class FirmwareV1RoleTests(unittest.TestCase):
    def test_build_and_validate_frozen_role(self):
        role = build_firmware_v1_role()
        validate_firmware_v1_role(role)
        self.assertIn("plain-http-artifact-serving", role["core_runtime_required"])
        self.assertIn("firmware-source-tracked-in-repository", role["lifecycle_required"])
        self.assertFalse(role["fixed_boundary"]["browser_tls_on_edge"])
        self.assertFalse(role["fixed_boundary"]["wireguard_required_for_v1"])

    def test_responsibility_classes_are_disjoint(self):
        required = set(CORE_RUNTIME_REQUIRED) | set(LIFECYCLE_REQUIRED)
        candidate = set(CANDIDATE_ONLY)
        excluded = set(EXPLICITLY_NOT_V1_RESPONSIBILITIES)
        self.assertFalse(required & candidate)
        self.assertFalse(required & excluded)
        self.assertFalse(candidate & excluded)

    def test_wireguard_is_candidate_not_v1_requirement(self):
        self.assertIn("wireguard-management-transport", CANDIDATE_ONLY)
        self.assertNotIn("wireguard-management-transport", CORE_RUNTIME_REQUIRED)
        self.assertNotIn("wireguard-management-transport", LIFECYCLE_REQUIRED)
        self.assertFalse(FIXED_BOUNDARY["wireguard_required_for_v1"])

    def test_browser_tls_and_hosted_ap_are_outside_v1_firmware(self):
        self.assertIn("browser-https-termination", EXPLICITLY_NOT_V1_RESPONSIBILITIES)
        self.assertIn(
            "esp32-hosted-browser-access-point",
            EXPLICITLY_NOT_V1_RESPONSIBILITIES,
        )
        self.assertFalse(FIXED_BOUNDARY["browser_tls_on_edge"])
        self.assertFalse(FIXED_BOUNDARY["esp32_hosted_ap_required"])

    def test_candidate_capability_cannot_be_promoted_by_mutating_profile(self):
        role = build_firmware_v1_role()
        role["core_runtime_required"] = list(role["core_runtime_required"]) + [
            "wireguard-management-transport"
        ]
        with self.assertRaises(FirmwareV1RoleContractError):
            validate_firmware_v1_role(role)

    def test_documentation_carries_same_v1_boundary(self):
        design = (REPO / "docs/MILESTONE_5_DESIGN.md").read_text()
        firmware_readme = (REPO / "ms5/esp32_reference/README.md").read_text()

        for text in (design, firmware_readme):
            self.assertIn("core runtime", text.lower())
            self.assertIn("candidate-only", text.lower())
            self.assertIn("firmware source", text.lower())
            self.assertIn("serial", text.lower())
            self.assertIn("WireGuard", text)

        self.assertIn("may conclude that WireGuard is not retained", design)
        self.assertIn("CT102 does not build or flash firmware", firmware_readme)


if __name__ == "__main__":
    unittest.main(verbosity=2)
