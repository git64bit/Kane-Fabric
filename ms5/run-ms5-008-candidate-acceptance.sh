#!/usr/bin/env bash
set -euo pipefail

ROOT=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

fail() {
    printf 'MS5_008_CANDIDATE_REPOSITORY_ACCEPTANCE=FAIL reason=%s\n' "$*" >&2
    exit 1
}

[[ "$(git rev-parse --show-toplevel)" == "$ROOT" ]] || fail "unexpected repository root"
[[ "$(git branch --show-current)" == "main" ]] || fail "checkout is not on main"
[[ "$(git config --get branch.main.remote)" == "origin" ]] || fail "main does not track origin"
[[ "$(git config --get branch.main.merge)" == "refs/heads/main" ]] || fail "main upstream is not origin/main"
[[ "$(git status --porcelain)" == "" ]] || fail "worktree is not clean"

python3 development/check-ms5-work-sequence-authority.py
python3 development/check-dependency-policy.py
python3 -m compileall -q ms5
python3 -m unittest ms5.tests.test_management_transport_candidate -v
bash ms5/run-tests.sh

python3 - <<'PY'
import json
from pathlib import Path

candidate = json.loads(Path("ms5/management-transport-candidate.json").read_text())
manifest = json.loads(Path("third_party/manifest.json").read_text())

wireguard = [
    item for item in manifest.get("third_party", [])
    if isinstance(item, dict) and "wireguard" in str(item.get("key", "")).lower()
]
if wireguard:
    raise SystemExit("WireGuard unexpectedly present in third_party/manifest.json")

print("candidate_transport=" + candidate["transport"])
print("candidate_version=" + candidate["candidate"]["version"])
print("candidate_commit=" + candidate["candidate"]["source_commit"])
print("candidate_dependency_version=" + candidate["candidate"]["evaluation_dependency_pin"]["version"])
print("candidate_dependency_commit=" + candidate["candidate"]["evaluation_dependency_pin"]["source_commit"])
print("wireguard_retained=NO")
print("decision_state=" + candidate["decision"]["state_before_runtime_evidence"])
PY

printf 'repository_head=%s\n' "$(git rev-parse HEAD)"
printf 'worktree_clean=PASS\n'
printf 'MS5_008_CANDIDATE_REPOSITORY_ACCEPTANCE=PASS\n'
