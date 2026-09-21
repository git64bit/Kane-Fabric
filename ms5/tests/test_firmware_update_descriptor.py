from __future__ import annotations

import copy
import unittest

from ms5.tools.kane_fabric_firmware_authority import build_release_manifest
from ms5.tools.kane_fabric_firmware_authorization import (
    build_authorization_envelope,
    derive_key_id_sha256,
)
from ms5.tools.kane_fabric_firmware_update_descriptor import (
    FirmwareUpdateDescriptorError,
    build_update_descriptor,
    validate_update_descriptor,
)

A = "a" * 64
B = "b" * 64
COMMIT = "c" * 40
PUBLIC_KEY = b"\x04" + bytes(range(1, 65))
SIGNATURE = bytes(range(64))


class FirmwareUpdateDescriptorTests(unittest.TestCase):
    def _manifest(self):
        return build_release_manifest(
            device_family="esp32-s3",
            target="esp32s3",
            release_version="0.2.0",
            release_sequence=2,
            firmware_name="kane_fabric_ms5_edge_reference.bin",
            firmware_sha256=A,
            firmware_byte_length=900000,
            source_repository="git64bit/Kane-Fabric",
            source_commit=COMMIT,
            toolchain_record="ms5/toolchain-selection.json",
            toolchain_record_sha256=B,
            build_identity="cpe-build:test",
            rollback_floor_sequence=1,
            recovery_compatible=True,
        )

    def _authorization(self, manifest):
        return build_authorization_envelope(
            manifest_sha256=manifest["manifest_sha256"],
            key_id_sha256=derive_key_id_sha256(PUBLIC_KEY),
            signature=SIGNATURE,
        )

    def test_descriptor_is_derived_from_manifest_and_authorization(self):
        manifest = self._manifest()
        descriptor = build_update_descriptor(
            manifest,
            self._authorization(manifest),
        )
        validate_update_descriptor(descriptor)
        self.assertEqual(manifest["manifest_sha256"], descriptor["manifest_sha256"])
        self.assertEqual(A, descriptor["firmware_sha256"])
        self.assertEqual(900000, descriptor["firmware_byte_length"])
        self.assertEqual(2, descriptor["release_sequence"])
        self.assertEqual(1, descriptor["rollback_floor_sequence"])

    def test_authorization_for_another_manifest_is_rejected(self):
        manifest = self._manifest()
        other = copy.deepcopy(manifest)
        other["manifest_sha256"] = "d" * 64
        with self.assertRaises(FirmwareUpdateDescriptorError):
            build_update_descriptor(
                manifest,
                self._authorization(other),
            )

    def test_non_esp32_reference_target_is_rejected(self):
        manifest = build_release_manifest(
            device_family="other",
            target="generic",
            release_version="0.2.0",
            release_sequence=2,
            firmware_name="firmware.bin",
            firmware_sha256=A,
            firmware_byte_length=900000,
            source_repository="git64bit/Kane-Fabric",
            source_commit=COMMIT,
            toolchain_record="ms5/toolchain-selection.json",
            toolchain_record_sha256=B,
            build_identity="cpe-build:test",
            rollback_floor_sequence=1,
            recovery_compatible=True,
        )
        with self.assertRaises(FirmwareUpdateDescriptorError):
            build_update_descriptor(
                manifest,
                self._authorization(manifest),
            )

    def test_descriptor_rejects_sequence_floor_drift(self):
        manifest = self._manifest()
        descriptor = build_update_descriptor(
            manifest,
            self._authorization(manifest),
        )
        descriptor["rollback_floor_sequence"] = 3
        with self.assertRaises(FirmwareUpdateDescriptorError):
            validate_update_descriptor(descriptor)


if __name__ == "__main__":
    unittest.main(verbosity=2)
