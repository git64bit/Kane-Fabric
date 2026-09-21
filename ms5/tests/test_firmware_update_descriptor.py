from __future__ import annotations

import copy
import unittest

from ms5.tools.kane_fabric_firmware_authority import build_release_manifest
from ms5.tools.kane_fabric_firmware_authorization import (
    authorization_payload_sha256,
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
        release = manifest["release"]
        firmware = manifest["firmware"]
        recovery = manifest["recovery"]
        payload_sha = authorization_payload_sha256(
            device_family=release["device_family"],
            target=release["target"],
            manifest_sha256=manifest["manifest_sha256"],
            firmware_sha256=firmware["sha256"],
            firmware_byte_length=firmware["byte_length"],
            release_sequence=release["sequence"],
            rollback_floor_sequence=recovery["rollback_floor_sequence"],
        )
        return build_authorization_envelope(
            authorization_payload_sha256=payload_sha,
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

    def test_authorization_for_changed_firmware_fields_is_rejected(self):
        manifest = self._manifest()
        authorization = self._authorization(manifest)
        changed = copy.deepcopy(manifest)
        changed["firmware"] = dict(changed["firmware"])
        changed["firmware"]["sha256"] = "d" * 64
        changed["manifest_sha256"] = manifest["manifest_sha256"]
        with self.assertRaises(Exception):
            build_update_descriptor(changed, authorization)

    def test_descriptor_field_tampering_breaks_payload_identity(self):
        manifest = self._manifest()
        descriptor = build_update_descriptor(
            manifest,
            self._authorization(manifest),
        )
        descriptor["firmware_byte_length"] += 1
        with self.assertRaises(FirmwareUpdateDescriptorError):
            validate_update_descriptor(descriptor)

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
