#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import struct
import sys
import unittest
from pathlib import Path


def load_contract_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "kane_fabric_substrate.py"
    )
    spec = importlib.util.spec_from_file_location(
        "_kane_fabric_substrate_contract", module_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load substrate contract: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


contract = load_contract_module()

JURISDICTION = {
    "country_code": "US",
    "state_code": "IL",
    "fips_code": "17089",
    "county_key": "kane-county",
    "name": "Kane County",
}


class SubstrateContractTests(unittest.TestCase):
    def test_magic_values_are_eight_bytes(self):
        self.assertEqual(contract.ROAD_MAGIC, b"KFSR001\n")
        self.assertEqual(contract.WATER_MAGIC, b"KFSW001\n")
        self.assertEqual(len(contract.ROAD_MAGIC), 8)
        self.assertEqual(len(contract.WATER_MAGIC), 8)

    def test_canonical_json_fixed_vector(self):
        value = {"z": 1, "a": ["Kane", 2, False], "u": "é"}
        data = contract.canonical_json_bytes(value)
        self.assertEqual(
            data,
            b'{"a":["Kane",2,false],"u":"\xc3\xa9","z":1}',
        )
        self.assertEqual(
            contract.sha256_bytes(data),
            "92f4f7190bf0f8e73b11c6090ccef972f635a23711115436fb48f782725ff287",
        )

    def test_jurisdiction_validation(self):
        self.assertEqual(
            contract.validate_jurisdiction(JURISDICTION),
            JURISDICTION,
        )

        bad = dict(JURISDICTION)
        bad["fips_code"] = "1708"
        with self.assertRaises(contract.SubstrateContractError):
            contract.validate_jurisdiction(bad)

    def test_container_prefix_round_trip(self):
        index = {
            "compression": "zlib-deflate",
            "format": contract.ROAD_FORMAT,
            "jurisdiction": JURISDICTION,
            "levels": [],
            "srs_id": 4326,
            "version": 1,
        }
        data = contract.encode_container_prefix(contract.ROAD_MAGIC, index)
        decoded, payload_start = contract.decode_container_index(
            data,
            expected_magic=contract.ROAD_MAGIC,
            expected_format=contract.ROAD_FORMAT,
        )
        self.assertEqual(decoded, index)
        self.assertEqual(payload_start, len(data))

    def test_noncanonical_index_rejected(self):
        index = {
            "compression": "zlib-deflate",
            "format": contract.ROAD_FORMAT,
            "jurisdiction": JURISDICTION,
            "levels": [],
            "srs_id": 4326,
            "version": 1,
        }
        noncanonical = json.dumps(index, sort_keys=False, indent=1).encode("utf-8")
        data = (
            contract.ROAD_MAGIC
            + struct.pack(">Q", len(noncanonical))
            + noncanonical
        )
        with self.assertRaisesRegex(
            contract.SubstrateContractError,
            "not canonical",
        ):
            contract.decode_container_index(
                data,
                expected_magic=contract.ROAD_MAGIC,
                expected_format=contract.ROAD_FORMAT,
            )

    def test_truncated_index_rejected(self):
        data = contract.ROAD_MAGIC + struct.pack(">Q", 10) + b"{}"
        with self.assertRaisesRegex(
            contract.SubstrateContractError,
            "truncated",
        ):
            contract.decode_container_index(
                data,
                expected_magic=contract.ROAD_MAGIC,
                expected_format=contract.ROAD_FORMAT,
            )

    def test_content_identity_fixed_vector(self):
        releases = [
            {
                "dataset_key": "roads",
                "release_key": "r1",
                "content_sha256": "0" * 64,
                "feature_count": 10,
            },
            {
                "dataset_key": "county-boundary",
                "release_key": "b1",
                "content_sha256": "1" * 64,
                "feature_count": 1,
            },
            {
                "dataset_key": "water-fox-river",
                "release_key": "w1",
                "content_sha256": "2" * 64,
                "feature_count": 1,
            },
            {
                "dataset_key": "water-creeks",
                "release_key": "w2",
                "content_sha256": "3" * 64,
                "feature_count": 5,
            },
        ]
        components = [
            {
                "role": "county_overview",
                "path": "county-overview.json",
                "format": contract.OVERVIEW_FORMAT,
                "version": 1,
                "byte_length": 100,
                "sha256": "4" * 64,
            },
            {
                "role": "roads",
                "path": "roads-lod.kfs",
                "format": contract.ROAD_FORMAT,
                "version": 1,
                "byte_length": 200,
                "sha256": "5" * 64,
            },
            {
                "role": "water",
                "path": "water-lod.kfs",
                "format": contract.WATER_FORMAT,
                "version": 1,
                "byte_length": 300,
                "sha256": "6" * 64,
            },
        ]
        expected = (
            "28b4748799c92ba5570bc53a92f1fa968f68a4e8660e3fe6bdcf5e2ffd8023db"
        )

        self.assertEqual(
            contract.compute_substrate_content_sha256(
                JURISDICTION,
                releases,
                components,
            ),
            expected,
        )
        self.assertEqual(
            contract.compute_substrate_content_sha256(
                JURISDICTION,
                list(reversed(releases)),
                components,
            ),
            expected,
        )

    def test_component_order_is_frozen(self):
        releases = [
            {
                "dataset_key": "roads",
                "release_key": "r1",
                "content_sha256": "0" * 64,
                "feature_count": 10,
            },
        ]
        components = [
            {
                "role": "roads",
                "path": "roads-lod.kfs",
                "format": contract.ROAD_FORMAT,
                "version": 1,
                "byte_length": 200,
                "sha256": "5" * 64,
            },
            {
                "role": "county_overview",
                "path": "county-overview.json",
                "format": contract.OVERVIEW_FORMAT,
                "version": 1,
                "byte_length": 100,
                "sha256": "4" * 64,
            },
            {
                "role": "water",
                "path": "water-lod.kfs",
                "format": contract.WATER_FORMAT,
                "version": 1,
                "byte_length": 300,
                "sha256": "6" * 64,
            },
        ]

        with self.assertRaisesRegex(
            contract.SubstrateContractError,
            "component roles",
        ):
            contract.compute_substrate_content_sha256(
                JURISDICTION,
                releases,
                components,
            )


if __name__ == "__main__":
    unittest.main()
