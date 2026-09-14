#!/usr/bin/env python3
"""Stage a verified MS5 immutable artifact tree for read-only edge imaging."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from ms5.tools.common import canonical_json_bytes
from ms5.tools.kane_fabric_storage import validate_inventory, verify_inventory_files


class EdgeImageError(RuntimeError):
    pass


def load_inventory(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EdgeImageError(f"unable to load storage inventory: {exc}") from exc
    if not isinstance(value, dict):
        raise EdgeImageError("storage inventory must be a JSON object")
    validate_inventory(value)
    return value


def stage_inventory(
    inventory: dict[str, object],
    source_root: Path,
    destination: Path,
) -> Path:
    validate_inventory(inventory)
    source_root = source_root.resolve()
    verify_inventory_files(inventory, source_root)

    destination = destination.resolve()
    if destination.exists():
        raise EdgeImageError(f"destination already exists: {destination}")

    destination.parent.mkdir(parents=True, exist_ok=True)

    stage = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}.stage.",
            dir=destination.parent,
        )
    )
    try:
        for artifact in inventory["artifacts"]:
            relative = Path(str(artifact["path"]))
            source = (source_root / relative).resolve()
            try:
                source.relative_to(source_root)
            except ValueError as exc:
                raise EdgeImageError("artifact escaped source root") from exc

            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)

            with source.open("rb") as src, target.open("xb") as dst:
                shutil.copyfileobj(src, dst, length=64 * 1024)

        metadata = stage / ".kane-fabric-storage-inventory.json"
        metadata.write_bytes(canonical_json_bytes(inventory) + b"\n")

        verify_inventory_files(inventory, stage)
        stage.rename(destination)
    finally:
        if stage.exists():
            shutil.rmtree(stage)

    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inventory", type=Path)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()

    inventory = load_inventory(args.inventory)
    result = stage_inventory(inventory, args.source_root, args.destination)
    print(
        json.dumps(
            {
                "destination": str(result),
                "inventory_sha256": inventory["inventory_sha256"],
                "artifact_count": len(inventory["artifacts"]),
                "status": "staged-and-verified",
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
