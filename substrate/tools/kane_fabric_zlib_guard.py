#!/usr/bin/env python3
"""Fail closed when the release-byte zlib implementation is not the declared pin."""

from __future__ import annotations

import json
import sys
import zlib
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parents[2]
THIRD_PARTY_MANIFEST = ROOT / "third_party" / "manifest.json"
DEPENDENCY_KEY = "zlib"


def _require_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{label} is missing or invalid")
    return value


def declared_zlib_pin(manifest_path: Path = THIRD_PARTY_MANIFEST) -> dict[str, str]:
    """Load the compiler/runtime zlib versions declared by the dependency inventory."""

    try:
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Unable to read Kane Fabric dependency manifest {manifest_path}: {exc}"
        ) from exc

    root = _require_mapping(document, "third-party manifest")
    inventory = root.get("third_party")
    if not isinstance(inventory, list):
        raise RuntimeError("third-party manifest third_party inventory is invalid")

    matches = [
        item
        for item in inventory
        if isinstance(item, Mapping) and str(item.get("key", "")) == DEPENDENCY_KEY
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"third-party manifest must contain exactly one {DEPENDENCY_KEY!r} entry"
        )

    pin = _require_mapping(matches[0].get("pin"), "zlib dependency pin")
    status = str(pin.get("status", "")).strip()
    version = str(pin.get("version", "")).strip()
    compile_version = str(pin.get("observed_compile_version", "")).strip() or version
    runtime_version = str(pin.get("observed_runtime_version", "")).strip() or version

    if not status:
        raise RuntimeError("zlib dependency pin status is missing")
    if not compile_version or not runtime_version:
        raise RuntimeError(
            "zlib dependency pin must declare compile and runtime versions"
        )

    return {
        "compile_version": compile_version,
        "runtime_version": runtime_version,
        "status": status,
    }


def require_pinned_zlib(manifest_path: Path = THIRD_PARTY_MANIFEST) -> dict[str, str]:
    """Require exact compile/runtime zlib identity before producing .kfs bytes."""

    pin = declared_zlib_pin(manifest_path)
    actual_compile = str(zlib.ZLIB_VERSION)
    actual_runtime = str(zlib.ZLIB_RUNTIME_VERSION)
    if (
        actual_compile != pin["compile_version"]
        or actual_runtime != pin["runtime_version"]
    ):
        raise RuntimeError(
            "Kane Fabric .kfs compiler zlib identity mismatch: "
            f"expected compile={pin['compile_version']} runtime={pin['runtime_version']} "
            f"from {manifest_path}; observed compile={actual_compile} "
            f"runtime={actual_runtime}. Refusing to produce release-identity bytes."
        )

    return {
        "compile_version": actual_compile,
        "runtime_version": actual_runtime,
        "status": "pinned-zlib-match",
    }


def main() -> int:
    try:
        result = require_pinned_zlib()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
