#!/usr/bin/env python3
"""Transitional compatibility helpers for Kane Fabric MS-2 extraction.

The frozen Kane Condo 0.4 checkout remains a regression oracle during MS-2.
These helpers allow Fabric-owned entry points to reuse donor behavior while
substituting Fabric's database and geometry contracts. This dependency is
explicitly temporary and must be removed before MS-2 completion.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType

DEFAULT_DONOR_TOOLS = Path(
    "/var/lib/kane-fabric/reconstruction-code/kane-condo-0.4/database/tools"
)


def load_sibling(name: str) -> ModuleType:
    path = Path(__file__).resolve().with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(f"_kane_fabric_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Kane Fabric module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def donor_tools_root() -> Path:
    configured = os.environ.get("KANE_FABRIC_DONOR_TOOLS")
    root = Path(configured) if configured else DEFAULT_DONOR_TOOLS
    root = root.resolve()
    if not root.is_dir():
        raise RuntimeError(
            "Frozen Kane Condo donor tools are unavailable. "
            f"Set KANE_FABRIC_DONOR_TOOLS or restore: {root}"
        )
    return root


def load_donor(name: str) -> ModuleType:
    path = donor_tools_root() / f"{name}.py"
    if not path.is_file():
        raise RuntimeError(f"Frozen donor module is missing: {path}")
    spec = importlib.util.spec_from_file_location(f"_kane_fabric_donor_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load frozen donor module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


FABRIC_DB = load_sibling("kane_fabric_db")
FABRIC_GEOMETRY = load_sibling("kane_fabric_geometry")


class DatabaseCompatibility:
    """Expose donor-shaped DB helpers backed by Kane Fabric validation."""

    table_names = staticmethod(FABRIC_DB.table_names)
    valid_datetime = staticmethod(FABRIC_DB.valid_datetime)
    utc_now = staticmethod(FABRIC_DB.utc_now)

    @staticmethod
    def validate_database(path: Path) -> list[str]:
        result = FABRIC_DB.validate_database(path)
        return list(result["errors"])


DB = DatabaseCompatibility()
