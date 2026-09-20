from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ms5.tools.kane_fabric_management_transport import (
    ManagementTransportContractError,
    load_candidate,
    validate_candidate,
    validate_repository_binding,
)

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_PATH = ROOT / "ms5" / "management-transport-candidate.json"
TOOLCHAIN_PATH = ROOT / "ms5" / "toolchain-selection.json"
MANIFEST_PATH = ROOT / "third_party" / "manifest.json"


class ManagementTransportCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = load_candidate(CANDIDATE_PATH)
        cls.toolchain = json.loads(TOOLCHAIN_PATH.read_text(encoding="utf-8"))
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_repository_candidate_valid(self):
        validate_candidate(self.candidate)

    def test_repository_binding_valid(self):
        validate_repository_binding(self.candidate, self.toolchain, self.manifest)

    def test_candidate_is_not_retained(self):
        self.assertEqual(
            self.candidate["status"],
            "candidate-evaluation-only-not-retained",
        )
        self.assertFalse(self.candidate["boundaries"]["retained_dependency"])
        self.assertFalse(
            self.candidate["boundaries"][
                "third_party_manifest_entry_allowed_before_retain_decision"
            ]
        )

    def test_browser_path_remains_independent(self):
        self.assertFalse(self.candidate["boundaries"]["browser_path_prerequisite"])
        self.assertFalse(self.candidate["boundaries"]["firmware_v1_requirement"])

    def test_participant_router_control_is_not_required(self):
        boundaries = self.candidate["boundaries"]
        self.assertFalse(boundaries["participant_router_administration_required"])
        self.assertFalse(boundaries["inbound_port_forwarding_required"])
        self.assertFalse(boundaries["dhcp_reservation_required"])
        self.assertFalse(boundaries["static_participant_lan_address_required"])

    def test_transport_identity_is_not_fabric_identity(self):
        boundaries = self.candidate["boundaries"]
        self.assertFalse(boundaries["management_identity_is_fabric_identity"])
        self.assertFalse(boundaries["transport_locator_is_fabric_identity"])
        self.assertFalse(boundaries["wireguard_key_is_fabric_identity"])

    def test_wireguard_source_commit_drift_is_rejected(self):
        value = copy.deepcopy(self.candidate)
        value["candidate"]["source_commit"] = "0" * 40
        with self.assertRaises(ManagementTransportContractError):
            validate_candidate(value)

    def test_moving_wireguard_tag_is_rejected(self):
        value = copy.deepcopy(self.candidate)
        value["candidate"]["tag"] = "dev"
        with self.assertRaises(ManagementTransportContractError):
            validate_candidate(value)

    def test_declared_dependency_range_cannot_float_during_evaluation(self):
        value = copy.deepcopy(self.candidate)
        value["candidate"]["evaluation_dependency_pin"]["version"] = "latest"
        with self.assertRaises(ManagementTransportContractError):
            validate_candidate(value)

    def test_required_runtime_evidence_cannot_be_dropped(self):
        value = copy.deepcopy(self.candidate)
        value["required_evidence"].remove("wifi_interruption_and_reconnect")
        with self.assertRaises(ManagementTransportContractError):
            validate_candidate(value)

    def test_all_decision_outcomes_remain_valid(self):
        self.assertEqual(
            self.candidate["decision"]["allowed_results"],
            ["retain", "reject", "defer"],
        )
        self.assertEqual(
            self.candidate["decision"]["state_before_runtime_evidence"],
            "defer",
        )

    def test_wireguard_manifest_retention_before_decision_is_rejected(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["third_party"].append(
            {
                "key": "esphome-wireguard",
                "role": "firmware-library",
                "license": "BSD-3-Clause",
                "pin": {"version": "0.4.6"},
            }
        )
        with self.assertRaises(ManagementTransportContractError):
            validate_repository_binding(self.candidate, self.toolchain, manifest)


if __name__ == "__main__":
    unittest.main(verbosity=2)
