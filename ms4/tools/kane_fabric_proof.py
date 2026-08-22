#!/usr/bin/env python3
"""Compile the deterministic Kane County MS4 proof publication.

This command reads the authoritative Fabric GeoPackage and the accepted MS3
substrate package read-only. It writes a new proof bundle to an explicit,
previously nonexistent output directory and never promotes geographic state.

The MS3 substrate manifest is authoritative only for the four-file substrate
publication and the releases that publication actually contains. Accepted
geography outside that substrate, including buildings, is resolved from the
authoritative GeoPackage whose full database SHA-256 is pinned below.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from collections.abc import Mapping
from pathlib import Path

from ms4.tools.kane_fabric_partition import (
    build_partition_descriptor,
    canonical_json_bytes,
)
from ms4.tools.kane_fabric_placement import (
    build_placement_plan,
    validate_placement_plan,
)
from ms4.tools.kane_fabric_scope import bounded_region_scope
from ms4.tools.kane_fabric_selection import build_selection_manifest
from ms4.tools.kane_fabric_subscription import (
    build_subscription_documents,
    select_objects_for_partition,
    validate_subscription_documents,
)

FORMAT = "kane-fabric-ms4-composition-manifest"
VERSION = 1
ACCEPTED_DATABASE_SHA256 = "31e362b696a37f1b9c45ae355c5669511a3128c17a651108a62e20d1cedebd67"
ACCEPTED_SUBSTRATE_SHA256 = "fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc"
ACCEPTED_COMPONENTS = {
    "county-overview.json": (
        1670,
        "f0995177625e28adc39e0ddd842ea22fbc1935239d6d1f7d54f377edde62e942",
    ),
    "roads-lod.kfs": (
        4014272,
        "4c897db58a55961d76e720d3905b57a76fe199f5396c876b57e56ecaeaaee4d2",
    ),
    "water-lod.kfs": (
        3183647,
        "dc4786b2904869fc5f910fa0d1b1a5767f1204fda99f34b2745f1ef7088f7f89",
    ),
    "substrate-manifest.json": (
        1797,
        "1143324ace2dd7c47ad5f79e0763fdf978be5447527095e9e6f96d46b3fd1d13",
    ),
}
PROOF_PARTITION_BOUNDS = {
    "west": [-88.60, 41.60, -88.295, 42.20],
    "east": [-88.305, 41.60, -88.00, 42.20],
}


class ProofError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_canonical_json(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ProofError(f"{path} is invalid JSON: {exc}") from exc
    if not isinstance(value, dict) or canonical_json_bytes(value) != data:
        raise ProofError(f"{path} is not canonical JSON")
    return value


def write_json(path: Path, value: object) -> dict[str, object]:
    data = canonical_json_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {
        "path": path.name,
        "byte_length": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def verify_ms3_package(package_dir: Path) -> dict[str, object]:
    package_dir = package_dir.resolve()
    for name, (expected_length, expected_sha) in ACCEPTED_COMPONENTS.items():
        path = package_dir / name
        if not path.is_file():
            raise ProofError(f"accepted MS3 component is missing: {path}")
        actual_length = path.stat().st_size
        actual_sha = sha256_file(path)
        if (actual_length, actual_sha) != (expected_length, expected_sha):
            raise ProofError(
                f"accepted MS3 component identity mismatch for {name}: "
                f"length={actual_length} sha256={actual_sha}"
            )
    manifest = read_canonical_json(package_dir / "substrate-manifest.json")
    if manifest.get("substrate_content_sha256") != ACCEPTED_SUBSTRATE_SHA256:
        raise ProofError("MS3 substrate content identity is not the accepted release")
    return manifest


def accepted_release_map(manifest: Mapping[str, object]) -> dict[str, dict[str, object]]:
    """Return release identities carried by the accepted MS3 substrate manifest."""

    releases = manifest.get("accepted_releases")
    if not isinstance(releases, list):
        raise ProofError("MS3 accepted release inventory is invalid")
    result: dict[str, dict[str, object]] = {}
    for item in releases:
        if not isinstance(item, dict) or not isinstance(item.get("dataset_key"), str):
            raise ProofError("MS3 accepted release entry is invalid")
        dataset_key = str(item["dataset_key"])
        if dataset_key in result:
            raise ProofError(f"MS3 accepted release inventory duplicates {dataset_key}")
        result[dataset_key] = dict(item)
    return result


def select_authoritative_building(
    database: Path,
    expected_release: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Select one deterministic persistent building from accepted DB geography.

    ``expected_release`` is an optional independent cross-check. It is not
    required for discovery because buildings are deliberately outside the MS3
    four-file substrate publication.
    """

    connection = sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute(
            "SELECT pb.building_key, sb.source_feature_id, "
            "sb.min_x, sb.min_y, sb.max_x, sb.max_y, "
            "sb.geometry_sha256, sr.release_key, sr.content_sha256 "
            "FROM project_building pb "
            "JOIN source_building sb "
            "ON sb.source_building_id = pb.created_from_source_building_id "
            "JOIN source_release sr "
            "ON sr.source_release_id = sb.source_release_id "
            "JOIN dataset d ON d.dataset_id = sr.dataset_id "
            "WHERE pb.lifecycle_status = 'active' "
            "AND sr.lifecycle_status = 'accepted' "
            "AND d.dataset_key = 'buildings' "
            "AND sb.max_x >= -88.305 AND sb.min_x <= -88.295 "
            "AND sb.max_y >= 41.60 AND sb.min_y <= 42.20 "
            "ORDER BY ABS(((sb.min_x + sb.max_x) / 2.0) + 88.300), "
            "ABS(((sb.min_y + sb.max_y) / 2.0) - 41.880), "
            "pb.building_key LIMIT 1"
        ).fetchone()
    except sqlite3.Error as exc:
        raise ProofError(f"authoritative building query failed: {exc}") from exc
    finally:
        connection.close()

    if row is None:
        raise ProofError(
            "no accepted persistent building identity crosses the MS4 proof overlap"
        )

    result = dict(row)
    if expected_release is not None:
        if result["release_key"] != expected_release.get("release_key"):
            raise ProofError(
                "proof building release_key disagrees with expected accepted release inventory"
            )
        if result["content_sha256"] != expected_release.get("content_sha256"):
            raise ProofError(
                "proof building release content identity disagrees with expected accepted inventory"
            )

    bounds = [result[key] for key in ("min_x", "min_y", "max_x", "max_y")]
    if any(value is None for value in bounds):
        raise ProofError("proof building has null bounds")
    return result


