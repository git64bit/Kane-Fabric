from __future__ import annotations

import copy
import hashlib
import unittest

from ms4.tools.kane_fabric_partition import build_partition_descriptor, canonical_json_bytes
from ms4.tools.kane_fabric_scope import bounded_region_scope, composite_scope
from ms4.tools.kane_fabric_subscription import (
    SubscriptionContractError,
    build_subscription_documents,
    select_objects_for_partition,
    validate_subscription_documents,
)

JURISDICTION = {
    "country_code": "US",
    "state_code": "IL",
    "fips_code": "17089",
    "county_key": "kane-county-il",
    "name": "Kane County",
}
BUILDING_RELEASE = {
    "release_key": "kane-buildings-20250730-086f09eba5ad",
    "content_sha256": "086f09eba5ad5b21eea1b6c9a8158eaf8c509a258c53509d115eaf1d19a7f799",
}
ACCEPTED = {"buildings": BUILDING_RELEASE}
AUTHORITATIVE_OBJECTS = {"buildings": {"building-1", "building-2"}}

PARTITION_A = build_partition_descriptor(
    JURISDICTION, bounded_region_scope([-88.6, 41.6, -88.4, 41.9])
)
PARTITION_B = build_partition_descriptor(
    JURISDICTION, bounded_region_scope([-88.4, 41.6, -88.2, 41.9])
)


def reference(object_key: str) -> dict[str, str]:
    return {
        "kind": "building",
        "dataset_key": "buildings",
        "release_key": BUILDING_RELEASE["release_key"],
        "source_content_sha256": BUILDING_RELEASE["content_sha256"],
        "object_key": object_key,
    }


def build_docs(objects, coverage=(PARTITION_A,)):
    return build_subscription_documents(
        subscription_key="condo",
        owner={"application_key": "condo", "name": "Condo proof"},
        jurisdiction=JURISDICTION,
        substrate_content_sha256="f" * 64,
        coverage_partitions=coverage,
        rights={"license": "proof-only", "owner": "Condo application"},
        objects=objects,
    )


def validate_docs(manifest, objects_doc, partitions=(PARTITION_A,)):
    return validate_subscription_documents(
        manifest,
        objects_doc,
        partition_descriptors=partitions,
        accepted_releases=ACCEPTED,
        authoritative_object_keys=AUTHORITATIVE_OBJECTS,
    )


def rehash_manifest(manifest):
    body = {
        key: value
        for key, value in manifest.items()
        if key not in {"generation_sha256", "generation_key"}
    }
    digest = hashlib.sha256(canonical_json_bytes(body)).hexdigest()
    manifest["generation_sha256"] = digest
    manifest["generation_key"] = "kfsg1-" + digest[:32]


