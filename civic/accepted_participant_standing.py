from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from civic.epoch_manifest import (
    CivicManifestError,
    derive_key_id,
    validate_epoch_manifest,
)
from civic.object_store import CivicObjectStoreError, verify_object_bytes
from civic.signed_history_record import VerifiedHistoryRecord


RECORD_TYPE = "kane-civic-accepted-participant-standing-v1"
SHA256_BYTES = 32
P256_PUBLIC_KEY_BYTES = 65

BODY_FIELDS = {
    "participant_record_sha256",
    "governing_profile",
    "standing_class",
    "valid_from_ms",
    "valid_until_ms",
    "participation",
    "qualification",
    "recording_operator_participant_record_sha256",
}

GOVERNING_PROFILE_FIELDS = {
    "profile_id",
    "profile_sha256",
    "source_set_sha256",
}

PARTICIPATION_FIELDS = {
    "required",
    "policy_id",
    "valid_from_ms",
    "valid_until_ms",
    "authority_evidence",
    "supplementary_evidence",
}

QUALIFICATION_FIELDS = {
    "path_id",
    "claim_responsibility",
    "authority_evidence",
    "supplementary_evidence",
}

EVIDENCE_FIELDS = {
    "sha256",
    "byte_length",
    "media_type",
    "semantic_role",
}

CLAIM_RESPONSIBILITY = frozenset(
    {
        "participant_claimed",
        "operator_attested",
        "other_published_attestation",
    }
)

PERMITTED_SIGNER_KINDS = frozenset({"participant", "signing_node"})


class CivicParticipantStandingError(ValueError):
    """Raised when a participant-standing record violates its v1 contract."""


@dataclass(frozen=True)
class StandingEvidence:
    sha256: bytes
    byte_length: int
    media_type: str
    semantic_role: str


@dataclass(frozen=True)
class StandingGoverningSource:
    source_id: str
    role: str
    sha256: bytes
    byte_length: int
    media_type: str
    exact_bytes: bytes


@dataclass(frozen=True)
class StandingProfileContext:
    profile_id: str
    profile_sha256: bytes
    source_set_sha256: bytes
    profile_bytes: bytes
    governing_sources: tuple[StandingGoverningSource, ...]


@dataclass(frozen=True)
class StandingProfileRequest:
    participant_record_sha256: bytes
    standing_class: str
    valid_from_ms: int
    valid_until_ms: int | None
    participation_required: bool
    participation_policy_id: str | None
    participation_valid_from_ms: int | None
    participation_valid_until_ms: int | None
    participation_authority_evidence: tuple[StandingEvidence, ...]
    participation_supplementary_evidence: tuple[StandingEvidence, ...]
    qualification_path_id: str
    claim_responsibility: str
    qualification_authority_evidence: tuple[StandingEvidence, ...]
    qualification_supplementary_evidence: tuple[StandingEvidence, ...]


ProfileSemanticsValidator = Callable[
    [StandingProfileContext, StandingProfileRequest],
    None,
]
ObjectLoader = Callable[[bytes], bytes]


@dataclass(frozen=True)
class VerifiedParticipantStanding:
    """Type-specific result after generic signed-history verification.

    The caller supplies the exact retained profile/source objects and a
    profile-specific semantic validator because the generic Civic layer does
    not invent source-derived standing rules.
    """

    record_sha256: bytes
    participant_record_sha256: bytes
    profile_id: str
    profile_sha256: bytes
    source_set_sha256: bytes
    standing_class: str
    valid_from_ms: int
    valid_until_ms: int | None
    evaluation_time_ms: int
    participation_required: bool
    participation_policy_id: str | None
    participation_valid_from_ms: int | None
    participation_valid_until_ms: int | None
    participation_authority_evidence: tuple[StandingEvidence, ...]
    participation_supplementary_evidence: tuple[StandingEvidence, ...]
    qualification_path_id: str
    claim_responsibility: str
    qualification_authority_evidence: tuple[StandingEvidence, ...]
    qualification_supplementary_evidence: tuple[StandingEvidence, ...]
    recording_operator_participant_record_sha256: bytes
    signer_kind: str
    signer_key_id: bytes


