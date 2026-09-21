from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from ms5.tools.kane_fabric_edge_image import EdgeImageError, load_inventory, stage_inventory
from ms5.tools.kane_fabric_storage import build_inventory, verify_inventory_files


REPO = Path(__file__).resolve().parents[2]
REFERENCE = REPO / "ms5" / "esp32_reference"


class Esp32ReferenceTests(unittest.TestCase):
    def test_reference_hardware_defaults_pin_target_and_flash_size(self):
        defaults = (REFERENCE / "sdkconfig.defaults").read_text().splitlines()
        self.assertIn('CONFIG_IDF_TARGET="esp32s3"', defaults)
        self.assertIn("CONFIG_ESPTOOLPY_FLASHSIZE_16MB=y", defaults)

    def test_ms5_009_reference_layout_adds_ota_without_moving_accepted_partitions(self):
        partitions = (REFERENCE / "partitions.fabric-4m.csv").read_text()
        self.assertIn("factory,    app,  factory, 0x10000,  1M,", partitions)
        self.assertIn("fabric,     data, fat,     0x110000, 4M,", partitions)
        self.assertIn("otadata,    data, ota,     0x510000, 8K,", partitions)
        self.assertIn("ota_0,      app,  ota_0,   0x520000, 1M,", partitions)
        self.assertIn("ota_1,      app,  ota_1,   0x620000, 1M,", partitions)

        defaults = (REFERENCE / "sdkconfig.defaults").read_text().splitlines()
        self.assertIn("CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE=y", defaults)
        self.assertNotIn("CONFIG_BOOTLOADER_APP_ANTI_ROLLBACK=y", defaults)

    def test_ms5_009_lifecycle_uses_application_controlled_trial_confirmation(self):
        source = (
            REFERENCE
            / "components/kane_fabric_firmware_lifecycle/kane_fabric_firmware_lifecycle.c"
        ).read_text()
        self.assertIn("ESP_OTA_IMG_PENDING_VERIFY", source)
        self.assertIn("esp_ota_mark_app_valid_cancel_rollback", source)
        self.assertIn("esp_ota_mark_app_invalid_rollback_and_reboot", source)
        self.assertNotIn("esp_http_client", source)
        self.assertNotIn("wireguard", source.lower())

    def test_ms5_009_app_confirms_only_after_usable_runtime_path(self):
        app = (REFERENCE / "main/app_main.c").read_text()
        confirm = "kf_firmware_lifecycle_confirm_healthy_boot()"
        self.assertEqual(2, app.count(confirm))
        self.assertLess(
            app.index("MS5-007 local provisioning portal active"),
            app.index(confirm),
        )
        ready = app.index("MS5-007 HTTP artifact server ready")
        final_confirm = app.rindex(confirm)
        self.assertLess(ready, final_confirm)
        self.assertGreater(final_confirm, app.index("kf_artifact_server_register"))

    def test_ms5_009_update_writer_requires_pre_authorized_exact_image(self):
        header = (
            REFERENCE
            / "components/kane_fabric_firmware_update/include/kane_fabric_firmware_update.h"
        ).read_text()
        source = (
            REFERENCE
            / "components/kane_fabric_firmware_update/kane_fabric_firmware_update.c"
        ).read_text()

        self.assertIn("higher layer has authenticated and accepted", header)
        self.assertIn("firmware_byte_length", header)
        self.assertIn("firmware_sha256", header)
        self.assertIn("esp_ota_get_next_update_partition", source)
        self.assertIn("esp_ota_begin", source)
        self.assertIn("esp_ota_write", source)
        self.assertIn("PSA_ALG_SHA_256", source)
        self.assertIn("psa_hash_update", source)
        self.assertIn("psa_hash_finish", source)
        self.assertIn("ESP_ERR_INVALID_CRC", source)
        self.assertIn("esp_ota_end", source)
        self.assertIn("esp_ota_set_boot_partition", source)

    def test_ms5_009_update_writer_is_transport_and_signer_independent(self):
        source = (
            REFERENCE
            / "components/kane_fabric_firmware_update/kane_fabric_firmware_update.c"
        ).read_text().lower()
        cmake = (
            REFERENCE
            / "components/kane_fabric_firmware_update/CMakeLists.txt"
        ).read_text().lower()

        for forbidden in (
            "esp_http_client",
            "esp_https_ota",
            "wireguard",
            "private_key",
            "signing_key",
            "esp_restart",
        ):
            self.assertNotIn(forbidden, source)
            self.assertNotIn(forbidden, cmake)

    def test_ms5_009_update_writer_selects_trial_only_after_digest_check(self):
        source = (
            REFERENCE
            / "components/kane_fabric_firmware_update/kane_fabric_firmware_update.c"
        ).read_text()
        digest_check = source.index("memcmp(")
        ota_end = source.index("esp_ota_end(handle)")
        boot_select = source.index("esp_ota_set_boot_partition(partition)")
        self.assertLess(digest_check, ota_end)
        self.assertLess(ota_end, boot_select)

    def test_ms5_009_device_authorization_is_public_key_only(self):
        header = (
            REFERENCE
            / "components/kane_fabric_firmware_authorization/include/kane_fabric_firmware_authorization.h"
        ).read_text()
        source = (
            REFERENCE
            / "components/kane_fabric_firmware_authorization/kane_fabric_firmware_authorization.c"
        ).read_text()

        self.assertIn("P256_PUBLIC_KEY_BYTES 65U", header)
        self.assertIn("P256_SIGNATURE_BYTES 64U", header)
        self.assertIn("No private release-signing key", header)
        self.assertIn("PSA_KEY_TYPE_ECC_PUBLIC_KEY(PSA_ECC_FAMILY_SECP_R1)", source)
        self.assertIn("PSA_ALG_ECDSA(PSA_ALG_SHA_256)", source)
        self.assertIn("psa_verify_hash", source)
        self.assertIn("psa_destroy_key", source)
        self.assertNotIn("PSA_KEY_TYPE_ECC_KEY_PAIR", source)
        self.assertNotIn("psa_generate_key", source)

    def test_ms5_009_device_authorization_binds_key_id_to_public_key(self):
        source = (
            REFERENCE
            / "components/kane_fabric_firmware_authorization/kane_fabric_firmware_authorization.c"
        ).read_text()
        self.assertIn("psa_hash_compute", source)
        self.assertIn("derived_key_id", source)
        self.assertIn("authorization->key_id_sha256", source)
        self.assertLess(
            source.index("authorization->key_id_sha256"),
            source.index("psa_import_key"),
        )

    def test_host_range_core_compiles_and_passes(self):
        compiler = shutil.which("cc")
        if compiler is None:
            self.skipTest(
                "host C compiler unavailable in CT102; authoritative pinned ESP-IDF compile is accepted on fw"
            )
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / "http-core-test"
            subprocess.run(
                [
                    compiler,
                    "-std=c11",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-I",
                    str(REFERENCE / "components/kane_fabric_http/include"),
                    str(REFERENCE / "components/kane_fabric_http/kane_fabric_http.c"),
                    str(REFERENCE / "host_test/test_kane_fabric_http.c"),
                    "-o",
                    str(binary),
                ],
                check=True,
                cwd=REPO,
            )
            subprocess.run([str(binary)], check=True)

    def test_artifact_server_uses_exact_length_raw_streaming(self):
        source = (
            REFERENCE
            / "components/kane_fabric_artifact_server/kane_fabric_artifact_server.c"
        ).read_text()
        self.assertIn("httpd_send(req", source)
        self.assertIn("Content-Length: %", source)
        self.assertIn("206 Partial Content", source)
        self.assertIn("416 Range Not Satisfiable", source)
        self.assertIn("Content-Range: bytes */", source)
        self.assertIn("Access-Control-Allow-Origin: *", source)
        self.assertIn("Access-Control-Expose-Headers:", source)
        self.assertNotIn("httpd_resp_send_chunk", source)

    def test_storage_mount_is_raw_read_only(self):
        source = (
            REFERENCE / "components/kane_fabric_storage/kane_fabric_storage.c"
        ).read_text()
        self.assertIn("esp_vfs_fat_spiflash_mount_ro", source)
        self.assertIn("esp_vfs_fat_spiflash_unmount_ro", source)
        self.assertIn(".format_if_mount_failed = false", source)
        self.assertNotIn(".read_only = true", source)
        self.assertNotIn("format_rw", source)

    def test_components_depend_only_on_esp_idf_builtins(self):
        artifact_cmake = (
            REFERENCE / "components/kane_fabric_artifact_server/CMakeLists.txt"
        ).read_text()
        storage_cmake = (
            REFERENCE / "components/kane_fabric_storage/CMakeLists.txt"
        ).read_text()
        self.assertIn("REQUIRES esp_http_server kane_fabric_http", artifact_cmake)
        self.assertIn("REQUIRES fatfs", storage_cmake)
        for forbidden in ("littlefs", "mongoose", "civetweb", "arduino"):
            self.assertNotIn(forbidden, artifact_cmake.lower())
            self.assertNotIn(forbidden, storage_cmake.lower())

    def test_reference_app_uses_generic_fabric_storage_not_county_mirroring(self):
        cmake = (REFERENCE / "CMakeLists.txt").read_text()
        app = (REFERENCE / "main/app_main.c").read_text()
        self.assertNotIn("partitions.csv", cmake)
        self.assertNotIn("0x", cmake)
        self.assertIn('.partition_label = "fabric"', app)
        for county_artifact in (
            "county-overview.json",
            "roads-lod.kfs",
            "water-lod.kfs",
            "substrate-manifest.json",
        ):
            self.assertNotIn(county_artifact, app)

    def test_reference_app_builds_and_verifies_participant_image(self):
        cmake = (REFERENCE / "main/CMakeLists.txt").read_text()
        app = (REFERENCE / "main/app_main.c").read_text()

        self.assertIn("../participant_image", cmake)
        self.assertIn("participant.json", cmake)
        self.assertIn("fatfs_create_rawflash_image(", cmake)
        self.assertNotIn("../probe_image", cmake)
        self.assertNotIn("probe.txt", cmake)

        self.assertIn('relative_path = "participant.json"', app)
        self.assertIn("PARTICIPANT_VERIFICATION", app)
        self.assertIn("MS5-007 participant image verified", app)
        self.assertNotIn('relative_path = "probe.txt"', app)
        self.assertNotIn("PROBE_VERIFICATION", app)

    def test_reference_app_keeps_browser_tls_off_the_esp32(self):
        app = (REFERENCE / "main/app_main.c").read_text()
        self.assertIn("HTTPD_DEFAULT_CONFIG()", app)
        self.assertIn("httpd_start(&HTTP_SERVER", app)
        self.assertIn("kf_artifact_server_register", app)
        for forbidden in (
            "httpd_ssl_start",
            "esp_https_server",
            "servercert",
            "prvtkey",
            "browser-trusted HTTPS server startup",
        ):
            self.assertNotIn(forbidden, app)

    def test_reference_contract_docs_keep_tls_at_wiregate(self):
        header = (
            REFERENCE
            / "components/kane_fabric_artifact_server/include/kane_fabric_artifact_server.h"
        ).read_text()
        gates = (REPO / "docs/CONSUMER_INTERFACE_GATES.md").read_text()
        ms3 = (REPO / "docs/MILESTONE_3_DESIGN.md").read_text()

        self.assertIn("plain HTTP", header)
        self.assertIn("Wiregate hub", header)
        self.assertNotIn("HTTP/HTTPS server", header)
        self.assertNotIn("browser-trusted HTTPS server", header)

        self.assertIn("browser HTTPS terminates at the Wiregate hub", gates)
        self.assertNotIn(
            "normal browser must reach a local physical Fabric edge and obtain a secure context",
            gates,
        )
        self.assertNotIn("Fabric edge TLS keys", gates)

        self.assertIn("Historical Milestone 3 design baseline", ms3)
        self.assertIn("later accepted MS5 transport correction supersedes", ms3)

    def test_reference_participant_image_is_verified_and_bounded(self):
        image = REFERENCE / "participant_image"
        inventory = load_inventory(image / ".kane-fabric-storage-inventory.json")
        verify_inventory_files(inventory, image)

        self.assertEqual(
            "02c9230496b677f12e49af696afbc5fb06116fe10c3d9818ec85e6f2445ac7a3",
            inventory["logical_placement_sha256"],
        )
        self.assertEqual(
            ["participant-publication"],
            [item["artifact_key"] for item in inventory["artifacts"]],
        )
        self.assertEqual(
            ["participant.json"],
            [item["path"] for item in inventory["artifacts"]],
        )

        publication = json.loads((image / "participant.json").read_text())
        self.assertEqual(
            "kane-fabric-participant-publication",
            publication["format"],
        )
        association = publication["association_unit_identity"]["association_anchor"]
        self.assertEqual(
            "synthetic-public-recording-authority",
            association["recording_authority_reference"],
        )
        geographic_ref = publication["descriptor_instances"][0]["geographic_refs"][0]
        self.assertEqual("buildings", geographic_ref["dataset_key"])
        self.assertEqual(
            "kcb-aee53d8f13ccc7eebbf23d2a4c42d7d1d939f9b4b057584966642827bace7fb1",
            geographic_ref["object_key"],
        )

    def test_edge_image_staging_preserves_verified_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            destination = root / "image"
            first = source / "substrate/substrate-manifest.json"
            second = source / "composition/composition-manifest.json"
            first.parent.mkdir(parents=True)
            second.parent.mkdir(parents=True)
            first.write_bytes(b"substrate")
            second.write_bytes(b"composition")

            inventory = build_inventory(
                logical_placement_sha256="a" * 64,
                artifacts=[
                    {
                        "artifact_key": "substrate-manifest",
                        "path": "substrate/substrate-manifest.json",
                        "byte_length": first.stat().st_size,
                        "sha256": hashlib.sha256(first.read_bytes()).hexdigest(),
                    },
                    {
                        "artifact_key": "composition-manifest",
                        "path": "composition/composition-manifest.json",
                        "byte_length": second.stat().st_size,
                        "sha256": hashlib.sha256(second.read_bytes()).hexdigest(),
                    },
                ],
            )

            result = stage_inventory(inventory, source, destination)
            self.assertEqual(destination.resolve(), result)
            self.assertEqual(
                b"substrate",
                (destination / "substrate/substrate-manifest.json").read_bytes(),
            )
            self.assertEqual(
                b"composition",
                (destination / "composition/composition-manifest.json").read_bytes(),
            )
            self.assertTrue(
                (destination / ".kane-fabric-storage-inventory.json").is_file()
            )

    def test_edge_image_refuses_existing_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            destination = root / "image"
            artifact = source / "one.bin"
            artifact.parent.mkdir(parents=True)
            artifact.write_bytes(b"x")
            destination.mkdir()

            inventory = build_inventory(
                logical_placement_sha256="a" * 64,
                artifacts=[
                    {
                        "artifact_key": "one",
                        "path": "one.bin",
                        "byte_length": 1,
                        "sha256": hashlib.sha256(b"x").hexdigest(),
                    }
                ],
            )

            with self.assertRaises(EdgeImageError):
                stage_inventory(inventory, source, destination)


if __name__ == "__main__":
    unittest.main(verbosity=2)
