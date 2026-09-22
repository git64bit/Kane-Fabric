from __future__ import annotations

from typing import Mapping

from civic.cose import (
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
    CivicManifestError,
    decode_epoch_manifest,
    derive_key_id,
    encode_epoch_manifest,
)


class CivicSignedManifestError(ValueError):
    """Raised when a signed Civic Epoch Manifest violates the v1 contract."""


def _signing_node_fields(
    manifest: Mapping[str, object],
) -> tuple[bytes, bytes]:
    signing_node = manifest.get("signing_node")
    if not isinstance(signing_node, Mapping):
        raise CivicSignedManifestError("manifest signing_node must be a map")

    public_key = signing_node.get("public_key")
    key_id = signing_node.get("key_id")

    if not isinstance(public_key, bytes):
        raise CivicSignedManifestError("manifest signing_node.public_key must be bytes")
    if not isinstance(key_id, bytes):
        raise CivicSignedManifestError("manifest signing_node.key_id must be bytes")

    try:
        derived = derive_key_id(public_key)
    except CivicManifestError as exc:
        raise CivicSignedManifestError(str(exc)) from exc

    if derived != key_id:
        raise CivicSignedManifestError(
            "manifest signing_node.key_id does not match signing_node.public_key"
        )

    return public_key, key_id


def sign_epoch_manifest_fixture(
    manifest: Mapping[str, object],
    *,
    private_scalar: int,
    nonce_scalar: int,
) -> bytes:
    """Create a complete fixture-only signed Civic Epoch Manifest.

    This helper never generates or persists a private key. The caller supplies
    an explicit non-production scalar and nonce used only to create a
    deterministic repository/test signature.
    """

    try:
        payload = encode_epoch_manifest(manifest)
        declared_public_key, key_id = _signing_node_fields(manifest)
        fixture_public_key = public_key_from_private_scalar(private_scalar)
    except (CivicManifestError, CivicEcdsaError) as exc:
        raise CivicSignedManifestError(str(exc)) from exc

    if fixture_public_key != declared_public_key:
        raise CivicSignedManifestError(
            "fixture private scalar does not match manifest signing-node public key"
        )

    try:
        sig_structure = build_sig_structure(payload, key_id)
        signature = sign_sig_structure_fixture(
            private_scalar=private_scalar,
            nonce_scalar=nonce_scalar,
            sig_structure=sig_structure,
        )
        return build_cose_sign1(payload, key_id, signature)
    except (CivicCoseError, CivicEcdsaError) as exc:
        raise CivicSignedManifestError(str(exc)) from exc


def verify_signed_epoch_manifest(data: bytes) -> dict[str, object]:
    """Verify and return a complete signed Civic Epoch Manifest.

    Verification binds the exact embedded payload to the manifest-declared
    Signing Node public key and requires the COSE kid to equal the manifest
    signing_node.key_id.
    """

    try:
        parsed = parse_cose_sign1(data)
        manifest = decode_epoch_manifest(parsed.payload)
        public_key, manifest_key_id = _signing_node_fields(manifest)
    except (CivicCoseError, CivicManifestError) as exc:
        raise CivicSignedManifestError(str(exc)) from exc

    if parsed.key_id != manifest_key_id:
        raise CivicSignedManifestError(
            "COSE kid does not match manifest signing_node.key_id"
        )

    try:
        sig_structure = build_sig_structure(parsed.payload, parsed.key_id)
        valid = verify_sig_structure(
            public_key,
            sig_structure,
            parsed.signature,
        )
    except (CivicCoseError, CivicEcdsaError) as exc:
        raise CivicSignedManifestError(str(exc)) from exc

    if not valid:
        raise CivicSignedManifestError("Civic Epoch Manifest signature is invalid")

    return manifest
