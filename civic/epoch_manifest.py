from __future__ import annotations

import hashlib
from typing import Mapping

from civic.codec import CivicCodecError, decode_deterministic, encode_deterministic


FORMAT = "kane-civic-epoch-manifest"
VERSION = 1
CRYPTO_PROFILE = "kane-civic-ecdsa-p256-sha256-v1"

SHA256_BYTES = 32
P256_PUBLIC_KEY_BYTES = 65

TOP_LEVEL_FIELDS = {
    "format",
    "version",
    "crypto_profile",
    "hoa_root_id",
    "epoch_sequence",
    "predecessor_manifest_sha256",
    "effective_time_ms",
    "governing_profile",
    "governing_sources",
    "participants",
    "operator",
    "signing_node",
    "history",
    "ceremony",
    "object_index",
}


class CivicManifestError(ValueError):
    """Raised when an Epoch Manifest violates the Civic v1 contract."""


def _map(value: object, label: str, fields: set[str]) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise CivicManifestError(f"{label} must be a map")
    if any(not isinstance(key, str) for key in value):
        raise CivicManifestError(f"{label} map keys must be text")
    if set(value) != fields:
        raise CivicManifestError(f"{label} fields are invalid")
    return value


def _bytes(value: object, label: str, size: int | None = None) -> bytes:
    if not isinstance(value, bytes):
        raise CivicManifestError(f"{label} must be bytes")
    if size is not None and len(value) != size:
        raise CivicManifestError(f"{label} must be exactly {size} bytes")
    return value


def _sha256(value: object, label: str, *, optional: bool = False) -> bytes | None:
    if value is None and optional:
        return None
    return _bytes(value, label, SHA256_BYTES)


def _text(value: object, label: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value:
        raise CivicManifestError(f"{label} must be nonempty text")
    return value


def _uint(value: object, label: str, *, positive: bool = False) -> int:
    minimum = 1 if positive else 0
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < minimum
        or value > 0xFFFFFFFFFFFFFFFF
    ):
        qualifier = "positive " if positive else ""
        raise CivicManifestError(f"{label} must be a {qualifier}uint64")
    return value


def derive_key_id(public_key: bytes) -> bytes:
    public_key = _bytes(public_key, "public_key", P256_PUBLIC_KEY_BYTES)
    if public_key[0] != 0x04:
        raise CivicManifestError("public_key must be uncompressed SEC1 P-256 form")
    return hashlib.sha256(public_key).digest()


def _validate_governing_profile(value: object) -> None:
    item = _map(
        value,
        "governing_profile",
        {"profile_id", "profile_sha256", "source_set_sha256"},
    )
    _text(item["profile_id"], "governing_profile.profile_id")
    _sha256(item["profile_sha256"], "governing_profile.profile_sha256")
    _sha256(item["source_set_sha256"], "governing_profile.source_set_sha256")


def _validate_governing_sources(value: object) -> None:
    if not isinstance(value, list):
        raise CivicManifestError("governing_sources must be an array")

    source_ids: list[bytes] = []

    for index, raw in enumerate(value):
        item = _map(
            raw,
            f"governing_sources[{index}]",
            {
                "source_id",
                "role",
                "sha256",
                "byte_length",
                "media_type",
                "title",
                "source_uri",
            },
        )

        source_id = _text(item["source_id"], f"governing_sources[{index}].source_id")
        assert source_id is not None
        source_ids.append(source_id.encode("utf-8"))

        _text(item["role"], f"governing_sources[{index}].role")
        _sha256(item["sha256"], f"governing_sources[{index}].sha256")
        _uint(item["byte_length"], f"governing_sources[{index}].byte_length")
        _text(item["media_type"], f"governing_sources[{index}].media_type")
        _text(item["title"], f"governing_sources[{index}].title", optional=True)
        _text(item["source_uri"], f"governing_sources[{index}].source_uri", optional=True)

    if source_ids != sorted(source_ids):
        raise CivicManifestError("governing_sources must be sorted by source_id UTF-8 bytes")
    if len(source_ids) != len(set(source_ids)):
        raise CivicManifestError("governing_sources source_id values must be unique")


