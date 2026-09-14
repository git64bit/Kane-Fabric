from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ms5.tools.kane_fabric_toolchain import (
    ToolchainContractError,
    load_selection,
    validate_manifest_binding,
    validate_toolchain_selection,
)

ROOT = Path(__file__).resolve().parents[2]
SELECTION_PATH = ROOT / "ms5" / "toolchain-selection.json"
MANIFEST_PATH = ROOT / "third_party" / "manifest.json"


class ToolchainSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selection = load_selection(SELECTION_PATH)
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_repository_selection_valid(self):
        validate_toolchain_selection(self.selection)

    def test_manifest_binding_valid(self):
        validate_manifest_binding(self.selection, self.manifest)

    def test_moving_sdk_tag_is_rejected(self):
        value = copy.deepcopy(self.selection)
        value["sdk"]["tag"] = "release/v6.0"
        with self.assertRaises(ToolchainContractError):
            validate_toolchain_selection(value)

    def test_sdk_source_hash_drift_is_rejected(self):
        value = copy.deepcopy(self.selection)
        value["sdk"]["source_sha256"] = "0" * 64
        with self.assertRaises(ToolchainContractError):
            validate_toolchain_selection(value)

    def test_compiler_hash_drift_is_rejected(self):
        value = copy.deepcopy(self.selection)
        value["compiler"]["source_sha256"] = "f" * 64
        with self.assertRaises(ToolchainContractError):
            validate_toolchain_selection(value)

    def test_live_release_resolution_cannot_be_enabled(self):
        value = copy.deepcopy(self.selection)
        value["dependency_boundary"]["package_manager_resolution_at_release"] = True
        with self.assertRaises(ToolchainContractError):
            validate_toolchain_selection(value)

    def test_manifest_sdk_drift_is_rejected(self):
        manifest = copy.deepcopy(self.manifest)
        entry = next(item for item in manifest["third_party"] if item["key"] == "esp-idf")
        entry["pin"]["version"] = "6.1"
        with self.assertRaises(ToolchainContractError):
            validate_manifest_binding(self.selection, manifest)

    def test_wireguard_cannot_be_retained_before_ms5_008(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["third_party"].append(
            {
                "key": "wireguard-example",
                "license": "BSD-3-Clause",
                "license_impact": "does-not-relicense-kane-fabric",
                "pin": {"status": "selected-not-vendored"},
                "reason": "invalid early retention",
                "role": "firmware-library",
                "vendoring_requirement": "required-before-firmware-release",
            }
        )
        with self.assertRaises(ToolchainContractError):
            validate_manifest_binding(self.selection, manifest)


if __name__ == "__main__":
    unittest.main(verbosity=2)
