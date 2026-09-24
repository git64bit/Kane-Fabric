from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
from typing import Protocol, runtime_checkable

from civic.ecdsa import (
    CivicEcdsaError,
    N,
    SIGNATURE_BYTES,
    public_key_from_private_scalar,
    sign_sig_structure_rfc6979,
    verify_sig_structure,
)
from civic.epoch_manifest import CivicManifestError, derive_key_id


KEY_REF_PATTERN = re.compile(r"^sw1-[0-9a-f]{32}$")
PRIVATE_SCALAR_BYTES = 32
ADMISSION_TEST_BYTES = b"kane-civic-production-key-admission-v1"


class CivicProductionSigningError(ValueError):
    """Raised when production key custody or signing violates the Civic contract."""


class CivicKeyRole(str, Enum):
    PARTICIPANT_EPOCH = "participant_epoch"
    SIGNING_NODE = "signing_node"


class CivicCustodyState(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DESTROYED = "destroyed"


class CivicAuthorityBindingState(str, Enum):
    UNBOUND = "unbound"
    CANDIDATE = "candidate"
    CURRENT = "current"
    RETIRED = "retired"


@dataclass(frozen=True)
class CivicLocalKeyMetadata:
    key_ref: str
    role: CivicKeyRole
    public_key: bytes
    key_id: bytes
    custody_state: CivicCustodyState


@dataclass(frozen=True)
class CivicAuthorityKeyBinding:
    """Public authority context supplied by a verified Civic state layer.

    This object is deliberately not stored by a signer provider.  Constructing
    one does not itself prove that the authority state was accepted; callers
    must derive it from the verified candidate/current/historical Civic context
    appropriate to the operation.
    """

    hoa_root_id: bytes
    epoch_sequence: int
    role: CivicKeyRole
    public_key: bytes
    key_id: bytes
    state: CivicAuthorityBindingState

    def __post_init__(self) -> None:
        if not isinstance(self.hoa_root_id, bytes) or len(self.hoa_root_id) != 32:
            raise CivicProductionSigningError(
                "hoa_root_id must be exactly 32 bytes"
            )
        if (
            not isinstance(self.epoch_sequence, int)
            or isinstance(self.epoch_sequence, bool)
            or self.epoch_sequence < 1
        ):
            raise CivicProductionSigningError(
                "epoch_sequence must be a positive integer"
            )
        if not isinstance(self.role, CivicKeyRole):
            raise CivicProductionSigningError(
                "role must be a CivicKeyRole"
            )
        if not isinstance(self.state, CivicAuthorityBindingState):
            raise CivicProductionSigningError(
                "state must be a CivicAuthorityBindingState"
            )
        if not isinstance(self.public_key, bytes):
            raise CivicProductionSigningError(
                "public_key must be bytes"
            )
        if not isinstance(self.key_id, bytes) or len(self.key_id) != 32:
            raise CivicProductionSigningError(
                "key_id must be exactly 32 bytes"
            )
        try:
            derived = derive_key_id(self.public_key)
        except CivicManifestError as exc:
            raise CivicProductionSigningError(str(exc)) from exc
        if derived != self.key_id:
            raise CivicProductionSigningError(
                "authority binding key_id does not match public_key"
            )


@runtime_checkable
class CivicSignerProvider(Protocol):
    """Platform-neutral local private-key custody/signing provider."""

    def generate_key(self, role: CivicKeyRole) -> str:
        ...

    def metadata(self, key_ref: str) -> CivicLocalKeyMetadata:
        ...

    def public_key(self, key_ref: str) -> bytes:
        ...

    def sign_sig_structure(
        self,
        key_ref: str,
        exact_sig_structure: bytes,
    ) -> bytes:
        ...

    def set_unavailable(self, key_ref: str) -> None:
        ...

    def set_available(self, key_ref: str) -> None:
        ...

    def destroy_key(self, key_ref: str) -> None:
        ...


def generate_hoa_root_id() -> bytes:
    """Generate a new opaque public HOA root identifier from OS CSPRNG."""

    return secrets.token_bytes(32)


def _secure_private_scalar() -> int:
    """Sample one unbiased P-256 scalar from the operating-system CSPRNG."""

    while True:
        candidate = int.from_bytes(
            secrets.token_bytes(PRIVATE_SCALAR_BYTES),
            "big",
        )
        if 1 <= candidate < N:
            return candidate


def _validate_role(role: CivicKeyRole) -> CivicKeyRole:
    if not isinstance(role, CivicKeyRole):
        raise CivicProductionSigningError(
            "role must be a CivicKeyRole"
        )
    return role


def _validate_key_ref(key_ref: str) -> str:
    if not isinstance(key_ref, str) or KEY_REF_PATTERN.fullmatch(key_ref) is None:
        raise CivicProductionSigningError("key_ref is malformed")
    return key_ref


def _validate_sig_structure(value: bytes) -> bytes:
    if not isinstance(value, bytes):
        raise CivicProductionSigningError(
            "exact_sig_structure must be bytes"
        )
    return value


def _self_verify_signature(
    public_key: bytes,
    exact_sig_structure: bytes,
    signature: bytes,
) -> None:
    if not isinstance(signature, bytes) or len(signature) != SIGNATURE_BYTES:
        raise CivicProductionSigningError(
            "provider signature must be exactly 64-byte P1363"
        )

    try:
        valid = verify_sig_structure(
            public_key,
            exact_sig_structure,
            signature,
        )
    except CivicEcdsaError as exc:
        raise CivicProductionSigningError(str(exc)) from exc

    if not valid:
        raise CivicProductionSigningError(
            "provider signature failed mandatory public self-verification"
        )


class FileSoftwareSignerProvider:
    """Owner-controlled filesystem software provider.

    The caller supplies the provider root directory.  No Civic authority state
    is stored here.  Files contain only local private-key custody plus
    non-authoritative metadata.

    Private scalar files are fixed 32-byte big-endian values.  That storage
    representation is provider-local and is not a Civic authority format.
    """

    _METADATA_FIELDS = {
        "format",
        "version",
        "key_ref",
        "role",
        "public_key_hex",
        "key_id_hex",
        "custody_state",
    }

    def __init__(self, root: str | os.PathLike[str]) -> None:
        self._root = Path(root)
        try:
            self._root.mkdir(
                mode=0o700,
                parents=True,
                exist_ok=True,
            )
            if not self._root.is_dir():
                raise CivicProductionSigningError(
                    "software signer provider root is not a directory"
                )
            if os.name == "posix":
                os.chmod(self._root, 0o700)
        except OSError as exc:
            raise CivicProductionSigningError(
                "software signer provider root is unavailable"
            ) from exc

    def _private_path(self, key_ref: str) -> Path:
        return self._root / f"{_validate_key_ref(key_ref)}.key"

    def _metadata_path(self, key_ref: str) -> Path:
        return self._root / f"{_validate_key_ref(key_ref)}.json"

    def _write_new_file(
        self,
        path: Path,
        data: bytes,
        *,
        mode: int = 0o600,
    ) -> None:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        try:
            fd = os.open(path, flags, mode)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
            except BaseException:
                try:
                    os.unlink(path)
                except OSError:
                    pass
                raise
            if os.name == "posix":
                os.chmod(path, mode)
        except OSError as exc:
            raise CivicProductionSigningError(
                "software signer provider could not persist new key material"
            ) from exc

    def _replace_metadata(
        self,
        key_ref: str,
        metadata: dict[str, object],
    ) -> None:
        destination = self._metadata_path(key_ref)
        temporary = self._root / (
            f".{key_ref}.{secrets.token_hex(8)}.tmp"
        )
        data = (
            json.dumps(
                metadata,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")

        try:
            self._write_new_file(temporary, data)
            os.replace(temporary, destination)
            if os.name == "posix":
                os.chmod(destination, 0o600)
        except BaseException:
            try:
                temporary.unlink()
            except OSError:
                pass
            raise

    def _metadata_dict(
        self,
        *,
        key_ref: str,
        role: CivicKeyRole,
        public_key: bytes,
        key_id: bytes,
        custody_state: CivicCustodyState,
    ) -> dict[str, object]:
        return {
            "format": "kane-civic-software-key-metadata",
            "version": 1,
            "key_ref": key_ref,
            "role": role.value,
            "public_key_hex": public_key.hex(),
            "key_id_hex": key_id.hex(),
            "custody_state": custody_state.value,
        }

    def _read_metadata_dict(
        self,
        key_ref: str,
    ) -> dict[str, object]:
        path = self._metadata_path(key_ref)
        try:
            raw = path.read_bytes()
        except FileNotFoundError as exc:
            raise CivicProductionSigningError(
                "unknown key_ref"
            ) from exc
        except OSError as exc:
            raise CivicProductionSigningError(
                "key metadata is unavailable"
            ) from exc

        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CivicProductionSigningError(
                "key metadata is malformed"
            ) from exc

        if not isinstance(value, dict) or set(value) != self._METADATA_FIELDS:
            raise CivicProductionSigningError(
                "key metadata fields are invalid"
            )
        if (
            value.get("format") != "kane-civic-software-key-metadata"
            or value.get("version") != 1
            or value.get("key_ref") != key_ref
        ):
            raise CivicProductionSigningError(
                "key metadata identity is invalid"
            )

        return value

    def metadata(self, key_ref: str) -> CivicLocalKeyMetadata:
        key_ref = _validate_key_ref(key_ref)
        value = self._read_metadata_dict(key_ref)

        try:
            role = CivicKeyRole(value["role"])
            custody_state = CivicCustodyState(value["custody_state"])
            public_key = bytes.fromhex(value["public_key_hex"])
            key_id = bytes.fromhex(value["key_id_hex"])
        except (ValueError, TypeError) as exc:
            raise CivicProductionSigningError(
                "key metadata value is invalid"
            ) from exc

        try:
            derived = derive_key_id(public_key)
        except CivicManifestError as exc:
            raise CivicProductionSigningError(
                "key metadata public key is invalid"
            ) from exc

        if derived != key_id:
            raise CivicProductionSigningError(
                "key metadata key_id does not match public_key"
            )

        return CivicLocalKeyMetadata(
            key_ref=key_ref,
            role=role,
            public_key=public_key,
            key_id=key_id,
            custody_state=custody_state,
        )

    def public_key(self, key_ref: str) -> bytes:
        return self.metadata(key_ref).public_key

    def _read_private_scalar(
        self,
        key_ref: str,
        metadata: CivicLocalKeyMetadata,
    ) -> int:
        if metadata.custody_state != CivicCustodyState.AVAILABLE:
            raise CivicProductionSigningError(
                "private key is not available for signing"
            )

        path = self._private_path(key_ref)

        try:
            if os.name == "posix":
                mode = path.stat().st_mode & 0o777
                if mode & 0o077:
                    raise CivicProductionSigningError(
                        "private key file permissions are too broad"
                    )
            private_bytes = path.read_bytes()
        except FileNotFoundError as exc:
            raise CivicProductionSigningError(
                "private key bytes are unavailable"
            ) from exc
        except OSError as exc:
            raise CivicProductionSigningError(
                "private key bytes are unavailable"
            ) from exc

        if len(private_bytes) != PRIVATE_SCALAR_BYTES:
            raise CivicProductionSigningError(
                "private key storage length is invalid"
            )

        private_scalar = int.from_bytes(private_bytes, "big")
        if not 1 <= private_scalar < N:
            raise CivicProductionSigningError(
                "private key scalar is outside the P-256 range"
            )

        try:
            derived_public_key = public_key_from_private_scalar(
                private_scalar
            )
        except CivicEcdsaError as exc:
            raise CivicProductionSigningError(str(exc)) from exc

        if derived_public_key != metadata.public_key:
            raise CivicProductionSigningError(
                "private key bytes do not match stored public key"
            )

        return private_scalar

    def _admission_self_test(
        self,
        private_scalar: int,
        public_key: bytes,
    ) -> None:
        try:
            signature = sign_sig_structure_rfc6979(
                private_scalar,
                ADMISSION_TEST_BYTES,
            )
        except CivicEcdsaError as exc:
            raise CivicProductionSigningError(
                "generated software key failed admission signing"
            ) from exc

        _self_verify_signature(
            public_key,
            ADMISSION_TEST_BYTES,
            signature,
        )

    def generate_key(self, role: CivicKeyRole) -> str:
        role = _validate_role(role)
        private_scalar = _secure_private_scalar()

        try:
            public_key = public_key_from_private_scalar(
                private_scalar
            )
            key_id = derive_key_id(public_key)
        except (CivicEcdsaError, CivicManifestError) as exc:
            raise CivicProductionSigningError(
                "generated software key is invalid"
            ) from exc

        self._admission_self_test(
            private_scalar,
            public_key,
        )

        while True:
            key_ref = f"sw1-{secrets.token_hex(16)}"
            if (
                not self._private_path(key_ref).exists()
                and not self._metadata_path(key_ref).exists()
            ):
                break

        private_path = self._private_path(key_ref)
        metadata_path = self._metadata_path(key_ref)

        try:
            self._write_new_file(
                private_path,
                private_scalar.to_bytes(
                    PRIVATE_SCALAR_BYTES,
                    "big",
                ),
            )
            self._write_new_file(
                metadata_path,
                (
                    json.dumps(
                        self._metadata_dict(
                            key_ref=key_ref,
                            role=role,
                            public_key=public_key,
                            key_id=key_id,
                            custody_state=CivicCustodyState.AVAILABLE,
                        ),
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    + "\n"
                ).encode("utf-8"),
            )
        except BaseException:
            try:
                private_path.unlink()
            except OSError:
                pass
            try:
                metadata_path.unlink()
            except OSError:
                pass
            raise

        return key_ref

    def sign_sig_structure(
        self,
        key_ref: str,
        exact_sig_structure: bytes,
    ) -> bytes:
        exact_sig_structure = _validate_sig_structure(
            exact_sig_structure
        )
        metadata = self.metadata(key_ref)
        private_scalar = self._read_private_scalar(
            key_ref,
            metadata,
        )

        try:
            signature = sign_sig_structure_rfc6979(
                private_scalar,
                exact_sig_structure,
            )
        except CivicEcdsaError as exc:
            raise CivicProductionSigningError(
                "software provider signing failed"
            ) from exc

        _self_verify_signature(
            metadata.public_key,
            exact_sig_structure,
            signature,
        )
        return signature

    def set_unavailable(self, key_ref: str) -> None:
        metadata = self.metadata(key_ref)
        if metadata.custody_state == CivicCustodyState.DESTROYED:
            raise CivicProductionSigningError(
                "destroyed key cannot be marked unavailable"
            )

        self._replace_metadata(
            key_ref,
            self._metadata_dict(
                key_ref=key_ref,
                role=metadata.role,
                public_key=metadata.public_key,
                key_id=metadata.key_id,
                custody_state=CivicCustodyState.UNAVAILABLE,
            ),
        )

    def set_available(self, key_ref: str) -> None:
        metadata = self.metadata(key_ref)
        if metadata.custody_state == CivicCustodyState.DESTROYED:
            raise CivicProductionSigningError(
                "destroyed key cannot be made available"
            )

        available_metadata = CivicLocalKeyMetadata(
            key_ref=metadata.key_ref,
            role=metadata.role,
            public_key=metadata.public_key,
            key_id=metadata.key_id,
            custody_state=CivicCustodyState.AVAILABLE,
        )
        self._read_private_scalar(
            key_ref,
            available_metadata,
        )

        self._replace_metadata(
            key_ref,
            self._metadata_dict(
                key_ref=key_ref,
                role=metadata.role,
                public_key=metadata.public_key,
                key_id=metadata.key_id,
                custody_state=CivicCustodyState.AVAILABLE,
            ),
        )

    def destroy_key(self, key_ref: str) -> None:
        metadata = self.metadata(key_ref)
        private_path = self._private_path(key_ref)

        try:
            private_path.unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise CivicProductionSigningError(
                "private key destruction failed"
            ) from exc

        self._replace_metadata(
            key_ref,
            self._metadata_dict(
                key_ref=key_ref,
                role=metadata.role,
                public_key=metadata.public_key,
                key_id=metadata.key_id,
                custody_state=CivicCustodyState.DESTROYED,
            ),
        )


def _provider_metadata(
    provider: CivicSignerProvider,
    key_ref: str,
) -> CivicLocalKeyMetadata:
    if not isinstance(provider, CivicSignerProvider):
        raise CivicProductionSigningError(
            "provider does not implement CivicSignerProvider"
        )
    metadata = provider.metadata(key_ref)
    if not isinstance(metadata, CivicLocalKeyMetadata):
        raise CivicProductionSigningError(
            "provider metadata result is invalid"
        )
    return metadata


def _sign_bound_sig_structure(
    provider: CivicSignerProvider,
    *,
    key_ref: str,
    binding: CivicAuthorityKeyBinding,
    required_state: CivicAuthorityBindingState,
    exact_sig_structure: bytes,
) -> bytes:
    if not isinstance(binding, CivicAuthorityKeyBinding):
        raise CivicProductionSigningError(
            "binding must be CivicAuthorityKeyBinding"
        )
    if binding.state != required_state:
        raise CivicProductionSigningError(
            f"authority binding must be {required_state.value}"
        )

    exact_sig_structure = _validate_sig_structure(
        exact_sig_structure
    )
    metadata = _provider_metadata(provider, key_ref)

    if metadata.custody_state != CivicCustodyState.AVAILABLE:
        raise CivicProductionSigningError(
            "bound private key is unavailable"
        )
    if metadata.role != binding.role:
        raise CivicProductionSigningError(
            "provider key role does not match authority binding"
        )
    if metadata.public_key != binding.public_key:
        raise CivicProductionSigningError(
            "provider public key does not match authority binding"
        )
    if metadata.key_id != binding.key_id:
        raise CivicProductionSigningError(
            "provider key_id does not match authority binding"
        )

    signature = provider.sign_sig_structure(
        key_ref,
        exact_sig_structure,
    )

    _self_verify_signature(
        binding.public_key,
        exact_sig_structure,
        signature,
    )
    return signature


def sign_candidate_sig_structure(
    provider: CivicSignerProvider,
    *,
    key_ref: str,
    binding: CivicAuthorityKeyBinding,
    exact_sig_structure: bytes,
) -> bytes:
    """Sign candidate-composition bytes under an explicit candidate binding."""

    return _sign_bound_sig_structure(
        provider,
        key_ref=key_ref,
        binding=binding,
        required_state=CivicAuthorityBindingState.CANDIDATE,
        exact_sig_structure=exact_sig_structure,
    )


def sign_current_sig_structure(
    provider: CivicSignerProvider,
    *,
    key_ref: str,
    binding: CivicAuthorityKeyBinding,
    exact_sig_structure: bytes,
) -> bytes:
    """Sign current-authority bytes under an explicit current binding."""

    return _sign_bound_sig_structure(
        provider,
        key_ref=key_ref,
        binding=binding,
        required_state=CivicAuthorityBindingState.CURRENT,
        exact_sig_structure=exact_sig_structure,
    )


def make_candidate_binding(
    *,
    hoa_root_id: bytes,
    epoch_sequence: int,
    role: CivicKeyRole,
    public_key: bytes,
) -> CivicAuthorityKeyBinding:
    """Create a public candidate binding projection.

    This helper performs structural/key-identity validation only.  It does not
    claim that governance accepted the candidate.
    """

    try:
        key_id = derive_key_id(public_key)
    except CivicManifestError as exc:
        raise CivicProductionSigningError(str(exc)) from exc

    return CivicAuthorityKeyBinding(
        hoa_root_id=hoa_root_id,
        epoch_sequence=epoch_sequence,
        role=role,
        public_key=public_key,
        key_id=key_id,
        state=CivicAuthorityBindingState.CANDIDATE,
    )


def make_current_binding(
    *,
    hoa_root_id: bytes,
    epoch_sequence: int,
    role: CivicKeyRole,
    public_key: bytes,
) -> CivicAuthorityKeyBinding:
    """Create a public current binding projection.

    Callers must invoke this only from already verified accepted Civic authority
    state.  The local provider does not call or persist this helper.
    """

    try:
        key_id = derive_key_id(public_key)
    except CivicManifestError as exc:
        raise CivicProductionSigningError(str(exc)) from exc

    return CivicAuthorityKeyBinding(
        hoa_root_id=hoa_root_id,
        epoch_sequence=epoch_sequence,
        role=role,
        public_key=public_key,
        key_id=key_id,
        state=CivicAuthorityBindingState.CURRENT,
    )


def make_retired_binding(
    *,
    hoa_root_id: bytes,
    epoch_sequence: int,
    role: CivicKeyRole,
    public_key: bytes,
) -> CivicAuthorityKeyBinding:
    """Create a historical retired binding projection."""

    try:
        key_id = derive_key_id(public_key)
    except CivicManifestError as exc:
        raise CivicProductionSigningError(str(exc)) from exc

    return CivicAuthorityKeyBinding(
        hoa_root_id=hoa_root_id,
        epoch_sequence=epoch_sequence,
        role=role,
        public_key=public_key,
        key_id=key_id,
        state=CivicAuthorityBindingState.RETIRED,
    )
