from __future__ import annotations

import json
import unittest
from pathlib import Path

from ms5.tools.kane_fabric_firmware_authority import (
    FIXED_AUTHORITY_BOUNDARY,
    FirmwareAuthorityContractError,
    build_authority_state,
    build_release_manifest,
    validate_authority_state,
    validate_release_manifest,
)

A = "a" * 64
B = "b" * 64
COMMIT = "c" * 40
REPO = Path(__file__).resolve().parents[2]


class FirmwareAuthorityTests(unittest.TestCase):
    def _manifest(self, *, family: str = "esp32-s3", sequence: int = 1):
        return build_release_manifest(
            device_family=family,
            target="esp32s3" if family == "esp32-s3" else "generic",
            release_version="0.1.0",
            release_sequence=sequence,
            firmware_name="firmware.bin",
            firmware_sha256=A,
            firmware_byte_length=1234,
            source_repository="git64bit/Kane-Fabric",
            source_commit=COMMIT,
            toolchain_record="ms5/toolchain-selection.json",
            toolchain_record_sha256=B,
            build_identity="cpe-build:test",
            rollback_floor_sequence=0,
            recovery_compatible=True,
        )

    def test_placeholder_authority_has_no_signing_key_or_network_identity(self):
        state = build_authority_state(enabled_device_families=["esp32-s3"])
        validate_authority_state(state)
        self.assertIsNone(state["network_identity"])
        self.assertFalse(state["private_signing_key_created"])
        self.assertFalse(state["signing_enabled"])
        self.assertTrue(FIXED_AUTHORITY_BOUNDARY["hardware_backed_signer_required_for_activation"])

    def test_authority_is_generalized_by_device_family(self):
        state = build_authority_state(
            enabled_device_families=["future-family", "esp32-s3", "zigbee-family-a"]
        )
        validate_authority_state(state)
        self.assertEqual(
            ["esp32-s3", "future-family", "zigbee-family-a"],
            state["enabled_device_families"],
        )

    def test_container_private_key_activation_is_rejected_in_placeholder_state(self):
        state = build_authority_state(enabled_device_families=["esp32-s3"])
        state["private_signing_key_created"] = True
        with self.assertRaises(FirmwareAuthorityContractError):
            validate_authority_state(state)

    def test_tracked_placeholder_state_validates(self):
        state = json.loads(
            (REPO / "ms5/firmware_authority/authority-state.json").read_text()
        )
        validate_authority_state(state)

    def test_inert_container_spec_is_pinned_and_host_mediated(self):
        spec = json.loads(
            (REPO / "ms5/firmware_authority/container-spec.json").read_text()
        )
        self.assertEqual("annales", spec["physical_host"]["hostname"])
        self.assertEqual("firmware-authority", spec["instance"]["name"])
        self.assertEqual("default", spec["instance"]["project"])
        self.assertTrue(spec["instance"]["unprivileged"])
        self.assertTrue(spec["instance"]["boot_autostart"])
        self.assertEqual(
            "6330af160fc7a345119549990a92e7cba23c25bc846e4906729f525d6ddd1b19",
            spec["image"]["fingerprint"],
        )
        self.assertEqual("fingerprint", spec["image"]["pinned_by"])
        self.assertEqual("2", spec["resources"]["limits_cpu"])
        self.assertEqual("2GiB", spec["resources"]["limits_memory"])
        self.assertEqual("16GiB", spec["resources"]["root_disk_size"])
        self.assertEqual("lxdbr0", spec["network"]["network"])
        self.assertFalse(spec["network"]["independent_cpe_address"])
        self.assertFalse(spec["network"]["wireguard_peer"])
        self.assertTrue(spec["prohibited_initial_devices"]["gpu"])
        self.assertTrue(spec["prohibited_initial_devices"]["host_directory_passthrough"])
        self.assertTrue(spec["prohibited_initial_devices"]["proxy"])
        self.assertTrue(spec["prohibited_initial_devices"]["usb_signer"])
        self.assertFalse(spec["authority_state"]["private_signing_key_created"])
        self.assertFalse(spec["authority_state"]["signing_enabled"])
        self.assertFalse(spec["authority_state"]["hardware_signer_attached"])
        self.assertTrue(spec["creation_policy"]["create_stopped_first"])
        self.assertTrue(spec["creation_policy"]["inspect_expanded_config_before_start"])

    def test_authority_document_keeps_ms5_009_activation_boundary(self):
        text = (REPO / "docs/MS5_FIRMWARE_AUTHORITY_NODE.md").read_text()
        self.assertIn("MS5-009", text)
        self.assertIn("private signing key: NOT CREATED", text)
        self.assertIn("unprivileged LXC/LXD container", text)
        self.assertIn("hardware-backed", text)

    def test_release_manifest_builds_and_validates(self):
        manifest = self._manifest()
        validate_release_manifest(manifest)
        self.assertEqual("esp32-s3", manifest["release"]["device_family"])
        self.assertEqual(A, manifest["firmware"]["sha256"])

    def test_manifest_identity_changes_when_firmware_changes(self):
        first = self._manifest()
        second = self._manifest()
        second["firmware"] = dict(second["firmware"])
        second["firmware"]["sha256"] = "d" * 64
        with self.assertRaises(FirmwareAuthorityContractError):
            validate_release_manifest(second)
        self.assertNotEqual(A, second["firmware"]["sha256"])
        self.assertEqual(first["manifest_sha256"], self._manifest()["manifest_sha256"])

    def test_manifest_rejects_rollback_floor_above_release_sequence(self):
        with self.assertRaises(FirmwareAuthorityContractError):
            build_release_manifest(
                device_family="esp32-s3",
                target="esp32s3",
                release_version="0.1.0",
                release_sequence=2,
                firmware_name="firmware.bin",
                firmware_sha256=A,
                firmware_byte_length=1234,
                source_repository="git64bit/Kane-Fabric",
                source_commit=COMMIT,
                toolchain_record="ms5/toolchain-selection.json",
                toolchain_record_sha256=B,
                build_identity="cpe-build:test",
                rollback_floor_sequence=3,
                recovery_compatible=True,
            )

    def test_manifest_is_device_family_generic(self):
        manifest = self._manifest(family="zigbee-family-a", sequence=7)
        validate_release_manifest(manifest)
        self.assertEqual("zigbee-family-a", manifest["release"]["device_family"])
        self.assertEqual(7, manifest["release"]["sequence"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
