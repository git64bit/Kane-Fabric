from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from ms5.tools.kane_fabric_edge import (
    EdgeContractError,
    SECURITY_POSTURE,
    TRUST_BOUNDARY,
    build_edge_instance,
    validate_edge_instance,
)
from ms5.tools.kane_fabric_keys import (
    KeyProviderContractError,
    build_key_provider,
    validate_key_provider,
)
from ms5.tools.kane_fabric_storage import (
    StorageContractError,
    activate_inventory,
    build_activation_state,
    build_inventory,
    recover_activation,
    rollback_activation,
    validate_activation_state,
    validate_inventory,
    verify_inventory_files,
)

A = "a" * 64
B = "b" * 64
C = "c" * 64


class EdgeContractTests(unittest.TestCase):
    def _edge(self, label: str = "node-a"):
        return build_edge_instance(
            logical_placement_sha256=A,
            platform_class="esp32-s3-class",
            instance_label=label,
            storage_backend="sd-card",
            browser_transport="wiregate-hub-proxy",
            management_transport="none",
        )

    def test_build_and_validate(self):
        doc = self._edge()
        validate_edge_instance(doc)
        self.assertEqual(A, doc["logical"]["logical_placement_sha256"])
        self.assertEqual(TRUST_BOUNDARY, doc["trust_boundary"])
        self.assertEqual(SECURITY_POSTURE, doc["security_posture"])

    def test_replacement_changes_physical_identity_not_logical_placement(self):
        first = self._edge("node-a")
        second = self._edge("replacement-node")
        self.assertEqual(first["logical"], second["logical"])
        self.assertNotEqual(first["physical_instance_sha256"], second["physical_instance_sha256"])

    def test_authority_cannot_be_added(self):
        doc = self._edge()
        doc["trust_boundary"] = dict(doc["trust_boundary"])
        doc["trust_boundary"]["candidate_promotion"] = True
        with self.assertRaises(EdgeContractError):
            validate_edge_instance(doc)

    def test_irreversible_efuse_cannot_be_required(self):
        doc = self._edge()
        doc["security_posture"] = dict(doc["security_posture"])
        doc["security_posture"]["irreversible_efuse_required"] = True
        with self.assertRaises(EdgeContractError):
            validate_edge_instance(doc)


