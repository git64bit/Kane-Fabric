from __future__ import annotations

import copy
import unittest

from ms4.tools.kane_fabric_placement import (
    PlacementContractError,
    build_placement_plan,
    validate_placement_plan,
)

PARTITION = "kfp1-" + "a" * 32
GEN_A = "kfsg1-" + "b" * 32
GEN_B = "kfsg1-" + "c" * 32


class PlacementTests(unittest.TestCase):
    def test_physical_relocation_does_not_change_logical_identity(self) -> None:
        common = {
            "partition_key": PARTITION,
            "substrate_content_sha256": "f" * 64,
            "subscription_generation_keys": [GEN_B, GEN_A],
        }
        first = build_placement_plan(
            **common,
            physical={"node_label": "edge-a", "storage_path": "/media/a", "ip": "10.0.0.1"},
        )
        second = build_placement_plan(
            **common,
            physical={"node_label": "edge-b", "storage_path": "/media/b", "ip": "10.0.0.2"},
        )
        self.assertEqual(first["logical"], second["logical"])
        self.assertEqual(first["logical_content_sha256"], second["logical_content_sha256"])
        validate_placement_plan(first)
        validate_placement_plan(second)

    def test_logical_change_changes_identity(self) -> None:
        first = build_placement_plan(
            partition_key=PARTITION,
            substrate_content_sha256="f" * 64,
            subscription_generation_keys=[GEN_A],
            physical={"node": "edge-a"},
        )
        second = build_placement_plan(
            partition_key="kfp1-" + "d" * 32,
            substrate_content_sha256="f" * 64,
            subscription_generation_keys=[GEN_A],
            physical={"node": "edge-a"},
        )
        self.assertNotEqual(first["logical_content_sha256"], second["logical_content_sha256"])

    def test_logical_tampering_fails(self) -> None:
        plan = build_placement_plan(
            partition_key=PARTITION,
            substrate_content_sha256="f" * 64,
            subscription_generation_keys=[GEN_A],
            physical={"node": "edge-a"},
        )
        bad = copy.deepcopy(plan)
        bad["logical"]["partition_key"] = "kfp1-" + "e" * 32
        with self.assertRaises(PlacementContractError):
            validate_placement_plan(bad)


if __name__ == "__main__":
    unittest.main()