def _validate_participants(value: object) -> tuple[set[bytes], set[bytes]]:
    if not isinstance(value, list) or not value:
        raise CivicManifestError("participants must be a nonempty array")

    participant_ids: list[bytes] = []
    key_ids: set[bytes] = set()

    for index, raw in enumerate(value):
        item = _map(
            raw,
            f"participants[{index}]",
            {
                "participant_record_sha256",
                "participant_key_id",
                "participant_public_key",
                "standing_record_sha256",
                "issuance_record_sha256",
            },
        )

        participant_id = _sha256(
            item["participant_record_sha256"],
            f"participants[{index}].participant_record_sha256",
        )
        assert participant_id is not None
        participant_ids.append(participant_id)

        key_id = _sha256(
            item["participant_key_id"],
            f"participants[{index}].participant_key_id",
        )
        assert key_id is not None

        public_key = _bytes(
            item["participant_public_key"],
            f"participants[{index}].participant_public_key",
            P256_PUBLIC_KEY_BYTES,
        )
        if public_key[0] != 0x04:
            raise CivicManifestError(
                f"participants[{index}].participant_public_key must be uncompressed SEC1"
            )
        if derive_key_id(public_key) != key_id:
            raise CivicManifestError(
                f"participants[{index}].participant_key_id does not match public key"
            )
        if key_id in key_ids:
            raise CivicManifestError("participant_key_id values must be unique")
        key_ids.add(key_id)

        _sha256(
            item["standing_record_sha256"],
            f"participants[{index}].standing_record_sha256",
        )
        _sha256(
            item["issuance_record_sha256"],
            f"participants[{index}].issuance_record_sha256",
        )

    if participant_ids != sorted(participant_ids):
        raise CivicManifestError(
            "participants must be sorted by participant_record_sha256"
        )
    if len(participant_ids) != len(set(participant_ids)):
        raise CivicManifestError("participant_record_sha256 values must be unique")

    return set(participant_ids), key_ids


def _validate_operator(value: object, participant_ids: set[bytes]) -> None:
    item = _map(
        value,
        "operator",
        {"participant_record_sha256", "selection_record_sha256"},
    )
    participant_id = _sha256(
        item["participant_record_sha256"],
        "operator.participant_record_sha256",
    )
    if participant_id not in participant_ids:
        raise CivicManifestError("operator must reference a current participant")
    _sha256(item["selection_record_sha256"], "operator.selection_record_sha256")


def _validate_signing_node(value: object, participant_key_ids: set[bytes]) -> None:
    item = _map(
        value,
        "signing_node",
        {"key_id", "public_key", "authorization_record_sha256"},
    )

    key_id = _sha256(item["key_id"], "signing_node.key_id")
    assert key_id is not None

    public_key = _bytes(
        item["public_key"],
        "signing_node.public_key",
        P256_PUBLIC_KEY_BYTES,
    )
    if public_key[0] != 0x04:
        raise CivicManifestError("signing_node.public_key must be uncompressed SEC1")
    if derive_key_id(public_key) != key_id:
        raise CivicManifestError("signing_node.key_id does not match public key")
    if key_id in participant_key_ids:
        raise CivicManifestError("signing-node key must not reuse a participant key")

    _sha256(
        item["authorization_record_sha256"],
        "signing_node.authorization_record_sha256",
    )


def _validate_history(value: object) -> None:
    item = _map(
        value,
        "history",
        {
            "accepted_history_head_sha256",
            "witness_head_sha256",
            "diagnostics_head_sha256",
            "knowledge_head_sha256",
        },
    )
    _sha256(
        item["accepted_history_head_sha256"],
        "history.accepted_history_head_sha256",
    )
    _sha256(
        item["witness_head_sha256"],
        "history.witness_head_sha256",
        optional=True,
    )
    _sha256(
        item["diagnostics_head_sha256"],
        "history.diagnostics_head_sha256",
        optional=True,
    )
    _sha256(
        item["knowledge_head_sha256"],
        "history.knowledge_head_sha256",
        optional=True,
    )


def _validate_ceremony(value: object) -> None:
    item = _map(
        value,
        "ceremony",
        {"ceremony_record_sha256", "governance_proof_sha256"},
    )
    _sha256(item["ceremony_record_sha256"], "ceremony.ceremony_record_sha256")

    proofs = item["governance_proof_sha256"]
    if not isinstance(proofs, list):
        raise CivicManifestError("ceremony.governance_proof_sha256 must be an array")

    parsed: list[bytes] = []
    for index, proof in enumerate(proofs):
        digest = _sha256(
            proof,
            f"ceremony.governance_proof_sha256[{index}]",
        )
        assert digest is not None
        parsed.append(digest)

    if parsed != sorted(parsed):
        raise CivicManifestError("ceremony governance proofs must be sorted bytewise")
    if len(parsed) != len(set(parsed)):
        raise CivicManifestError("ceremony governance proofs must be unique")


