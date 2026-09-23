from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import unicodedata

from civic.codec import CivicCodecError, decode_deterministic, encode_deterministic
from civic.epoch_manifest import (
    CRYPTO_PROFILE,
    CivicManifestError,
    derive_key_id,
    manifest_sha256,
    validate_epoch_manifest,
)


FORMAT = "kane-civic-ceremony-record"
VERSION = 1
MEDIA_TYPE = "application/kane-civic-ceremony+cbor"
SEMANTIC_ROLE = "ceremony-record"

SHA256_BYTES = 32
P256_PUBLIC_KEY_BYTES = 65
UINT64_MAX = 0xFFFFFFFFFFFFFFFF

TRANSITION_KINDS = frozenset({"bootstrap", "successor"})

TOP_LEVEL_FIELDS = {
    "format",
    "version",
    "crypto_profile",
    "transition_kind",
    "hoa_root_id",
    "epoch_sequence",
    "predecessor_manifest_sha256",
    "effective_time_ms",
    "governing_profile",
    "participants",
    "operator_participant_record_sha256",
    "signing_node",
    "governance_policy",
    "governance_proof_sha256",
}

GOVERNING_PROFILE_FIELDS = {
    "profile_id",
    "profile_sha256",
    "source_set_sha256",
}

PARTICIPANT_FIELDS = {
    "participant_record_sha256",
    "participant_key_id",
    "participant_public_key",
}

SIGNING_NODE_FIELDS = {
    "key_id",
    "public_key",
}

GOVERNANCE_POLICY_FIELDS = {
    "policy_id",
    "policy_sha256",
}


class CivicCeremonyError(ValueError):
    """Raised when a Civic ceremony record violates its v1 contract."""


@dataclass(frozen=True)
class VerifiedCeremonyRecord:
    """Canonical ceremony bytes verified against one Epoch Manifest."""

    exact_bytes: bytes
    ceremony_record_sha256: bytes
    value: dict[str, object]
    transition_kind: str
    hoa_root_id: bytes
    epoch_sequence: int
    predecessor_manifest_sha256: bytes | None
    effective_time_ms: int
    governance_policy_id: str
    governance_policy_sha256: bytes
    governance_proof_sha256: tuple[bytes, ...]


def _map(
    value: object,
    label: str,
    required_fields: set[str],
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise CivicCeremonyError(f"{label} must be a map")
    if any(not isinstance(key, str) for key in value):
        raise CivicCeremonyError(f"{label} map keys must be text")
    if set(value) != required_fields:
        raise CivicCeremonyError(f"{label} fields are invalid")
    return value


def _text(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or unicodedata.normalize("NFC", value) != value
    ):
        raise CivicCeremonyError(f"{label} must be nonempty NFC text")
    return value


def _uint(value: object, label: str, *, positive: bool = False) -> int:
    minimum = 1 if positive else 0
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < minimum
        or value > UINT64_MAX
    ):
        qualifier = "positive " if positive else ""
        raise CivicCeremonyError(f"{label} must be a {qualifier}uint64")
    return value


def _bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise CivicCeremonyError(f"{label} must be boolean")
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
        raise CivicCeremonyError(f"{label} must be exactly 32 bytes")
    return value


def _public_key(value: object, label: str) -> bytes:
    if (
        not isinstance(value, bytes)
        or len(value) != P256_PUBLIC_KEY_BYTES
        or value[0] != 0x04
    ):
        raise CivicCeremonyError(
            f"{label} must be 65-byte uncompressed SEC1 P-256 form"
        )

    try:
        derive_key_id(value)
    except CivicManifestError as exc:
        raise CivicCeremonyError(str(exc)) from exc

    return value


def _validate_key_pair(
    key_id_value: object,
    public_key_value: object,
    label: str,
) -> tuple[bytes, bytes]:
    key_id = _sha256(key_id_value, f"{label}.key_id")
    assert isinstance(key_id, bytes)

    public_key = _public_key(public_key_value, f"{label}.public_key")

    try:
        derived = derive_key_id(public_key)
    except CivicManifestError as exc:
        raise CivicCeremonyError(str(exc)) from exc

    if derived != key_id:
        raise CivicCeremonyError(
            f"{label}.key_id does not match {label}.public_key"
        )

    return key_id, public_key


