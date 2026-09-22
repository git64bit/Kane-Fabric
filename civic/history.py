from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import hashlib

from civic.codec import CivicCodecError, _Decoder, decode_deterministic, encode_deterministic


VALID_HISTORY_STREAMS = frozenset({"accepted", "witness", "diagnostics", "knowledge"})


class CivicHistoryError(ValueError):
    """Raised when Civic history storage or linkage is invalid."""


@dataclass(frozen=True)
class CivicSequenceRecord:
    """One independently identifiable record stored in a Civic CBOR Sequence."""

    offset: int
    byte_length: int
    sha256: bytes
    encoded: bytes
    value: object


@dataclass(frozen=True)
class CivicHistoryLink:
    """Authenticated linkage metadata extracted from one Civic history record."""

    stream: str
    predecessor_record_sha256: bytes | None


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


def parse_history_link(value: object) -> CivicHistoryLink:
    """Validate the frozen Civic v1 history-link map.

    The caller is responsible for extracting this map from authenticated record
    content. This module does not freeze the surrounding event schema or decide
    how a particular record type is authenticated.
    """

    if not isinstance(value, dict):
        raise CivicHistoryError("history_link must be a map")

    if set(value) != {"stream", "predecessor_record_sha256"}:
        raise CivicHistoryError(
            "history_link must contain exactly stream and predecessor_record_sha256"
        )

    stream = value["stream"]
    predecessor = value["predecessor_record_sha256"]

    if not isinstance(stream, str) or stream not in VALID_HISTORY_STREAMS:
        raise CivicHistoryError("invalid Civic history stream")

    if predecessor is not None:
        if not isinstance(predecessor, bytes) or len(predecessor) != 32:
            raise CivicHistoryError(
                "predecessor_record_sha256 must be null or exactly 32 bytes"
            )

    return CivicHistoryLink(
        stream=stream,
        predecessor_record_sha256=predecessor,
    )


def verify_linked_history_sequence(
    data: bytes,
    *,
    stream: str,
    expected_head_sha256: bytes | None,
    authenticated_link_for_record: Callable[[CivicSequenceRecord], object],
) -> tuple[CivicSequenceRecord, ...]:
    """Verify sequence order against authenticated predecessor links.

    authenticated_link_for_record must return the history_link map from record
    content whose authentication has already been verified by the record-format
    layer. A null expected head requires an empty stream; a non-null head
    requires at least one record and must equal the final exact record hash.
    """

    if stream not in VALID_HISTORY_STREAMS:
        raise CivicHistoryError("invalid expected Civic history stream")

    if expected_head_sha256 is not None:
        if (
            not isinstance(expected_head_sha256, bytes)
            or len(expected_head_sha256) != 32
        ):
            raise CivicHistoryError(
                "expected history head must be null or exactly 32 bytes"
            )

    records = decode_history_sequence(data)

    if expected_head_sha256 is None:
        if records:
            raise CivicHistoryError(
                "null history head requires an empty history sequence"
            )
        return records

    if not records:
        raise CivicHistoryError(
            "non-null history head requires at least one history record"
        )

    predecessor: bytes | None = None

    for index, record in enumerate(records):
        try:
            raw_link = authenticated_link_for_record(record)
        except CivicHistoryError:
            raise
        except Exception as exc:
            raise CivicHistoryError(
                f"could not extract authenticated history_link from record {index}"
            ) from exc

        link = parse_history_link(raw_link)

        if link.stream != stream:
            raise CivicHistoryError(
                f"record {index} declares history stream {link.stream!r}, "
                f"expected {stream!r}"
            )

        if link.predecessor_record_sha256 != predecessor:
            if index == 0:
                raise CivicHistoryError(
                    "genesis history record must declare a null predecessor"
                )
            raise CivicHistoryError(
                f"record {index} predecessor does not match prior record identity"
            )

        predecessor = record.sha256

    if records[-1].sha256 != expected_head_sha256:
        raise CivicHistoryError(
            "final history record identity does not match expected history head"
        )

    return records