def _validate_object_index(value: object) -> None:
    if not isinstance(value, list):
        raise CivicManifestError("object_index must be an array")

    object_hashes: list[bytes] = []

    for index, raw in enumerate(value):
        item = _map(
            raw,
            f"object_index[{index}]",
            {
                "sha256",
                "byte_length",
                "media_type",
                "semantic_role",
                "name",
                "cid",
                "inline",
            },
        )

        digest = _sha256(item["sha256"], f"object_index[{index}].sha256")
        assert digest is not None
        object_hashes.append(digest)

        byte_length = _uint(
            item["byte_length"],
            f"object_index[{index}].byte_length",
        )
        _text(item["media_type"], f"object_index[{index}].media_type")
        _text(item["semantic_role"], f"object_index[{index}].semantic_role")
        _text(item["name"], f"object_index[{index}].name", optional=True)
        _text(item["cid"], f"object_index[{index}].cid", optional=True)

        inline = item["inline"]
        if inline is not None:
            raw_bytes = _bytes(inline, f"object_index[{index}].inline")
            if len(raw_bytes) != byte_length:
                raise CivicManifestError(
                    f"object_index[{index}] inline byte length mismatch"
                )
            if hashlib.sha256(raw_bytes).digest() != digest:
                raise CivicManifestError(
                    f"object_index[{index}] inline SHA-256 mismatch"
                )

    if object_hashes != sorted(object_hashes):
        raise CivicManifestError("object_index must be sorted by SHA-256 bytes")
    if len(object_hashes) != len(set(object_hashes)):
        raise CivicManifestError("object_index SHA-256 values must be unique")


def validate_epoch_manifest(value: Mapping[str, object]) -> None:
    manifest = _map(value, "manifest", TOP_LEVEL_FIELDS)

    if manifest["format"] != FORMAT or manifest["version"] != VERSION:
        raise CivicManifestError("manifest format/version is unsupported")
    if manifest["crypto_profile"] != CRYPTO_PROFILE:
        raise CivicManifestError("manifest cryptographic profile is unsupported")

    _sha256(manifest["hoa_root_id"], "hoa_root_id")

    epoch_sequence = _uint(
        manifest["epoch_sequence"],
        "epoch_sequence",
        positive=True,
    )
    predecessor = _sha256(
        manifest["predecessor_manifest_sha256"],
        "predecessor_manifest_sha256",
        optional=True,
    )
    if epoch_sequence == 1 and predecessor is not None:
        raise CivicManifestError("epoch 1 must not have a predecessor")
    if epoch_sequence > 1 and predecessor is None:
        raise CivicManifestError("later epochs must name a predecessor")

    _uint(manifest["effective_time_ms"], "effective_time_ms")
    _validate_governing_profile(manifest["governing_profile"])
    _validate_governing_sources(manifest["governing_sources"])

    participant_ids, participant_key_ids = _validate_participants(
        manifest["participants"]
    )
    _validate_operator(manifest["operator"], participant_ids)
    _validate_signing_node(manifest["signing_node"], participant_key_ids)

    _validate_history(manifest["history"])
    _validate_ceremony(manifest["ceremony"])
    _validate_object_index(manifest["object_index"])

    try:
        encode_deterministic(dict(manifest))
    except CivicCodecError as exc:
        raise CivicManifestError(str(exc)) from exc


def encode_epoch_manifest(value: Mapping[str, object]) -> bytes:
    validate_epoch_manifest(value)
    return encode_deterministic(dict(value))


def decode_epoch_manifest(data: bytes) -> dict[str, object]:
    try:
        value = decode_deterministic(data)
    except CivicCodecError as exc:
        raise CivicManifestError(str(exc)) from exc

    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise CivicManifestError("manifest must decode to a text-keyed map")

    validate_epoch_manifest(value)
    return value  # type: ignore[return-value]


def manifest_sha256(value_or_bytes: Mapping[str, object] | bytes) -> bytes:
    if isinstance(value_or_bytes, bytes):
        decode_epoch_manifest(value_or_bytes)
        data = value_or_bytes
    else:
        data = encode_epoch_manifest(value_or_bytes)

    return hashlib.sha256(data).digest()
