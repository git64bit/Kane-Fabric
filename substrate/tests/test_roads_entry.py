#!/usr/bin/env python3
"""Guard the public MS3 road compiler database-read boundary."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRY_PATH = ROOT / "substrate" / "tools" / "kane_fabric_roads_entry.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ENTRY = load_module("_kane_fabric_roads_entry_guard_test", ENTRY_PATH)


class RoadEntryBoundaryTests(unittest.TestCase):
    def test_public_build_loader_is_fabric_read_adapter(self) -> None:
        self.assertIs(ENTRY.ROADS.load_accepted_roads, ENTRY.load_accepted_roads)
        self.assertIs(
            ENTRY.FABRIC_READ.load_accepted_map_layer,
            ENTRY.load_accepted_roads.__globals__["FABRIC_READ"].load_accepted_map_layer,
        )


if __name__ == "__main__":
    unittest.main()
