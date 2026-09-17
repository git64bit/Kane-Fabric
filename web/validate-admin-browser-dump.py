#!/usr/bin/env python3
"""Validate a rendered Administrative Descriptor DOM dump.

This gate verifies that the real browser loaded the descriptor-driven
Administrative Web surface, rendered generic controls, and presented the exact
canonical SHA-256 identity of the current Illinois condominium insurance
reference descriptor.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESCRIPTOR = ROOT / "administration/descriptors/illinois/condominium/insurance.v1.json"


def canonicalize(value: object) -> str:
    if isinstance(value, list):
        return "[" + ",".join(canonicalize(entry) for entry in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(
            json.dumps(key, ensure_ascii=False) + ":" + canonicalize(value[key])
            for key in sorted(value)
        ) + "}"
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def descriptor_sha256() -> str:
    descriptor = json.loads(DESCRIPTOR.read_text(encoding="utf-8"))
    canonical = canonicalize(descriptor).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} DOM_DUMP.html")

    html = Path(sys.argv[1]).read_text(encoding="utf-8")
    expected_hash = descriptor_sha256()

    checks = {
        "administrative_header": "Administrative Infrastructure" in html,
        "descriptor_title": "Illinois Condominium" in html and "Insurance" in html,
        "descriptor_loaded_without_error": "Administrative descriptor not loaded" not in html,
        "descriptor_exact_sha256": f"SHA-256 {expected_hash}" in html,
        "descriptor_summary": "Descriptor v1" in html and "3 sections" in html and "14 controls" in html,
        "association_policy_collection": "Insurance policies" in html,
        "add_policy_action": "Add policy" in html,
        "statewide_framework": "Statewide framework" in html,
        "form_input_rendered": re.search(r"<input(?:\s|>)", html) is not None,
        "form_select_rendered": re.search(r"<select(?:\s|>)", html) is not None,
        "form_textarea_rendered": re.search(r"<textarea(?:\s|>)", html) is not None,
    }

    for name, passed in checks.items():
        print(f"{name}={'PASS' if passed else 'FAIL'}")

    failed = [name for name, passed in checks.items() if not passed]
    print()
    print(f"admin_browser_checks={len(checks) - len(failed)}/{len(checks)}")
    print(f"descriptor_sha256={expected_hash}")

    if failed:
        print("FAILED:", ", ".join(failed))
        return 1

    print("admin_browser_render=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