def _map(
    value: object,
    label: str,
    required_fields: set[str] | None = None,
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise CivicParticipantStandingError(f"{label} must be a map")
    if any(not isinstance(key, str) for key in value):
        raise CivicParticipantStandingError(f"{label} map keys must be text")
    if required_fields is not None and set(value) != required_fields:
        raise CivicParticipantStandingError(f"{label} fields are invalid")
    return value


def _sha256(value: object, label: str) -> bytes:
    if not isinstance(value, bytes) or len(value) != SHA256_BYTES:
        raise CivicParticipantStandingError(
            f"{label} must be exactly 32 bytes"
        )
    return value


def _text(
    value: object,
    label: str,
    *,
    optional: bool = False,
) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value:
        raise CivicParticipantStandingError(f"{label} must be nonempty text")
    return value


def _uint64(
    value: object,
    label: str,
    *,
    optional: bool = False,
) -> int | None:
    if value is None and optional:
        return None
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
        or value > 0xFFFFFFFFFFFFFFFF
    ):
        raise CivicParticipantStandingError(f"{label} must be a uint64")
    return value


def _public_key(value: object, label: str) -> bytes:
    if (
        not isinstance(value, bytes)
        or len(value) != P256_PUBLIC_KEY_BYTES
        or value[0] != 0x04
    ):
        raise CivicParticipantStandingError(
            f"{label} must be 65-byte uncompressed SEC1 P-256 form"
        )

    try:
        derive_key_id(value)
    except CivicManifestError as exc:
        raise CivicParticipantStandingError(str(exc)) from exc

    return value


def _evidence_list(
    value: object,
    label: str,
) -> tuple[StandingEvidence, ...]:
    if not isinstance(value, list):
        raise CivicParticipantStandingError(f"{label} must be an array")

    result: list[StandingEvidence] = []
    digests: list[bytes] = []

    for index, raw in enumerate(value):
        item = _map(
            raw,
            f"{label}[{index}]",
            EVIDENCE_FIELDS,
        )
        digest = _sha256(
            item["sha256"],
            f"{label}[{index}].sha256",
        )
        byte_length = _uint64(
            item["byte_length"],
            f"{label}[{index}].byte_length",
        )
        media_type = _text(
            item["media_type"],
            f"{label}[{index}].media_type",
        )
        semantic_role = _text(
            item["semantic_role"],
            f"{label}[{index}].semantic_role",
        )
        assert isinstance(byte_length, int)
        assert isinstance(media_type, str)
        assert isinstance(semantic_role, str)

        result.append(
            StandingEvidence(
                sha256=digest,
                byte_length=byte_length,
                media_type=media_type,
                semantic_role=semantic_role,
            )
        )
        digests.append(digest)

    if digests != sorted(digests):
        raise CivicParticipantStandingError(
            f"{label} must be sorted bytewise ascending by sha256"
        )
    if len(digests) != len(set(digests)):
        raise CivicParticipantStandingError(
            f"{label} must not contain duplicate sha256 values"
        )

    return tuple(result)


def _object_index_by_sha256(
    epoch_manifest: Mapping[str, object],
) -> dict[bytes, Mapping[str, object]]:
    raw_index = epoch_manifest["object_index"]
    if not isinstance(raw_index, list):
        raise CivicParticipantStandingError(
            "Epoch Manifest object_index must be an array"
        )

    result: dict[bytes, Mapping[str, object]] = {}
    for index, raw in enumerate(raw_index):
        item = _map(raw, f"Epoch Manifest object_index[{index}]")
        digest = _sha256(
            item.get("sha256"),
            f"Epoch Manifest object_index[{index}].sha256",
        )
        result[digest] = item
    return result


