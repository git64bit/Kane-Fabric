#!/usr/bin/env python3
"""Validate a dumped WEB-002 DOM against the accepted Kane County MS3/MS4 proof identities."""

from __future__ import annotations

import html.parser
import json
import sys
from pathlib import Path

EXPECTED_SUBSTRATE = "fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc"
EXPECTED_COMPOSITION = "a58c8398248cee05b7baad9ae289fe0581bdb3624ce1aff3aa8a49721f92ee53"


class DumpParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root_state: str | None = None
        self.in_status = False
        self.status_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "html":
            self.root_state = values.get("data-state")
        if tag == "pre" and values.get("id") == "machine-status":
            self.in_status = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "pre" and self.in_status:
            self.in_status = False

    def handle_data(self, data: str) -> None:
        if self.in_status:
            self.status_parts.append(data)


def fail(message: str) -> None:
    raise SystemExit(f"WEB-002 browser acceptance failed: {message}")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} DOM_DUMP.html")
    parser = DumpParser()
    parser.feed(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if parser.root_state != "verified":
        fail(f"document state is {parser.root_state!r}, expected 'verified'")
    raw = "".join(parser.status_parts).strip()
    if not raw:
        fail("machine-status payload is empty")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"machine-status payload is invalid JSON: {exc}")

    if payload.get("status") != "web-002-verified":
        fail("application did not report web-002-verified")
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

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    print("web_002_browser_dump=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
