#!/usr/bin/env bash
set -euo pipefail

ROOT=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

fail() {
    printf 'MS5_009_REPOSITORY_ACCEPTANCE=FAIL reason=%s\n' "$*" >&2
    exit 1
}

[[ "$(git rev-parse --show-toplevel)" == "$ROOT" ]] || fail "unexpected repository root"
[[ "$(git branch --show-current)" == "main" ]] || fail "checkout is not on main"
[[ "$(git config --get branch.main.remote)" == "origin" ]] || fail "main does not track origin"
[[ "$(git config --get branch.main.merge)" == "refs/heads/main" ]] || fail "main upstream is not origin/main"
[[ "$(git status --porcelain)" == "" ]] || fail "worktree is not clean"

LOCAL_HEAD=$(git rev-parse HEAD)
ORIGIN_HEAD=$(git rev-parse origin/main)
[[ "$LOCAL_HEAD" == "$ORIGIN_HEAD" ]] || fail "local main is not exactly origin/main"

printf '%s\n' '--- MS5 authority/dependency gates ---'
python3 development/check-ms5-work-sequence-authority.py
python3 development/check-dependency-policy.py

printf '%s\n' '--- Python syntax gate ---'
python3 -m compileall -q ms5

printf '%s\n' '--- focused MS5-009 contract gates ---'
python3 -m unittest     ms5.tests.test_firmware_authority     ms5.tests.test_firmware_lifecycle     ms5.tests.test_firmware_authorization     ms5.tests.test_firmware_update_descriptor     ms5.tests.test_esp32_reference     -v

printf '%s\n' '--- complete MS5 repository suite ---'
bash ms5/run-tests.sh

printf '%s\n' '--- frozen decision/lifecycle assertions ---'
python3 - <<'PY'
import json
from pathlib import Path

decision = json.loads(
    Path("ms5/management-transport-decision.json").read_text(encoding="utf-8")
)
lifecycle = json.loads(
    Path("ms5/firmware-lifecycle-contract.json").read_text(encoding="utf-8")
)
authorization = json.loads(
    Path("ms5/firmware-authorization-contract.json").read_text(encoding="utf-8")
)
authority = json.loads(
    Path("ms5/firmware_authority/authority-state.json").read_text(encoding="utf-8")
)
third_party = json.loads(
    Path("third_party/manifest.json").read_text(encoding="utf-8")
)

if decision.get("work_item") != "MS5-008" or decision.get("outcome") != "defer":
    raise SystemExit("MS5-008 decision is not frozen to defer")
if decision.get("retained") is not False:
    raise SystemExit("MS5-008 transport unexpectedly retained")

wireguard = [
    item
    for item in third_party.get("third_party", [])
    if isinstance(item, dict) and "wireguard" in str(item.get("key", "")).lower()
]
if wireguard:
    raise SystemExit("WireGuard unexpectedly present in third_party/manifest.json")

if lifecycle.get("work_item") != "MS5-009":
    raise SystemExit("firmware lifecycle contract is not MS5-009")
if lifecycle.get("status") != "contract-active-signing-inert":
    raise SystemExit("MS5-009 lifecycle status drifted")

authority_boundary = lifecycle.get("authority_boundary", {})
if authority_boundary.get("signature_envelope_status") != "frozen":
    raise SystemExit("firmware signature envelope is not frozen")
if authority_boundary.get("authorization_target") != "firmware_authorization_payload_sha256":
    raise SystemExit("firmware authorization target drifted")
if authority_boundary.get("signing_activation_status") != "not-activated":
    raise SystemExit("release signing unexpectedly activated")

if authorization.get("signature_algorithm") != "ecdsa-p256-sha256":
    raise SystemExit("authorization signature algorithm drifted")
if authorization.get("signature_encoding") != "p1363-r-s-64":
    raise SystemExit("authorization signature encoding drifted")
if authorization.get("authorization_payload_bytes") != 152:
    raise SystemExit("authorization payload size drifted")

if authority.get("private_signing_key_created") is not False:
    raise SystemExit("Firmware Authority unexpectedly records a private signing key")
if authority.get("signing_enabled") is not False:
    raise SystemExit("Firmware Authority unexpectedly records signing enabled")

print("ms5_008_outcome=defer")
print("wireguard_retained=NO")
print("ms5_009_status=" + lifecycle["status"])
print("ms5_009_contract_sha256=" + lifecycle["contract_sha256"])
print("authorization_target=" + authority_boundary["authorization_target"])
print("authorization_algorithm=" + authorization["signature_algorithm"])
print("authorization_payload_bytes=" + str(authorization["authorization_payload_bytes"]))
print("firmware_authority_private_key_created=NO")
print("firmware_authority_signing_enabled=NO")
PY

[[ "$(git status --porcelain)" == "" ]] || fail "worktree changed during acceptance"

printf 'repository_head=%s\n' "$(git rev-parse HEAD)"
printf 'origin_main_head=%s\n' "$(git rev-parse origin/main)"
printf 'worktree_clean=PASS\n'
printf 'MS5_009_REPOSITORY_ACCEPTANCE=PASS\n'
