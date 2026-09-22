from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from civic.epoch_manifest import CivicManifestError, validate_epoch_manifest
from civic.signed_history_record import VerifiedHistoryRecord


RECORD_TYPE = "kane-civic-accepted-operator-selection-v1"
SHA256_BYTES = 32

BODY_FIELDS = {
    "selected_participant_record_sha256",
    "selection_proof_sha256",
}

PERMITTED_SIGNER_KINDS = frozenset({"participant", "signing_node"})


class CivicOperatorSelectionError(ValueError):
    """Raised when an operator-selection record violates its v1 contract."""


@dataclass(frozen=True)
class VerifiedOperatorSelection:
    """Type-specific result after generic signed-history verification.

    Selection-proof hashes remain unresolved governance obligations. This type
    verifies their identity and manifest relationship but does not decide
    whether the applicable governing sources make them sufficient.
    """

    record_sha256: bytes
    selected_participant_record_sha256: bytes
    selection_proof_sha256: tuple[bytes, ...]
    signer_kind: str
    signer_key_id: bytes


def _map(
    value: object,
    label: str,
    required_fields: set[str] | None = None,
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise CivicOperatorSelectionError(f"{label} must be a map")
    if any(not isinstance(key, str) for key in value):
        raise CivicOperatorSelectionError(f"{label} map keys must be text")
    if required_fields is not None and set(value) != required_fields:
        raise CivicOperatorSelectionError(f"{label} fields are invalid")
    return value


def _sha256(value: object, label: str) -> bytes:
    if not isinstance(value, bytes) or len(value) != SHA256_BYTES:
        raise CivicOperatorSelectionError(
            f"{label} must be exactly 32 bytes"
        )
    return value


def _selection_proofs(value: object) -> tuple[bytes, ...]:
    if not isinstance(value, list):
        raise CivicOperatorSelectionError(
            "selection_proof_sha256 must be an array"
        )

    proofs = tuple(
        _sha256(item, f"selection_proof_sha256[{index}]")
        for index, item in enumerate(value)
    )

    if tuple(sorted(proofs)) != proofs:
        raise CivicOperatorSelectionError(
            "selection_proof_sha256 must be sorted bytewise ascending"
        )
    if len(set(proofs)) != len(proofs):
        raise CivicOperatorSelectionError(
            "selection_proof_sha256 must not contain duplicates"
        )

    return proofs


def verify_accepted_operator_selection(
    record: VerifiedHistoryRecord,
    *,
    epoch_manifest: Mapping[str, object],
) -> VerifiedOperatorSelection:
    """Verify the type-specific operator-selection invariants.

    The caller must first perform generic signed-history verification and must
    separately establish accepted-history chain inclusion. This function does
    not prescribe an election, appointment, consent, or ceremony mechanism.
    It returns any identified selection-proof hashes for later source-derived
    governance interpretation.
    """

    try:
        validate_epoch_manifest(epoch_manifest)
    except CivicManifestError as exc:
        raise CivicOperatorSelectionError(
            "referenced Epoch Manifest is invalid"
        ) from exc

    payload = _map(record.payload, "history record payload")

    if payload.get("record_type") != RECORD_TYPE:
        raise CivicOperatorSelectionError(
            "record_type is not the operator-selection v1 type"
        )

    if record.history_link.stream != "accepted":
        raise CivicOperatorSelectionError(
            "operator-selection record must be in accepted history"
        )

    if payload.get("hoa_root_id") != epoch_manifest["hoa_root_id"]:
        raise CivicOperatorSelectionError(
            "operator-selection HOA root does not match Epoch Manifest"
        )
    if payload.get("epoch_sequence") != epoch_manifest["epoch_sequence"]:
        raise CivicOperatorSelectionError(
            "operator-selection epoch does not match Epoch Manifest"
        )

    ceremony = _map(epoch_manifest["ceremony"], "Epoch Manifest ceremony")
    if payload.get("ceremony_record_sha256") != ceremony["ceremony_record_sha256"]:
        raise CivicOperatorSelectionError(
            "operator-selection ceremony context does not match Epoch Manifest"
        )

    signer = _map(payload.get("signer"), "signer")
    signer_kind = signer.get("kind")
    if not isinstance(signer_kind, str) or signer_kind not in PERMITTED_SIGNER_KINDS:
        raise CivicOperatorSelectionError(
            "operator-selection signer kind is not permitted"
        )

    signer_key_id = _sha256(signer.get("key_id"), "signer.key_id")
    if signer_key_id != record.signer_key_id:
        raise CivicOperatorSelectionError(
            "payload signer key does not match verified signer key"
        )

    body = _map(payload.get("body"), "body", BODY_FIELDS)
    selected_participant_id = _sha256(
        body["selected_participant_record_sha256"],
        "selected_participant_record_sha256",
    )
    selection_proofs = _selection_proofs(body["selection_proof_sha256"])

    operator = _map(epoch_manifest["operator"], "Epoch Manifest operator")
    manifest_operator_id = _sha256(
        operator["participant_record_sha256"],
        "Epoch Manifest operator participant_record_sha256",
    )
    selection_record_sha256 = _sha256(
        operator["selection_record_sha256"],
        "Epoch Manifest operator selection_record_sha256",
    )

    if selected_participant_id != manifest_operator_id:
        raise CivicOperatorSelectionError(
            "selected participant does not match Epoch Manifest operator"
        )

    participants = epoch_manifest["participants"]
    if not isinstance(participants, list):
        raise CivicOperatorSelectionError(
            "Epoch Manifest participants must be an array"
        )

    participant_matches = [
        item
        for item in participants
        if isinstance(item, Mapping)
        and item.get("participant_record_sha256") == selected_participant_id
    ]
    if len(participant_matches) != 1:
        raise CivicOperatorSelectionError(
            "selected operator must resolve to exactly one current participant"
        )

    if record.record_sha256 != selection_record_sha256:
        raise CivicOperatorSelectionError(
            "record identity does not match Epoch Manifest selection record"
        )

    manifest_proofs_value = ceremony["governance_proof_sha256"]
    if not isinstance(manifest_proofs_value, list):
        raise CivicOperatorSelectionError(
            "Epoch Manifest governance proof set is invalid"
        )

    manifest_proofs = tuple(
        _sha256(item, f"Epoch Manifest governance_proof_sha256[{index}]")
        for index, item in enumerate(manifest_proofs_value)
    )

    if any(proof not in set(manifest_proofs) for proof in selection_proofs):
        raise CivicOperatorSelectionError(
            "selection proof is not present in Epoch Manifest ceremony governance proofs"
        )

    return VerifiedOperatorSelection(
        record_sha256=record.record_sha256,
        selected_participant_record_sha256=selected_participant_id,
        selection_proof_sha256=selection_proofs,
        signer_kind=signer_kind,
        signer_key_id=signer_key_id,
    )
