from __future__ import annotations

import hashlib


# NIST P-256 / secp256r1 parameters.
P = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
A = P - 3
B = 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B
N = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
GX = 0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296
GY = 0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5

PUBLIC_KEY_BYTES = 65
SIGNATURE_BYTES = 64

Point = tuple[int, int] | None
G: Point = (GX, GY)


class CivicEcdsaError(ValueError):
    """Raised when Civic P-256 inputs are malformed or invalid."""


def _inverse(value: int, modulus: int) -> int:
    if value % modulus == 0:
        raise CivicEcdsaError("inverse does not exist")
    return pow(value, -1, modulus)


def _is_on_curve(point: Point) -> bool:
    if point is None:
        return True
    x, y = point
    if not (0 <= x < P and 0 <= y < P):
        return False
    return (y * y - (x * x * x + A * x + B)) % P == 0


def _point_add(left: Point, right: Point) -> Point:
    if left is None:
        return right
    if right is None:
        return left

    x1, y1 = left
    x2, y2 = right

    if x1 == x2 and (y1 + y2) % P == 0:
        return None

    if left == right:
        slope = ((3 * x1 * x1 + A) * _inverse(2 * y1, P)) % P
    else:
        slope = ((y2 - y1) * _inverse(x2 - x1, P)) % P

    x3 = (slope * slope - x1 - x2) % P
    y3 = (slope * (x1 - x3) - y1) % P
    return (x3, y3)


def _scalar_multiply(scalar: int, point: Point) -> Point:
    if not isinstance(scalar, int) or isinstance(scalar, bool):
        raise CivicEcdsaError("scalar must be an integer")
    if scalar < 0:
        raise CivicEcdsaError("scalar must be nonnegative")
    if point is not None and not _is_on_curve(point):
        raise CivicEcdsaError("point is not on P-256")

    result: Point = None
    addend = point
    value = scalar

    while value:
        if value & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)
        value >>= 1

    return result


def _parse_public_key(public_key: bytes) -> Point:
    if not isinstance(public_key, bytes):
        raise CivicEcdsaError("public_key must be bytes")
    if len(public_key) != PUBLIC_KEY_BYTES or public_key[0] != 0x04:
        raise CivicEcdsaError(
            "public_key must be 65-byte uncompressed SEC1 P-256 form"
        )

    point = (
        int.from_bytes(public_key[1:33], "big"),
        int.from_bytes(public_key[33:65], "big"),
    )
    if not _is_on_curve(point):
        raise CivicEcdsaError("public_key point is not on P-256")
    return point


def public_key_from_private_scalar(private_scalar: int) -> bytes:
    """Derive an uncompressed SEC1 public key from a non-production fixture scalar."""

    if (
        not isinstance(private_scalar, int)
        or isinstance(private_scalar, bool)
        or not 1 <= private_scalar < N
    ):
        raise CivicEcdsaError("private_scalar must be in the P-256 scalar range")

    point = _scalar_multiply(private_scalar, G)
    if point is None:
        raise CivicEcdsaError("private scalar produced point at infinity")

    x, y = point
    return b"\x04" + x.to_bytes(32, "big") + y.to_bytes(32, "big")


def sign_sig_structure_fixture(
    private_scalar: int,
    nonce_scalar: int,
    sig_structure: bytes,
) -> bytes:
    """Create a fixture-only P1363 r||s signature over SHA-256(sig_structure).

    The nonce is explicit by design. This function is for deterministic repository
    fixtures and tests only; it is not a production key-generation or signing API.
    """

    if (
        not isinstance(private_scalar, int)
        or isinstance(private_scalar, bool)
        or not 1 <= private_scalar < N
    ):
        raise CivicEcdsaError("private_scalar must be in the P-256 scalar range")
    if (
        not isinstance(nonce_scalar, int)
        or isinstance(nonce_scalar, bool)
        or not 1 <= nonce_scalar < N
    ):
        raise CivicEcdsaError("nonce_scalar must be in the P-256 scalar range")
    if not isinstance(sig_structure, bytes):
        raise CivicEcdsaError("sig_structure must be bytes")

    point = _scalar_multiply(nonce_scalar, G)
    if point is None:
        raise CivicEcdsaError("nonce produced point at infinity")

    r = point[0] % N
    if r == 0:
        raise CivicEcdsaError("fixture nonce produced r=0")

    z = int.from_bytes(hashlib.sha256(sig_structure).digest(), "big")
    s = (_inverse(nonce_scalar, N) * (z + r * private_scalar)) % N
    if s == 0:
        raise CivicEcdsaError("fixture nonce produced s=0")

    return r.to_bytes(32, "big") + s.to_bytes(32, "big")


def verify_sig_structure(
    public_key: bytes,
    sig_structure: bytes,
    signature: bytes,
) -> bool:
    """Verify a Civic P-256/SHA-256 P1363 r||s signature."""

    public_point = _parse_public_key(public_key)

    if not isinstance(sig_structure, bytes):
        raise CivicEcdsaError("sig_structure must be bytes")
    if not isinstance(signature, bytes):
        raise CivicEcdsaError("signature must be bytes")
    if len(signature) != SIGNATURE_BYTES:
        return False

    r = int.from_bytes(signature[:32], "big")
    s = int.from_bytes(signature[32:], "big")
    if not (1 <= r < N and 1 <= s < N):
        return False

    z = int.from_bytes(hashlib.sha256(sig_structure).digest(), "big")
    w = _inverse(s, N)
    u1 = (z * w) % N
    u2 = (r * w) % N

    point = _point_add(
        _scalar_multiply(u1, G),
        _scalar_multiply(u2, public_point),
    )
    if point is None:
        return False

    return point[0] % N == r
