from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from civic.authority_transaction import (
    FileAcceptedStateSelector,
)
from civic.epoch_manifest import derive_key_id
from civic.object_store import object_path
from civic.production_signing import (
    CivicCustodyState,
    CivicKeyRole,
    CivicLocalKeyMetadata,
)
from civic.signing_node import (
    CivicReplicaClosure,
    CivicSigningNode,
    CivicSigningNodeError,
    CivicSigningNodeOperationalState,
    FileCivicObjectRepository,
    REFERENCE_NAME,
    REFERENCE_VERSION,
)
from civic.tests.test_authority_transaction import (
    build_bootstrap_fixture,
    build_successor_fixture,
    persist_fixture,
)
from civic.tests.test_epoch_manifest import P1, P2, h


class StaticSignerProvider:
    """Protocol-conforming test custody adapter over one fixed public key."""

    def __init__(
        self,
        *,
        public_key: bytes = P2,
        role: CivicKeyRole = CivicKeyRole.SIGNING_NODE,
        custody_state: CivicCustodyState = CivicCustodyState.AVAILABLE,
        key_ref: str = "test-signing-key",
    ) -> None:
        self.key_ref = key_ref
        self.role = role
        self.custody_state = custody_state
        self._public_key = public_key

    def generate_key(self, role: CivicKeyRole) -> str:
        raise AssertionError(
            "piece-6 conformance tests must not generate provider keys"
        )

    def metadata(self, key_ref: str) -> CivicLocalKeyMetadata:
        if key_ref != self.key_ref:
            raise ValueError("unknown test key reference")
        return CivicLocalKeyMetadata(
            key_ref=self.key_ref,
            role=self.role,
            public_key=self._public_key,
            key_id=derive_key_id(self._public_key),
            custody_state=self.custody_state,
        )

    def public_key(self, key_ref: str) -> bytes:
        if key_ref != self.key_ref:
            raise ValueError("unknown test key reference")
        return self._public_key

    def sign_sig_structure(
        self,
        key_ref: str,
        exact_sig_structure: bytes,
    ) -> bytes:
        raise AssertionError(
            "Signing Node orchestration tests do not expose generic signing"
        )

    def set_unavailable(self, key_ref: str) -> None:
        if key_ref != self.key_ref:
            raise ValueError("unknown test key reference")
        self.custody_state = CivicCustodyState.UNAVAILABLE

    def set_available(self, key_ref: str) -> None:
        if key_ref != self.key_ref:
            raise ValueError("unknown test key reference")
        self.custody_state = CivicCustodyState.AVAILABLE

    def destroy_key(self, key_ref: str) -> None:
        if key_ref != self.key_ref:
            raise ValueError("unknown test key reference")
        self.custody_state = CivicCustodyState.DESTROYED


def resolver_for(
    provider: StaticSignerProvider,
):
    expected_key_id = derive_key_id(provider._public_key)

    def resolve(key_id: bytes) -> str | None:
        if key_id == expected_key_id:
            return provider.key_ref
        return None

    return resolve


def unresolved_key_ref(_key_id: bytes) -> None:
    return None


def make_node(
    root: Path,
    *,
    provider: StaticSignerProvider | None = None,
    expected_hoa_root_id: bytes | None = None,
    resolver=None,
) -> CivicSigningNode:
    if provider is None:
        return CivicSigningNode(
            objects=FileCivicObjectRepository(
                root / "objects"
            ),
            selector=FileAcceptedStateSelector(
                root / "selector"
            ),
            expected_hoa_root_id=expected_hoa_root_id,
        )

    return CivicSigningNode(
        objects=FileCivicObjectRepository(
            root / "objects"
        ),
        selector=FileAcceptedStateSelector(
            root / "selector"
        ),
        signer_provider=provider,
        resolve_signing_key_ref=(
            resolver
            if resolver is not None
            else resolver_for(provider)
        ),
        expected_hoa_root_id=expected_hoa_root_id,
    )


def persist_and_select_bootstrap(
    root: Path,
) -> tuple[CivicSigningNode, object]:
    fixture = build_bootstrap_fixture()
    persist_fixture(
        root / "objects",
        fixture,
    )

    node = make_node(root)
    candidate = node.verify_candidate(
        fixture.replica_sha256
    )
    committed = node.commit_candidate(candidate)

    if (
        committed.commit.selection.replica_sha256
        != fixture.replica_sha256
    ):
        raise AssertionError(
            "bootstrap fixture did not select exact replica"
        )

    return node, fixture