def _validate_governing_profile(value: object) -> Mapping[str, object]:
    item = _map(
        value,
        "governing_profile",
        GOVERNING_PROFILE_FIELDS,
    )

    _text(item["profile_id"], "governing_profile.profile_id")
    _sha256(
        item["profile_sha256"],
        "governing_profile.profile_sha256",
    )
    _sha256(
        item["source_set_sha256"],
        "governing_profile.source_set_sha256",
    )

    return item


def _validate_participants(
    value: object,
) -> tuple[tuple[dict[str, object], ...], frozenset[bytes], frozenset[bytes]]:
    if not isinstance(value, list) or not value:
        raise CivicCeremonyError("participants must be a nonempty array")

    normalized: list[dict[str, object]] = []
    participant_ids: list[bytes] = []
    key_ids: list[bytes] = []

    for index, raw in enumerate(value):
        label = f"participants[{index}]"
        item = _map(raw, label, PARTICIPANT_FIELDS)

        participant_id = _sha256(
            item["participant_record_sha256"],
            f"{label}.participant_record_sha256",
        )
        assert isinstance(participant_id, bytes)

        key_id, public_key = _validate_key_pair(
            item["participant_key_id"],
            item["participant_public_key"],
            label,
        )

        participant_ids.append(participant_id)
        key_ids.append(key_id)

        normalized.append(
            {
                "participant_record_sha256": participant_id,
                "participant_key_id": key_id,
                "participant_public_key": public_key,
            }
        )

    if participant_ids != sorted(participant_ids):
        raise CivicCeremonyError(
            "participants must be sorted by participant_record_sha256"
        )
    if len(participant_ids) != len(set(participant_ids)):
        raise CivicCeremonyError(
            "participant_record_sha256 values must be unique"
        )
    if len(key_ids) != len(set(key_ids)):
        raise CivicCeremonyError(
            "participant_key_id values must be unique"
        )

    return (
        tuple(normalized),
        frozenset(participant_ids),
        frozenset(key_ids),
    )


def _validate_signing_node(value: object) -> Mapping[str, object]:
    item = _map(value, "signing_node", SIGNING_NODE_FIELDS)
    _validate_key_pair(
        item["key_id"],
        item["public_key"],
        "signing_node",
    )
    return item


def _validate_governance_policy(value: object) -> Mapping[str, object]:
    item = _map(
        value,
        "governance_policy",
        GOVERNANCE_POLICY_FIELDS,
    )
    _text(item["policy_id"], "governance_policy.policy_id")
    _sha256(
        item["policy_sha256"],
        "governance_policy.policy_sha256",
    )
    return item


def _validate_governance_proofs(value: object) -> tuple[bytes, ...]:
    if not isinstance(value, list) or not value:
        raise CivicCeremonyError(
            "governance_proof_sha256 must be a nonempty array"
        )

    proofs: list[bytes] = []
    for index, raw in enumerate(value):
        proof = _sha256(
            raw,
            f"governance_proof_sha256[{index}]",
        )
        assert isinstance(proof, bytes)
        proofs.append(proof)

    if proofs != sorted(proofs):
        raise CivicCeremonyError(
            "governance_proof_sha256 must be sorted bytewise"
        )
    if len(proofs) != len(set(proofs)):
        raise CivicCeremonyError(
            "governance_proof_sha256 values must be unique"
        )

    return tuple(proofs)


