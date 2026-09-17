#!/usr/bin/env python3
"""Validate a rendered Administrative Descriptor DOM dump.

The gate loads the same bootstrap used by the browser, computes the exact
canonical SHA-256 identity of every enabled local descriptor, and verifies that
the real browser rendered all of them without a descriptor-load failure.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
BOOTSTRAP = WEB / "admin-app.json"


def canonicalize(value: object) -> str:
    if isinstance(value, list):
        return "[" + ",".join(canonicalize(entry) for entry in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(
            json.dumps(key, ensure_ascii=False) + ":" + canonicalize(value[key])
            for key in sorted(value)
        ) + "}"
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def descriptor_info(source: dict[str, object]) -> dict[str, object]:
    raw_url = source.get("url")
    if not isinstance(raw_url, str) or "://" in raw_url:
        raise SystemExit(f"browser acceptance requires a repository-local descriptor source: {raw_url!r}")
    path = (WEB / raw_url).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError as exc:
        raise SystemExit(f"descriptor source escapes repository root: {raw_url!r}") from exc
    descriptor = json.loads(path.read_text(encoding="utf-8"))
    canonical = canonicalize(descriptor).encode("utf-8")

    sections = 0
    controls = 0

    def count_controls(items: list[dict[str, object]]) -> None:
        nonlocal controls
        for control in items:
            controls += 1
            nested = control.get("item_controls")
            if isinstance(nested, list):
                count_controls(nested)

    pages = descriptor.get("pages", [])
    for page in pages:
        for section in page.get("sections", []):
            sections += 1
            count_controls(section.get("controls", []))

    return {
        "path": path,
        "id": descriptor.get("descriptor_id"),
        "title": descriptor.get("title"),
        "version": descriptor.get("descriptor_version"),
        "sections": sections,
        "controls": controls,
        "sha256": hashlib.sha256(canonical).hexdigest(),
    }


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} DOM_DUMP.html")

    html = Path(sys.argv[1]).read_text(encoding="utf-8")
    decoded_html = unescape(html)
    bootstrap = json.loads(BOOTSTRAP.read_text(encoding="utf-8"))
    sources = [source for source in bootstrap.get("descriptor_sources", []) if source.get("enabled", True)]
    if not sources:
        raise SystemExit("administrative bootstrap has no enabled descriptor sources")
    descriptors = [descriptor_info(source) for source in sources]

    checks = {
        "administrative_header": "Administrative Infrastructure" in decoded_html,
        "descriptor_loaded_without_error": "Administrative descriptor not loaded" not in decoded_html,
        "all_descriptor_titles": all(str(info["title"]) in decoded_html for info in descriptors),
        "all_descriptor_exact_sha256": all(f"SHA-256 {info['sha256']}" in html for info in descriptors),
        "all_descriptor_summaries": all(
            f"Descriptor v{info['version']} · {info['sections']} sections · {info['controls']} controls" in decoded_html
            for info in descriptors
        ),
        "insurance_policy_collection": "Insurance policies" in decoded_html,
        "insurance_add_policy_action": "Add policy" in decoded_html,
        "records_inventory": "Statewide required record inventory" in decoded_html,
        "records_add_record_set_action": "Add record set" in decoded_html,
        "records_access_rule": "10 business days" in decoded_html,
        "finance_budget_framework": "Statewide fiscal framework" in decoded_html,
        "finance_budget_line_collection": "Add budget line" in decoded_html,
        "finance_separate_assessment_collection": "Add separate assessment" in decoded_html,
        "finance_unit_metadata_rendered": re.search(r'class="admin-unit">USD</small>', html) is not None,
        "governance_framework": "Statewide governance framework" in decoded_html,
        "governance_board_collection": "Add board member" in decoded_html,
        "governance_meeting_collection": "Add meeting" in decoded_html,
        "governance_election_collection": "Add election" in decoded_html,
        "governance_notice_rules": "at least 4 times annually" in decoded_html and "48 hours" in decoded_html and "not less than 10 and not more than 30 days" in decoded_html,
        "form_input_rendered": re.search(r"<input(?:\s|>)", html) is not None,
        "form_select_rendered": re.search(r"<select(?:\s|>)", html) is not None,
        "form_textarea_rendered": re.search(r"<textarea(?:\s|>)", html) is not None,
    }

    for name, passed in checks.items():
        print(f"{name}={'PASS' if passed else 'FAIL'}")

    failed = [name for name, passed in checks.items() if not passed]
    print()
    print(f"admin_browser_checks={len(checks) - len(failed)}/{len(checks)}")
    for info in descriptors:
        print(f"descriptor={info['id']} sha256={info['sha256']}")

    if failed:
        print("FAILED:", ", ".join(failed))
        return 1

    print("admin_browser_render=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
