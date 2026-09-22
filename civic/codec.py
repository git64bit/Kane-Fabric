from __future__ import annotations

from dataclasses import dataclass
import unicodedata
from typing import Any


class CivicCodecError(ValueError):
    """Raised when Civic CBOR is unsupported, malformed, or non-deterministic."""


@dataclass(frozen=True)
class CborTag:
    tag: int
    value: object


def _encode_head(major: int, value: int) -> bytes:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise CivicCodecError("CBOR head value must be a nonnegative integer")

    prefix = major << 5
    if value < 24:
        return bytes((prefix | value,))
    if value <= 0xFF:
        return bytes((prefix | 24, value))
    if value <= 0xFFFF:
        return bytes((prefix | 25,)) + value.to_bytes(2, "big")
    if value <= 0xFFFFFFFF:
        return bytes((prefix | 26,)) + value.to_bytes(4, "big")
    if value <= 0xFFFFFFFFFFFFFFFF:
        return bytes((prefix | 27,)) + value.to_bytes(8, "big")
    raise CivicCodecError("integer exceeds CBOR uint64 range")


def encode_deterministic(value: Any) -> bytes:
    """Encode the Civic v1 CBOR subset using RFC 8949 core deterministic form."""

    if value is None:
        return b"\xf6"
    if value is False:
        return b"\xf4"
    if value is True:
        return b"\xf5"

    if isinstance(value, int):
        if value >= 0:
            return _encode_head(0, value)
        return _encode_head(1, -1 - value)

    if isinstance(value, bytes):
        return _encode_head(2, len(value)) + value

    if isinstance(value, str):
        if unicodedata.normalize("NFC", value) != value:
            raise CivicCodecError("text must be NFC-normalized before encoding")
        raw = value.encode("utf-8")
        return _encode_head(3, len(raw)) + raw

    if isinstance(value, (list, tuple)):
        body = b"".join(encode_deterministic(item) for item in value)
        return _encode_head(4, len(value)) + body

    if isinstance(value, dict):
        items: list[tuple[bytes, bytes]] = []
        for key, item in value.items():
            if not isinstance(key, (int, str)) or isinstance(key, bool):
                raise CivicCodecError("map keys must be integer or text")
            encoded_key = encode_deterministic(key)
            items.append((encoded_key, encode_deterministic(item)))

        # RFC 8949 core deterministic map ordering:
        # shorter encoded keys first, then bytewise lexical order.
        items.sort(key=lambda pair: (len(pair[0]), pair[0]))
        body = b"".join(key + item for key, item in items)
        return _encode_head(5, len(items)) + body

    if isinstance(value, CborTag):
        if not isinstance(value.tag, int) or isinstance(value.tag, bool) or value.tag < 0:
            raise CivicCodecError("CBOR tag must be a nonnegative integer")
        return _encode_head(6, value.tag) + encode_deterministic(value.value)

    if isinstance(value, float):
        raise CivicCodecError("floating-point values are prohibited in Civic v1")

    raise CivicCodecError(f"unsupported CBOR value type: {type(value).__name__}")


class _Decoder:
    def __init__(self, data: bytes):
        if not isinstance(data, bytes):
            raise CivicCodecError("CBOR input must be bytes")
        self._data = data
        self._offset = 0

    @property
    def offset(self) -> int:
        return self._offset

    def _take(self, count: int) -> bytes:
        end = self._offset + count
        if end > len(self._data):
            raise CivicCodecError("truncated CBOR input")
        chunk = self._data[self._offset:end]
        self._offset = end
        return chunk

    def _argument(self, additional: int) -> int:
        if additional < 24:
            return additional
        if additional == 24:
            return int.from_bytes(self._take(1), "big")
        if additional == 25:
            return int.from_bytes(self._take(2), "big")
        if additional == 26:
            return int.from_bytes(self._take(4), "big")
        if additional == 27:
            return int.from_bytes(self._take(8), "big")
        if additional == 31:
            raise CivicCodecError("indefinite-length CBOR is prohibited")
        raise CivicCodecError("reserved CBOR additional information")

    def item(self) -> object:
        initial = self._take(1)[0]
        major = initial >> 5
        additional = initial & 0x1F

        if major in (0, 1):
            argument = self._argument(additional)
            return argument if major == 0 else -1 - argument

        if major == 2:
            return self._take(self._argument(additional))

        if major == 3:
            raw = self._take(self._argument(additional))
            try:
                value = raw.decode("utf-8", "strict")
            except UnicodeDecodeError as exc:
                raise CivicCodecError("CBOR text is not valid UTF-8") from exc
            if unicodedata.normalize("NFC", value) != value:
                raise CivicCodecError("CBOR text is not NFC-normalized")
            return value

        if major == 4:
            return [self.item() for _ in range(self._argument(additional))]

        if major == 5:
            count = self._argument(additional)
            result: dict[object, object] = {}
            for _ in range(count):
                key = self.item()
                if not isinstance(key, (int, str)) or isinstance(key, bool):
                    raise CivicCodecError("map keys must be integer or text")
                if key in result:
                    raise CivicCodecError("duplicate CBOR map key")
                result[key] = self.item()
            return result

        if major == 6:
            return CborTag(self._argument(additional), self.item())

        if major == 7:
            if additional == 20:
                return False
            if additional == 21:
                return True
            if additional == 22:
                return None
            if additional in (25, 26, 27):
                raise CivicCodecError("floating-point values are prohibited in Civic v1")
            if additional == 31:
                raise CivicCodecError("unexpected CBOR break code")
            raise CivicCodecError("unsupported CBOR simple value")

        raise CivicCodecError("unsupported CBOR major type")


def decode_deterministic(data: bytes) -> object:
    """Decode one Civic CBOR item and require its exact deterministic encoding."""

    decoder = _Decoder(data)
    value = decoder.item()

    if decoder.offset != len(data):
        raise CivicCodecError("trailing bytes after CBOR item")

    # Re-encoding is the canonicality test. This rejects non-shortest integer
    # and length encodings as well as incorrectly ordered maps.
    if encode_deterministic(value) != data:
        raise CivicCodecError("CBOR input is not core deterministic encoding")

    return value
