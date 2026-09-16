from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from ms5.tools.kane_fabric_edge_image import EdgeImageError, stage_inventory
from ms5.tools.kane_fabric_storage import build_inventory


REPO = Path(__file__).resolve().parents[2]
REFERENCE = REPO / "ms5" / "esp32_reference"


class Esp32ReferenceTests(unittest.TestCase):
    def test_reference_hardware_defaults_pin_target_and_flash_size(self):
        defaults = (REFERENCE / "sdkconfig.defaults").read_text().splitlines()
        self.assertIn('CONFIG_IDF_TARGET="esp32s3"', defaults)
        self.assertIn("CONFIG_ESPTOOLPY_FLASHSIZE_16MB=y", defaults)

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
        source = (REFERENCE / "components/kane_fabric_artifact_server/kane_fabric_artifact_server.c").read_text()
        self.assertIn("httpd_send(req", source)
        self.assertIn("Content-Length: %", source)
        self.assertIn("206 Partial Content", source)
        self.assertIn("416 Range Not Satisfiable", source)
        self.assertIn("Content-Range: bytes */", source)
        self.assertIn("Access-Control-Allow-Origin: *", source)
        self.assertIn("Access-Control-Expose-Headers:", source)
        self.assertNotIn("httpd_resp_send_chunk", source)

    def test_storage_mount_is_raw_read_only(self):
        source = (REFERENCE / "components/kane_fabric_storage/kane_fabric_storage.c").read_text()
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

    def test_reference_build_probe_has_no_fixed_storage_capacity(self):
        cmake = (REFERENCE / "CMakeLists.txt").read_text()
        app = (REFERENCE / "main/app_main.c").read_text()
        self.assertNotIn("partitions.csv", cmake)
        self.assertNotIn("0x", cmake)
        self.assertIn("deployment/runtime integration work", app)

    def test_reference_app_keeps_browser_tls_off_the_esp32(self):
        app = (REFERENCE / "main/app_main.c").read_text()
        self.assertIn("plain HTTP artifact-server startup", app)
        self.assertIn("HTTPS terminates at the Wiregate hub", app)
        self.assertNotIn("browser-trusted HTTPS server startup", app)

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
            self.assertEqual(b"substrate", (destination / "substrate/substrate-manifest.json").read_bytes())
            self.assertEqual(b"composition", (destination / "composition/composition-manifest.json").read_bytes())
            self.assertTrue((destination / ".kane-fabric-storage-inventory.json").is_file())

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
