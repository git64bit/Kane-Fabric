from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib

from civic.codec import CivicCodecError, decode_deterministic, encode_deterministic
from civic.cose import (
    HISTORY_RECORD_CONTENT_TYPE,
    CivicCoseError,
    build_cose_sign1,
    build_sig_structure,
    parse_cose_sign1,
)
from civic.ecdsa import (
    CivicEcdsaError,
    public_key_from_private_scalar,
    sign_sig_structure_fixture,
    verify_sig_structure,
)
from civic.epoch_manifest import (
    CRYPTO_PROFILE,
    CivicManifestError,
    derive_key_id,
    validate_epoch_manifest,
)
from civic.history import CivicHistoryError, CivicHistoryLink, parse_history_link


FORMAT = "kane-civic-history-record"
VERSION = 1
SHA256_BYTES = 32

TOP_LEVEL_FIELDS = {
    "format",
    "version",
    "crypto_profile",
    "hoa_root_id",
    "epoch_sequence",
    "ceremony_record_sha256",
    "record_type",
    "history_link",
    "signer",
    "body",
}

SIGNER_FIELDS = {
    "kind",
    "key_id",
    "participant_record_sha256",
}

SIGNER_KINDS = frozenset({"signing_node", "participant"})


class CivicSignedHistoryRecordError(ValueError):
    """Raised when a signed Civic history record violates the v1 contract."""


@dataclass(frozen=True)
class VerifiedHistoryRecord:
    """Verified generic Civic history record and authenticated linkage."""

    signed_bytes: bytes
    record_sha256: bytes
    payload: dict[str, object]
    history_link: CivicHistoryLink
    signer_public_key: bytes
    signer_key_id: bytes