def building_release_identity(building: Mapping[str, object]) -> dict[str, object]:
    return {
        "dataset_key": "buildings",
        "release_key": str(building["release_key"]),
        "content_sha256": str(building["content_sha256"]),
    }


def fabric_reference(building: Mapping[str, object]) -> dict[str, str]:
    return {
        "kind": "building",
        "dataset_key": "buildings",
        "release_key": str(building["release_key"]),
        "source_content_sha256": str(building["content_sha256"]),
        "object_key": str(building["building_key"]),
    }


def _subscription_spec(
    key: str,
) -> tuple[dict[str, str], dict[str, str], dict[str, object]]:
    if key == "condo":
        return (
            {"application_key": "condo-proof", "name": "Condo proof subscription"},
            {"license": "proof-only", "owner": "Condo proof application"},
            {
                "proof_kind": "condo-building-association",
                "unit_label": "proof-unit-a",
            },
        )
    if key == "industry":
        return (
            {
                "application_key": "industry-proof",
                "name": "Industry / Mechanical Compiler proof subscription",
            },
            {"license": "proof-only", "owner": "Industry proof application"},
            {
                "proof_kind": "industry-site-capability",
                "capabilities": ["fabrication"],
                "synthetic_contract_shape": True,
            },
        )
    raise ProofError(f"unknown proof subscription key: {key}")


