#!/usr/bin/env python3
"""Compile and validate Milestone 3 release evidence from accepted CT102 artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

EXPECTED_DATABASE_SHA256 = "31e362b696a37f1b9c45ae355c5669511a3128c17a651108a62e20d1cedebd67"
EXPECTED_SUBSTRATE_CONTENT_SHA256 = "fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc"
EXPECTED_EVIDENCE_SHA256 = {
    "ms3-007-substrate-proof.json": "8093011b62d169388cbe264bc7cb4b7b9903d56e2f768c0249dc26107ed7680c",
    "ms3-008-browser-proof.json": "42339593d8598dda52ec61356177837ce2a9152809b6620d62c510ca7d87fcd5",
    "ms3-009-browser-render-proof.json": "75c85fff2ba5e56616697b5f31c3442619943673c95e0ba44af0d1772d2e6cc5",
}
EXPECTED_PACKAGE = {
    "county-overview.json": {
        "byte_length": 1670,
        "sha256": "f0995177625e28adc39e0ddd842ea22fbc1935239d6d1f7d54f377edde62e942",
    },
    "roads-lod.kfs": {
        "byte_length": 4014272,
        "sha256": "4c897db58a55961d76e720d3905b57a76fe199f5396c876b57e56ecaeaaee4d2",
    },
    "water-lod.kfs": {
        "byte_length": 3183647,
        "sha256": "dc4786b2904869fc5f910fa0d1b1a5767f1204fda99f34b2745f1ef7088f7f89",
    },
    "substrate-manifest.json": {
        "byte_length": 1797,
        "sha256": "1143324ace2dd7c47ad5f79e0763fdf978be5447527095e9e6f96d46b3fd1d13",
    },
}
EXPECTED_MS3_010_CANDIDATE = "091ee5da40f50a4a018d45604906c037b1a644b8"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} is not a JSON object")
    return value


def require_file(path: Path) -> None:
    if not path.is_file():
        raise RuntimeError(f"required evidence file is missing: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    parser.add_argument("package", type=Path)
    parser.add_argument("evidence_directory", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--candidate-head", required=True)
    args = parser.parse_args()

    require_file(args.database)
    database_sha = sha256_file(args.database)
    if database_sha != EXPECTED_DATABASE_SHA256:
        raise RuntimeError(f"authoritative database SHA-256 changed: {database_sha}")

    actual_names = sorted(path.name for path in args.package.iterdir() if path.is_file())
    expected_names = sorted(EXPECTED_PACKAGE)
    if actual_names != expected_names:
        raise RuntimeError(f"package inventory mismatch: {actual_names}")

    package: dict[str, object] = {}
    total_package_bytes = 0
    for name in expected_names:
        path = args.package / name
        expected = EXPECTED_PACKAGE[name]
        actual_size = path.stat().st_size
        actual_sha = sha256_file(path)
        if actual_size != expected["byte_length"] or actual_sha != expected["sha256"]:
            raise RuntimeError(f"package component identity mismatch: {name}")
        package[name] = {"byte_length": actual_size, "sha256": actual_sha}
        total_package_bytes += actual_size

    if total_package_bytes != 7201386:
        raise RuntimeError(f"unexpected package byte length: {total_package_bytes}")

    manifest = load_json(args.package / "substrate-manifest.json")
    if manifest.get("substrate_content_sha256") != EXPECTED_SUBSTRATE_CONTENT_SHA256:
        raise RuntimeError("manifest substrate content identity changed")

    evidence: dict[str, object] = {}
    for name, expected_sha in EXPECTED_EVIDENCE_SHA256.items():
        path = args.evidence_directory / name
        require_file(path)
        actual_sha = sha256_file(path)
        if actual_sha != expected_sha:
            raise RuntimeError(f"accepted evidence identity changed: {name}: {actual_sha}")
        load_json(path)
        evidence[name] = {"sha256": actual_sha}

    edge_path = args.evidence_directory / "ms3-010-edge-compatibility-proof.json"
    require_file(edge_path)
    edge = load_json(edge_path)
    edge_sha = sha256_file(edge_path)
    if edge.get("format") != "kane-fabric-ms3-edge-compatibility-proof":
        raise RuntimeError("MS3-010 evidence format is invalid")
    if edge.get("candidate_head") != EXPECTED_MS3_010_CANDIDATE:
        raise RuntimeError("MS3-010 candidate head is unexpected")
    if edge.get("database_sha256") != EXPECTED_DATABASE_SHA256:
        raise RuntimeError("MS3-010 database identity is invalid")
    if edge.get("substrate_content_sha256") != EXPECTED_SUBSTRATE_CONTENT_SHA256:
        raise RuntimeError("MS3-010 substrate identity is invalid")
    edge_contract = edge.get("edge_contract")
    if not isinstance(edge_contract, dict):
        raise RuntimeError("MS3-010 edge contract is missing")
    if edge_contract.get("completed_esp_idf_firmware") is not False:
        raise RuntimeError("MS3-010 must not claim completed ESP-IDF firmware")
    if edge_contract.get("final_http_contract_deferred_to_milestone_5") is not True:
        raise RuntimeError("MS3-010 must preserve Milestone 5 final HTTP contract boundary")
    if edge_contract.get("whole_kfs_residency_required") is not False:
        raise RuntimeError("MS3-010 does not prove bounded component serving")
    evidence[edge_path.name] = {"sha256": edge_sha}

    proof = {
        "authoritative_database": {
            "path": str(args.database),
            "sha256": database_sha,
        },
        "candidate_head": args.candidate_head,
        "evidence": evidence,
        "format": "kane-fabric-milestone-3-release-proof",
        "milestone": 3,
        "package": {
            "components": package,
            "directory": str(args.package),
            "file_count": len(package),
            "total_byte_length": total_package_bytes,
        },
        "release_status": "accepted",
        "substrate_content_sha256": EXPECTED_SUBSTRATE_CONTENT_SHA256,
        "version": 1,
    }

    payload = canonical_bytes(proof)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name("." + args.output.name + ".tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, args.output)

    print(json.dumps({
        "database_sha256": database_sha,
        "evidence": evidence,
        "release_evidence_sha256": hashlib.sha256(payload).hexdigest(),
        "status": "milestone-3-closeout-passed",
        "substrate_content_sha256": EXPECTED_SUBSTRATE_CONTENT_SHA256,
        "total_package_byte_length": total_package_bytes,
    }, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