def _load_exact_object(
    *,
    descriptor: Mapping[str, object],
    load_object: ObjectLoader,
    label: str,
) -> bytes:
    digest = _sha256(descriptor.get("sha256"), f"{label}.sha256")
    byte_length = _uint64(
        descriptor.get("byte_length"),
        f"{label}.byte_length",
    )
    assert isinstance(byte_length, int)

    inline = descriptor.get("inline")
    if inline is not None:
        if not isinstance(inline, bytes):
            raise CivicParticipantStandingError(
                f"{label}.inline must be bytes or null"
            )
        data = inline
    else:
        try:
            data = load_object(digest)
        except Exception as exc:
            raise CivicParticipantStandingError(
                f"{label} is unavailable"
            ) from exc

    try:
        verify_object_bytes(
            data,
            expected_sha256=digest,
            expected_byte_length=byte_length,
        )
    except CivicObjectStoreError as exc:
        raise CivicParticipantStandingError(
            f"{label} failed exact-byte verification"
        ) from exc

    return data


def _require_authority_evidence(
    evidence: tuple[StandingEvidence, ...],
    *,
    object_index: Mapping[bytes, Mapping[str, object]],
    load_object: ObjectLoader,
    label: str,
) -> None:
    for index, item in enumerate(evidence):
        descriptor = object_index.get(item.sha256)
        if descriptor is None:
            raise CivicParticipantStandingError(
                f"{label}[{index}] is not authority-required in Epoch Manifest object_index"
            )

        descriptor_length = _uint64(
            descriptor.get("byte_length"),
            f"{label}[{index}] object_index.byte_length",
        )
        descriptor_media_type = _text(
            descriptor.get("media_type"),
            f"{label}[{index}] object_index.media_type",
        )
        descriptor_semantic_role = _text(
            descriptor.get("semantic_role"),
            f"{label}[{index}] object_index.semantic_role",
        )

        if descriptor_length != item.byte_length:
            raise CivicParticipantStandingError(
                f"{label}[{index}] byte length does not match Epoch Manifest object_index"
            )
        if descriptor_media_type != item.media_type:
            raise CivicParticipantStandingError(
                f"{label}[{index}] media type does not match Epoch Manifest object_index"
            )
        if descriptor_semantic_role != item.semantic_role:
            raise CivicParticipantStandingError(
                f"{label}[{index}] semantic role does not match Epoch Manifest object_index"
            )

        _load_exact_object(
            descriptor=descriptor,
            load_object=load_object,
            label=f"{label}[{index}]",
        )


