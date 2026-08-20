#!/usr/bin/env python3
"""Validate that the browser probe used only bounded selective .kfs reads."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


class ContractError(RuntimeError):
    pass


def load_events(path: Path) -> list[dict[str, object]]:
    events = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ContractError(f"invalid JSONL at line {line_number}: {exc}") from exc
        if not isinstance(event, dict):
            raise ContractError(f"event at line {line_number} is not an object")
        events.append(event)
    return events


def by_path(events: list[dict[str, object]], path: str) -> list[dict[str, object]]:
    return [event for event in events if event.get("path") == path]


def require_small_get(events: list[dict[str, object]], path: str) -> None:
    matches = by_path(events, path)
    if len(matches) != 1:
        raise ContractError(f"{path} request count is {len(matches)}; expected 1")
    event = matches[0]
    if event.get("status") != 200 or event.get("range") is not None:
        raise ContractError(f"{path} must use one ordinary GET")


def require_flat_ranges(events: list[dict[str, object]], path: str) -> dict[str, object]:
    matches = by_path(events, path)
    if len(matches) != 3:
        raise ContractError(f"{path} request count is {len(matches)}; expected exactly 3")
    if any(event.get("status") != 206 for event in matches):
        raise ContractError(f"{path} contains a non-206 request")
    if any(event.get("range") is None for event in matches):
        raise ContractError(f"{path} contains a whole-file GET")

    prefix, index, chunk = matches
    if (prefix.get("start"), prefix.get("end"), prefix.get("length")) != (0, 15, 16):
        raise ContractError(f"{path} first request is not the fixed 16-byte prefix")
    if index.get("start") != 16:
        raise ContractError(f"{path} second request does not begin at the canonical index")
    if not isinstance(index.get("end"), int) or not isinstance(chunk.get("start"), int):
        raise ContractError(f"{path} range event offsets are invalid")
    if chunk["start"] != index["end"] + 1:
        raise ContractError(f"{path} selected chunk does not begin at payload offset zero")

    totals = {event.get("total") for event in matches}
    if len(totals) != 1:
        raise ContractError(f"{path} range responses disagree on representation length")
    total = totals.pop()
    if not isinstance(total, int) or total <= 0:
        raise ContractError(f"{path} representation length is invalid")
    requested = sum(int(event["length"]) for event in matches)
    if requested >= total:
        raise ContractError(f"{path} probe read {requested} of {total} bytes; not selective")

    return {
        "component_byte_length": total,
        "request_count": len(matches),
        "selected_byte_length": requested,
        "selected_fraction": requested / total,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    args = parser.parse_args()

    events = load_events(args.log.resolve())
    require_small_get(events, "/substrate-manifest.json")
    require_small_get(events, "/county-overview.json")
    roads = require_flat_ranges(events, "/roads-lod.kfs")
    water = require_flat_ranges(events, "/water-lod.kfs")

    expected_paths = {
        "/substrate-manifest.json",
        "/county-overview.json",
        "/roads-lod.kfs",
        "/water-lod.kfs",
    }
    actual_paths = {str(event.get("path")) for event in events}
    if actual_paths != expected_paths:
        raise ContractError(
            f"probe request paths mismatch: expected {sorted(expected_paths)!r}, "
            f"found {sorted(actual_paths)!r}"
        )

    print(
        json.dumps(
            {
                "request_count": len(events),
                "roads": roads,
                "status": "selective-range-contract-passed",
                "water": water,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
