from __future__ import annotations

import hashlib
import json
from typing import Any

from civic.cose import parse_cose_sign1
from civic.signed_manifest import verify_signed_epoch_manifest


FORMAT = "kane-civic-epoch-manifest-diagnostic-projection"
VERSION = 1
AUTHORITY_STATUS = "derived-non-authoritative"


def _json_value(value: object) -> Any:
    if isinstance(value, bytes):
        return {
            "encoding": "hex",
            "byte_length": len(value),
            "value": value.hex(),
        }

    if isinstance(value, list):
        return [_json_value(item) for item in value]

    if isinstance(value, dict):
        return {
            str(key): _json_value(item)
            for key, item in value.items()
        }

    return value


def build_diagnostic_projection(signed_manifest: bytes) -> dict[str, object]:
    """Build a human-readable projection from a verified signed manifest.

    The projection is derived diagnostic material only. Authority remains in the
    exact COSE_Sign1 bytes and their embedded deterministic-CBOR payload.
    """

    manifest = verify_signed_epoch_manifest(signed_manifest)
    parsed = parse_cose_sign1(signed_manifest)

    return {
        "format": FORMAT,
        "version": VERSION,
        "authority_status": AUTHORITY_STATUS,
        "notice": (
            "Generated diagnostic projection only; not Civic authority bytes. "
            "Verify the referenced COSE_Sign1 and deterministic-CBOR payload."
        ),
        "source": {
            "cose_sign1_sha256": hashlib.sha256(signed_manifest).hexdigest(),
            "cose_sign1_byte_length": len(signed_manifest),
            "manifest_payload_sha256": hashlib.sha256(parsed.payload).hexdigest(),
            "manifest_payload_byte_length": len(parsed.payload),
            "protected_header_sha256": hashlib.sha256(parsed.protected).hexdigest(),
            "protected_header_byte_length": len(parsed.protected),
            "signing_node_key_id_hex": parsed.key_id.hex(),
        },
        "manifest": _json_value(manifest),
    }


def encode_diagnostic_projection_json(signed_manifest: bytes) -> bytes:
    """Return deterministic UTF-8 JSON for a verified signed manifest."""

    projection = build_diagnostic_projection(signed_manifest)
    return (
        json.dumps(
            projection,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")