class StorageContractTests(unittest.TestCase):
    def _inventory(self, content: bytes = b"abc", placement: str = A):
        return build_inventory(
            logical_placement_sha256=placement,
            artifacts=[
                {
                    "artifact_key": "substrate-manifest",
                    "path": "publication/substrate-manifest.json",
                    "byte_length": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            ],
        )

    def _edge(self, placement: str = A):
        return build_edge_instance(
            logical_placement_sha256=placement,
            platform_class="esp32-s3-class",
            instance_label="storage-node",
            storage_backend="sd-card",
            browser_transport="wiregate-hub-proxy",
            management_transport="none",
        )

    def test_inventory_is_deterministic(self):
        artifact1 = {
            "artifact_key": "b",
            "path": "b.bin",
            "byte_length": 1,
            "sha256": hashlib.sha256(b"b").hexdigest(),
        }
        artifact2 = {
            "artifact_key": "a",
            "path": "a.bin",
            "byte_length": 1,
            "sha256": hashlib.sha256(b"a").hexdigest(),
        }
        x = build_inventory(logical_placement_sha256=A, artifacts=[artifact1, artifact2])
        y = build_inventory(logical_placement_sha256=A, artifacts=[artifact2, artifact1])
        self.assertEqual(x, y)
        validate_inventory(x)

    def test_storage_location_is_not_inventory_identity(self):
        content = b"abc"
        doc = self._inventory(content)
        identity = doc["inventory_sha256"]
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            for root in (Path(a), Path(b)):
                path = root / "publication/substrate-manifest.json"
                path.parent.mkdir(parents=True)
                path.write_bytes(content)
                verify_inventory_files(doc, root)
        self.assertEqual(identity, doc["inventory_sha256"])

    def test_mutated_file_fails_verification(self):
        doc = self._inventory(b"abc")
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "publication/substrate-manifest.json"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"abd")
            with self.assertRaises(StorageContractError):
                verify_inventory_files(doc, Path(d))

    def test_activation_requires_matching_verified_identity(self):
        state = build_activation_state(active_inventory_sha256=None, rollback_inventory_sha256=None)
        candidate = self._inventory()
        with self.assertRaises(StorageContractError):
            activate_inventory(
                state,
                candidate,
                edge_instance=self._edge(),
                verified_inventory_sha256=B,
            )
        self.assertIsNone(state["active_inventory_sha256"])

    def test_activation_requires_matching_edge_logical_placement(self):
        state = build_activation_state(active_inventory_sha256=None, rollback_inventory_sha256=None)
        candidate = self._inventory(placement=B)
        with self.assertRaises(StorageContractError):
            activate_inventory(
                state,
                candidate,
                edge_instance=self._edge(A),
                verified_inventory_sha256=candidate["inventory_sha256"],
            )
        self.assertIsNone(state["active_inventory_sha256"])

    def test_activation_swaps_whole_inventory_and_keeps_rollback(self):
        old = build_inventory(
            logical_placement_sha256=A,
            artifacts=[{
                "artifact_key": "old",
                "path": "old.bin",
                "byte_length": 1,
                "sha256": hashlib.sha256(b"x").hexdigest(),
            }],
        )
        new = self._inventory()
        state = build_activation_state(
            active_inventory_sha256=old["inventory_sha256"],
            rollback_inventory_sha256=None,
        )
        next_state = activate_inventory(
            state,
            new,
            edge_instance=self._edge(),
            verified_inventory_sha256=new["inventory_sha256"],
        )
        self.assertEqual(new["inventory_sha256"], next_state["active_inventory_sha256"])
        self.assertEqual(old["inventory_sha256"], next_state["rollback_inventory_sha256"])

    def test_rollback_without_active_inventory_is_rejected(self):
        with self.assertRaises(StorageContractError):
            build_activation_state(
                active_inventory_sha256=None,
                rollback_inventory_sha256=B,
            )

    def test_rollback_and_recovery(self):
        state = build_activation_state(active_inventory_sha256=A, rollback_inventory_sha256=B)
        rolled = rollback_activation(state)
        self.assertEqual(B, rolled["active_inventory_sha256"])
        self.assertEqual(A, rolled["rollback_inventory_sha256"])
        recovered = recover_activation(state, {B})
        self.assertEqual(B, recovered["active_inventory_sha256"])
        self.assertIsNone(recovered["rollback_inventory_sha256"])
        validate_activation_state(recovered)

    def test_recovery_fails_closed_without_verified_generation(self):
        state = build_activation_state(active_inventory_sha256=A, rollback_inventory_sha256=B)
        with self.assertRaises(StorageContractError):
            recover_activation(state, {C})

    def test_parent_traversal_path_rejected(self):
        with self.assertRaises(StorageContractError):
            build_inventory(
                logical_placement_sha256=A,
                artifacts=[{
                    "artifact_key": "bad",
                    "path": "../escape.bin",
                    "byte_length": 1,
                    "sha256": hashlib.sha256(b"x").hexdigest(),
                }],
            )

    def test_duplicate_paths_rejected(self):
        base = {
            "byte_length": 1,
            "sha256": hashlib.sha256(b"x").hexdigest(),
        }
        with self.assertRaises(StorageContractError):
            build_inventory(
                logical_placement_sha256=A,
                artifacts=[
                    {"artifact_key": "a", "path": "same.bin", **base},
                    {"artifact_key": "b", "path": "same.bin", **base},
                ],
            )


class KeyProviderTests(unittest.TestCase):
    def test_software_provider_valid_without_private_keys(self):
        doc = build_key_provider(
            provider_class="software",
            provider_instance="nvs-key-store",
            keys=[],
        )
        validate_key_provider(doc)

    def test_management_key_is_allowed(self):
        doc = build_key_provider(
            provider_class="software",
            provider_instance="nvs-key-store",
            keys=[
                {"role": "management-transport-client", "key_ref": "wg-key-1"},
            ],
        )
        validate_key_provider(doc)

    def test_external_provider_is_substitutable(self):
        software = build_key_provider(
            provider_class="software",
            provider_instance="software-store",
            keys=[{"role": "management-transport-client", "key_ref": "wg-a"}],
        )
        external = build_key_provider(
            provider_class="external",
            provider_instance="optional-secure-element",
            keys=[{"role": "management-transport-client", "key_ref": "slot-1"}],
        )
        validate_key_provider(software)
        validate_key_provider(external)
        self.assertNotEqual(
            software["provider_fingerprint_sha256"],
            external["provider_fingerprint_sha256"],
        )

    def test_duplicate_private_key_role_rejected(self):
        with self.assertRaises(KeyProviderContractError):
            build_key_provider(
                provider_class="software",
                provider_instance="store",
                keys=[
                    {"role": "management-transport-client", "key_ref": "a"},
                    {"role": "management-transport-client", "key_ref": "b"},
                ],
            )

    def test_browser_tls_key_role_rejected_from_edge(self):
        with self.assertRaises(KeyProviderContractError):
            build_key_provider(
                provider_class="software",
                provider_instance="store",
                keys=[{"role": "browser-tls-server", "key_ref": "tls"}],
            )

    def test_authority_role_rejected(self):
        with self.assertRaises(KeyProviderContractError):
            build_key_provider(
                provider_class="external",
                provider_instance="store",
                keys=[{"role": "fabric-release-signing", "key_ref": "bad"}],
            )

    def test_civic_anchor_role_rejected_from_fabric_edge_contract(self):
        with self.assertRaises(KeyProviderContractError):
            build_key_provider(
                provider_class="external",
                provider_instance="store",
                keys=[{"role": "civic-anchor", "key_ref": "anchor"}],
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
