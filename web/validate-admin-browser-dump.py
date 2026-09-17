#!/usr/bin/env python3
"""Validate a rendered Administrative Descriptor DOM dump.

The gate loads the same bootstrap used by the browser, computes the exact
canonical SHA-256 identity of every enabled local descriptor, and verifies that
the real browser rendered all of them without a descriptor-load failure.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
BOOTSTRAP = WEB / "admin-app.json"


def canonicalize_number(value: float) -> str:
    """Match ECMAScript JSON.stringify number spelling for finite JSON numbers."""
    if not math.isfinite(value):
        raise ValueError("non-finite number is not valid descriptor JSON")
    if value == 0:
        return "0"

    text = repr(value).lower()
    if "e" not in text:
        return text[:-2] if text.endswith(".0") else text

    mantissa, exponent_text = text.split("e")
    exponent = int(exponent_text)
    negative = mantissa.startswith("-")
    unsigned = mantissa[1:] if negative else mantissa
    digits = unsigned.replace(".", "")

    # ECMAScript emits fixed notation for values in [1e-6, 1e21).
    if 1e-6 <= abs(value) < 1e21:
        point = 1 + exponent
        if point <= 0:
            fixed = "0." + "0" * (-point) + digits
        elif point >= len(digits):
            fixed = digits + "0" * (point - len(digits))
        else:
            fixed = digits[:point] + "." + digits[point:]
        return ("-" if negative else "") + fixed

    coefficient = unsigned[:-2] if unsigned.endswith(".0") else unsigned
    exponent_part = ("+" if exponent >= 0 else "") + str(exponent)
    return ("-" if negative else "") + coefficient + "e" + exponent_part


def canonicalize(value: object) -> str:
    if isinstance(value, list):
        return "[" + ",".join(canonicalize(entry) for entry in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(
            json.dumps(key, ensure_ascii=False) + ":" + canonicalize(value[key])
            for key in sorted(value)
        ) + "}"
    if isinstance(value, float):
        return canonicalize_number(value)
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
        "management_framework": "Statewide management and licensing framework" in decoded_html,
        "management_arrangement": "Association management arrangement" in decoded_html,
        "management_fund_safeguards": "Association-fund and insurance safeguards" in decoded_html,
        "management_service_contract_collection": "Add agreement" in decoded_html,
        "management_license_boundary": "requires a current valid Department license unless a statutory exemption applies" in decoded_html and "may not commingle" in decoded_html,
        "resale_framework": "Statewide resale framework" in decoded_html,
        "resale_disclosure_collection": "Add disclosure item" in decoded_html,
        "resale_request_collection": "Add resale request" in decoded_html,
        "resale_lender_collection": "Add lender notice" in decoded_html,
        "resale_current_timing_boundary": "9 resale disclosure categories" in decoded_html and "within 10 business days" in decoded_html and "within 72 hours" in decoded_html and "Within 15 days" in decoded_html,
        "property_framework": "Statewide property and recording framework" in decoded_html,
        "property_unit_collection": "Add unit" in decoded_html,
        "property_amendment_collection": "Add amendment" in decoded_html,
        "property_tax_collection": "Add tax reference" in decoded_html,
        "property_identity_tax_boundary": "incorporated or unincorporated" in decoded_html and "$1.00 per year" in decoded_html and "not against the condominium property as a whole" in decoded_html,
        "collections_framework": "Statewide collection and lien framework" in decoded_html,
        "collections_case_collection": "Add collection case" in decoded_html,
        "collections_lien_event_collection": "Add lien event" in decoded_html,
        "collections_successor_boundary": "6 months immediately preceding" in decoded_html and "within 20 days" in decoded_html,
        "collections_fee_process_boundary": "management contract" in decoded_html and "notice and an opportunity to be heard" in decoded_html,
        "enforcement_framework": "Statewide rules and fine framework" in decoded_html,
        "enforcement_rule_collection": "Add rule" in decoded_html,
        "enforcement_violation_collection": "Add violation case" in decoded_html,
        "enforcement_adoption_boundary": "specific purpose of discussing the proposed rules and regulations" in decoded_html and "full text of the proposed rules and regulations" in decoded_html and "No quorum is required" in decoded_html,
        "enforcement_fine_process_boundary": "notice and an opportunity to be heard" in decoded_html and "does not itself state a universal numeric notice period" in decoded_html,
        "maintenance_framework": "Statewide maintenance and access framework" in decoded_html,
        "maintenance_asset_collection": "Add asset" in decoded_html,
        "maintenance_event_collection": "Add maintenance event" in decoded_html,
        "maintenance_improvement_boundary": "exceeding 5%" in decoded_html and "20% of the association votes" in decoded_html and "within 21 days" in decoded_html and "within 30 days" in decoded_html,
        "maintenance_emergency_access_boundary": "immediate danger to the structural integrity" in decoded_html and "access to each unit" in decoded_html,
        "turnover_framework": "Statewide developer-control and turnover framework" in decoded_html,
        "turnover_package_collection": "Add turnover item" in decoded_html,
        "turnover_contract_collection": "Add turnover agreement" in decoded_html,
        "turnover_election_boundary": "60 days after the developer has conveyed 75%" in decoded_html and "3 years after recording of the declaration" in decoded_html and "at least 21 days notice" in decoded_html and "holding 20% of the association interest" in decoded_html,
        "turnover_delivery_contract_boundary": "Within 60 days following election" in decoded_html and "within 10 days after a written demand" in decoded_html and "during the 180-day period" in decoded_html and "at least 60 days before that 180-day period expires" in decoded_html and "effective 30 days after certified-mail notice" in decoded_html,
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