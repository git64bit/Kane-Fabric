from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile


SHA256_BYTES = 32


class CivicObjectStoreError(ValueError):
    """Raised when Civic content-addressed object storage is inconsistent."""


def object_sha256(data: bytes) -> bytes:
    """Return the Civic content identity of exact object bytes."""

    if not isinstance(data, bytes):
        raise CivicObjectStoreError("Civic object must be bytes")
    return hashlib.sha256(data).digest()


def object_path(root: Path | str, sha256: bytes) -> Path:
    """Return the deterministic local path for one SHA-256 Civic object.

    The path is a storage projection only. It is not part of Civic identity.
    """

    if not isinstance(sha256, bytes) or len(sha256) != SHA256_BYTES:
        raise CivicObjectStoreError("object sha256 must be exactly 32 bytes")

    root_path = Path(root)
    hex_digest = sha256.hex()
    return root_path / hex_digest[:2] / hex_digest[2:]


def verify_object_bytes(
    data: bytes,
    *,
    expected_sha256: bytes,
    expected_byte_length: int,
) -> None:
    """Verify exact bytes against an Epoch Manifest object descriptor identity."""

    if not isinstance(data, bytes):
        raise CivicObjectStoreError("Civic object must be bytes")

    if not isinstance(expected_sha256, bytes) or len(expected_sha256) != SHA256_BYTES:
        raise CivicObjectStoreError("expected object sha256 must be exactly 32 bytes")

    if (
        not isinstance(expected_byte_length, int)
        or isinstance(expected_byte_length, bool)
        or expected_byte_length < 0
    ):
        raise CivicObjectStoreError("expected byte length must be a non-negative integer")

    if len(data) != expected_byte_length:
        raise CivicObjectStoreError("object byte length does not match descriptor")

    if hashlib.sha256(data).digest() != expected_sha256:
        raise CivicObjectStoreError("object sha256 does not match descriptor")


def put_object(root: Path | str, data: bytes) -> bytes:
    """Store exact bytes by SHA-256 without changing their Civic identity.

    Existing content is accepted only when its exact bytes verify to the same
    digest. New content is written to a temporary file in the target directory
    and atomically installed with os.replace.
    """

    digest = object_sha256(data)
    target = object_path(root, digest)
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        existing = target.read_bytes()
        verify_object_bytes(
            existing,
            expected_sha256=digest,
            expected_byte_length=len(data),
        )
        if existing != data:
            raise CivicObjectStoreError(
                "existing object bytes differ despite matching descriptor identity"
            )
        return digest

    fd, temporary_name = tempfile.mkstemp(
        prefix=".civic-object-",
        dir=target.parent,
    )
    temporary = Path(temporary_name)

    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())

        verify_object_bytes(
            temporary.read_bytes(),
            expected_sha256=digest,
            expected_byte_length=len(data),
        )

        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()

    return digest


def get_object(
    root: Path | str,
    sha256: bytes,
    *,
    expected_byte_length: int | None = None,
) -> bytes:
    """Load a stored Civic object and verify its exact SHA-256 identity."""

    target = object_path(root, sha256)

    try:
        data = target.read_bytes()
    except FileNotFoundError as exc:
        raise CivicObjectStoreError("Civic object is not present in local store") from exc

    if expected_byte_length is None:
        expected_byte_length = len(data)

    verify_object_bytes(
        data,
        expected_sha256=sha256,
        expected_byte_length=expected_byte_length,
    )
    return data


def has_object(root: Path | str, sha256: bytes) -> bool:
    """Return True only when the addressed local object exists and verifies."""

    target = object_path(root, sha256)
    if not target.exists():
        return False

    try:
        data = target.read_bytes()
        verify_object_bytes(
            data,
            expected_sha256=sha256,
            expected_byte_length=len(data),
        )
    except (OSError, CivicObjectStoreError):
        return False

    return True