def compile_into(
    database: Path,
    package_dir: Path,
    output_dir: Path,
) -> dict[str, object]:
    database = database.resolve()
    package_dir = package_dir.resolve()

    database_sha_before = sha256_file(database)
    if database_sha_before != ACCEPTED_DATABASE_SHA256:
        raise ProofError(
            f"authoritative database SHA-256 {database_sha_before} "
            "is not the accepted MS4 baseline"
        )

    substrate_manifest = verify_ms3_package(package_dir)
    jurisdiction = substrate_manifest.get("jurisdiction")
    if not isinstance(jurisdiction, dict):
        raise ProofError("accepted substrate jurisdiction is invalid")

    # The MS3 manifest binds the substrate releases only. Buildings are accepted
    # geography outside the substrate and therefore come from the pinned
    # authoritative GeoPackage.
    accepted = accepted_release_map(substrate_manifest)
    building = select_authoritative_building(database)
    database_building_release = building_release_identity(building)
    manifest_building_release = accepted.get("buildings")
    if manifest_building_release is not None:
        if (
            manifest_building_release.get("release_key")
            != database_building_release["release_key"]
            or manifest_building_release.get("content_sha256")
            != database_building_release["content_sha256"]
        ):
            raise ProofError(
                "MS3 manifest buildings identity conflicts with accepted database geography"
            )
    accepted["buildings"] = database_building_release

    partitions = {
        name: build_partition_descriptor(
            jurisdiction,
            bounded_region_scope(bounds),
            label=f"MS4 Kane County proof {name} partition",
        )
        for name, bounds in PROOF_PARTITION_BOUNDS.items()
    }

    building_bounds = [
        building[key] for key in ("min_x", "min_y", "max_x", "max_y")
    ]
    reference = fabric_reference(building)
    authoritative_object_keys = {"buildings": {str(building["building_key"])}}

    partition_entries: list[dict[str, object]] = []
    for name, descriptor in partitions.items():
        descriptor_path = output_dir / "partitions" / f"{name}.json"
        descriptor_meta = write_json(descriptor_path, descriptor)

        selection = build_selection_manifest(package_dir, descriptor)
        selection_path = output_dir / "selections" / f"{name}.json"
        selection_meta = write_json(selection_path, selection)

        partition_entries.append(
            {
                "name": name,
                "partition_key": descriptor["partition_key"],
                "descriptor_path": f"partitions/{name}.json",
                "descriptor_sha256": descriptor_meta["sha256"],
                "selection_path": f"selections/{name}.json",
                "selection_sha256": selection_meta["sha256"],
            }
        )

    subscription_entries: list[dict[str, object]] = []
    generation_keys: list[str] = []

    for key in ("condo", "industry"):
        owner, rights, payload = _subscription_spec(key)
        manifest, objects_doc = build_subscription_documents(
            subscription_key=key,
            owner=owner,
            jurisdiction=jurisdiction,
            substrate_content_sha256=ACCEPTED_SUBSTRATE_SHA256,
            coverage_partitions=list(partitions.values()),
            rights=rights,
            objects=[
                {
                    "object_key": (
                        f"{key}-proof-{str(building['building_key'])[-16:]}"
                    ),
                    "bounds": building_bounds,
                    "geographic_refs": [reference],
                    "payload": payload,
                }
            ],
        )

        validate_subscription_documents(
            manifest,
            objects_doc,
            partition_descriptors=list(partitions.values()),
            accepted_releases=accepted,
            authoritative_object_keys=authoritative_object_keys,
        )

        for descriptor in partitions.values():
            selected = select_objects_for_partition(
                descriptor,
                manifest,
                objects_doc,
            )
            if len(selected) != 1:
                raise ProofError(
                    f"{key} proof object is not selected exactly once "
                    "by every proof partition"
                )

        subdir = output_dir / "subscriptions" / key
        manifest_meta = write_json(
            subdir / "subscription-manifest.json",
            manifest,
        )
        objects_meta = write_json(subdir / "objects.json", objects_doc)

        generation_keys.append(str(manifest["generation_key"]))
        subscription_entries.append(
            {
                "subscription_key": key,
                "generation_key": manifest["generation_key"],
                "manifest_path": (
                    f"subscriptions/{key}/subscription-manifest.json"
                ),
                "manifest_sha256": manifest_meta["sha256"],
                "objects_path": f"subscriptions/{key}/objects.json",
                "objects_sha256": objects_meta["sha256"],
            }
        )

    placement_a = build_placement_plan(
        partition_key=str(partitions["west"]["partition_key"]),
        substrate_content_sha256=ACCEPTED_SUBSTRATE_SHA256,
        subscription_generation_keys=generation_keys,
        physical={
            "node_label": "proof-node-a",
            "storage_path": "/media/proof-a",
            "network_hint": "10.0.0.1",
        },
    )
    placement_b = build_placement_plan(
        partition_key=str(partitions["west"]["partition_key"]),
        substrate_content_sha256=ACCEPTED_SUBSTRATE_SHA256,
        subscription_generation_keys=generation_keys,
        physical={
            "node_label": "proof-node-b",
            "storage_path": "/media/proof-b",
            "network_hint": "10.0.0.2",
        },
    )
    validate_placement_plan(placement_a)
    validate_placement_plan(placement_b)
    if (
        placement_a["logical_content_sha256"]
        != placement_b["logical_content_sha256"]
    ):
        raise ProofError(
            "physical relocation changed MS4 logical placement identity"
        )

    write_json(output_dir / "placements" / "node-a.json", placement_a)
    write_json(output_dir / "placements" / "node-b.json", placement_b)

    database_sha_after = sha256_file(database)
    if database_sha_after != database_sha_before:
        raise ProofError(
            "authoritative database bytes changed during read-only "
            "MS4 proof compilation"
        )

    body = {
        "format": FORMAT,
        "version": VERSION,
        "jurisdiction": jurisdiction,
        "substrate_content_sha256": ACCEPTED_SUBSTRATE_SHA256,
        "source_database_sha256": database_sha_before,
        "proof_building": {
            "building_key": building["building_key"],
            "source_feature_id": building["source_feature_id"],
            "geometry_sha256": building["geometry_sha256"],
            "bounds": [str(value) for value in building_bounds],
            "release_key": building["release_key"],
            "release_content_sha256": building["content_sha256"],
        },
        "partitions": partition_entries,
        "subscriptions": subscription_entries,
        "edge_placement_logical_sha256": placement_a[
            "logical_content_sha256"
        ],
    }
    composition_sha = hashlib.sha256(canonical_json_bytes(body)).hexdigest()
    composition = {**body, "composition_sha256": composition_sha}
    write_json(output_dir / "composition-manifest.json", composition)
    return composition


def compile_proof(
    database: Path,
    package_dir: Path,
    output_dir: Path,
) -> dict[str, object]:
    """Build into a sibling staging directory and publish by atomic rename."""

    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise ProofError(f"proof output already exists: {output_dir}")

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(
            prefix=f".{output_dir.name}.stage-",
            dir=output_dir.parent,
        )
    )

    try:
        composition = compile_into(database, package_dir, stage)
        os.replace(stage, output_dir)
        return composition
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    result = compile_proof(
        args.database,
        args.package_dir,
        args.output_dir,
    )
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
