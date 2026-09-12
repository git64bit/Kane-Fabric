#!/usr/bin/env python3
"""Regression tests for the Milestone 5 work-sequence authority guard."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

CHECKER_PATH = Path(__file__).resolve().with_name("check-ms5-work-sequence-authority.py")


def load_checker():
    spec = importlib.util.spec_from_file_location("_ms5_work_sequence_checker", CHECKER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load checker: {CHECKER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CHECKER = load_checker()

ITEMS = """MS5-001  physical-edge threat model, trust boundary, and replaceability contract
MS5-002  storage inventory, verification, activation, rollback, and recovery contract
MS5-003  device cryptographic role separation and replaceable key-provider boundary
MS5-004  browser secure-origin plus local AP/STA access contract
MS5-005  ESP-IDF/toolchain and retained dependency selection plan
MS5-006  ESP32-S3 immutable artifact storage and HTTP byte-range implementation
MS5-007  real browser consumption of accepted MS3/MS4 generations from ESP32-S3
MS5-008  management transport and WireGuard runtime/resource feasibility proof
MS5-009  firmware authenticity, update, rollback, and recovery proof
MS5-010  physical device replacement/reprovisioning identity-preservation proof
MS5-011  constrained-resource and concurrent-workload acceptance evidence
MS5-012  release evidence and milestone closeout"""


class WorkSequenceAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "docs").mkdir()
        self._write_design(ITEMS)
        self._write(
            "docs/ROADMAP.md",
            "Milestone 5 current. Design authority: `docs/MILESTONE_5_DESIGN.md`\n",
        )
        self._write(
            "docs/HANDOFF.md",
            "Current work MS5-001. Design authority: `docs/MILESTONE_5_DESIGN.md`\n",
        )
        self._write(
            "README.md",
            "Milestone 5 is current. See `docs/MILESTONE_5_DESIGN.md`.\n",
        )
        self._write_state(
            current=5,
            design="docs/MILESTONE_5_DESIGN.md",
            next_work_item="MS5-001 physical-edge threat model",
            previous={"number": 4, "status": "released"},
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _write_design(self, items: str) -> None:
        self._write(
            "docs/MILESTONE_5_DESIGN.md",
            "# Milestone 5 Design\n\n"
            "## Normative implementation order\n\n"
            "```text\n"
            f"{items}\n"
            "```\n\n"
            "## Exit gate\n\n"
            "Physical edge proof.\n",
        )

    def _write_state(
        self,
        *,
        current: int,
        design: str,
        next_work_item: str,
        previous: dict[str, object],
    ) -> None:
        self._write(
            "docs/CURRENT_STATE.json",
            json.dumps(
                {
                    "schema_version": 1,
                    "milestone": {
                        "current": current,
                        "design": design,
                        "next_work_item": next_work_item,
                        "previous_milestone": previous,
                    },
                },
                indent=2,
            )
            + "\n",
        )

    def _errors(self) -> list[str]:
        return CHECKER.validate(self.root)["errors"]

    def test_canonical_design_sequence_passes(self) -> None:
        result = CHECKER.validate(self.root)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(
            [f"MS5-{number:03d}" for number in range(1, 13)],
            result["normative_work_items"],
        )

    def test_normative_sequence_must_be_contiguous(self) -> None:
        self._write_design(ITEMS.replace("MS5-006  ESP32-S3 immutable artifact storage and HTTP byte-range implementation\n", ""))
        result = CHECKER.validate(self.root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("strictly contiguous" in error for error in result["errors"]))

    def test_duplicate_full_sequence_in_roadmap_fails(self) -> None:
        self._write(
            "docs/ROADMAP.md",
            "Design authority: `docs/MILESTONE_5_DESIGN.md`\n\n" + ITEMS + "\n",
        )
        self.assertTrue(any("duplicates the complete normative" in error for error in self._errors()))

    def test_roadmap_must_reference_design(self) -> None:
        self._write("docs/ROADMAP.md", "Milestone 5 current.\n")
        self.assertTrue(any("docs/ROADMAP.md must reference" in error for error in self._errors()))

    def test_handoff_must_reference_design(self) -> None:
        self._write("docs/HANDOFF.md", "Current work MS5-001.\n")
        self.assertTrue(any("docs/HANDOFF.md must reference" in error for error in self._errors()))

    def test_current_state_design_pointer_must_match_while_ms5_current(self) -> None:
        self._write_state(
            current=5,
            design="docs/OTHER.md",
            next_work_item="MS5-001 physical-edge threat model",
            previous={"number": 4, "status": "released"},
        )
        self.assertTrue(any("milestone.design must be" in error for error in self._errors()))

    def test_current_state_next_item_must_exist(self) -> None:
        self._write_state(
            current=5,
            design="docs/MILESTONE_5_DESIGN.md",
            next_work_item="MS5-099 nonexistent",
            previous={"number": 4, "status": "released"},
        )
        self.assertTrue(any("identifier absent" in error for error in self._errors()))

    def test_released_ms5_state_can_advance(self) -> None:
        self._write_state(
            current=6,
            design="docs/MILESTONE_6_DESIGN.md",
            next_work_item="MS6-001 next milestone",
            previous={"number": 5, "status": "released"},
        )
        result = CHECKER.validate(self.root)
        self.assertTrue(result["valid"], result["errors"])

    def test_advanced_state_requires_released_ms5_record(self) -> None:
        self._write_state(
            current=6,
            design="docs/MILESTONE_6_DESIGN.md",
            next_work_item="MS6-001 next milestone",
            previous={"number": 5, "status": "in-progress"},
        )
        self.assertTrue(any("must identify Milestone 5 as released" in error for error in self._errors()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