def validate_ceremony_record(value: Mapping[str, object]) -> None:
    """Validate one logical canonical v1 ceremony record."""

    ceremony = _map(value, "ceremony record", TOP_LEVEL_FIELDS)

    if ceremony["format"] != FORMAT or ceremony["version"] != VERSION:
        raise CivicCeremonyError(
            "ceremony record format/version is unsupported"
        )
    if ceremony["crypto_profile"] != CRYPTO_PROFILE:
        raise CivicCeremonyError(
            "ceremony record cryptographic profile is unsupported"
        )

    transition_kind = _text(
        ceremony["transition_kind"],
        "transition_kind",
    )
    if transition_kind not in TRANSITION_KINDS:
        raise CivicCeremonyError("transition_kind is unsupported")

    _sha256(ceremony["hoa_root_id"], "hoa_root_id")

    epoch_sequence = _uint(
        ceremony["epoch_sequence"],
        "epoch_sequence",
        positive=True,
    )
    predecessor = _sha256(
        ceremony["predecessor_manifest_sha256"],
        "predecessor_manifest_sha256",
        optional=True,
    )

    if transition_kind == "bootstrap":
        if epoch_sequence != 1:
            raise CivicCeremonyError(
                "bootstrap ceremony must use epoch_sequence 1"
            )
        if predecessor is not None:
            raise CivicCeremonyError(
                "bootstrap ceremony must not name a predecessor manifest"
            )
    else:
        if epoch_sequence <= 1:
            raise CivicCeremonyError(
                "successor ceremony must use epoch_sequence greater than 1"
            )
        if predecessor is None:
            raise CivicCeremonyError(
                "successor ceremony must name a predecessor manifest"
            )

    _uint(ceremony["effective_time_ms"], "effective_time_ms")
    _validate_governing_profile(ceremony["governing_profile"])

    _, participant_ids, participant_key_ids = _validate_participants(
        ceremony["participants"]
    )

    operator_id = _sha256(
        ceremony["operator_participant_record_sha256"],
        "operator_participant_record_sha256",
    )
    assert isinstance(operator_id, bytes)
    if operator_id not in participant_ids:
        raise CivicCeremonyError(
            "operator_participant_record_sha256 must reference a ceremony participant"
        )

    signing_node = _validate_signing_node(ceremony["signing_node"])
    signing_node_key_id = _sha256(
        signing_node["key_id"],
        "signing_node.key_id",
    )
    assert isinstance(signing_node_key_id, bytes)
    if signing_node_key_id in participant_key_ids:
        raise CivicCeremonyError(
            "signing-node key must not reuse a participant key"
        )

    _validate_governance_policy(ceremony["governance_policy"])
    _validate_governance_proofs(ceremony["governance_proof_sha256"])

    try:
        encode_deterministic(dict(ceremony))
    except CivicCodecError as exc:
        raise CivicCeremonyError(str(exc)) from exc


def encode_ceremony_record(value: Mapping[str, object]) -> bytes:
    """Encode one canonical v1 ceremony record."""

    validate_ceremony_record(value)
    return encode_deterministic(dict(value))


def decode_ceremony_record(data: bytes) -> dict[str, object]:
    """Decode exact deterministic-CBOR ceremony bytes."""

    try:
        value = decode_deterministic(data)
    except CivicCodecError as exc:
        raise CivicCeremonyError(str(exc)) from exc

    if (
        not isinstance(value, dict)
        or any(not isinstance(key, str) for key in value)
    ):
        raise CivicCeremonyError(
            "ceremony record must decode to a text-keyed map"
        )

    validate_ceremony_record(value)
    return value  # type: ignore[return-value]


def ceremony_record_sha256(
    value_or_bytes: Mapping[str, object] | bytes,
) -> bytes:
    """Return SHA-256 identity of exact canonical ceremony payload bytes."""

    if isinstance(value_or_bytes, bytes):
        decode_ceremony_record(value_or_bytes)
        data = value_or_bytes
    else:
        data = encode_ceremony_record(value_or_bytes)

    return hashlib.sha256(data).digest()


def _manifest_participant_projection(
    epoch_manifest: Mapping[str, object],
) -> list[dict[str, object]]:
    participants = epoch_manifest["participants"]
    assert isinstance(participants, list)

    result: list[dict[str, object]] = []
    for raw in participants:
        assert isinstance(raw, Mapping)
        result.append(
            {
                "participant_record_sha256": raw[
                    "participant_record_sha256"
                ],
                "participant_key_id": raw["participant_key_id"],
                "participant_public_key": raw["participant_public_key"],
            }
        )
    return result