def _load_profile_context(
    body_profile: Mapping[str, object],
    *,
    epoch_manifest: Mapping[str, object],
    object_index: Mapping[bytes, Mapping[str, object]],
    load_object: ObjectLoader,
) -> StandingProfileContext:
    manifest_profile = _map(
        epoch_manifest["governing_profile"],
        "Epoch Manifest governing_profile",
        GOVERNING_PROFILE_FIELDS,
    )

    profile_id = _text(
        body_profile["profile_id"],
        "governing_profile.profile_id",
    )
    profile_sha256 = _sha256(
        body_profile["profile_sha256"],
        "governing_profile.profile_sha256",
    )
    source_set_sha256 = _sha256(
        body_profile["source_set_sha256"],
        "governing_profile.source_set_sha256",
    )
    assert isinstance(profile_id, str)

    if body_profile != manifest_profile:
        raise CivicParticipantStandingError(
            "standing governing profile does not match Epoch Manifest"
        )

    profile_descriptor = object_index.get(profile_sha256)
    if profile_descriptor is None:
        raise CivicParticipantStandingError(
            "governing profile exact bytes are not authority-required in Epoch Manifest object_index"
        )

    profile_bytes = _load_exact_object(
        descriptor=profile_descriptor,
        load_object=load_object,
        label="governing profile object",
    )

    raw_sources = epoch_manifest["governing_sources"]
    if not isinstance(raw_sources, list):
        raise CivicParticipantStandingError(
            "Epoch Manifest governing_sources must be an array"
        )

    governing_sources: list[StandingGoverningSource] = []
    for index, raw in enumerate(raw_sources):
        item = _map(raw, f"Epoch Manifest governing_sources[{index}]")
        source_id = _text(
            item.get("source_id"),
            f"Epoch Manifest governing_sources[{index}].source_id",
        )
        role = _text(
            item.get("role"),
            f"Epoch Manifest governing_sources[{index}].role",
        )
        digest = _sha256(
            item.get("sha256"),
            f"Epoch Manifest governing_sources[{index}].sha256",
        )
        byte_length = _uint64(
            item.get("byte_length"),
            f"Epoch Manifest governing_sources[{index}].byte_length",
        )
        media_type = _text(
            item.get("media_type"),
            f"Epoch Manifest governing_sources[{index}].media_type",
        )
        assert isinstance(source_id, str)
        assert isinstance(role, str)
        assert isinstance(byte_length, int)
        assert isinstance(media_type, str)

        indexed = object_index.get(digest)
        if indexed is not None:
            data = _load_exact_object(
                descriptor=indexed,
                load_object=load_object,
                label=f"governing source {source_id}",
            )
            indexed_length = _uint64(
                indexed.get("byte_length"),
                f"governing source {source_id} object_index.byte_length",
            )
            indexed_media_type = _text(
                indexed.get("media_type"),
                f"governing source {source_id} object_index.media_type",
            )
            if indexed_length != byte_length:
                raise CivicParticipantStandingError(
                    f"governing source {source_id} byte length conflicts with object_index"
                )
            if indexed_media_type != media_type:
                raise CivicParticipantStandingError(
                    f"governing source {source_id} media type conflicts with object_index"
                )
        else:
            try:
                data = load_object(digest)
            except Exception as exc:
                raise CivicParticipantStandingError(
                    f"governing source {source_id} is unavailable"
                ) from exc
            try:
                verify_object_bytes(
                    data,
                    expected_sha256=digest,
                    expected_byte_length=byte_length,
                )
            except CivicObjectStoreError as exc:
                raise CivicParticipantStandingError(
                    f"governing source {source_id} failed exact-byte verification"
                ) from exc

        governing_sources.append(
            StandingGoverningSource(
                source_id=source_id,
                role=role,
                sha256=digest,
                byte_length=byte_length,
                media_type=media_type,
                exact_bytes=data,
            )
        )

    return StandingProfileContext(
        profile_id=profile_id,
        profile_sha256=profile_sha256,
        source_set_sha256=source_set_sha256,
        profile_bytes=profile_bytes,
        governing_sources=tuple(governing_sources),
    )


