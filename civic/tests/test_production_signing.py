from __future__ import annotations

import inspect
import json
import os
from pathlib import Path
import tempfile
import unittest

import civic.production_signing as production_signing
from civic.ecdsa import (
    N,
    public_key_from_private_scalar,
    sign_sig_structure_rfc6979,
    verify_sig_structure,
)
from civic.epoch_manifest import derive_key_id
from civic.production_signing import (
    CivicAuthorityBindingState,
    CivicAuthorityKeyBinding,
    CivicCustodyState,
    CivicKeyRole,
    CivicLocalKeyMetadata,
    CivicProductionSigningError,
    FileSoftwareSignerProvider,
    generate_hoa_root_id,
    make_candidate_binding,
    make_current_binding,
    make_retired_binding,
    sign_candidate_sig_structure,
    sign_current_sig_structure,
)


ROOT_ID = bytes.fromhex(
    "00112233445566778899aabbccddeeff"
    "102132435465768798a9bacbdcedfe0f"
)


class InvalidSignatureProvider(FileSoftwareSignerProvider):
    def sign_sig_structure(
        self,
        key_ref: str,
        exact_sig_structure: bytes,
    ) -> bytes:
        self.metadata(key_ref)
        return b"\x00" * 64


class CivicProductionSigningTests(unittest.TestCase):
    def test_rfc6979_p256_sha256_known_vector(self) -> None:
        private_scalar = int(
            "C9AFA9D845BA75166B5C215767B1D693"
            "4E50C3DB36E89B127B8A622B120F6721",
            16,
        )
        expected_signature = bytes.fromhex(
            "EFD48B2AACB6A8FD1140DD9CD45E81D6"
            "9D2C877B56AAF991C34D0EA84EAF3716"
            "F7CB1C942D657C41D436C7A1B6E29F6"
            "5F3E900DBB9AFF4064DC4AB2F843ACDA8"
        )

        signature = sign_sig_structure_rfc6979(
            private_scalar,
            b"sample",
        )

        self.assertEqual(expected_signature, signature)
        self.assertTrue(
            verify_sig_structure(
                public_key_from_private_scalar(private_scalar),
                b"sample",
                signature,
            )
        )

    def test_generated_root_and_software_key_have_canonical_public_identity(self) -> None:
        root_id = generate_hoa_root_id()
        self.assertIsInstance(root_id, bytes)
        self.assertEqual(32, len(root_id))

        with tempfile.TemporaryDirectory() as directory:
            provider = FileSoftwareSignerProvider(directory)
            key_ref = provider.generate_key(CivicKeyRole.SIGNING_NODE)
            metadata = provider.metadata(key_ref)

            self.assertRegex(key_ref, r"^sw1-[0-9a-f]{32}$")
            self.assertEqual(CivicKeyRole.SIGNING_NODE, metadata.role)
            self.assertEqual(
                CivicCustodyState.AVAILABLE,
                metadata.custody_state,
            )
            self.assertEqual(65, len(metadata.public_key))
            self.assertEqual(0x04, metadata.public_key[0])
            self.assertEqual(
                derive_key_id(metadata.public_key),
                metadata.key_id,
            )

            private_bytes = (
                Path(directory) / f"{key_ref}.key"
            ).read_bytes()
            self.assertEqual(32, len(private_bytes))
            private_scalar = int.from_bytes(private_bytes, "big")
            self.assertGreaterEqual(private_scalar, 1)
            self.assertLess(private_scalar, N)
            self.assertEqual(
                metadata.public_key,
                public_key_from_private_scalar(private_scalar),
            )

            if os.name == "posix":
                self.assertEqual(
                    0o700,
                    Path(directory).stat().st_mode & 0o777,
                )
                self.assertEqual(
                    0o600,
                    (
                        Path(directory) / f"{key_ref}.key"
                    ).stat().st_mode
                    & 0o777,
                )
                self.assertEqual(
                    0o600,
                    (
                        Path(directory) / f"{key_ref}.json"
                    ).stat().st_mode
                    & 0o777,
                )

    def test_key_generation_stores_custody_not_authority_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = FileSoftwareSignerProvider(directory)
            key_ref = provider.generate_key(
                CivicKeyRole.PARTICIPANT_EPOCH
            )

            raw_metadata = json.loads(
                (
                    Path(directory) / f"{key_ref}.json"
                ).read_text(encoding="utf-8")
            )

            self.assertEqual(
                {
                    "format",
                    "version",
                    "key_ref",
                    "role",
                    "public_key_hex",
                    "key_id_hex",
                    "custody_state",
                },
                set(raw_metadata),
            )
            self.assertNotIn("authority_state", raw_metadata)
            self.assertNotIn("epoch_sequence", raw_metadata)
            self.assertNotIn("hoa_root_id", raw_metadata)

            metadata = provider.metadata(key_ref)
            candidate = make_candidate_binding(
                hoa_root_id=ROOT_ID,
                epoch_sequence=1,
                role=CivicKeyRole.PARTICIPANT_EPOCH,
                public_key=metadata.public_key,
            )

            with self.assertRaises(CivicProductionSigningError):
                sign_current_sig_structure(
                    provider,
                    key_ref=key_ref,
                    binding=candidate,
                    exact_sig_structure=b"not-current",
                )

    def test_candidate_and_current_bindings_are_explicit_and_state_specific(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = FileSoftwareSignerProvider(directory)
            key_ref = provider.generate_key(CivicKeyRole.SIGNING_NODE)
            public_key = provider.public_key(key_ref)

            candidate = make_candidate_binding(
                hoa_root_id=ROOT_ID,
                epoch_sequence=2,
                role=CivicKeyRole.SIGNING_NODE,
                public_key=public_key,
            )
            current = make_current_binding(
                hoa_root_id=ROOT_ID,
                epoch_sequence=2,
                role=CivicKeyRole.SIGNING_NODE,
                public_key=public_key,
            )
            retired = make_retired_binding(
                hoa_root_id=ROOT_ID,
                epoch_sequence=1,
                role=CivicKeyRole.SIGNING_NODE,
                public_key=public_key,
            )

            candidate_signature = sign_candidate_sig_structure(
                provider,
                key_ref=key_ref,
                binding=candidate,
                exact_sig_structure=b"candidate-operation",
            )
            current_signature = sign_current_sig_structure(
                provider,
                key_ref=key_ref,
                binding=current,
                exact_sig_structure=b"current-operation",
            )

            self.assertTrue(
                verify_sig_structure(
                    public_key,
                    b"candidate-operation",
                    candidate_signature,
                )
            )
            self.assertTrue(
                verify_sig_structure(
                    public_key,
                    b"current-operation",
                    current_signature,
                )
            )

            with self.assertRaises(CivicProductionSigningError):
                sign_current_sig_structure(
                    provider,
                    key_ref=key_ref,
                    binding=candidate,
                    exact_sig_structure=b"wrong-state",
                )
            with self.assertRaises(CivicProductionSigningError):
                sign_candidate_sig_structure(
                    provider,
                    key_ref=key_ref,
                    binding=current,
                    exact_sig_structure=b"wrong-state",
                )
            with self.assertRaises(CivicProductionSigningError):
                sign_current_sig_structure(
                    provider,
                    key_ref=key_ref,
                    binding=retired,
                    exact_sig_structure=b"retired",
                )

    def test_wrong_role_and_wrong_key_are_rejected_before_authority_signing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = FileSoftwareSignerProvider(directory)
            node_ref = provider.generate_key(CivicKeyRole.SIGNING_NODE)
            participant_ref = provider.generate_key(
                CivicKeyRole.PARTICIPANT_EPOCH
            )

            node_metadata = provider.metadata(node_ref)
            participant_metadata = provider.metadata(participant_ref)

            wrong_role = CivicAuthorityKeyBinding(
                hoa_root_id=ROOT_ID,
                epoch_sequence=1,
                role=CivicKeyRole.PARTICIPANT_EPOCH,
                public_key=node_metadata.public_key,
                key_id=node_metadata.key_id,
                state=CivicAuthorityBindingState.CURRENT,
            )
            with self.assertRaises(CivicProductionSigningError):
                sign_current_sig_structure(
                    provider,
                    key_ref=node_ref,
                    binding=wrong_role,
                    exact_sig_structure=b"wrong-role",
                )

            participant_binding = make_current_binding(
                hoa_root_id=ROOT_ID,
                epoch_sequence=1,
                role=CivicKeyRole.PARTICIPANT_EPOCH,
                public_key=participant_metadata.public_key,
            )
            with self.assertRaises(CivicProductionSigningError):
                sign_current_sig_structure(
                    provider,
                    key_ref=node_ref,
                    binding=participant_binding,
                    exact_sig_structure=b"wrong-key",
                )

    def test_unavailable_key_fails_closed_and_can_be_deliberately_restored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = FileSoftwareSignerProvider(directory)
            key_ref = provider.generate_key(CivicKeyRole.SIGNING_NODE)
            public_key = provider.public_key(key_ref)
            binding = make_current_binding(
                hoa_root_id=ROOT_ID,
                epoch_sequence=1,
                role=CivicKeyRole.SIGNING_NODE,
                public_key=public_key,
            )

            provider.set_unavailable(key_ref)
            self.assertEqual(
                CivicCustodyState.UNAVAILABLE,
                provider.metadata(key_ref).custody_state,
            )
            with self.assertRaises(CivicProductionSigningError):
                sign_current_sig_structure(
                    provider,
                    key_ref=key_ref,
                    binding=binding,
                    exact_sig_structure=b"unavailable",
                )

            provider.set_available(key_ref)
            signature = sign_current_sig_structure(
                provider,
                key_ref=key_ref,
                binding=binding,
                exact_sig_structure=b"available-again",
            )
            self.assertTrue(
                verify_sig_structure(
                    public_key,
                    b"available-again",
                    signature,
                )
            )

    def test_destroyed_key_cannot_sign_or_be_reactivated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = FileSoftwareSignerProvider(directory)
            key_ref = provider.generate_key(CivicKeyRole.SIGNING_NODE)
            public_key = provider.public_key(key_ref)
            binding = make_current_binding(
                hoa_root_id=ROOT_ID,
                epoch_sequence=1,
                role=CivicKeyRole.SIGNING_NODE,
                public_key=public_key,
            )

            provider.destroy_key(key_ref)

            self.assertFalse(
                (Path(directory) / f"{key_ref}.key").exists()
            )
            self.assertEqual(
                CivicCustodyState.DESTROYED,
                provider.metadata(key_ref).custody_state,
            )

            with self.assertRaises(CivicProductionSigningError):
                sign_current_sig_structure(
                    provider,
                    key_ref=key_ref,
                    binding=binding,
                    exact_sig_structure=b"destroyed",
                )
            with self.assertRaises(CivicProductionSigningError):
                provider.set_available(key_ref)

    def test_private_key_tamper_is_detected_before_signing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = FileSoftwareSignerProvider(directory)
            first_ref = provider.generate_key(CivicKeyRole.SIGNING_NODE)
            second_ref = provider.generate_key(CivicKeyRole.SIGNING_NODE)

            first_metadata = provider.metadata(first_ref)
            binding = make_current_binding(
                hoa_root_id=ROOT_ID,
                epoch_sequence=1,
                role=CivicKeyRole.SIGNING_NODE,
                public_key=first_metadata.public_key,
            )

            first_path = Path(directory) / f"{first_ref}.key"
            second_path = Path(directory) / f"{second_ref}.key"
            first_path.write_bytes(second_path.read_bytes())
            if os.name == "posix":
                os.chmod(first_path, 0o600)

            with self.assertRaises(CivicProductionSigningError):
                sign_current_sig_structure(
                    provider,
                    key_ref=first_ref,
                    binding=binding,
                    exact_sig_structure=b"tampered-private-key",
                )

    def test_mandatory_post_sign_verification_rejects_bad_provider_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = InvalidSignatureProvider(directory)
            key_ref = provider.generate_key(CivicKeyRole.SIGNING_NODE)
            metadata = provider.metadata(key_ref)
            binding = make_current_binding(
                hoa_root_id=ROOT_ID,
                epoch_sequence=1,
                role=CivicKeyRole.SIGNING_NODE,
                public_key=metadata.public_key,
            )

            with self.assertRaises(CivicProductionSigningError):
                sign_current_sig_structure(
                    provider,
                    key_ref=key_ref,
                    binding=binding,
                    exact_sig_structure=b"bad-provider-output",
                )

    def test_production_module_has_no_fixture_signing_dependency(self) -> None:
        source = inspect.getsource(production_signing)

        self.assertNotIn("sign_sig_structure_fixture", source)
        self.assertNotIn("sign_epoch_manifest_fixture", source)
        self.assertNotIn("sign_history_record_fixture", source)
        self.assertNotIn("sign_governance_proof_fixture", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
