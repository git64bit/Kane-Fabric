#!/usr/bin/env python3
"""Enforce the explicitly accepted zlib identity for substrate byte production."""

from __future__ import annotations

import argparse
import json
import sys
import zlib
from collections.abc import Mapping
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
THIRD_PARTY_MANIFEST = ROOT / "third_party" / "manifest.json"
DEPENDENCY_KEY = "zlib"
EXPECTED_FIELDS = ("expected_compile_version", "expected_runtime_version")


def _require_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{label} is missing or invalid")
    return value


def _require_version(pin: Mapping[str, object], field: str) -> str:
    value = pin.get(field)
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise RuntimeError(f"zlib dependency pin {field} is missing or invalid")
    return value


def expected_zlib_identity(
    manifest_path: Path = THIRD_PARTY_MANIFEST,
) -> dict[str, str]:
    """Read only the normative expected zlib identity from the dependency manifest."""

    try:
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Unable to read Kane Fabric dependency manifest {manifest_path}: {exc}"
        ) from exc

    root = _require_mapping(document, "third-party manifest")
    if root.get("schema_version") != 1:
        raise RuntimeError("third-party manifest schema is unsupported")
    inventory = root.get("third_party")
    if not isinstance(inventory, list):
        raise RuntimeError("third-party manifest third_party inventory is invalid")

    matches = [
        item
        for item in inventory
        if isinstance(item, Mapping) and item.get("key") == DEPENDENCY_KEY
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"third-party manifest must contain exactly one {DEPENDENCY_KEY!r} entry"
        )

    pin = _require_mapping(matches[0].get("pin"), "zlib dependency pin")
    return {field: _require_version(pin, field) for field in EXPECTED_FIELDS}


def observed_zlib_identity() -> dict[str, str]:
    """Return the zlib identities exposed by the currently executing Python runtime."""

    return {
        "observed_compile_version": str(zlib.ZLIB_VERSION),
        "observed_runtime_version": str(zlib.ZLIB_RUNTIME_VERSION),
    }


def require_accepted_zlib(
    manifest_path: Path = THIRD_PARTY_MANIFEST,
) -> dict[str, str]:
    """Fail closed unless executing zlib exactly matches the accepted compiler pin."""

    expected = expected_zlib_identity(manifest_path)
    observed = observed_zlib_identity()
    if (
        expected["expected_compile_version"]
        != observed["observed_compile_version"]
        or expected["expected_runtime_version"]
        != observed["observed_runtime_version"]
    ):
        raise RuntimeError(
            "Kane Fabric substrate compilation refused: zlib identity mismatch; "
            f"expected compile={expected['expected_compile_version']} "
            f"runtime={expected['expected_runtime_version']}; "
            f"observed compile={observed['observed_compile_version']} "
            f"runtime={observed['observed_runtime_version']}. "
            "Refusing to produce substrate publication bytes until the explicit "
            "compiler dependency pin is reviewed and updated."
        )

    return {
        **expected,
        **observed,
        "status": "match",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="compare executing zlib with the accepted compiler pin")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command != "check":
            raise RuntimeError(f"Unknown command: {args.command}")
        result = require_accepted_zlib()
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
