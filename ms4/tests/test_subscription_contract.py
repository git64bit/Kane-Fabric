from __future__ import annotations

import copy
import unittest

from ms4.tools.kane_fabric_partition import build_partition_descriptor
from ms4.tools.kane_fabric_scope import bounded_region_scope
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


def reference(object_key: str) -> dict[str, str]:
    return {
        "kind": "building",
        "dataset_key": "buildings",
        "release_key": BUILDING_RELEASE["release_key"],
        "source_content_sha256": BUILDING_RELEASE["content_sha256"],
        "object_key": object_key,
    }


def build_docs(objects, coverage=("partition-a",)):
    return build_subscription_documents(
        subscription_key="condo",
        owner={"application_key": "condo", "name": "Condo proof"},
        jurisdiction=JURISDICTION,
        substrate_content_sha256="f" * 64,
        coverage_partition_keys=coverage,
        rights={"license": "proof-only", "owner": "Condo application"},
        objects=objects,
    )


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
        validate_subscription_documents(*first, accepted_releases=ACCEPTED)
        changed_manifest, _ = build_subscription_documents(
            subscription_key="condo",
            owner={"application_key": "condo", "name": "Condo proof"},
            jurisdiction=JURISDICTION,
            substrate_content_sha256="f" * 64,
            coverage_partition_keys=["partition-a"],
            rights={"license": "different-license", "owner": "Condo application"},
            objects=objects,
        )
        self.assertNotEqual(first[0]["generation_sha256"], changed_manifest["generation_sha256"])

    def test_reference_must_bind_accepted_release_identity(self) -> None:
        manifest, objects_doc = build_docs(
            [{
                "object_key": "unit-a",
                "bounds": [-88.5, 41.7, -88.4, 41.8],
                "geographic_refs": [reference("building-1")],
                "payload": {},
            }]
        )
        bad = copy.deepcopy(objects_doc)
        bad["objects"][0]["geographic_refs"][0]["release_key"] = "wrong-release"
        with self.assertRaises(SubscriptionContractError):
            validate_subscription_documents(manifest, bad, accepted_releases=ACCEPTED)

    def test_cross_boundary_object_retains_one_identity_in_both_partitions(self) -> None:
        left = build_partition_descriptor(JURISDICTION, bounded_region_scope([-88.6, 41.6, -88.4, 41.9]))
        right = build_partition_descriptor(JURISDICTION, bounded_region_scope([-88.4, 41.6, -88.2, 41.9]))
        crossing = {
            "object_key": "crossing-service-area",
            "bounds": [-88.45, 41.7, -88.35, 41.8],
            "geographic_refs": [reference("building-1")],
            "payload": {"state": "active"},
        }
        manifest, objects_doc = build_docs([crossing], coverage=(left["partition_key"], right["partition_key"]))
        validate_subscription_documents(manifest, objects_doc, accepted_releases=ACCEPTED)
        selected_left = select_objects_for_partition(left, objects_doc)
        selected_right = select_objects_for_partition(right, objects_doc)
        self.assertEqual(len(selected_left), 1)
        self.assertEqual(len(selected_right), 1)
        self.assertEqual(selected_left[0]["object_sha256"], selected_right[0]["object_sha256"])
        self.assertEqual(selected_left[0], selected_right[0])

    def test_subscription_component_tampering_fails(self) -> None:
        manifest, objects_doc = build_docs(
            [{
                "object_key": "unit-a",
                "bounds": [-88.5, 41.7, -88.4, 41.8],
                "geographic_refs": [],
                "payload": {"value": 1},
            }]
        )
        objects_doc["objects"][0]["payload"]["value"] = 2
        with self.assertRaisesRegex(SubscriptionContractError, "component bytes"):
            validate_subscription_documents(manifest, objects_doc)


if __name__ == "__main__":
    unittest.main()
