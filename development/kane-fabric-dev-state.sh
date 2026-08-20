#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
STATE_FILE="$REPO/docs/CURRENT_STATE.json"
MODE="quick"

if [ "${1:-}" = "--deep" ]; then
  MODE="deep"
elif [ "${1:-}" != "" ]; then
  echo "usage: $0 [--deep]" >&2
  exit 2
fi

python3 - "$REPO" "$STATE_FILE" "$MODE" <<'PY'
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

repo = Path(sys.argv[1]).resolve()
state_file = Path(sys.argv[2]).resolve()
mode = sys.argv[3]


def run(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        list(args),
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(args)}\n{result.stderr.strip()}"
        )
    return result.stdout.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def authority_summary(path: Path) -> dict[str, object]:
    reader = subprocess.run(
        [
            "bash",
            str(repo / "database" / "kane-fabric-read.sh"),
            "authority",
            str(path),
        ],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    result: dict[str, object] = {"exit": reader.returncode}
    if reader.stdout.strip():
        try:
            result["result"] = json.loads(reader.stdout)
        except json.JSONDecodeError:
            result["stdout"] = reader.stdout.strip()
    if reader.stderr.strip():
        result["stderr"] = reader.stderr.strip()
    return result


def current_database_summary(path: Path) -> dict[str, object]:
    summary: dict[str, object] = {
        "path": str(path),
        "exists": path.is_file(),
    }
    if not path.is_file():
        return summary

    summary["byte_length"] = path.stat().st_size

    try:
        connection = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        summary["looks_like_fabric"] = {
            "county",
            "dataset",
            "source_release",
            "schema_migration",
        }.issubset(tables)
        connection.close()
    except sqlite3.Error as exc:
        summary["sqlite_error"] = str(exc)

    if summary.get("looks_like_fabric") is True:
        summary["authority"] = authority_summary(path)

    if mode == "deep":
        summary["sha256"] = sha256_file(path)
        validator = subprocess.run(
            [
                "bash",
                str(repo / "database" / "kane-fabric-db.sh"),
                "validate",
                str(path),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        summary["fabric_validation_exit"] = validator.returncode
        if validator.stdout.strip():
            try:
                summary["fabric_validation"] = json.loads(validator.stdout)
            except json.JSONDecodeError:
                summary["fabric_validation_stdout"] = validator.stdout.strip()
        if validator.stderr.strip():
            summary["fabric_validation_stderr"] = validator.stderr.strip()

    return summary


if not state_file.is_file():
    raise SystemExit(f"ERROR: current-state file missing: {state_file}")

state = json.loads(state_file.read_text(encoding="utf-8"))
recorded_checkout = state["deployment"]["checkout"]
recorded_db = state["operational_state"]["database"]

branch = run("git", "branch", "--show-current")
head = run("git", "rev-parse", "HEAD")
origin = run("git", "remote", "get-url", "origin")
upstream = run("git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", check=False)
status_porcelain = run("git", "status", "--porcelain")
fetch_refspecs = [
    line
    for line in run("git", "config", "--get-all", "remote.origin.fetch", check=False).splitlines()
    if line
]

recorded_head = recorded_checkout.get("last_observed_head")
head_relation = "unknown"
if recorded_head:
    exists = subprocess.run(
        ["git", "cat-file", "-e", f"{recorded_head}^{{commit}}"],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0
    if exists:
        if head == recorded_head:
            head_relation = "exact"
        elif subprocess.run(
            ["git", "merge-base", "--is-ancestor", recorded_head, head],
            cwd=repo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0:
            head_relation = "live-head-ahead-of-recorded"
        elif subprocess.run(
            ["git", "merge-base", "--is-ancestor", head, recorded_head],
            cwd=repo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0:
            head_relation = "live-head-behind-recorded"
        else:
            head_relation = "diverged"

configured_db_path = recorded_db.get("path")
database: dict[str, object]
if configured_db_path:
    database = {
        "configured": current_database_summary(Path(configured_db_path)),
        "discovery_required": False,
    }
else:
    db_root = Path(state["operational_state"]["root"]) / "database"
    candidates = []
    if db_root.is_dir():
        for path in sorted(db_root.glob("*.gpkg")):
            candidates.append(current_database_summary(path))
        for directory in sorted(p for p in db_root.iterdir() if p.is_dir()):
            for path in sorted(directory.glob("*.gpkg")):
                candidates.append(current_database_summary(path))
    database = {
        "configured": None,
        "discovery_required": True,
        "candidate_count": len(candidates),
        "candidates": candidates,
    }

configured = database.get("configured")
authority_readable = True
if isinstance(configured, dict):
    authority = configured.get("authority")
    authority_readable = (
        configured.get("exists") is True
        and configured.get("looks_like_fabric") is True
        and isinstance(authority, dict)
        and authority.get("exit") == 0
        and isinstance(authority.get("result"), dict)
        and authority["result"].get("authority") == "accepted-geographic-state"
    )

checks = {
    "repo_path_matches_recorded": str(repo) == recorded_checkout.get("path"),
    "origin_matches_recorded": origin == recorded_checkout.get("origin"),
    "branch_matches_recorded": branch == recorded_checkout.get("branch"),
    "upstream_matches_recorded": upstream == recorded_checkout.get("upstream"),
    "worktree_clean": not status_porcelain,
    "fetch_refspec_matches_recorded": recorded_checkout.get("fetch_refspec") in fetch_refspecs,
    "configured_database_authority_readable": authority_readable,
}

result = {
    "format": "kane-fabric-dev-state",
    "version": 1,
    "mode": mode,
    "recorded_state": {
        "observed_date": state.get("observed_date"),
        "milestone": state.get("milestone"),
        "accepted_tests": state.get("accepted_tests"),
        "next_safe_action": state.get("next_safe_action"),
    },
    "live": {
        "hostname": os.uname().nodename,
        "repo_path": str(repo),
        "branch": branch,
        "head": head,
        "recorded_head": recorded_head,
        "head_relation": head_relation,
        "origin": origin,
        "upstream": upstream,
        "fetch_refspecs": fetch_refspecs,
        "worktree_clean": not status_porcelain,
        "worktree_changes": status_porcelain.splitlines(),
        "database": database,
    },
    "checks": checks,
    "ready_for_read_only_work": all(checks.values()),
}

print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))

if not checks["repo_path_matches_recorded"]:
    raise SystemExit(3)
if not checks["origin_matches_recorded"]:
    raise SystemExit(4)
if not checks["branch_matches_recorded"]:
    raise SystemExit(5)
if not checks["upstream_matches_recorded"]:
    raise SystemExit(6)
if not checks["worktree_clean"]:
    raise SystemExit(7)
if not checks["fetch_refspec_matches_recorded"]:
    raise SystemExit(8)
if not checks["configured_database_authority_readable"]:
    raise SystemExit(9)
PY
