#!/usr/bin/env python3
"""Public water-compiler entry point with release-byte compression guarding."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load support module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


TOOLS = Path(__file__).resolve().parent
WATER = _load_module(
    "_kane_fabric_water_implementation",
    TOOLS / "kane_fabric_water.py",
)
COMPRESSION = _load_module(
    "_kane_fabric_water_compression_guard",
    TOOLS / "kane_fabric_zlib_guard.py",
)

_UNGUARDED_BUILD_COMPONENT = WATER.build_component


def build_component(database: Path, output: Path):
    """Guard release-byte compression before entering the water compiler."""

    COMPRESSION.require_pinned_zlib()
    return _UNGUARDED_BUILD_COMPONENT(database, output)


WATER.build_component = build_component


def main() -> int:
    return int(WATER.main())


if __name__ == "__main__":
    raise SystemExit(main())