def _manifest_signing_node_projection(
    epoch_manifest: Mapping[str, object],
) -> dict[str, object]:
    signing_node = epoch_manifest["signing_node"]
    assert isinstance(signing_node, Mapping)
    return {
        "key_id": signing_node["key_id"],
        "public_key": signing_node["public_key"],
    }


def _verify_object_index_binding(
    ceremony_bytes: bytes,
    ceremony_sha256: bytes,
    epoch_manifest: Mapping[str, object],
) -> None:
    object_index = epoch_manifest["object_index"]
    assert isinstance(object_index, list)

    matches = [
        item
        for item in object_index
        if (
            isinstance(item, Mapping)
            and item.get("sha256") == ceremony_sha256
        )
    ]
    if len(matches) != 1:
        raise CivicCeremonyError(
            "Epoch Manifest must contain exactly one ceremony object descriptor"
        )

    descriptor = matches[0]

    if descriptor.get("byte_length") != len(ceremony_bytes):
        raise CivicCeremonyError(
            "ceremony object descriptor byte_length does not match exact bytes"
        )
    if descriptor.get("media_type") != MEDIA_TYPE:
        raise CivicCeremonyError(
            "ceremony object descriptor media_type is invalid"
        )
    if descriptor.get("semantic_role") != SEMANTIC_ROLE:
        raise CivicCeremonyError(
            "ceremony object descriptor semantic_role is invalid"
        )

    inline = descriptor.get("inline")
    if inline is not None and inline != ceremony_bytes:
        raise CivicCeremonyError(
            "ceremony object descriptor inline bytes do not match exact ceremony bytes"
        )


def _verify_successor_predecessor(
    ceremony: Mapping[str, object],
    epoch_manifest: Mapping[str, object],
    predecessor_manifest: Mapping[str, object],
) -> None:
    try:
        validate_epoch_manifest(predecessor_manifest)
    except CivicManifestError as exc:
        raise CivicCeremonyError(
            "predecessor Epoch Manifest is invalid"
        ) from exc

    if predecessor_manifest["hoa_root_id"] != ceremony["hoa_root_id"]:
        raise CivicCeremonyError(
            "successor ceremony HOA root does not match predecessor"
        )

    predecessor_sequence = predecessor_manifest["epoch_sequence"]
    assert isinstance(predecessor_sequence, int)

    if ceremony["epoch_sequence"] != predecessor_sequence + 1:
        raise CivicCeremonyError(
            "successor ceremony epoch_sequence is not predecessor + 1"
        )

    try:
        predecessor_sha256 = manifest_sha256(predecessor_manifest)
    except CivicManifestError as exc:
        raise CivicCeremonyError(
            "predecessor Epoch Manifest identity cannot be derived"
        ) from exc

    if ceremony["predecessor_manifest_sha256"] != predecessor_sha256:
        raise CivicCeremonyError(
            "successor ceremony predecessor_manifest_sha256 is incorrect"
        )
    if epoch_manifest["predecessor_manifest_sha256"] != predecessor_sha256:
        raise CivicCeremonyError(
            "Epoch Manifest predecessor_manifest_sha256 is incorrect"
        )

    previous_participants = predecessor_manifest["participants"]
    current_participants = ceremony["participants"]
    assert isinstance(previous_participants, list)
    assert isinstance(current_participants, list)

    previous_by_id = {
        item["participant_record_sha256"]: item
        for item in previous_participants
        if isinstance(item, Mapping)
    }

    for current in current_participants:
        assert isinstance(current, Mapping)
        participant_id = current["participant_record_sha256"]
        previous = previous_by_id.get(participant_id)
        if previous is None:
            continue

        if current["participant_key_id"] == previous["participant_key_id"]:
            raise CivicCeremonyError(
                "continuing successor participant must use a new participant_key_id"
            )
        if current["participant_public_key"] == previous["participant_public_key"]:
            raise CivicCeremonyError(
                "continuing successor participant must use a new participant_public_key"
            )