class SubscriptionContractTests(unittest.TestCase):
    def test_generation_is_deterministic_and_independent(self) -> None:
        objects = [
            {
                "object_key": "unit-a",
                "bounds": [-88.5, 41.7, -88.4, 41.8],
                "geographic_refs": [reference("building-1")],
                "payload": {"classification": "residential"},
            }
        ]
        first = build_docs(objects)
        second = build_docs(copy.deepcopy(objects))
        self.assertEqual(first, second)
        validate_docs(*first)
        changed_manifest, _ = build_subscription_documents(
            subscription_key="condo",
            owner={"application_key": "condo", "name": "Condo proof"},
            jurisdiction=JURISDICTION,
            substrate_content_sha256="f" * 64,
            coverage_partitions=[PARTITION_A],
            rights={"license": "different-license", "owner": "Condo application"},
            objects=objects,
        )
        self.assertNotEqual(
            first[0]["generation_sha256"],
            changed_manifest["generation_sha256"],
        )

    def test_builder_requires_verified_partition_descriptors(self) -> None:
        with self.assertRaises(SubscriptionContractError):
            build_subscription_documents(
                subscription_key="condo",
                owner={"application_key": "condo", "name": "Condo proof"},
                jurisdiction=JURISDICTION,
                substrate_content_sha256="f" * 64,
                coverage_partitions=[{"partition_key": "partition-a"}],
                rights={"license": "proof-only", "owner": "Condo application"},
                objects=[],
            )

    def test_validator_rejects_unknown_coverage_even_when_generation_rehashed(self) -> None:
        manifest, objects_doc = build_docs([])
        manifest["coverage_partition_keys"] = [
            "kfp1-00000000000000000000000000000000"
        ]
        rehash_manifest(manifest)
        with self.assertRaisesRegex(SubscriptionContractError, "unknown/unverified"):
            validate_docs(manifest, objects_doc)

    def test_validator_rejects_malformed_owner_even_when_generation_rehashed(self) -> None:
        manifest, objects_doc = build_docs([])
        manifest["owner"]["application_key"] = "Condo"
        rehash_manifest(manifest)
        with self.assertRaisesRegex(SubscriptionContractError, "lowercase hyphenated"):
            validate_docs(manifest, objects_doc)

    def test_validator_rejects_extra_manifest_field_even_when_generation_rehashed(self) -> None:
        manifest, objects_doc = build_docs([])
        manifest["physical_node"] = "edge-a"
        rehash_manifest(manifest)
        with self.assertRaisesRegex(SubscriptionContractError, "keys mismatch"):
            validate_docs(manifest, objects_doc)

    def test_reference_must_bind_accepted_release_identity(self) -> None:
        manifest, objects_doc = build_docs(
            [
                {
                    "object_key": "unit-a",
                    "bounds": [-88.5, 41.7, -88.4, 41.8],
                    "geographic_refs": [reference("building-1")],
                    "payload": {},
                }
            ]
        )
        bad = copy.deepcopy(objects_doc)
        bad["objects"][0]["geographic_refs"][0]["release_key"] = "wrong-release"
        with self.assertRaises(SubscriptionContractError):
            validate_docs(manifest, bad)

    def test_reference_object_key_must_exist_in_authoritative_inventory(self) -> None:
        manifest, objects_doc = build_docs(
            [
                {
                    "object_key": "unit-a",
                    "bounds": [-88.5, 41.7, -88.4, 41.8],
                    "geographic_refs": [reference("nonexistent-building")],
                    "payload": {},
                }
            ]
        )
        with self.assertRaisesRegex(SubscriptionContractError, "authoritative accepted identity"):
            validate_docs(manifest, objects_doc)

    def test_cross_boundary_object_retains_one_identity_in_both_partitions(self) -> None:
        crossing = {
            "object_key": "crossing-service-area",
            "bounds": [-88.45, 41.7, -88.35, 41.8],
            "geographic_refs": [reference("building-1")],
            "payload": {"state": "active"},
        }
        manifest, objects_doc = build_docs(
            [crossing], coverage=(PARTITION_A, PARTITION_B)
        )
        validate_subscription_documents(
            manifest,
            objects_doc,
            partition_descriptors=[PARTITION_A, PARTITION_B],
            accepted_releases=ACCEPTED,
            authoritative_object_keys=AUTHORITATIVE_OBJECTS,
        )
        selected_left = select_objects_for_partition(
            PARTITION_A, manifest, objects_doc
        )
        selected_right = select_objects_for_partition(
            PARTITION_B, manifest, objects_doc
        )
        self.assertEqual(len(selected_left), 1)
        self.assertEqual(len(selected_right), 1)
        self.assertEqual(
            selected_left[0]["object_sha256"],
            selected_right[0]["object_sha256"],
        )
        self.assertEqual(selected_left[0], selected_right[0])

    def test_selection_rejects_partition_not_declared_in_coverage(self) -> None:
        manifest, objects_doc = build_docs(
            [
                {
                    "object_key": "unit-a",
                    "bounds": [-88.5, 41.7, -88.3, 41.8],
                    "geographic_refs": [reference("building-1")],
                    "payload": {},
                }
            ],
            coverage=(PARTITION_A,),
        )
        with self.assertRaisesRegex(SubscriptionContractError, "not declared"):
            select_objects_for_partition(PARTITION_B, manifest, objects_doc)

    def test_composite_union_subscription_selection_excludes_gap(self) -> None:
        west = build_partition_descriptor(
            JURISDICTION,
            bounded_region_scope([-88.60, 41.60, -88.50, 41.70]),
        )
        east = build_partition_descriptor(
            JURISDICTION,
            bounded_region_scope([-88.20, 41.60, -88.10, 41.70]),
        )
        composite = build_partition_descriptor(
            JURISDICTION, composite_scope([west, east])
        )
        objects = [
            {
                "object_key": "west",
                "bounds": [-88.58, 41.62, -88.55, 41.65],
                "geographic_refs": [reference("building-1")],
                "payload": {},
            },
            {
                "object_key": "gap",
                "bounds": [-88.40, 41.62, -88.35, 41.65],
                "geographic_refs": [reference("building-2")],
                "payload": {},
            },
            {
                "object_key": "east",
                "bounds": [-88.18, 41.62, -88.15, 41.65],
                "geographic_refs": [reference("building-2")],
                "payload": {},
            },
        ]
        manifest, objects_doc = build_docs(objects, coverage=(composite,))
        validate_subscription_documents(
            manifest,
            objects_doc,
            partition_descriptors=[composite],
            accepted_releases=ACCEPTED,
            authoritative_object_keys=AUTHORITATIVE_OBJECTS,
        )
        selected = select_objects_for_partition(
            composite, manifest, objects_doc
        )
        self.assertEqual([item["object_key"] for item in selected], ["east", "west"])

    def test_subscription_component_tampering_fails(self) -> None:
        manifest, objects_doc = build_docs(
            [
                {
                    "object_key": "unit-a",
                    "bounds": [-88.5, 41.7, -88.4, 41.8],
                    "geographic_refs": [],
                    "payload": {"value": 1},
                }
            ]
        )
        objects_doc["objects"][0]["payload"]["value"] = 2
        with self.assertRaisesRegex(SubscriptionContractError, "component bytes"):
            validate_subscription_documents(
                manifest,
                objects_doc,
                partition_descriptors=[PARTITION_A],
            )


if __name__ == "__main__":
    unittest.main()
