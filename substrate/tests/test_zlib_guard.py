#!/usr/bin/env python3
"""Regression tests for fail-closed .kfs zlib compiler identity enforcement."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "substrate" / "tools"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


GUARD = load_module("_kane_fabric_zlib_guard_test", TOOLS / "kane_fabric_zlib_guard.py")
ROADS_ENTRY = load_module(
    "_kane_fabric_zlib_guard_roads_entry_test",
    TOOLS / "kane_fabric_roads_entry.py",
)
WATER_ENTRY = load_module(
    "_kane_fabric_zlib_guard_water_entry_test",
    TOOLS / "kane_fabric_water_entry.py",
)


class ZlibGuardTests(unittest.TestCase):
    def test_repository_pin_matches_current_compiler_runtime(self) -> None:
        result = GUARD.require_pinned_zlib()
        self.assertEqual("pinned-zlib-match", result["status"])
        self.assertEqual(zlib.ZLIB_VERSION, result["compile_version"])
        self.assertEqual(zlib.ZLIB_RUNTIME_VERSION, result["runtime_version"])

    def test_runtime_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "third_party": [
                            {
                                "key": "zlib",
                                "pin": {
                                    "status": "test-pin",
                                    "observed_compile_version": zlib.ZLIB_VERSION,
                                    "observed_runtime_version": "0.0.0-mismatch",
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                RuntimeError,
                r"zlib identity mismatch.*Refusing to produce release-identity bytes",
            ):
                GUARD.require_pinned_zlib(manifest)

    def test_road_build_checks_guard_before_compiler(self) -> None:
        with mock.patch.object(
            ROADS_ENTRY.COMPRESSION,
            "require_pinned_zlib",
            side_effect=RuntimeError("blocked by zlib guard"),
        ), mock.patch.object(ROADS_ENTRY, "_UNGUARDED_BUILD_COMPONENT") as compiler:
            with self.assertRaisesRegex(RuntimeError, "blocked by zlib guard"):
                ROADS_ENTRY.ROADS.build_component(Path("database"), Path("roads.kfs"))
            compiler.assert_not_called()

    def test_water_build_checks_guard_before_compiler(self) -> None:
        with mock.patch.object(
            WATER_ENTRY.COMPRESSION,
            "require_pinned_zlib",
            side_effect=RuntimeError("blocked by zlib guard"),
        ), mock.patch.object(WATER_ENTRY, "_UNGUARDED_BUILD_COMPONENT") as compiler:
            with self.assertRaisesRegex(RuntimeError, "blocked by zlib guard"):
                WATER_ENTRY.WATER.build_component(Path("database"), Path("water.kfs"))
            compiler.assert_not_called()

    def test_supported_shell_paths_use_guarded_entry_points(self) -> None:
        water_wrapper = (ROOT / "substrate" / "kane-fabric-water.sh").read_text(
            encoding="utf-8"
        )
        package_wrapper = (ROOT / "substrate" / "kane-fabric-package.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("kane_fabric_water_entry.py", water_wrapper)
        self.assertIn("kane_fabric_zlib_guard.py", package_wrapper)
        self.assertIn('"${1:-}" = "build"', package_wrapper)


if __name__ == "__main__":
    unittest.main()
