#!/usr/bin/env python3
"""Regression tests for the Milestone 4 work-sequence authority guard."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

CHECKER_PATH = Path(__file__).resolve().with_name("check-ms4-work-sequence-authority.py")


def load_checker():
    spec = importlib.util.spec_from_file_location("_ms4_work_sequence_checker", CHECKER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load checker: {CHECKER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CHECKER = load_checker()

ITEMS = """MS4-001  partition descriptor and deterministic identity contract
MS4-002  administrative/bounded scope normalization and inclusion rules
MS4-003  substrate partition selection manifest/reference model
MS4-004  subscription manifest and independent generation contract
MS4-005  geographic identity references and ownership/rights boundary
MS4-006  Condo proof subscription
MS4-007  Industry / Mechanical Compiler proof subscription
MS4-008  browser composition of substrate + multiple scoped subscriptions
MS4-009  multi-partition / cross-boundary composition proof
MS4-010  edge-placement compatibility proof without ESP-IDF implementation
MS4-011  release evidence and milestone closeout"""


class WorkSequenceAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "docs").mkdir()
        self._write_design(ITEMS)
        self._write(
            "docs/ROADMAP.md",
            "Current item: `MS4-001`\nDesign authority: `docs/MILESTONE_4_DESIGN.md`\n",
        )
        self._write(
            "docs/HANDOFF.md",
            "Current work: MS4-001\nDesign authority: `docs/MILESTONE_4_DESIGN.md`\n",
        )
        self._write(
            "README.md",
            "Milestone 4 is current. See `docs/MILESTONE_4_DESIGN.md`.\n",
        )
        self._write_state(
            "docs/MILESTONE_4_DESIGN.md",
            "MS4-001 partition descriptor",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _write_design(self, items: str) -> None:
        self._write(
            "docs/MILESTONE_4_DESIGN.md",
            "# Milestone 4 Design\n\n"
            "MS4-003 depends on accepted substrate identity.\n"
            "MS4-007 remains a synthetic proof.\n\n"
            "## Normative implementation order\n\n"
            "The normative sequence is:\n\n"
            "```text\n"
            f"{items}\n"
            "```\n\n"
            "## Exit gate\n\n"
            "MS4-003 and MS4-007 may be referenced here without changing sequence parsing.\n",
        )

    def _write_state(self, design: str, next_work_item: str) -> None:
        self._write(
            "docs/CURRENT_STATE.json",
            json.dumps(
                {
                    "schema_version": 1,
                    "milestone": {
                        "current": 4,
                        "design": design,
                        "next_work_item": next_work_item,
                    },
                },
                indent=2,
            )
            + "\n",
        )

    def _write_released_state(self) -> None:
        self._write(
            "docs/CURRENT_STATE.json",
            json.dumps(
                {
                    "schema_version": 1,
                    "milestone": {
                        "current": 5,
                        "next_work_item": "Define Milestone 5 edge contract",
                        "previous_milestone": {
                            "number": 4,
                            "status": "released",
                        },
                    },
                },
                indent=2,
            )
            + "\n",
        )

    def _errors(self) -> list[str]:
        return CHECKER.validate(self.root)["errors"]

    def test_canonical_design_sequence_passes_and_incidental_references_are_ignored(self) -> None:
        result = CHECKER.validate(self.root)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(
            [f"MS4-{number:03d}" for number in range(1, 12)],
            result["normative_work_items"],
        )

    def test_normative_sequence_can_extend_contiguously(self) -> None:
        self._write_design(ITEMS + "\nMS4-012  deliberately added future work item")
        result = CHECKER.validate(self.root)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual("MS4-012", result["normative_work_items"][-1])

    def test_duplicate_full_identifier_set_in_current_document_fails_even_with_prose_between_items(self) -> None:
        copied = "\n".join(
            f"{line}\nExplanation for copied item {index}."
            for index, line in enumerate(ITEMS.splitlines(), start=1)
        )
        self._write(
            "docs/ROADMAP.md",
            "Design authority: `docs/MILESTONE_4_DESIGN.md`\n\n" + copied + "\n",
        )
        self.assertTrue(
            any("duplicates the complete normative" in error for error in self._errors())
        )

    def test_missing_duplicate_or_out_of_order_identifier_in_normative_sequence_fails(self) -> None:
        cases = {
            "missing": ITEMS.replace("MS4-006  Condo proof subscription\n", ""),
            "duplicate": ITEMS.replace(
                "MS4-007  Industry / Mechanical Compiler proof subscription",
                "MS4-006  duplicate Condo proof\n"
                "MS4-007  Industry / Mechanical Compiler proof subscription",
            ),
            "out-of-order": ITEMS.replace(
                "MS4-005  geographic identity references and ownership/rights boundary\n"
                "MS4-006  Condo proof subscription",
                "MS4-006  Condo proof subscription\n"
                "MS4-005  geographic identity references and ownership/rights boundary",
            ),
        }
        for label, items in cases.items():
            with self.subTest(label=label):
                self._write_design(items)
                result = CHECKER.validate(self.root)
                self.assertFalse(result["valid"])
                self.assertTrue(
                    any(
                        "normative Milestone 4 work-sequence" in error
                        for error in result["errors"]
                    )
                )
                self._write_design(ITEMS)

    def test_roadmap_missing_design_authority_reference_fails(self) -> None:
        self._write("docs/ROADMAP.md", "Current item: MS4-001\n")
        self.assertTrue(
            any("docs/ROADMAP.md must reference" in error for error in self._errors())
        )

    def test_handoff_missing_design_authority_reference_fails(self) -> None:
        self._write("docs/HANDOFF.md", "Current work: MS4-001\n")
        self.assertTrue(
            any("docs/HANDOFF.md must reference" in error for error in self._errors())
        )

    def test_current_state_design_pointer_elsewhere_fails_while_ms4_is_current(self) -> None:
        self._write_state("docs/OTHER_DESIGN.md", "MS4-001 partition descriptor")
        self.assertTrue(
            any("milestone.design must be" in error for error in self._errors())
        )

    def test_current_state_next_item_absent_from_normative_sequence_fails(self) -> None:
        self._write_state("docs/MILESTONE_4_DESIGN.md", "MS4-012 future item")
        self.assertTrue(any("identifier absent" in error for error in self._errors()))

    def test_released_ms4_state_can_advance_to_ms5(self) -> None:
        self._write_released_state()
        result = CHECKER.validate(self.root)
        self.assertTrue(result["valid"], result["errors"])

    def test_ms4_release_record_is_historical_not_second_live_authority(self) -> None:
        self._write_released_state()
        self._write("docs/MILESTONE_4_RELEASE.md", ITEMS + "\n")
        result = CHECKER.validate(self.root)
        self.assertTrue(result["valid"], result["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