class CivicSigningNodeConformanceTests(unittest.TestCase):
    def test_unselected_valid_objects_remain_uninitialized_and_are_not_auto_selected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = build_bootstrap_fixture()
            persist_fixture(
                root / "objects",
                fixture,
            )

            node = make_node(root)
            startup = node.startup()

            self.assertEqual(
                CivicSigningNodeOperationalState.UNINITIALIZED,
                startup.operational_state,
            )
            self.assertFalse(
                startup.current_signing_enabled
            )
            self.assertIsNone(
                FileAcceptedStateSelector(
                    root / "selector"
                ).read()
            )

    def test_selected_valid_state_verifies_without_private_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            node, fixture = persist_and_select_bootstrap(
                root
            )

            startup = node.startup()

            self.assertEqual(
                CivicSigningNodeOperationalState.STATE_VERIFIED,
                startup.operational_state,
            )
            self.assertIsNotNone(
                startup.verified_state
            )
            self.assertIsNone(
                startup.current_binding
            )
            self.assertFalse(
                startup.current_signing_enabled
            )
            self.assertEqual(
                fixture.manifest["hoa_root_id"],
                startup.verified_state.current_manifest[
                    "hoa_root_id"
                ],
            )

    def test_exact_current_provider_reaches_ready_and_status_is_secret_free(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, fixture = persist_and_select_bootstrap(
                root
            )
            provider = StaticSignerProvider()
            node = make_node(
                root,
                provider=provider,
                expected_hoa_root_id=fixture.manifest[
                    "hoa_root_id"
                ],
            )

            startup = node.startup()

            self.assertEqual(
                CivicSigningNodeOperationalState.READY_CURRENT,
                startup.operational_state,
            )
            self.assertTrue(
                startup.current_signing_enabled
            )
            binding = node.current_signing_binding()
            self.assertEqual(
                fixture.manifest["hoa_root_id"],
                binding.hoa_root_id,
            )
            self.assertEqual(
                1,
                binding.epoch_sequence,
            )
            self.assertEqual(
                P2,
                binding.public_key,
            )
            self.assertEqual(
                derive_key_id(P2),
                binding.key_id,
            )

            status = node.status()
            self.assertEqual(
                REFERENCE_NAME,
                status["reference_name"],
            )
            self.assertEqual(
                REFERENCE_VERSION,
                status["reference_version"],
            )
            self.assertTrue(
                status["current_signing_enabled"]
            )
            self.assertNotIn(
                "current_key_ref",
                status,
            )
            self.assertNotIn(
                provider.key_ref,
                repr(status),
            )
            self.assertFalse(
                hasattr(node, "sign_any_current_bytes")
            )
            self.assertFalse(
                hasattr(node, "generate_key")
            )

    def test_unavailable_wrong_or_unresolved_current_key_requires_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            persist_and_select_bootstrap(root)

            cases = [
                (
                    StaticSignerProvider(
                        custody_state=(
                            CivicCustodyState.UNAVAILABLE
                        )
                    ),
                    None,
                    "current-key-unavailable",
                ),
                (
                    StaticSignerProvider(
                        public_key=P1,
                    ),
                    lambda _key_id: "test-signing-key",
                    "current-key-binding-mismatch",
                ),
                (
                    StaticSignerProvider(),
                    unresolved_key_ref,
                    "current-key-not-locally-resolved",
                ),
            ]

            for provider, resolver, failure in cases:
                with self.subTest(
                    failure=failure
                ):
                    node = make_node(
                        root,
                        provider=provider,
                        resolver=resolver,
                    )
                    startup = node.startup()

                    self.assertEqual(
                        CivicSigningNodeOperationalState.RECOVERY_REQUIRED,
                        startup.operational_state,
                    )
                    self.assertFalse(
                        startup.current_signing_enabled
                    )
                    self.assertEqual(
                        failure,
                        startup.failure_classification,
                    )

    def test_selected_replica_or_selector_corruption_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, fixture = persist_and_select_bootstrap(
                root
            )

            object_path(
                root / "objects",
                fixture.replica_sha256,
            ).write_bytes(b"corrupt")

            startup = make_node(root).startup()
            self.assertEqual(
                CivicSigningNodeOperationalState.FAILED_CLOSED,
                startup.operational_state,
            )
            self.assertFalse(
                startup.current_signing_enabled
            )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selector_root = root / "selector"
            selector = FileAcceptedStateSelector(
                selector_root
            )
            self.assertIsNone(selector.read())

            (selector_root / "accepted-state.json").write_bytes(
                b"{not-json"
            )

            startup = make_node(root).startup()
            self.assertEqual(
                CivicSigningNodeOperationalState.FAILED_CLOSED,
                startup.operational_state,
            )
            self.assertEqual(
                "selector-integrity-failure",
                startup.failure_classification,
            )

    def test_export_import_preserves_exact_closure_and_import_does_not_select(self) -> None:
        with tempfile.TemporaryDirectory() as source_directory:
            source_root = Path(source_directory)
            source_node, fixture = (
                persist_and_select_bootstrap(
                    source_root
                )
            )

            closure = (
                source_node.export_selected_replica_closure()
            )

            self.assertEqual(
                fixture.replica_bytes,
                closure.replica_bytes,
            )
            self.assertGreater(
                len(closure.objects),
                0,
            )

            for item in closure.objects:
                self.assertEqual(
                    item.sha256,
                    hashlib.sha256(
                        item.exact_bytes
                    ).digest(),
                )
                self.assertEqual(
                    item.byte_length,
                    len(item.exact_bytes),
                )

            forbidden = b"test-signing-key"
            self.assertNotIn(
                forbidden,
                closure.replica_bytes,
            )
            for item in closure.objects:
                self.assertNotIn(
                    forbidden,
                    item.exact_bytes,
                )

            with tempfile.TemporaryDirectory() as target_directory:
                target_root = Path(
                    target_directory
                )
                target_node = make_node(
                    target_root
                )

                imported = (
                    target_node.import_replica_closure(
                        closure,
                        expected_hoa_root_id=(
                            fixture.manifest[
                                "hoa_root_id"
                            ]
                        ),
                    )
                )

                self.assertEqual(
                    fixture.replica_sha256,
                    imported.replica_sha256,
                )
                self.assertIsNone(
                    FileAcceptedStateSelector(
                        target_root / "selector"
                    ).read()
                )
                self.assertEqual(
                    CivicSigningNodeOperationalState.UNINITIALIZED,
                    target_node.startup().operational_state,
                )

    def test_import_failure_leaves_selector_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as source_directory:
            source_root = Path(source_directory)
            source_node, _ = (
                persist_and_select_bootstrap(
                    source_root
                )
            )
            closure = (
                source_node.export_selected_replica_closure()
            )
            self.assertGreater(
                len(closure.objects),
                0,
            )

            incomplete = CivicReplicaClosure(
                replica_bytes=closure.replica_bytes,
                objects=closure.objects[1:],
            )

            with tempfile.TemporaryDirectory() as target_directory:
                target_root = Path(
                    target_directory
                )
                target_node = make_node(
                    target_root
                )
                selector = FileAcceptedStateSelector(
                    target_root / "selector"
                )

                with self.assertRaises(
                    CivicSigningNodeError
                ):
                    target_node.import_replica_closure(
                        incomplete
                    )

                self.assertIsNone(
                    selector.read()
                )

    def test_recovery_restore_binds_root_does_not_create_epoch_and_same_key_migration_restores_ready(self) -> None:
        with tempfile.TemporaryDirectory() as source_directory:
            source_root = Path(source_directory)
            source_node, fixture = (
                persist_and_select_bootstrap(
                    source_root
                )
            )
            closure = (
                source_node.export_selected_replica_closure()
            )

            with tempfile.TemporaryDirectory() as target_directory:
                target_root = Path(
                    target_directory
                )
                provider = StaticSignerProvider()
                recovering_node = make_node(
                    target_root,
                    provider=provider,
                    expected_hoa_root_id=(
                        fixture.manifest[
                            "hoa_root_id"
                        ]
                    ),
                    resolver=unresolved_key_ref,
                )

                imported = (
                    recovering_node.import_replica_closure(
                        closure,
                        expected_hoa_root_id=(
                            fixture.manifest[
                                "hoa_root_id"
                            ]
                        ),
                    )
                )

                with self.assertRaises(
                    CivicSigningNodeError
                ):
                    recovering_node.restore_verified_state(
                        imported,
                        expected_hoa_root_id=h(254),
                    )

                self.assertIsNone(
                    FileAcceptedStateSelector(
                        target_root / "selector"
                    ).read()
                )

                restored = (
                    recovering_node.restore_verified_state(
                        imported,
                        expected_hoa_root_id=(
                            fixture.manifest[
                                "hoa_root_id"
                            ]
                        ),
                    )
                )

                self.assertEqual(
                    CivicSigningNodeOperationalState.RECOVERY_REQUIRED,
                    restored.operational_state,
                )
                self.assertEqual(
                    1,
                    restored.verified_state.current_manifest[
                        "epoch_sequence"
                    ],
                )

                selection_before = (
                    FileAcceptedStateSelector(
                        target_root / "selector"
                    ).read()
                )
                self.assertIsNotNone(
                    selection_before
                )

                migrated_node = make_node(
                    target_root,
                    provider=StaticSignerProvider(
                        key_ref="migrated-same-key"
                    ),
                    expected_hoa_root_id=(
                        fixture.manifest[
                            "hoa_root_id"
                        ]
                    ),
                )
                migrated = migrated_node.startup()

                self.assertEqual(
                    CivicSigningNodeOperationalState.READY_CURRENT,
                    migrated.operational_state,
                )

                selection_after = (
                    FileAcceptedStateSelector(
                        target_root / "selector"
                    ).read()
                )
                self.assertEqual(
                    selection_before,
                    selection_after,
                )

                with self.assertRaises(
                    CivicSigningNodeError
                ):
                    migrated_node.restore_verified_state(
                        imported,
                        expected_hoa_root_id=(
                            fixture.manifest[
                                "hoa_root_id"
                            ]
                        ),
                    )

                self.assertEqual(
                    selection_after,
                    FileAcceptedStateSelector(
                        target_root / "selector"
                    ).read(),
                )

    def test_expected_root_mismatch_fails_closed_on_startup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            persist_and_select_bootstrap(root)

            node = make_node(
                root,
                expected_hoa_root_id=h(253),
            )
            startup = node.startup()

            self.assertEqual(
                CivicSigningNodeOperationalState.FAILED_CLOSED,
                startup.operational_state,
            )
            self.assertFalse(
                startup.current_signing_enabled
            )

    def test_successor_commit_uses_piece5_path_and_postcommit_key_failure_does_not_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, bootstrap = (
                persist_and_select_bootstrap(
                    root
                )
            )

            provider = StaticSignerProvider()
            node = make_node(
                root,
                provider=provider,
                expected_hoa_root_id=(
                    bootstrap.manifest[
                        "hoa_root_id"
                    ]
                ),
            )

            self.assertEqual(
                CivicSigningNodeOperationalState.READY_CURRENT,
                node.startup().operational_state,
            )

            predecessor = (
                node.verify_selected_public_state()
            )
            self.assertIsNotNone(predecessor)
            assert predecessor is not None

            successor = build_successor_fixture(
                predecessor,
                variant=7,
            )
            persist_fixture(
                root / "objects",
                successor,
            )

            candidate = node.verify_candidate(
                successor.replica_sha256
            )

            provider.set_unavailable(
                provider.key_ref
            )
            result = node.commit_candidate(
                candidate
            )

            self.assertEqual(
                successor.replica_sha256,
                result.commit.selection.replica_sha256,
            )
            self.assertEqual(
                2,
                result.commit.selection.current_epoch_sequence,
            )
            self.assertEqual(
                CivicSigningNodeOperationalState.RECOVERY_REQUIRED,
                result.startup.operational_state,
            )

            selected = (
                FileAcceptedStateSelector(
                    root / "selector"
                ).read()
            )
            self.assertIsNotNone(selected)
            assert selected is not None
            self.assertEqual(
                successor.replica_sha256,
                selected.replica_sha256,
            )

            provider.set_available(
                provider.key_ref
            )
            self.assertEqual(
                CivicSigningNodeOperationalState.READY_CURRENT,
                node.startup().operational_state,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
