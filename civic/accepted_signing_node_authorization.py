from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from civic.epoch_manifest import (
    CivicManifestError,
    derive_key_id,
    validate_epoch_manifest,
)
from civic.signed_history_record import VerifiedHistoryRecord


RECORD_TYPE = "kane-civic-accepted-signing-node-authorization-v1"
P256_PUBLIC_KEY_BYTES = 65
SHA256_BYTES = 32

BODY_FIELDS = {
    "authorized_key_id",
    "authorized_public_key",
    "governance_proof_sha256",
}


class CivicSigningNodeAuthorizationError(ValueError):
    """Raised when a Signing Node authorization record violates its v1 contract."""


@dataclass(frozen=True)
class VerifiedSigningNodeAuthorization:
    """Type-specific result after generic signed-history verification.

    Governance-proof hashes are returned as unresolved obligations for the
    source-derived governance layer. This type does not define ceremony
    mechanics or decide the semantic sufficiency of those proofs.
    """

    record_sha256: bytes
    authorized_key_id: bytes
    authorized_public_key: bytes
    governance_proof_sha256: tuple[bytes, ...]


def _map(
    value: object,
    label: str,
    required_fields: set[str] | None = None,
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise CivicSigningNodeAuthorizationError(f"{label} must be a map")
    if any(not isinstance(key, str) for key in value):
        raise CivicSigningNodeAuthorizationError(f"{label} map keys must be text")
    if required_fields is not None and set(value) != required_fields:
        raise CivicSigningNodeAuthorizationError(f"{label} fields are invalid")
    return value


def _sha256(value: object, label: str) -> bytes:
    if not isinstance(value, bytes) or len(value) != SHA256_BYTES:
        raise CivicSigningNodeAuthorizationError(
            f"{label} must be exactly 32 bytes"
        )
    return value


def _public_key(value: object) -> bytes:
    if (
        not isinstance(value, bytes)
        or len(value) != P256_PUBLIC_KEY_BYTES
        or value[0] != 0x04
    ):
        raise CivicSigningNodeAuthorizationError(
            "authorized_public_key must be 65-byte uncompressed SEC1 P-256 form"
        )
    try:
        derive_key_id(value)
    except CivicManifestError as exc:
        raise CivicSigningNodeAuthorizationError(str(exc)) from exc
    return value


def _governance_proofs(value: object) -> tuple[bytes, ...]:
    if not isinstance(value, list) or not value:
        raise CivicSigningNodeAuthorizationError(
            "governance_proof_sha256 must be a non-empty array"
        )

    proofs = tuple(
        _sha256(item, f"governance_proof_sha256[{index}]")
        for index, item in enumerate(value)
    )

    if tuple(sorted(proofs)) != proofs:
        raise CivicSigningNodeAuthorizationError(
            "governance_proof_sha256 must be sorted bytewise ascending"
        )
    if len(set(proofs)) != len(proofs):
        raise CivicSigningNodeAuthorizationError(
            "governance_proof_sha256 must not contain duplicates"
        )

    return proofs


def verify_accepted_signing_node_authorization(
    record: VerifiedHistoryRecord,
    *,
    epoch_manifest: Mapping[str, object],
) -> VerifiedSigningNodeAuthorization:
    """Verify the type-specific Signing Node authorization bindings.

    The caller must first perform generic signed-history verification and must
    separately establish accepted-history chain inclusion. This function does
    not define ceremony mechanics and does not interpret governance proofs.
    It returns the exact proof hashes that remain obligations for the
    source-derived governance layer.
    """

    try:
        validate_epoch_manifest(epoch_manifest)
    except CivicManifestError as exc:
        raise CivicSigningNodeAuthorizationError(
            "referenced Epoch Manifest is invalid"
        ) from exc

    payload = _map(record.payload, "history record payload")
    if payload.get("record_type") != RECORD_TYPE:
        raise CivicSigningNodeAuthorizationError(
            "record_type is not the Signing Node authorization v1 type"
        )

    if record.history_link.stream != "accepted":
        raise CivicSigningNodeAuthorizationError(
            "Signing Node authorization record must be in accepted history"
        )

    if payload.get("hoa_root_id") != epoch_manifest["hoa_root_id"]:
        raise CivicSigningNodeAuthorizationError(
            "Signing Node authorization HOA root does not match Epoch Manifest"
        )
    if payload.get("epoch_sequence") != epoch_manifest["epoch_sequence"]:
        raise CivicSigningNodeAuthorizationError(
            "Signing Node authorization epoch does not match Epoch Manifest"
        )

    ceremony = _map(epoch_manifest["ceremony"], "Epoch Manifest ceremony")
    if payload.get("ceremony_record_sha256") != ceremony["ceremony_record_sha256"]:
        raise CivicSigningNodeAuthorizationError(
            "Signing Node authorization ceremony context does not match Epoch Manifest"
        )

    signer = _map(payload.get("signer"), "signer")
    if signer.get("kind") != "signing_node":
        raise CivicSigningNodeAuthorizationError(
            "Signing Node authorization must be signed by the Signing Node"
        )
    if signer.get("participant_record_sha256") is not None:
        raise CivicSigningNodeAuthorizationError(
            "Signing Node authorization signer must not name a participant"
        )

    body = _map(payload.get("body"), "body", BODY_FIELDS)
    authorized_key_id = _sha256(
        body["authorized_key_id"],
        "authorized_key_id",
    )
    authorized_public_key = _public_key(body["authorized_public_key"])

    try:
        derived_key_id = derive_key_id(authorized_public_key)
    except CivicManifestError as exc:
        raise CivicSigningNodeAuthorizationError(str(exc)) from exc
    if derived_key_id != authorized_key_id:
        raise CivicSigningNodeAuthorizationError(
            "authorized_key_id does not match authorized_public_key"
        )

    signing_node = _map(
        epoch_manifest["signing_node"],
        "Epoch Manifest signing_node",
    )
    manifest_key_id = signing_node["key_id"]
    manifest_public_key = signing_node["public_key"]
    authorization_record_sha256 = signing_node["authorization_record_sha256"]

    if authorized_key_id != manifest_key_id:
        raise CivicSigningNodeAuthorizationError(
            "authorized key ID does not match Epoch Manifest Signing Node"
        )
    if authorized_public_key != manifest_public_key:
        raise CivicSigningNodeAuthorizationError(
            "authorized public key does not match Epoch Manifest Signing Node"
        )
    if signer.get("key_id") != authorized_key_id:
        raise CivicSigningNodeAuthorizationError(
            "record signer key does not match authorized Signing Node key"
        )
    if record.signer_key_id != authorized_key_id:
        raise CivicSigningNodeAuthorizationError(
            "verified signer key does not match authorized Signing Node key"
        )
    if record.signer_public_key != authorized_public_key:
        raise CivicSigningNodeAuthorizationError(
            "verified signer public key does not match authorized Signing Node key"
        )

    if record.record_sha256 != authorization_record_sha256:
        raise CivicSigningNodeAuthorizationError(
            "record identity does not match Epoch Manifest authorization record"
        )

    proofs = _governance_proofs(body["governance_proof_sha256"])
    manifest_proofs_value = ceremony["governance_proof_sha256"]
    if not isinstance(manifest_proofs_value, list):
        raise CivicSigningNodeAuthorizationError(
            "Epoch Manifest governance proof set is invalid"
        )
    manifest_proofs = tuple(manifest_proofs_value)

    if proofs != manifest_proofs:
        raise CivicSigningNodeAuthorizationError(
            "authorization governance proof set does not match Epoch Manifest ceremony"
        )

    return VerifiedSigningNodeAuthorization(
        record_sha256=record.record_sha256,
        authorized_key_id=authorized_key_id,
        authorized_public_key=authorized_public_key,
        governance_proof_sha256=proofs,
    )
