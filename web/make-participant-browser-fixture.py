#!/usr/bin/env python3
"""Build a synthetic participant publication using one real accepted MS4 geographic reference."""

from __future__ import annotations

import json
import sys
from pathlib import Path

EXPECTED_COMPOSITION = "a58c8398248cee05b7baad9ae289fe0581bdb3624ce1aff3aa8a49721f92ee53"


def fail(message: str) -> None:
    raise SystemExit(f"participant fixture generation failed: {message}")


def read_object(path: Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"{label} is unreadable or invalid JSON: {exc}")
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


def resolve_inside(root: Path, relative: str, label: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        fail(f"{label} escapes composition root")
    return path


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} MS4_COMPOSITION_DIR OUTPUT.json")

    root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    if not root.is_dir():
        fail(f"composition directory does not exist: {root}")

    composition = read_object(root / "composition-manifest.json", "composition manifest")
    if composition.get("format") != "kane-fabric-ms4-composition-manifest" or composition.get("version") != 1:
        fail("composition manifest format/version is not MS4 v1")
    if composition.get("composition_sha256") != EXPECTED_COMPOSITION:
        fail("composition is not the accepted MS4 proof identity")

    subscriptions = composition.get("subscriptions")
    if not isinstance(subscriptions, list):
        fail("composition subscriptions must be an array")
    condo = next(
        (
            entry
            for entry in subscriptions
            if isinstance(entry, dict) and entry.get("subscription_key") == "condo"
        ),
        None,
    )
    if condo is None:
        fail("accepted condo proof subscription is missing")
    objects_path = condo.get("objects_path")
    if not isinstance(objects_path, str) or not objects_path:
        fail("condo proof objects_path is missing")

    objects_doc = read_object(resolve_inside(root, objects_path, "objects_path"), "condo proof objects")
    objects = objects_doc.get("objects")
    if not isinstance(objects, list) or not objects or not isinstance(objects[0], dict):
        fail("condo proof must contain at least one object")
    refs = objects[0].get("geographic_refs")
    if not isinstance(refs, list) or not refs or not isinstance(refs[0], dict):
        fail("condo proof object must contain at least one geographic reference")

    publication = {
        "format": "kane-fabric-participant-publication",
        "format_version": 1,
        "association_unit_identity": {
            "format": "kane-fabric-association-unit-identity",
            "format_version": 1,
            "association_anchor": {
                "jurisdiction": {
                    "country_code": "US",
                    "state_code": "IL",
                },
                "recording_authority_reference": "synthetic-public-recording-authority",
                "original_declaration_recording_reference": "Synthetic Tract Book 14, Page 27",
            },
            "unit_anchors": [],
        },
        "descriptor_instances": [
            {
                "descriptor_id": "us.il.condominium.property",
                "descriptor_version": 1,
                "subject": {"kind": "association"},
                "geographic_refs": [refs[0]],
                "data": {
                    "association": {
                        "property": {
                            "condominium_name": "Synthetic Participant Condominium",
                            "declaration": {
                                "record_reference": "Synthetic Tract Book 14, Page 27"
                            },
                        }
                    }
                },
            }
        ],
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(publication, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "composition_sha256": EXPECTED_COMPOSITION,
                "geographic_reference": refs[0],
                "output": str(output),
                "participant_evidence": "synthetic",
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
