from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ms5.tools.kane_fabric_firmware_lifecycle import (
    FirmwareLifecycleContractError,
    build_firmware_lifecycle_contract,
    validate_firmware_lifecycle_contract,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "ms5" / "firmware-lifecycle-contract.json"


class FirmwareLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_tracked_contract_validates(self):
        validate_firmware_lifecycle_contract(self.contract)
        self.assertEqual(self.contract, build_firmware_lifecycle_contract())

    def test_management_transport_is_not_update_prerequisite(self):
        self.assertFalse(self.contract["update_boundary"]["management_transport_required"])
        self.assertTrue(self.contract["update_boundary"]["transport_agnostic"])

    def test_update_preserves_existing_data_boundaries(self):
        boundary = self.contract["update_boundary"]
        self.assertFalse(boundary["fabric_partition_rewritten_by_firmware_update"])
        self.assertFalse(boundary["nvs_erased_by_normal_firmware_update"])
        self.assertFalse(boundary["management_loss_invalidates_activated_publication"])

    def test_partition_plan_preserves_accepted_factory_and_fabric_offsets(self):
        preserved = {item["name"]: item for item in self.contract["partition_plan"]["preserve"]}
        self.assertEqual(0x10000, preserved["factory"]["offset"])
        self.assertEqual(0x100000, preserved["factory"]["size"])
        self.assertEqual(0x110000, preserved["fabric"]["offset"])
        self.assertEqual(0x400000, preserved["fabric"]["size"])

    def test_partition_plan_adds_two_aligned_ota_slots_in_unused_flash(self):
        added = {item["name"]: item for item in self.contract["partition_plan"]["add"]}
        self.assertEqual(0x510000, added["otadata"]["offset"])
        self.assertEqual(0x520000, added["ota_0"]["offset"])
        self.assertEqual(0x620000, added["ota_1"]["offset"])
        self.assertEqual(0, added["ota_0"]["offset"] % 0x10000)
        self.assertEqual(0, added["ota_1"]["offset"] % 0x10000)

    def test_signature_envelope_is_frozen_while_signer_remains_inert(self):
        authority = self.contract["authority_boundary"]
        self.assertEqual("selection-pending", authority["signer_provider_status"])
        self.assertEqual(
            "firmware_authorization_payload_sha256",
            authority["authorization_target"],
        )
        self.assertEqual(
            "kane-fabric-fw-auth-v1-fixed-binary",
            authority["authorization_payload_encoding"],
        )
        self.assertEqual("frozen", authority["signature_envelope_status"])
        self.assertEqual("ecdsa-p256-sha256", authority["signature_algorithm"])
        self.assertEqual("p1363-r-s-64", authority["signature_encoding"])
        self.assertEqual(
            "sec1-uncompressed-p256-65",
            authority["public_key_encoding"],
        )
        self.assertEqual(
            "sha256-public-key-bytes",
            authority["key_id_derivation"],
        )
        self.assertEqual("not-activated", authority["signing_activation_status"])
        self.assertTrue(authority["hardware_backed_non_exportable_signer_required"])
        self.assertFalse(authority["authority_container_private_key_file_allowed"])
        self.assertFalse(authority["edge_private_release_signing_key_allowed"])

    def test_boundary_drift_is_rejected(self):
        value = copy.deepcopy(self.contract)
        value["update_boundary"]["management_transport_required"] = True
        with self.assertRaises(FirmwareLifecycleContractError):
            validate_firmware_lifecycle_contract(value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
