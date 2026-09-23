from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from civic.epoch_manifest import (
    CivicManifestError,
    derive_key_id,
    validate_epoch_manifest,
)
from civic.signed_history_record import VerifiedHistoryRecord


RECORD_TYPE = "kane-civic-accepted-participant-issuance-v1"
SHA256_BYTES = 32
P256_PUBLIC_KEY_BYTES = 65

BODY_FIELDS = {
    "participant_record_sha256",
    "participant_key_id",
    "participant_public_key",
    "standing_record_sha256",
    "issuing_operator_participant_record_sha256",
}

PERMITTED_SIGNER_KINDS = frozenset({"participant", "signing_node"})


class CivicParticipantIssuanceError(ValueError):
    """Raised when a participant-issuance record violates its v1 contract."""


@dataclass(frozen=True)
class VerifiedParticipantIssuance:
    """Type-specific result after generic signed-history verification.

    Standing remains a separately verifiable obligation. This result preserves
    the exact participant/key/standing/operator bindings needed by that later
    source-derived standing verification.
    """

    record_sha256: bytes
    participant_record_sha256: bytes
    participant_key_id: bytes
    participant_public_key: bytes
    standing_record_sha256: bytes
    issuing_operator_participant_record_sha256: bytes
    signer_kind: str
    signer_key_id: bytes


