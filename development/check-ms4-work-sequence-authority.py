#!/usr/bin/env python3
"""Check that Milestone 4 has one normative detailed work-sequence authority."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DESIGN_RELATIVE = Path("docs/MILESTONE_4_DESIGN.md")
ROADMAP_RELATIVE = Path("docs/ROADMAP.md")
HANDOFF_RELATIVE = Path("docs/HANDOFF.md")
CURRENT_STATE_RELATIVE = Path("docs/CURRENT_STATE.json")
DESIGN_REFERENCE = DESIGN_RELATIVE.as_posix()
NORMATIVE_HEADING = "## Normative implementation order"
NORMATIVE_ITEM_RE = re.compile(r"^(MS4-\d{3})\b")
REFERENCE_ITEM_RE = re.compile(r"^\s*(?:[-*]\s+)?(MS4-\d{3})\b")
HISTORICAL_MILESTONE_RE = re.compile(r"^MILESTONE_[0-3]_")


def _read_text(root: Path, relative: Path) -> str:
    path = root / relative
    if not path.is_file():
        raise RuntimeError(f"required file is missing: {relative.as_posix()}")
    return path.read_text(encoding="utf-8")


def extract_normative_sequence(text: str) -> tuple[str, ...]:
    lines = text.splitlines()
    starts = [index for index, line in enumerate(lines) if line == NORMATIVE_HEADING]
    if len(starts) != 1:
        raise RuntimeError(
            f"{DESIGN_REFERENCE} must contain exactly one {NORMATIVE_HEADING!r} heading"
        )

    start = starts[0] + 1
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break

    identifiers = []
    for line in lines[start:end]:
        match = NORMATIVE_ITEM_RE.match(line)
        if match:
            identifiers.append(match.group(1))

    if not identifiers:
        raise RuntimeError("normative Milestone 4 work-sequence section contains no work items")
    if len(identifiers) != len(set(identifiers)):
        raise RuntimeError("normative Milestone 4 work-sequence contains a duplicate identifier")

    numbers = tuple(int(identifier.removeprefix("MS4-")) for identifier in identifiers)
    expected = tuple(range(1, max(numbers) + 1))
    if numbers != expected:
        raise RuntimeError(
            "normative Milestone 4 work-sequence identifiers must start at MS4-001 "
            "and be strictly contiguous and increasing"
        )
    return tuple(identifiers)


def _line_leading_identifiers(text: str) -> tuple[str, ...]:
    result = []
    for line in text.splitlines():
        match = REFERENCE_ITEM_RE.match(line)
        if match:
            result.append(match.group(1))
    return tuple(result)


def _contains_complete_identifier_set(
    values: tuple[str, ...], sequence: tuple[str, ...]
) -> bool:
    return set(sequence).issubset(set(values))


def iter_current_markdown(root: Path) -> Iterable[Path]:
    readme = root / "README.md"
    if readme.is_file():
        yield readme
    docs = root / "docs"
    if not docs.is_dir():
        return
    for path in sorted(docs.glob("*.md")):
        if path.relative_to(root) == DESIGN_RELATIVE:
            continue
        if HISTORICAL_MILESTONE_RE.match(path.name):
            continue
        yield path


def validate(root: Path = ROOT) -> dict[str, object]:
    root = root.resolve()
    errors: list[str] = []
    sequence: tuple[str, ...] = ()

    try:
        design_text = _read_text(root, DESIGN_RELATIVE)
        sequence = extract_normative_sequence(design_text)
    except (OSError, RuntimeError, UnicodeError) as exc:
        errors.append(str(exc))

    if sequence:
        for path in iter_current_markdown(root):
            relative = path.relative_to(root).as_posix()
            try:
                identifiers = _line_leading_identifiers(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError) as exc:
                errors.append(f"cannot read {relative}: {exc}")
                continue
            if _contains_complete_identifier_set(identifiers, sequence):
                errors.append(
                    f"{relative} duplicates the complete normative Milestone 4 work sequence; "
                    f"refer to {DESIGN_REFERENCE} instead"
                )

    for relative in (ROADMAP_RELATIVE, HANDOFF_RELATIVE):
        try:
            text = _read_text(root, relative)
        except (OSError, RuntimeError, UnicodeError) as exc:
            errors.append(str(exc))
            continue
        if DESIGN_REFERENCE not in text:
            errors.append(
                f"{relative.as_posix()} must reference the Milestone 4 design authority "
                f"{DESIGN_REFERENCE}"
            )

    try:
        state = json.loads(_read_text(root, CURRENT_STATE_RELATIVE))
        milestone = state.get("milestone") if isinstance(state, dict) else None
        if not isinstance(milestone, dict):
            errors.append("docs/CURRENT_STATE.json milestone object is missing or invalid")
        else:
            if milestone.get("design") != DESIGN_REFERENCE:
                errors.append(
                    f"docs/CURRENT_STATE.json milestone.design must be {DESIGN_REFERENCE}"
                )
            next_work_item = milestone.get("next_work_item")
            if not isinstance(next_work_item, str) or not next_work_item:
                errors.append(
                    "docs/CURRENT_STATE.json milestone.next_work_item is missing or invalid"
                )
            else:
                match = re.match(r"^(MS4-\d{3})\b", next_work_item)
                if not match:
                    errors.append(
                        "docs/CURRENT_STATE.json milestone.next_work_item must begin with an "
                        "MS4-NNN identifier"
                    )
                elif sequence and match.group(1) not in sequence:
                    errors.append(
                        "docs/CURRENT_STATE.json milestone.next_work_item names an identifier "
                        "absent from the normative Milestone 4 work sequence"
                    )
    except (json.JSONDecodeError, OSError, RuntimeError, UnicodeError) as exc:
        errors.append(f"docs/CURRENT_STATE.json is invalid: {exc}")

    return {
        "design_authority": DESIGN_REFERENCE,
        "normative_work_items": list(sequence),
        "valid": not errors,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="repository root to validate (defaults to this script's repository)",
    )
    args = parser.parse_args()
    result = validate(args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
