from __future__ import annotations

from dataclasses import dataclass
import hashlib

from civic.codec import CivicCodecError, _Decoder, decode_deterministic, encode_deterministic


class CivicHistoryError(ValueError):
    """Raised when a Civic CBOR Sequence is malformed or non-deterministic."""


@dataclass(frozen=True)
class CivicSequenceRecord:
    """One independently identifiable record stored in a Civic CBOR Sequence."""

    offset: int
    byte_length: int
    sha256: bytes
    encoded: bytes
    value: object


def history_record_sha256(record: bytes) -> bytes:
    """Return SHA-256 of one exact deterministic-CBOR record."""

    try:
        decode_deterministic(record)
    except CivicCodecError as exc:
        raise CivicHistoryError("history record is not one deterministic CBOR item") from exc

    return hashlib.sha256(record).digest()


def decode_history_sequence(data: bytes) -> tuple[CivicSequenceRecord, ...]:
    """Decode an RFC 8742-style sequence of deterministic Civic CBOR records.

    Each concatenated item is independently checked for Civic deterministic
    encoding and receives an identity equal to SHA-256 of its exact item bytes.
    Empty input is the empty sequence.
    """

    if not isinstance(data, bytes):
        raise CivicHistoryError("history sequence must be bytes")

    records: list[CivicSequenceRecord] = []
    offset = 0

    while offset < len(data):
        decoder = _Decoder(data[offset:])
        try:
            value = decoder.item()
        except CivicCodecError as exc:
            raise CivicHistoryError(
                f"invalid history record at byte offset {offset}"
            ) from exc

        consumed = decoder.offset
        if consumed <= 0:
            raise CivicHistoryError(
                f"history decoder made no progress at byte offset {offset}"
            )

        encoded = data[offset : offset + consumed]

        try:
            canonical = encode_deterministic(value)
        except CivicCodecError as exc:
            raise CivicHistoryError(
                f"unsupported history record at byte offset {offset}"
            ) from exc

        if canonical != encoded:
            raise CivicHistoryError(
                f"non-deterministic history record at byte offset {offset}"
            )

        records.append(
            CivicSequenceRecord(
                offset=offset,
                byte_length=consumed,
                sha256=hashlib.sha256(encoded).digest(),
                encoded=encoded,
                value=value,
            )
        )
        offset += consumed

    return tuple(records)


def append_history_record(sequence: bytes, record: bytes) -> bytes:
    """Append one deterministic-CBOR record without rewriting prior bytes.

    Existing sequence bytes are validated before append. The new record must be
    exactly one deterministic Civic CBOR item. Signing and record-schema
    semantics belong to the record format layered above this storage primitive.
    """

    if not isinstance(sequence, bytes):
        raise CivicHistoryError("history sequence must be bytes")
    if not isinstance(record, bytes):
        raise CivicHistoryError("history record must be bytes")

    decode_history_sequence(sequence)

    try:
        decode_deterministic(record)
    except CivicCodecError as exc:
        raise CivicHistoryError(
            "history record is not one deterministic CBOR item"
        ) from exc

    return sequence + record
