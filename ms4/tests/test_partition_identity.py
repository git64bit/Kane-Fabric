from __future__ import annotations

import copy
import unittest

from ms4.tools.kane_fabric_partition import (
    PartitionContractError,
    build_partition_descriptor,
    canonical_json_bytes,
    validate_partition_descriptor,
)


JURISDICTION = {
    "country_code": "US",
    "state_code": "IL",
    "fips_code": "17089",
    "county_key": "kane-county-il",
    "name": "Kane County",
}

SCOPE = {
    "scope_class": "bounded-region",
    "definition": {
        "bounds": ["-88.5000000", "41.7000000", "-88.2000000", "42.0000000"],
        "srs_id": 4326,
    },
}


class PartitionIdentityTests(unittest.TestCase):
    def test_descriptor_is_deterministic_under_mapping_order(self) -> None:
        first = build_partition_descriptor(JURISDICTION, SCOPE, label="Aurora focus")
        second = build_partition_descriptor(
            dict(reversed(list(JURISDICTION.items()))),
            {
                "definition": dict(reversed(list(SCOPE["definition"].items()))),
                "scope_class": "bounded-region",
            },
            label="Aurora focus",
        )
        self.assertEqual(first, second)
        self.assertEqual(canonical_json_bytes(first), canonical_json_bytes(second))

    def test_label_is_not_part_of_partition_identity(self) -> None:
        first = build_partition_descriptor(JURISDICTION, SCOPE, label="Human label A")
        second = build_partition_descriptor(JURISDICTION, SCOPE, label="Human label B")
        self.assertEqual(first["definition_sha256"], second["definition_sha256"])
        self.assertEqual(first["partition_key"], second["partition_key"])
        self.assertNotEqual(canonical_json_bytes(first), canonical_json_bytes(second))

    def test_physical_placement_metadata_cannot_enter_identity(self) -> None:
        for key, value in (
            ("device_id", "esp32-001"),
            ("hostname", "edge-a"),
            ("ssid", "fabric"),
            ("ip_address", "10.20.0.12"),
            ("storage_path", "/sdcard/partition"),
        ):
            scope = copy.deepcopy(SCOPE)
            scope["definition"][key] = value
            with self.subTest(key=key):
                with self.assertRaisesRegex(PartitionContractError, "physical placement"):
                    build_partition_descriptor(JURISDICTION, scope)

    def test_floating_point_scope_values_are_rejected_until_normalized(self) -> None:
        scope = copy.deepcopy(SCOPE)
        scope["definition"]["bounds"] = [-88.5, 41.7, -88.2, 42.0]
        with self.assertRaisesRegex(PartitionContractError, "floating-point"):
            build_partition_descriptor(JURISDICTION, scope)

    def test_descriptor_tampering_fails_validation(self) -> None:
        descriptor = build_partition_descriptor(JURISDICTION, SCOPE)
        descriptor["scope"]["definition"]["bounds"][0] = "-88.6000000"
        with self.assertRaisesRegex(PartitionContractError, "definition_sha256"):
            validate_partition_descriptor(descriptor)

    def test_partition_key_tampering_fails_validation(self) -> None:
        descriptor = build_partition_descriptor(JURISDICTION, SCOPE)
        descriptor["partition_key"] = "kfp1-00000000000000000000000000000000"
        with self.assertRaisesRegex(PartitionContractError, "partition_key"):
            validate_partition_descriptor(descriptor)

    def test_kane_county_fixed_vector(self) -> None:
        descriptor = build_partition_descriptor(JURISDICTION, SCOPE)
        self.assertEqual(
            descriptor["definition_sha256"],
            "f8951b5ef606d63b15e3110d93a8905b90d7a0b7c5aef0197d8469cd6e62788a",
        )
        self.assertEqual(
            descriptor["partition_key"],
            "kfp1-f8951b5ef606d63b15e3110d93a8905b",
        )

    def test_contract_is_not_kane_county_specific(self) -> None:
        descriptor = build_partition_descriptor(
            {
                "country_code": "US",
                "state_code": "WI",
                "fips_code": "55025",
                "county_key": "dane-county-wi",
                "name": "Dane County",
            },
            {
                "scope_class": "whole-jurisdiction",
                "definition": {"jurisdiction": True},
            },
        )
        self.assertTrue(descriptor["partition_key"].startswith("kfp1-"))
        validate_partition_descriptor(descriptor)


if __name__ == "__main__":
    unittest.main()