def verify_ceremony_record(
    ceremony_bytes: bytes,
    *,
    epoch_manifest: Mapping[str, object],
    predecessor_manifest: Mapping[str, object] | None = None,
) -> VerifiedCeremonyRecord:
    """Verify exact canonical ceremony bytes against one Epoch Manifest."""

    try:
        validate_epoch_manifest(epoch_manifest)
    except CivicManifestError as exc:
        raise CivicCeremonyError(
            "referenced Epoch Manifest is invalid"
        ) from exc

    if not isinstance(ceremony_bytes, bytes):
        raise CivicCeremonyError("ceremony exact bytes must be bytes")

    ceremony = decode_ceremony_record(ceremony_bytes)
    digest = hashlib.sha256(ceremony_bytes).digest()

    manifest_ceremony = epoch_manifest["ceremony"]
    assert isinstance(manifest_ceremony, Mapping)

    if manifest_ceremony["ceremony_record_sha256"] != digest:
        raise CivicCeremonyError(
            "ceremony SHA-256 does not match Epoch Manifest"
        )

    proof_hashes = _validate_governance_proofs(
        ceremony["governance_proof_sha256"]
    )
    if list(proof_hashes) != manifest_ceremony["governance_proof_sha256"]:
        raise CivicCeremonyError(
            "ceremony governance proofs do not match Epoch Manifest"
        )

    direct_fields = (
        "hoa_root_id",
        "epoch_sequence",
        "predecessor_manifest_sha256",
        "effective_time_ms",
        "governing_profile",
    )
    for field in direct_fields:
        if ceremony[field] != epoch_manifest[field]:
            raise CivicCeremonyError(
                f"ceremony {field} does not match Epoch Manifest"
            )

    if ceremony["participants"] != _manifest_participant_projection(
        epoch_manifest
    ):
        raise CivicCeremonyError(
            "ceremony participant projection does not match Epoch Manifest"
        )

    manifest_operator = epoch_manifest["operator"]
    assert isinstance(manifest_operator, Mapping)
    if (
        ceremony["operator_participant_record_sha256"]
        != manifest_operator["participant_record_sha256"]
    ):
        raise CivicCeremonyError(
            "ceremony operator does not match Epoch Manifest"
        )

    if ceremony["signing_node"] != _manifest_signing_node_projection(
        epoch_manifest
    ):
        raise CivicCeremonyError(
            "ceremony Signing Node projection does not match Epoch Manifest"
        )

    _verify_object_index_binding(
        ceremony_bytes,
        digest,
        epoch_manifest,
    )

    transition_kind = ceremony["transition_kind"]
    assert isinstance(transition_kind, str)

    if transition_kind == "bootstrap":
        if predecessor_manifest is not None:
            raise CivicCeremonyError(
                "bootstrap ceremony must not be verified with a predecessor manifest"
            )
    else:
        if predecessor_manifest is None:
            raise CivicCeremonyError(
                "successor ceremony requires the verified predecessor manifest"
            )
        _verify_successor_predecessor(
            ceremony,
            epoch_manifest,
            predecessor_manifest,
        )

    policy = ceremony["governance_policy"]
    assert isinstance(policy, Mapping)
    policy_id = policy["policy_id"]
    policy_sha256 = policy["policy_sha256"]
    assert isinstance(policy_id, str)
    assert isinstance(policy_sha256, bytes)

    hoa_root_id = ceremony["hoa_root_id"]
    epoch_sequence = ceremony["epoch_sequence"]
    effective_time_ms = ceremony["effective_time_ms"]
    predecessor_sha256 = ceremony["predecessor_manifest_sha256"]

    assert isinstance(hoa_root_id, bytes)
    assert isinstance(epoch_sequence, int)
    assert isinstance(effective_time_ms, int)
    assert predecessor_sha256 is None or isinstance(predecessor_sha256, bytes)

    return VerifiedCeremonyRecord(
        exact_bytes=ceremony_bytes,
        ceremony_record_sha256=digest,
        value=ceremony,
        transition_kind=transition_kind,
        hoa_root_id=hoa_root_id,
        epoch_sequence=epoch_sequence,
        predecessor_manifest_sha256=predecessor_sha256,
        effective_time_ms=effective_time_ms,
        governance_policy_id=policy_id,
        governance_policy_sha256=policy_sha256,
        governance_proof_sha256=proof_hashes,
    )
