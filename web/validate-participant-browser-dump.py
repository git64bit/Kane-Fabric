#!/usr/bin/env python3
"""Validate the real-browser participant-publication vertical slice."""

from __future__ import annotations

import html.parser
import json
import sys
from pathlib import Path

EXPECTED_SUBSTRATE = "fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc"
EXPECTED_COMPOSITION = "a58c8398248cee05b7baad9ae289fe0581bdb3624ce1aff3aa8a49721f92ee53"
EXPECTED_DESCRIPTOR = "us.il.condominium.property"
EXPECTED_CONTROL = "association.property.condominium_name"
EXPECTED_ID_PREFIX = "participant-0-us-il-condominium-property-"


class DumpParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root_attrs: dict[str, str | None] = {}
        self.participant_frames: list[tuple[str | None, str | None]] = []
        self.participant_control_seen = False
        self.in_status = False
        self.status_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "html":
            self.root_attrs = values
        if tag == "section" and "data-participant-descriptor-id" in values:
            self.participant_frames.append(
                (
                    values.get("data-participant-descriptor-id"),
                    values.get("data-participant-subject"),
                )
            )
        if tag in {"input", "select", "textarea"}:
            control_id = values.get("id") or ""
            if values.get("name") == EXPECTED_CONTROL and control_id.startswith(EXPECTED_ID_PREFIX):
                self.participant_control_seen = True
        if tag == "pre" and values.get("id") == "machine-status":
            self.in_status = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "pre" and self.in_status:
            self.in_status = False

    def handle_data(self, data: str) -> None:
        if self.in_status:
            self.status_parts.append(data)


def fail(message: str) -> None:
    raise SystemExit(f"participant browser acceptance failed: {message}")


def validate_machine_status(parser: DumpParser) -> None:
    raw = "".join(parser.status_parts).strip()
    if not raw:
        fail("machine-status payload is empty")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"machine-status payload is invalid JSON: {exc}")

    if payload.get("status") != "web-004-verified":
        fail(f"application status is {payload.get('status')!r}, expected 'web-004-verified'")
    if payload.get("substrate_content_sha256") != EXPECTED_SUBSTRATE:
        fail("substrate identity is not the accepted MS3 release")
    if payload.get("composition_sha256") != EXPECTED_COMPOSITION:
        fail("composition identity is not the accepted MS4 proof")
    if payload.get("jurisdiction") != "Kane County" or payload.get("jurisdiction_fips") != "17089":
        fail("jurisdiction identity is not Kane County / 17089")
    if payload.get("object_count") != 2 or payload.get("overlay_count") != 2:
        fail("expected exactly two composed objects and two visible overlays")
    if payload.get("physical_platform_assumed") is not False:
        fail("application reported a physical-platform assumption")

    generations = payload.get("subscription_generations")
    if not isinstance(generations, list) or len(generations) != 2:
        fail("expected exactly two verified subscription generations")
    keys = {entry.get("subscription_key") for entry in generations if isinstance(entry, dict)}
    if keys != {"condo", "industry"}:
        fail(f"unexpected subscription keys: {sorted(str(value) for value in keys)}")
    for entry in generations:
        if not isinstance(entry, dict):
            fail("subscription generation entry is not an object")
        generation = entry.get("generation_key")
        if not isinstance(generation, str) or not generation.startswith("kfsg1-") or len(generation) != 38:
            fail(f"invalid subscription generation key: {generation!r}")
        if entry.get("object_count") != 1:
            fail("each accepted proof subscription must contribute exactly one object")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} DOM_DUMP.html")

    parser = DumpParser()
    parser.feed(Path(sys.argv[1]).read_text(encoding="utf-8"))
    attrs = parser.root_attrs

    if attrs.get("data-state") != "verified" or attrs.get("data-verification") != "verified":
        fail("application is not in verified state")
    validate_machine_status(parser)

    if attrs.get("data-participant-publication") != "verified":
        fail(
            "participant publication state is "
            f"{attrs.get('data-participant-publication')!r}, expected 'verified'"
        )
    if attrs.get("data-participant-descriptor-count") != "1":
        fail("expected exactly one composed participant descriptor instance")
    if parser.participant_frames != [(EXPECTED_DESCRIPTOR, "association")]:
        fail(f"unexpected participant descriptor frames: {parser.participant_frames!r}")
    if not parser.participant_control_seen:
        fail(f"participant-rendered control {EXPECTED_CONTROL!r} was not present")

    print(
        "participant_browser_dump=PASS "
        f"status=web-004-verified descriptor={EXPECTED_DESCRIPTOR} "
        f"subject=association control={EXPECTED_CONTROL}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
