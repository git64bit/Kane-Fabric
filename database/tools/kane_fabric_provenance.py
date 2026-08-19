#!/usr/bin/env python3
"""Kane Fabric administrative provenance entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from kane_fabric_compat import DB, load_donor

DONOR = load_donor("kane_provenance")

# The donor validator dynamically loaded kane_db.py from its own checkout.
# Replace that single dependency with the Fabric-owned core validator.
DONOR.validate_core_database = DB.validate_database

ADMIN_TABLES = DONOR.ADMIN_TABLES
EXPECTED_COLUMNS = DONOR.EXPECTED_COLUMNS
KEY_PATTERN = DONOR.KEY_PATTERN
SHA256_PATTERN = DONOR.SHA256_PATTERN
DATETIME_PATTERN = DONOR.DATETIME_PATTERN

utc_now = DONOR.utc_now
valid_datetime = DONOR.valid_datetime
canonical_json = DONOR.canonical_json
normalize_descriptor = DONOR.normalize_descriptor
record_descriptor = DONOR.record_descriptor
trace_release = DONOR.trace_release
validate_schema = DONOR.validate_schema
validate_data = DONOR.validate_data
validate_database = DONOR.validate_database
build_parser = DONOR.build_parser


def main(argv: Sequence[str] | None = None) -> int:
    return int(DONOR.main(argv))


if __name__ == "__main__":
    raise SystemExit(main())
