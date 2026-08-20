#!/usr/bin/env python3
"""Regression tests for explicit substrate zlib compiler identity enforcement."""

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
MODULE_PATH = ROOT / "substrate" / "tools" / "kane_fabric_compression.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


COMPRESSION = load_module("_kane_fabric_compression_runtime_test", MODULE_PATH)


def write_manifest(
    path: Path,
    *,
    expected_compile: str | None,
    expected_runtime: str | None,
    observed_compile: str | None = None,
    observed_runtime: str | None = None,
) -> None:
    pin: dict[str, str] = {"status": "test-observation"}
    if expected_compile is not None:
        pin["expected_compile_version"] = expected_compile
    if expected_runtime is not None:
        pin["expected_runtime_version"] = expected_runtime
    if observed_compile is not None:
        pin["observed_compile_version"] = observed_compile
    if observed_runtime is not None:
        pin["observed_runtime_version"] = observed_runtime
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "third_party": [
                    {
                        "key": "zlib",
                        "pin": pin,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


class CompressionRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.manifest = Path(self.temp.name) / "manifest.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_matching_expected_identity_passes(self) -> None:
        write_manifest(
            self.manifest,
            expected_compile=zlib.ZLIB_VERSION,
            expected_runtime=zlib.ZLIB_RUNTIME_VERSION,
            observed_compile="historical-compile-value-is-not-authority",
            observed_runtime="historical-runtime-value-is-not-authority",
        )
        result = COMPRESSION.require_accepted_zlib(self.manifest)
        self.assertEqual("match", result["status"])
        self.assertEqual(zlib.ZLIB_VERSION, result["observed_compile_version"])
        self.assertEqual(zlib.ZLIB_RUNTIME_VERSION, result["observed_runtime_version"])

    def test_runtime_mismatch_fails_closed(self) -> None:
        write_manifest(
            self.manifest,
            expected_compile=zlib.ZLIB_VERSION,
            expected_runtime="0.0.0-deliberate-mismatch",
        )
        with self.assertRaisesRegex(RuntimeError, "zlib identity mismatch"):
            COMPRESSION.require_accepted_zlib(self.manifest)

    def test_compile_mismatch_fails_closed(self) -> None:
        write_manifest(
            self.manifest,
            expected_compile="0.0.0-deliberate-mismatch",
            expected_runtime=zlib.ZLIB_RUNTIME_VERSION,
        )
        with self.assertRaisesRegex(RuntimeError, "zlib identity mismatch"):
            COMPRESSION.require_accepted_zlib(self.manifest)

    def test_missing_expected_field_fails_closed(self) -> None:
        write_manifest(
            self.manifest,
            expected_compile=zlib.ZLIB_VERSION,
            expected_runtime=None,
            observed_runtime=zlib.ZLIB_RUNTIME_VERSION,
        )
        with self.assertRaisesRegex(
            RuntimeError, "expected_runtime_version is missing or invalid"
        ):
            COMPRESSION.require_accepted_zlib(self.manifest)

    def test_observed_match_cannot_override_expected_mismatch(self) -> None:
        write_manifest(
            self.manifest,
            expected_compile=zlib.ZLIB_VERSION,
            expected_runtime="0.0.0-deliberate-mismatch",
            observed_compile=zlib.ZLIB_VERSION,
            observed_runtime=zlib.ZLIB_RUNTIME_VERSION,
        )
        with self.assertRaisesRegex(RuntimeError, "zlib identity mismatch"):
            COMPRESSION.require_accepted_zlib(self.manifest)

    def test_observed_mismatch_cannot_override_expected_match(self) -> None:
        write_manifest(
            self.manifest,
            expected_compile=zlib.ZLIB_VERSION,
            expected_runtime=zlib.ZLIB_RUNTIME_VERSION,
            observed_compile="0.0.0-historical-mismatch",
            observed_runtime="0.0.0-historical-mismatch",
        )
        result = COMPRESSION.require_accepted_zlib(self.manifest)
        self.assertEqual("match", result["status"])

    def test_observation_uses_current_python_zlib_values(self) -> None:
        with mock.patch.object(COMPRESSION.zlib, "ZLIB_VERSION", "1.2.3-test"), mock.patch.object(
            COMPRESSION.zlib, "ZLIB_RUNTIME_VERSION", "4.5.6-test"
        ):
            self.assertEqual(
                {
                    "observed_compile_version": "1.2.3-test",
                    "observed_runtime_version": "4.5.6-test",
                },
                COMPRESSION.observed_zlib_identity(),
            )


if __name__ == "__main__":
    unittest.main()
