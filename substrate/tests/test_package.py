#!/usr/bin/env python3
"""Regression tests for complete Kane Fabric v1 substrate package compilation."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
DATABASE_TOOLS = ROOT / "database" / "tools"
TOOLS = ROOT / "substrate" / "tools"
TESTS = ROOT / "substrate" / "tests"
WRAPPER = ROOT / "substrate" / "kane-fabric-package.sh"

if str(DATABASE_TOOLS) not in sys.path:
    sys.path.insert(0, str(DATABASE_TOOLS))

import kane_fabric_db as fabric_db


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PACKAGE = load_module("_kane_fabric_package_test", TOOLS / "kane_fabric_package.py")
MANIFEST_TEST = load_module("_kane_fabric_package_fixture", TESTS / "test_manifest.py")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class _SourceFixture:
    _descriptor = MANIFEST_TEST.ManifestTests._descriptor
    _write_collection = MANIFEST_TEST.ManifestTests._write_collection
    _record_sources = MANIFEST_TEST.ManifestTests._record_sources


class PackageCompilerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.database = self.root / "fabric.gpkg"
        self.package = self.root / "active-substrate"
        fabric_db.init_database(self.database)
        fixture = _SourceFixture()
        fixture.root = self.root
        fixture.database = self.database
        fixture._record_sources()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _package_bytes(self, root: Path | None = None) -> dict[str, bytes]:
        root = self.package if root is None else root
        return {
            filename: (root / filename).read_bytes()
            for filename in PACKAGE.PACKAGE_FILES
        }

    def test_build_proves_reproducibility_is_read_only_and_activates_exact_inventory(self) -> None:
        database_before = sha256_file(self.database)
        result = PACKAGE.build_package(self.database, self.package)
        info = PACKAGE.validate_package(self.database, self.package)

        self.assertEqual("built-and-activated", result["status"])
        self.assertEqual("reproducible", result["reproducibility"])
        self.assertEqual(database_before, result["database_sha256"])
        self.assertEqual(database_before, sha256_file(self.database))
        self.assertEqual("valid", info["status"])
        self.assertEqual(
            set(PACKAGE.PACKAGE_FILES),
            {path.name for path in self.package.iterdir()},
        )
        self.assertEqual(
            result["substrate_content_sha256"],
            info["substrate_content_sha256"],
        )
        self.assertFalse(PACKAGE._backup_path(self.package).exists())
        self.assertFalse(
            any(
                path.name.startswith(PACKAGE._staging_prefix(self.package))
                for path in self.root.iterdir()
            )
        )

    def test_zlib_mismatch_fails_before_package_destination_mutation(self) -> None:
        guarded_parent = self.root / "guarded-parent"
        guarded_package = guarded_parent / "active-substrate"

        with mock.patch.object(
            PACKAGE.COMPRESSION,
            "require_accepted_zlib",
            side_effect=RuntimeError("simulated zlib mismatch"),
        ) as guard, mock.patch.object(
            PACKAGE, "recover_interrupted_activation"
        ) as recover:
            with self.assertRaisesRegex(RuntimeError, "simulated zlib mismatch"):
                PACKAGE.build_package(self.database, guarded_package)

        guard.assert_called_once_with()
        recover.assert_not_called()
        self.assertFalse(guarded_parent.exists())

    def test_direct_staged_build_zlib_mismatch_writes_nothing(self) -> None:
        stage = self.root / "direct-stage"
        stage.mkdir()

        with mock.patch.object(
            PACKAGE.COMPRESSION,
            "require_accepted_zlib",
            side_effect=RuntimeError("simulated zlib mismatch"),
        ) as guard, mock.patch.object(
            PACKAGE.OVERVIEW, "build_overview"
        ) as overview:
            with self.assertRaisesRegex(RuntimeError, "simulated zlib mismatch"):
                PACKAGE._build_staged_package(self.database, stage)

        guard.assert_called_once_with()
        overview.assert_not_called()
        self.assertEqual([], list(stage.iterdir()))

    def test_zlib_mismatch_preserves_existing_active_package(self) -> None:
        PACKAGE.build_package(self.database, self.package)
        previous = self._package_bytes()

        with mock.patch.object(
            PACKAGE.COMPRESSION,
            "require_accepted_zlib",
            side_effect=RuntimeError("simulated zlib mismatch"),
        ):
            with self.assertRaisesRegex(RuntimeError, "simulated zlib mismatch"):
                PACKAGE.build_package(self.database, self.package)

        self.assertEqual(previous, self._package_bytes())
        self.assertFalse(PACKAGE._backup_path(self.package).exists())
        self.assertFalse(
            any(
                path.name.startswith(PACKAGE._staging_prefix(self.package))
                for path in self.root.iterdir()
            )
        )

    def test_failed_post_activation_validation_restores_previous_complete_package(self) -> None:
        PACKAGE.build_package(self.database, self.package)
        previous = self._package_bytes()
        original_validate = PACKAGE.validate_package

        def fail_only_active(database: Path, package_dir: Path):
            result = original_validate(database, package_dir)
            if package_dir.resolve() == self.package.resolve():
                raise RuntimeError("simulated post-activation validation failure")
            return result

        with mock.patch.object(PACKAGE, "validate_package", side_effect=fail_only_active):
            with self.assertRaisesRegex(RuntimeError, "simulated post-activation"):
                PACKAGE.build_package(self.database, self.package)

        self.assertEqual(previous, self._package_bytes())
        self.assertFalse(PACKAGE._backup_path(self.package).exists())
        self.assertEqual("valid", original_validate(self.database, self.package)["status"])

    def test_failed_staged_build_never_replaces_active_package(self) -> None:
        PACKAGE.build_package(self.database, self.package)
        previous = self._package_bytes()

        with mock.patch.object(
            PACKAGE.WATER,
            "build_component",
            side_effect=RuntimeError("simulated water compiler failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "simulated water compiler failure"):
                PACKAGE.build_package(self.database, self.package)

        self.assertEqual(previous, self._package_bytes())
        self.assertEqual("valid", PACKAGE.validate_package(self.database, self.package)["status"])

    def test_recovery_rolls_back_unfinalized_activation_and_removes_staging(self) -> None:
        PACKAGE.build_package(self.database, self.package)
        previous = self._package_bytes()
        backup = PACKAGE._backup_path(self.package)
        os.replace(self.package, backup)
        self.package.mkdir()
        (self.package / "partial-file").write_text("incomplete", encoding="utf-8")
        stale = self.root / f"{PACKAGE._staging_prefix(self.package)}stale"
        stale.mkdir()
        (stale / "partial").write_text("stale", encoding="utf-8")

        PACKAGE.recover_interrupted_activation(self.package)

        self.assertEqual(previous, self._package_bytes())
        self.assertFalse(backup.exists())
        self.assertFalse(stale.exists())
        self.assertEqual("valid", PACKAGE.validate_package(self.database, self.package)["status"])

    def test_validation_rejects_extra_files(self) -> None:
        PACKAGE.build_package(self.database, self.package)
        (self.package / "unexpected.txt").write_text("not part of v1", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "file inventory is invalid"):
            PACKAGE.validate_package(self.database, self.package)

    def test_compare_requires_exact_byte_identity(self) -> None:
        PACKAGE.build_package(self.database, self.package)
        other = self.root / "other"
        shutil.copytree(self.package, other)
        result = PACKAGE.compare_packages(self.database, self.package, other)
        self.assertEqual("reproducible", result["status"])

        manifest = other / "substrate-manifest.json"
        document = json.loads(manifest.read_bytes())
        document["authoritative_database"]["byte_length"] += 1
        manifest.write_bytes(PACKAGE.CONTRACT.canonical_json_bytes(document))
        with self.assertRaisesRegex(RuntimeError, "database audit identity is stale|content identity"):
            PACKAGE.compare_packages(self.database, self.package, other)

    def test_shell_entry_point_builds_inspects_and_validates(self) -> None:
        build = subprocess.run(
            ["bash", str(WRAPPER), "build", str(self.database), str(self.package)],
            check=True,
            capture_output=True,
            text=True,
        )
        built = json.loads(build.stdout)
        self.assertEqual("built-and-activated", built["status"])
        self.assertEqual("reproducible", built["reproducibility"])

        inspect = subprocess.run(
            ["bash", str(WRAPPER), "inspect", str(self.package)],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            "valid-without-authority-check",
            json.loads(inspect.stdout)["status"],
        )

        validate = subprocess.run(
            ["bash", str(WRAPPER), "validate", str(self.database), str(self.package)],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual("valid", json.loads(validate.stdout)["status"])


if __name__ == "__main__":
    unittest.main()