def verify_accepted_participant_standing(
    record: VerifiedHistoryRecord,
    *,
    epoch_manifest: Mapping[str, object],
    evaluation_time_ms: int,
    load_object: ObjectLoader,
    validate_profile_semantics: ProfileSemanticsValidator,
) -> VerifiedParticipantStanding:
    """Verify the type-specific participant-standing invariants.

    The caller must first perform generic signed-history verification and must
    separately establish accepted-history chain inclusion.

    Exact governing-profile/source bytes and every authority-required standing
    evidence object are loaded by SHA-256. Profile-specific interpretation is
    delegated to an explicit validator because Civic must not invent
    source-derived qualification, participation, or standing-class semantics.
    """

    try:
        validate_epoch_manifest(epoch_manifest)
    except CivicManifestError as exc:
        raise CivicParticipantStandingError(
            "referenced Epoch Manifest is invalid"
        ) from exc

    evaluation_time = _uint64(
        evaluation_time_ms,
        "evaluation_time_ms",
    )
    assert isinstance(evaluation_time, int)

    payload = _map(record.payload, "history record payload")

    if payload.get("record_type") != RECORD_TYPE:
        raise CivicParticipantStandingError(
            "record_type is not the participant-standing v1 type"
        )

    if record.history_link.stream != "accepted":
        raise CivicParticipantStandingError(
            "participant-standing record must be in accepted history"
        )

    if payload.get("hoa_root_id") != epoch_manifest["hoa_root_id"]:
        raise CivicParticipantStandingError(
            "participant-standing HOA root does not match Epoch Manifest"
        )
    if payload.get("epoch_sequence") != epoch_manifest["epoch_sequence"]:
        raise CivicParticipantStandingError(
            "participant-standing epoch does not match Epoch Manifest"
        )

    ceremony = _map(epoch_manifest["ceremony"], "Epoch Manifest ceremony")
    if payload.get("ceremony_record_sha256") != ceremony["ceremony_record_sha256"]:
        raise CivicParticipantStandingError(
            "participant-standing ceremony context does not match Epoch Manifest"
        )

    signer = _map(payload.get("signer"), "signer")
    signer_kind = signer.get("kind")
    if not isinstance(signer_kind, str) or signer_kind not in PERMITTED_SIGNER_KINDS:
        raise CivicParticipantStandingError(
            "participant-standing signer kind is not permitted"
        )

    signer_key_id = _sha256(signer.get("key_id"), "signer.key_id")
    if signer_key_id != record.signer_key_id:
        raise CivicParticipantStandingError(
            "payload signer key does not match verified signer key"
        )

    body = _map(payload.get("body"), "body", BODY_FIELDS)

    participant_id = _sha256(
        body["participant_record_sha256"],
        "participant_record_sha256",
    )

    participants = epoch_manifest["participants"]
    if not isinstance(participants, list):
        raise CivicParticipantStandingError(
            "Epoch Manifest participants must be an array"
        )

    participant_matches = [
        item
        for item in participants
        if isinstance(item, Mapping)
        and item.get("participant_record_sha256") == participant_id
    ]
    if len(participant_matches) != 1:
        raise CivicParticipantStandingError(
            "standing subject must resolve to exactly one current participant"
        )

    participant = participant_matches[0]
    manifest_standing_record_sha256 = _sha256(
        participant["standing_record_sha256"],
        "Epoch Manifest participant standing_record_sha256",
    )

    if record.record_sha256 != manifest_standing_record_sha256:
        raise CivicParticipantStandingError(
            "record identity does not match Epoch Manifest participant standing record"
        )

    body_profile = _map(
        body["governing_profile"],
        "governing_profile",
        GOVERNING_PROFILE_FIELDS,
    )

    standing_class = _text(
        body["standing_class"],
        "standing_class",
    )
    valid_from = _uint64(
        body["valid_from_ms"],
        "valid_from_ms",
    )
    valid_until = _uint64(
        body["valid_until_ms"],
        "valid_until_ms",
        optional=True,
    )
    assert isinstance(standing_class, str)
    assert isinstance(valid_from, int)

    if valid_until is not None and valid_until <= valid_from:
        raise CivicParticipantStandingError(
            "valid_until_ms must be greater than valid_from_ms"
        )

    participation = _map(
        body["participation"],
        "participation",
        PARTICIPATION_FIELDS,
    )
    required_value = participation["required"]
    if not isinstance(required_value, bool):
        raise CivicParticipantStandingError(
            "participation.required must be boolean"
        )
    participation_required = required_value

    participation_policy_id = _text(
        participation["policy_id"],
        "participation.policy_id",
        optional=True,
    )
    participation_valid_from = _uint64(
        participation["valid_from_ms"],
        "participation.valid_from_ms",
        optional=True,
    )
    participation_valid_until = _uint64(
        participation["valid_until_ms"],
        "participation.valid_until_ms",
        optional=True,
    )
    participation_authority_evidence = _evidence_list(
        participation["authority_evidence"],
        "participation.authority_evidence",
    )
    participation_supplementary_evidence = _evidence_list(
        participation["supplementary_evidence"],
        "participation.supplementary_evidence",
    )

    if not participation_required:
        if (
            participation_policy_id is not None
            or participation_valid_from is not None
            or participation_valid_until is not None
            or participation_authority_evidence
            or participation_supplementary_evidence
        ):
            raise CivicParticipantStandingError(
                "participation fields must be null/empty when participation.required is false"
            )
    else:
        if participation_policy_id is None or participation_valid_from is None:
            raise CivicParticipantStandingError(
                "required participation must name policy_id and valid_from_ms"
            )
        if (
            participation_valid_until is not None
            and participation_valid_until <= participation_valid_from
        ):
            raise CivicParticipantStandingError(
                "participation.valid_until_ms must be greater than participation.valid_from_ms"
            )
        if valid_from < participation_valid_from:
            raise CivicParticipantStandingError(
                "standing valid_from_ms must not precede required participation"
            )
        if participation_valid_until is not None:
            if valid_until is None or valid_until > participation_valid_until:
                raise CivicParticipantStandingError(
                    "standing validity must not extend beyond required participation"
                )

    qualification = _map(
        body["qualification"],
        "qualification",
        QUALIFICATION_FIELDS,
    )
    qualification_path_id = _text(
        qualification["path_id"],
        "qualification.path_id",
    )
    claim_responsibility = _text(
        qualification["claim_responsibility"],
        "qualification.claim_responsibility",
    )
    assert isinstance(qualification_path_id, str)
    assert isinstance(claim_responsibility, str)

    if claim_responsibility not in CLAIM_RESPONSIBILITY:
        raise CivicParticipantStandingError(
            "qualification.claim_responsibility is not permitted"
        )

    qualification_authority_evidence = _evidence_list(
        qualification["authority_evidence"],
        "qualification.authority_evidence",
    )
    qualification_supplementary_evidence = _evidence_list(
        qualification["supplementary_evidence"],
        "qualification.supplementary_evidence",
    )

    recording_operator_id = _sha256(
        body["recording_operator_participant_record_sha256"],
        "recording_operator_participant_record_sha256",
    )

    operator = _map(epoch_manifest["operator"], "Epoch Manifest operator")
    manifest_operator_id = _sha256(
        operator["participant_record_sha256"],
        "Epoch Manifest operator participant_record_sha256",
    )
    if recording_operator_id != manifest_operator_id:
        raise CivicParticipantStandingError(
            "recording operator does not match Epoch Manifest operator"
        )

    if signer_kind == "participant":
        signer_participant_id = _sha256(
            signer.get("participant_record_sha256"),
            "signer.participant_record_sha256",
        )
        if signer_participant_id != recording_operator_id:
            raise CivicParticipantStandingError(
                "participant signer must be the recording operator"
            )

        operator_matches = [
            item
            for item in participants
            if isinstance(item, Mapping)
            and item.get("participant_record_sha256") == recording_operator_id
        ]
        if len(operator_matches) != 1:
            raise CivicParticipantStandingError(
                "recording operator must resolve to exactly one current participant"
            )

        operator_key_id = _sha256(
            operator_matches[0]["participant_key_id"],
            "Epoch Manifest operator participant_key_id",
        )
        operator_public_key = _public_key(
            operator_matches[0]["participant_public_key"],
            "Epoch Manifest operator participant_public_key",
        )

        if signer_key_id != operator_key_id:
            raise CivicParticipantStandingError(
                "participant signer key does not match recording operator key"
            )
        if record.signer_public_key != operator_public_key:
            raise CivicParticipantStandingError(
                "verified participant signer public key does not match recording operator"
            )

    elif signer_kind == "signing_node":
        if signer.get("participant_record_sha256") is not None:
            raise CivicParticipantStandingError(
                "Signing Node signer must not name a participant"
            )

        signing_node = _map(
            epoch_manifest["signing_node"],
            "Epoch Manifest signing_node",
        )
        signing_node_key_id = _sha256(
            signing_node["key_id"],
            "Epoch Manifest signing_node key_id",
        )
        signing_node_public_key = _public_key(
            signing_node["public_key"],
            "Epoch Manifest signing_node public_key",
        )

        if signer_key_id != signing_node_key_id:
            raise CivicParticipantStandingError(
                "Signing Node signer key does not match Epoch Manifest"
            )
        if record.signer_public_key != signing_node_public_key:
            raise CivicParticipantStandingError(
                "verified Signing Node public key does not match Epoch Manifest"
            )

    if evaluation_time < valid_from:
        raise CivicParticipantStandingError(
            "standing is not yet current at evaluation_time_ms"
        )
    if valid_until is not None and evaluation_time >= valid_until:
        raise CivicParticipantStandingError(
            "standing is expired at evaluation_time_ms"
        )

    if participation_required:
        assert participation_valid_from is not None
        if evaluation_time < participation_valid_from:
            raise CivicParticipantStandingError(
                "required participation is not yet current at evaluation_time_ms"
            )
        if (
            participation_valid_until is not None
            and evaluation_time >= participation_valid_until
        ):
            raise CivicParticipantStandingError(
                "required participation is expired at evaluation_time_ms"
            )

    object_index = _object_index_by_sha256(epoch_manifest)

    profile_context = _load_profile_context(
        body_profile,
        epoch_manifest=epoch_manifest,
        object_index=object_index,
        load_object=load_object,
    )

    _require_authority_evidence(
        participation_authority_evidence,
        object_index=object_index,
        load_object=load_object,
        label="participation.authority_evidence",
    )
    _require_authority_evidence(
        qualification_authority_evidence,
        object_index=object_index,
        load_object=load_object,
        label="qualification.authority_evidence",
    )

    profile_request = StandingProfileRequest(
        participant_record_sha256=participant_id,
        standing_class=standing_class,
        valid_from_ms=valid_from,
        valid_until_ms=valid_until,
        participation_required=participation_required,
        participation_policy_id=participation_policy_id,
        participation_valid_from_ms=participation_valid_from,
        participation_valid_until_ms=participation_valid_until,
        participation_authority_evidence=participation_authority_evidence,
        participation_supplementary_evidence=participation_supplementary_evidence,
        qualification_path_id=qualification_path_id,
        claim_responsibility=claim_responsibility,
        qualification_authority_evidence=qualification_authority_evidence,
        qualification_supplementary_evidence=qualification_supplementary_evidence,
    )

    try:
        validate_profile_semantics(
            profile_context,
            profile_request,
        )
    except CivicParticipantStandingError:
        raise
    except Exception as exc:
        raise CivicParticipantStandingError(
            "standing does not satisfy governing-profile semantics"
        ) from exc

    return VerifiedParticipantStanding(
        record_sha256=record.record_sha256,
        participant_record_sha256=participant_id,
        profile_id=profile_context.profile_id,
        profile_sha256=profile_context.profile_sha256,
        source_set_sha256=profile_context.source_set_sha256,
        standing_class=standing_class,
        valid_from_ms=valid_from,
        valid_until_ms=valid_until,
        evaluation_time_ms=evaluation_time,
        participation_required=participation_required,
        participation_policy_id=participation_policy_id,
        participation_valid_from_ms=participation_valid_from,
        participation_valid_until_ms=participation_valid_until,
        participation_authority_evidence=participation_authority_evidence,
        participation_supplementary_evidence=participation_supplementary_evidence,
        qualification_path_id=qualification_path_id,
        claim_responsibility=claim_responsibility,
        qualification_authority_evidence=qualification_authority_evidence,
        qualification_supplementary_evidence=qualification_supplementary_evidence,
        recording_operator_participant_record_sha256=recording_operator_id,
        signer_kind=signer_kind,
        signer_key_id=signer_key_id,
    )
