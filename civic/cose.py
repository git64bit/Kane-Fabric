from __future__ import annotations

from dataclasses import dataclass

from civic.codec import CborTag, CivicCodecError, decode_deterministic, encode_deterministic


COSE_SIGN1_TAG = 18
COSE_ALG_ESP256 = -9

EPOCH_CONTENT_TYPE = "application/kane-civic-epoch+cbor"
HISTORY_RECORD_CONTENT_TYPE = "application/kane-civic-history-record+cbor"

# Backward-compatible name for the original Epoch Manifest COSE contract.
CONTENT_TYPE = EPOCH_CONTENT_TYPE

KEY_ID_BYTES = 32
SIGNATURE_BYTES = 64


class CivicCoseError(ValueError):
    """Raised when a Civic COSE_Sign1 object violates the v1 contract."""


@dataclass(frozen=True)
class ParsedCoseSign1:
    protected: bytes
    payload: bytes
    signature: bytes
    key_id: bytes
    content_type: str


def _fixed_bytes(value: object, label: str, size: int) -> bytes:
    if not isinstance(value, bytes):
        raise CivicCoseError(f"{label} must be bytes")
    if len(value) != size:
        raise CivicCoseError(f"{label} must be exactly {size} bytes")
    return value


def _content_type(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise CivicCoseError("COSE content type must be nonempty text")
    return value


def build_protected_header(
    key_id: bytes,
    *,
    content_type: str = EPOCH_CONTENT_TYPE,
) -> bytes:
    key_id = _fixed_bytes(key_id, "key_id", KEY_ID_BYTES)
    content_type = _content_type(content_type)

    return encode_deterministic(
        {
            1: COSE_ALG_ESP256,
            3: content_type,
            4: key_id,
        }
    )


def build_sig_structure(
    payload: bytes,
    key_id: bytes,
    *,
    content_type: str = EPOCH_CONTENT_TYPE,
) -> bytes:
    if not isinstance(payload, bytes):
        raise CivicCoseError("payload must be bytes")

    protected = build_protected_header(
        key_id,
        content_type=content_type,
    )

    return encode_deterministic(
        [
            "Signature1",
            protected,
            b"",
            payload,
        ]
    )


def build_cose_sign1(
    payload: bytes,
    key_id: bytes,
    signature: bytes,
    *,
    content_type: str = EPOCH_CONTENT_TYPE,
) -> bytes:
    if not isinstance(payload, bytes):
        raise CivicCoseError("payload must be bytes")

    protected = build_protected_header(
        key_id,
        content_type=content_type,
    )
    signature = _fixed_bytes(signature, "signature", SIGNATURE_BYTES)

    return encode_deterministic(
        CborTag(
            COSE_SIGN1_TAG,
            [
                protected,
                {},
                payload,
                signature,
            ],
        )
    )


def parse_cose_sign1(
    data: bytes,
    *,
    expected_content_type: str = EPOCH_CONTENT_TYPE,
) -> ParsedCoseSign1:
    expected_content_type = _content_type(expected_content_type)

    try:
        decoded = decode_deterministic(data)
    except CivicCodecError as exc:
        raise CivicCoseError(str(exc)) from exc

    if not isinstance(decoded, CborTag) or decoded.tag != COSE_SIGN1_TAG:
        raise CivicCoseError("Civic signed record must be tagged COSE_Sign1")

    body = decoded.value
    if not isinstance(body, list) or len(body) != 4:
        raise CivicCoseError("COSE_Sign1 body must contain exactly four elements")

    protected, unprotected, payload, signature = body

    if not isinstance(protected, bytes):
        raise CivicCoseError("COSE protected header must be bytes")
    if unprotected != {}:
        raise CivicCoseError("COSE unprotected header must be empty in Civic v1")
    if not isinstance(payload, bytes):
        raise CivicCoseError("detached payloads are not allowed in Civic v1")

    signature = _fixed_bytes(signature, "signature", SIGNATURE_BYTES)

    try:
        header = decode_deterministic(protected)
    except CivicCodecError as exc:
        raise CivicCoseError("invalid COSE protected header") from exc

    if not isinstance(header, dict) or set(header) != {1, 3, 4}:
        raise CivicCoseError("COSE protected header fields are invalid")

    if header[1] != COSE_ALG_ESP256:
        raise CivicCoseError("COSE algorithm must be ESP256 (-9)")

    actual_content_type = _content_type(header[3])
    if actual_content_type != expected_content_type:
        raise CivicCoseError("COSE content type is invalid")

    key_id = _fixed_bytes(header[4], "COSE kid", KEY_ID_BYTES)

    return ParsedCoseSign1(
        protected=protected,
        payload=payload,
        signature=signature,
        key_id=key_id,
        content_type=actual_content_type,
    )