def _map(
    value: object,
    label: str,
    required_fields: set[str] | None = None,
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise CivicSignedHistoryRecordError(f"{label} must be a map")
    if any(not isinstance(key, str) for key in value):
        raise CivicSignedHistoryRecordError(f"{label} map keys must be text")
    if required_fields is not None and set(value) != required_fields:
        raise CivicSignedHistoryRecordError(f"{label} fields are invalid")
    return value


def _sha256(
    value: object,
    label: str,
    *,
    optional: bool = False,
) -> bytes | None:
    if optional and value is None:
        return None
    if not isinstance(value, bytes) or len(value) != SHA256_BYTES:
        raise CivicSignedHistoryRecordError(f"{label} must be exactly 32 bytes")
    return value


def _uint(value: object, label: str, *, positive: bool = False) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise CivicSignedHistoryRecordError(f"{label} must be a uint")
    if positive and value == 0:
        raise CivicSignedHistoryRecordError(f"{label} must be greater than zero")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise CivicSignedHistoryRecordError(f"{label} must be nonempty text")
    return value


def _validate_signer(value: object) -> Mapping[str, object]:
    signer = _map(value, "signer", SIGNER_FIELDS)

    kind = _text(signer["kind"], "signer.kind")
    if kind not in SIGNER_KINDS:
        raise CivicSignedHistoryRecordError("signer.kind is unsupported")

    _sha256(signer["key_id"], "signer.key_id")

    participant_id = _sha256(
        signer["participant_record_sha256"],
        "signer.participant_record_sha256",
        optional=True,
    )

    if kind == "signing_node" and participant_id is not None:
        raise CivicSignedHistoryRecordError(
            "signing_node signer must not name a participant record"
        )
    if kind == "participant" and participant_id is None:
        raise CivicSignedHistoryRecordError(
            "participant signer must name a participant record"
        )

    return signer


def validate_history_record_payload(value: Mapping[str, object]) -> None:
    """Validate the generic deterministic-CBOR Civic history payload."""

    payload = _map(value, "history record payload", TOP_LEVEL_FIELDS)

    if payload["format"] != FORMAT or payload["version"] != VERSION:
        raise CivicSignedHistoryRecordError(
            "history record format/version is unsupported"
        )
    if payload["crypto_profile"] != CRYPTO_PROFILE:
        raise CivicSignedHistoryRecordError(
            "history record cryptographic profile is unsupported"
        )

    _sha256(payload["hoa_root_id"], "hoa_root_id")
    _uint(payload["epoch_sequence"], "epoch_sequence", positive=True)
    _sha256(payload["ceremony_record_sha256"], "ceremony_record_sha256")
    _text(payload["record_type"], "record_type")

    try:
        parse_history_link(payload["history_link"])
    except CivicHistoryError as exc:
        raise CivicSignedHistoryRecordError(str(exc)) from exc

    _validate_signer(payload["signer"])
    _map(payload["body"], "body")

    try:
        encode_deterministic(dict(payload))
    except CivicCodecError as exc:
        raise CivicSignedHistoryRecordError(str(exc)) from exc


def encode_history_record_payload(value: Mapping[str, object]) -> bytes:
    validate_history_record_payload(value)
    return encode_deterministic(dict(value))


def decode_history_record_payload(data: bytes) -> dict[str, object]:
    try:
        value = decode_deterministic(data)
    except CivicCodecError as exc:
        raise CivicSignedHistoryRecordError(str(exc)) from exc

    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise CivicSignedHistoryRecordError(
            "history record payload must decode to a text-keyed map"
        )

    validate_history_record_payload(value)
    return value  # type: ignore[return-value]


def _resolve_epoch_manifest(
    payload: Mapping[str, object],
    epoch_manifests: Sequence[Mapping[str, object]],
) -> Mapping[str, object]:
    matches: list[Mapping[str, object]] = []

    for manifest in epoch_manifests:
        try:
            validate_epoch_manifest(manifest)
        except CivicManifestError as exc:
            raise CivicSignedHistoryRecordError(
                "candidate Epoch Manifest is invalid"
            ) from exc

        ceremony = manifest["ceremony"]
        assert isinstance(ceremony, Mapping)

        if (
            manifest["hoa_root_id"] == payload["hoa_root_id"]
            and manifest["epoch_sequence"] == payload["epoch_sequence"]
            and ceremony["ceremony_record_sha256"]
            == payload["ceremony_record_sha256"]
        ):
            matches.append(manifest)

    if len(matches) != 1:
        raise CivicSignedHistoryRecordError(
            "history record authority context must match exactly one accepted Epoch Manifest"
        )

    return matches[0]


def _resolve_signer(
    payload: Mapping[str, object],
    manifest: Mapping[str, object],
) -> tuple[bytes, bytes]:
    signer = payload["signer"]
    assert isinstance(signer, Mapping)

    kind = signer["kind"]
    key_id = signer["key_id"]
    participant_id = signer["participant_record_sha256"]

    assert isinstance(kind, str)
    assert isinstance(key_id, bytes)

    if kind == "signing_node":
        signing_node = manifest["signing_node"]
        assert isinstance(signing_node, Mapping)

        manifest_key_id = signing_node["key_id"]
        public_key = signing_node["public_key"]
        assert isinstance(manifest_key_id, bytes)
        assert isinstance(public_key, bytes)

        if participant_id is not None:
            raise CivicSignedHistoryRecordError(
                "signing_node signer must not name a participant record"
            )
        if key_id != manifest_key_id:
            raise CivicSignedHistoryRecordError(
                "history signer key does not match epoch Signing Node"
            )

    elif kind == "participant":
        if not isinstance(participant_id, bytes):
            raise CivicSignedHistoryRecordError(
                "participant signer must name a participant record"
            )

        participants = manifest["participants"]
        assert isinstance(participants, list)

        matches = [
            item
            for item in participants
            if isinstance(item, Mapping)
            and item["participant_record_sha256"] == participant_id
        ]
        if len(matches) != 1:
            raise CivicSignedHistoryRecordError(
                "participant signer is not uniquely present in referenced epoch"
            )

        participant = matches[0]
        manifest_key_id = participant["participant_key_id"]
        public_key = participant["participant_public_key"]
        assert isinstance(manifest_key_id, bytes)
        assert isinstance(public_key, bytes)

        if key_id != manifest_key_id:
            raise CivicSignedHistoryRecordError(
                "history signer key does not match epoch participant"
            )

    else:
        raise CivicSignedHistoryRecordError("signer.kind is unsupported")

    try:
        derived_key_id = derive_key_id(public_key)
    except CivicManifestError as exc:
        raise CivicSignedHistoryRecordError(str(exc)) from exc

    if derived_key_id != key_id:
        raise CivicSignedHistoryRecordError(
            "resolved signer key identifier does not match public key"
        )

    return public_key, key_id


def sign_history_record_fixture(
    payload: Mapping[str, object],
    *,
    epoch_manifest: Mapping[str, object],
    private_scalar: int,
    nonce_scalar: int,
) -> bytes:
    """Create one fixture-only signed Civic history record.

    The caller supplies an explicit non-production private scalar and nonce.
    This helper never generates or persists production key material.
    """

    try:
        payload_bytes = encode_history_record_payload(payload)
        manifest = _resolve_epoch_manifest(payload, [epoch_manifest])
        public_key, key_id = _resolve_signer(payload, manifest)
        fixture_public_key = public_key_from_private_scalar(private_scalar)
    except (CivicSignedHistoryRecordError, CivicEcdsaError) as exc:
        if isinstance(exc, CivicSignedHistoryRecordError):
            raise
        raise CivicSignedHistoryRecordError(str(exc)) from exc

    if fixture_public_key != public_key:
        raise CivicSignedHistoryRecordError(
            "fixture private scalar does not match resolved history signer"
        )

    try:
        sig_structure = build_sig_structure(
            payload_bytes,
            key_id,
            content_type=HISTORY_RECORD_CONTENT_TYPE,
        )
        signature = sign_sig_structure_fixture(
            private_scalar=private_scalar,
            nonce_scalar=nonce_scalar,
            sig_structure=sig_structure,
        )
        return build_cose_sign1(
            payload_bytes,
            key_id,
            signature,
            content_type=HISTORY_RECORD_CONTENT_TYPE,
        )
    except (CivicCoseError, CivicEcdsaError) as exc:
        raise CivicSignedHistoryRecordError(str(exc)) from exc


def verify_signed_history_record(
    data: bytes,
    *,
    epoch_manifests: Sequence[Mapping[str, object]],
) -> VerifiedHistoryRecord:
    """Verify one generic Civic history record against accepted epoch context."""

    try:
        parsed = parse_cose_sign1(
            data,
            expected_content_type=HISTORY_RECORD_CONTENT_TYPE,
        )
        payload = decode_history_record_payload(parsed.payload)
        manifest = _resolve_epoch_manifest(payload, epoch_manifests)
        public_key, signer_key_id = _resolve_signer(payload, manifest)
    except (CivicCoseError, CivicSignedHistoryRecordError) as exc:
        if isinstance(exc, CivicSignedHistoryRecordError):
            raise
        raise CivicSignedHistoryRecordError(str(exc)) from exc

    if parsed.key_id != signer_key_id:
        raise CivicSignedHistoryRecordError(
            "COSE kid does not match authenticated history signer key_id"
        )

    try:
        sig_structure = build_sig_structure(
            parsed.payload,
            parsed.key_id,
            content_type=HISTORY_RECORD_CONTENT_TYPE,
        )
        valid = verify_sig_structure(
            public_key,
            sig_structure,
            parsed.signature,
        )
    except (CivicCoseError, CivicEcdsaError) as exc:
        raise CivicSignedHistoryRecordError(str(exc)) from exc

    if not valid:
        raise CivicSignedHistoryRecordError(
            "Civic history record signature is invalid"
        )

    try:
        history_link = parse_history_link(payload["history_link"])
    except CivicHistoryError as exc:
        raise CivicSignedHistoryRecordError(str(exc)) from exc

    return VerifiedHistoryRecord(
        signed_bytes=data,
        record_sha256=hashlib.sha256(data).digest(),
        payload=payload,
        history_link=history_link,
        signer_public_key=public_key,
        signer_key_id=signer_key_id,
    )
