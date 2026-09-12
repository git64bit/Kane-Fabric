from __future__ import annotations

import json
import re
from typing import Any

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ContractError(ValueError):
    """Base error for MS5 contract validation."""


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError(f"value is not canonical-JSON compatible: {exc}") from exc


def nonempty_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a nonempty string")
    return value.strip()


def sha256_text(value: object, label: str) -> str:
    text = str(value)
    if not SHA256_RE.fullmatch(text):
        raise ContractError(f"{label} must be a lowercase SHA-256 hex digest")
    return text