def _map(
    value: object,
    label: str,
    required_fields: set[str] | None = None,
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise CivicParticipantIssuanceError(f"{label} must be a map")
    if any(not isinstance(key, str) for key in value):
        raise CivicParticipantIssuanceError(f"{label} map keys must be text")
    if required_fields is not None and set(value) != required_fields:
        raise CivicParticipantIssuanceError(f"{label} fields are invalid")
    return value


def _sha256(value: object, label: str) -> bytes:
    if not isinstance(value, bytes) or len(value) != SHA256_BYTES:
        raise CivicParticipantIssuanceError(
            f"{label} must be exactly 32 bytes"
        )
    return value


def _public_key(value: object) -> bytes:
    if (
        not isinstance(value, bytes)
        or len(value) != P256_PUBLIC_KEY_BYTES
        or value[0] != 0x04
    ):
        raise CivicParticipantIssuanceError(
            "participant_public_key must be 65-byte uncompressed SEC1 P-256 form"
        )

    try:
        derive_key_id(value)
    except CivicManifestError as exc:
        raise CivicParticipantIssuanceError(str(exc)) from exc

    return value


def verify_accepted_participant_issuance(
    record: VerifiedHistoryRecord,
    *,
    epoch_manifest: Mapping[str, object],
) -> VerifiedParticipantIssuance:
    """Verify the type-specific participant-issuance invariants.

    The caller must first perform generic signed-history verification and must
    separately establish accepted-history chain inclusion.

    This function verifies issuance identity, participant key binding, standing
    reference, and issuing-operator provenance. It does not interpret the
    standing record or prescribe the physical/administrative issuance process.
    """

    try:
        validate_epoch_manifest(epoch_manifest)
    except CivicManifestError as exc:
        raise CivicParticipantIssuanceError(
            "referenced Epoch Manifest is invalid"
        ) from exc

    payload = _map(record.payload, "history record payload")

    if payload.get("record_type") != RECORD_TYPE:
        raise CivicParticipantIssuanceError(
            "record_type is not the participant-issuance v1 type"
        )

    if record.history_link.stream != "accepted":
        raise CivicParticipantIssuanceError(
            "participant-issuance record must be in accepted history"
        )

    if payload.get("hoa_root_id") != epoch_manifest["hoa_root_id"]:
        raise CivicParticipantIssuanceError(
            "participant-issuance HOA root does not match Epoch Manifest"
        )
    if payload.get("epoch_sequence") != epoch_manifest["epoch_sequence"]:
        raise CivicParticipantIssuanceError(
            "participant-issuance epoch does not match Epoch Manifest"
        )

    ceremony = _map(epoch_manifest["ceremony"], "Epoch Manifest ceremony")
    if payload.get("ceremony_record_sha256") != ceremony["ceremony_record_sha256"]:
        raise CivicParticipantIssuanceError(
            "participant-issuance ceremony context does not match Epoch Manifest"
        )

    signer = _map(payload.get("signer"), "signer")
    signer_kind = signer.get("kind")
    if not isinstance(signer_kind, str) or signer_kind not in PERMITTED_SIGNER_KINDS:
        raise CivicParticipantIssuanceError(
            "participant-issuance signer kind is not permitted"
        )

    signer_key_id = _sha256(signer.get("key_id"), "signer.key_id")
    if signer_key_id != record.signer_key_id:
        raise CivicParticipantIssuanceError(
            "payload signer key does not match verified signer key"
        )

    body = _map(payload.get("body"), "body", BODY_FIELDS)

    participant_record_sha256 = _sha256(
        body["participant_record_sha256"],
        "participant_record_sha256",
    )
    participant_key_id = _sha256(
        body["participant_key_id"],
        "participant_key_id",
    )
    participant_public_key = _public_key(body["participant_public_key"])
    standing_record_sha256 = _sha256(
        body["standing_record_sha256"],
        "standing_record_sha256",
    )
    issuing_operator_id = _sha256(
        body["issuing_operator_participant_record_sha256"],
        "issuing_operator_participant_record_sha256",
    )

    try:
        derived_participant_key_id = derive_key_id(participant_public_key)
    except CivicManifestError as exc:
        raise CivicParticipantIssuanceError(str(exc)) from exc

    if derived_participant_key_id != participant_key_id:
        raise CivicParticipantIssuanceError(
            "participant_key_id does not match participant_public_key"
        )

    participants = epoch_manifest["participants"]
    if not isinstance(participants, list):
        raise CivicParticipantIssuanceError(
            "Epoch Manifest participants must be an array"
        )

    participant_matches = [
        item
        for item in participants
        if isinstance(item, Mapping)
        and item.get("participant_record_sha256") == participant_record_sha256
    ]
    if len(participant_matches) != 1:
        raise CivicParticipantIssuanceError(
            "issued participant must resolve to exactly one current participant"
        )

    participant = participant_matches[0]

    manifest_participant_key_id = _sha256(
        participant["participant_key_id"],
        "Epoch Manifest participant participant_key_id",
    )
    manifest_participant_public_key = _public_key(
        participant["participant_public_key"]
    )
    manifest_standing_record_sha256 = _sha256(
        participant["standing_record_sha256"],
        "Epoch Manifest participant standing_record_sha256",
    )
    manifest_issuance_record_sha256 = _sha256(
        participant["issuance_record_sha256"],
        "Epoch Manifest participant issuance_record_sha256",
    )

    if participant_key_id != manifest_participant_key_id:
        raise CivicParticipantIssuanceError(
            "participant key ID does not match Epoch Manifest participant"
        )
    if participant_public_key != manifest_participant_public_key:
        raise CivicParticipantIssuanceError(
            "participant public key does not match Epoch Manifest participant"
        )
    if standing_record_sha256 != manifest_standing_record_sha256:
        raise CivicParticipantIssuanceError(
            "standing record does not match Epoch Manifest participant"
        )

    operator = _map(epoch_manifest["operator"], "Epoch Manifest operator")
    manifest_operator_id = _sha256(
        operator["participant_record_sha256"],
        "Epoch Manifest operator participant_record_sha256",
    )

    if issuing_operator_id != manifest_operator_id:
        raise CivicParticipantIssuanceError(
            "issuing operator does not match Epoch Manifest operator"
        )

    if signer_kind == "participant":
        signer_participant_id = _sha256(
            signer.get("participant_record_sha256"),
            "signer.participant_record_sha256",
        )
        if signer_participant_id != issuing_operator_id:
            raise CivicParticipantIssuanceError(
                "participant signer must be the issuing operator"
            )

        operator_matches = [
            item
            for item in participants
            if isinstance(item, Mapping)
            and item.get("participant_record_sha256") == issuing_operator_id
        ]
        if len(operator_matches) != 1:
            raise CivicParticipantIssuanceError(
                "issuing operator must resolve to exactly one current participant"
            )

        operator_key_id = _sha256(
            operator_matches[0]["participant_key_id"],
            "Epoch Manifest operator participant_key_id",
        )
        operator_public_key = _public_key(
            operator_matches[0]["participant_public_key"]
        )

        if signer_key_id != operator_key_id:
            raise CivicParticipantIssuanceError(
                "participant signer key does not match issuing operator key"
            )
        if record.signer_public_key != operator_public_key:
            raise CivicParticipantIssuanceError(
                "verified participant signer public key does not match issuing operator"
            )

    elif signer_kind == "signing_node":
        if signer.get("participant_record_sha256") is not None:
            raise CivicParticipantIssuanceError(
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
            signing_node["public_key"]
        )

        if signer_key_id != signing_node_key_id:
            raise CivicParticipantIssuanceError(
                "Signing Node signer key does not match Epoch Manifest"
            )
        if record.signer_public_key != signing_node_public_key:
            raise CivicParticipantIssuanceError(
                "verified Signing Node public key does not match Epoch Manifest"
            )

    if record.record_sha256 != manifest_issuance_record_sha256:
        raise CivicParticipantIssuanceError(
            "record identity does not match Epoch Manifest participant issuance record"
        )

    return VerifiedParticipantIssuance(
        record_sha256=record.record_sha256,
        participant_record_sha256=participant_record_sha256,
        participant_key_id=participant_key_id,
        participant_public_key=participant_public_key,
        standing_record_sha256=standing_record_sha256,
        issuing_operator_participant_record_sha256=issuing_operator_id,
        signer_kind=signer_kind,
        signer_key_id=signer_key_id,
    )
