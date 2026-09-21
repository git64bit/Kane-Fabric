#!/usr/bin/env bash
set -euo pipefail

EXPECTED_HOST="fw"
EXPECTED_USER="cpe-build"
EXPECTED_REPO="https://github.com/git64bit/Kane-Fabric.git"
EXPECTED_IDF_HEAD="76f5dedd9950a3012fee8fb7d5586df21fc67802"

ROOT=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
PROJECT="$ROOT/ms5/esp32_reference"
BUILD="/home/cpe-build/build/Kane-Fabric-ms5-009-esp32_reference"
EVIDENCE="/home/cpe-build/evidence/Kane-Fabric/ms5-009"
CPE_ENV="/home/cpe-build/.config/cpe/env.sh"

fail() {
    printf 'MS5_009_FW_BUILD_ACCEPTANCE=FAIL reason=%s\n' "$*" >&2
    exit 1
}

[[ "$(hostname -s)" == "$EXPECTED_HOST" ]] || fail "must run on fw"
[[ "$(id -un)" == "$EXPECTED_USER" ]] || fail "must run as cpe-build"
[[ "$(git -C "$ROOT" rev-parse --show-toplevel)" == "$ROOT" ]] || fail "unexpected repository root"
[[ "$(git -C "$ROOT" branch --show-current)" == "main" ]] || fail "checkout is not on main"
[[ "$(git -C "$ROOT" remote get-url origin)" == "$EXPECTED_REPO" ]] || fail "origin mismatch"
[[ "$(git -C "$ROOT" status --porcelain)" == "" ]] || fail "worktree is not clean"
[[ "$(git -C "$ROOT" rev-parse HEAD)" == "$(git -C "$ROOT" rev-parse origin/main)" ]] || fail "local main is not exactly origin/main"

[[ -f "$CPE_ENV" ]] || fail "CPE environment file missing"
# shellcheck disable=SC1090
source "$CPE_ENV"
[[ -n "${IDF_PATH:-}" ]] || fail "IDF_PATH not set"
# shellcheck disable=SC1090
source "$IDF_PATH/export.sh" >/dev/null

[[ "$(git -C "$IDF_PATH" rev-parse HEAD)" == "$EXPECTED_IDF_HEAD" ]] || fail "ESP-IDF commit drift"
command -v idf.py >/dev/null 2>&1 || fail "idf.py unavailable"

mkdir -p "$EVIDENCE"
rm -rf "$BUILD"

printf 'repository_head=%s\n' "$(git -C "$ROOT" rev-parse HEAD)"
printf 'esp_idf_head=%s\n' "$(git -C "$IDF_PATH" rev-parse HEAD)"
printf 'project=%s\n' "$PROJECT"
printf 'build_dir=%s\n' "$BUILD"

idf.py -C "$PROJECT" -B "$BUILD" build

APP_BIN="$BUILD/kane_fabric_ms5_edge_reference.bin"
PARTITION_BIN="$BUILD/partition_table/partition-table.bin"
SDKCONFIG="$BUILD/config/sdkconfig.h"
SDKCONFIG_TEXT="$BUILD/sdkconfig"

[[ -f "$APP_BIN" ]] || fail "application binary missing"
[[ -f "$PARTITION_BIN" ]] || fail "generated partition table missing"
[[ -f "$SDKCONFIG" ]] || fail "generated sdkconfig header missing"
[[ -f "$SDKCONFIG_TEXT" ]] || fail "generated sdkconfig missing"

APP_BYTES=$(wc -c < "$APP_BIN" | tr -d ' ')
APP_SHA256=$(sha256sum "$APP_BIN" | awk '{print $1}')
PARTITION_SHA256=$(sha256sum "$PARTITION_BIN" | awk '{print $1}')

[[ "$APP_BYTES" -le 1048576 ]] || fail "application exceeds 1 MiB application slot"

grep -Fxq 'CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE=y' "$SDKCONFIG_TEXT" ||     fail "bootloader app rollback is not enabled"
if grep -Fxq 'CONFIG_BOOTLOADER_APP_ANTI_ROLLBACK=y' "$SDKCONFIG_TEXT"; then
    fail "irreversible anti-rollback unexpectedly enabled"
fi

PARTITION_CSV="$PROJECT/partitions.fabric-4m.csv"
grep -Eq '^factory,[[:space:]]+app,[[:space:]]+factory,[[:space:]]+0x10000,[[:space:]]+1M,' "$PARTITION_CSV" ||     fail "factory partition moved or resized"
grep -Eq '^fabric,[[:space:]]+data,[[:space:]]+fat,[[:space:]]+0x110000,[[:space:]]+4M,' "$PARTITION_CSV" ||     fail "Fabric partition moved or resized"
grep -Eq '^otadata,[[:space:]]+data,[[:space:]]+ota,[[:space:]]+0x510000,[[:space:]]+8K,' "$PARTITION_CSV" ||     fail "otadata partition mismatch"
grep -Eq '^ota_0,[[:space:]]+app,[[:space:]]+ota_0,[[:space:]]+0x520000,[[:space:]]+1M,' "$PARTITION_CSV" ||     fail "ota_0 partition mismatch"
grep -Eq '^ota_1,[[:space:]]+app,[[:space:]]+ota_1,[[:space:]]+0x620000,[[:space:]]+1M,' "$PARTITION_CSV" ||     fail "ota_1 partition mismatch"

python3 "$IDF_PATH/components/partition_table/gen_esp32part.py"     "$PARTITION_BIN"     "$EVIDENCE/generated-partition-table.csv"

grep -Eq '^factory,[[:space:]]+0x00,[[:space:]]+0x00,[[:space:]]+0x00010000,[[:space:]]+0x00100000'     "$EVIDENCE/generated-partition-table.csv" || fail "generated factory partition mismatch"
grep -Eq '^fabric,[[:space:]]+0x01,[[:space:]]+0x81,[[:space:]]+0x00110000,[[:space:]]+0x00400000'     "$EVIDENCE/generated-partition-table.csv" || fail "generated Fabric partition mismatch"
grep -Eq '^otadata,[[:space:]]+0x01,[[:space:]]+0x00,[[:space:]]+0x00510000,[[:space:]]+0x00002000'     "$EVIDENCE/generated-partition-table.csv" || fail "generated otadata partition mismatch"
grep -Eq '^ota_0,[[:space:]]+0x00,[[:space:]]+0x10,[[:space:]]+0x00520000,[[:space:]]+0x00100000'     "$EVIDENCE/generated-partition-table.csv" || fail "generated ota_0 partition mismatch"
grep -Eq '^ota_1,[[:space:]]+0x00,[[:space:]]+0x11,[[:space:]]+0x00620000,[[:space:]]+0x00100000'     "$EVIDENCE/generated-partition-table.csv" || fail "generated ota_1 partition mismatch"

idf.py -C "$PROJECT" -B "$BUILD" size > "$EVIDENCE/idf-size.txt"

cp "$SDKCONFIG_TEXT" "$EVIDENCE/sdkconfig.effective"
sha256sum "$APP_BIN" "$PARTITION_BIN" "$SDKCONFIG_TEXT" > "$EVIDENCE/build-artifact-sha256.txt"

[[ "$(git -C "$ROOT" status --porcelain)" == "" ]] || fail "repository worktree changed during build"

printf 'application_bytes=%s\n' "$APP_BYTES"
printf 'application_sha256=%s\n' "$APP_SHA256"
printf 'partition_table_sha256=%s\n' "$PARTITION_SHA256"
printf 'rollback_enabled=PASS\n'
printf 'anti_rollback_efuse_required=NO\n'
printf 'factory_partition_preserved=PASS\n'
printf 'fabric_partition_preserved=PASS\n'
printf 'ota_partition_plan=PASS\n'
printf 'device_flashed=NO\n'
printf 'worktree_clean=PASS\n'
printf 'evidence_dir=%s\n' "$EVIDENCE"
printf 'MS5_009_FW_BUILD_ACCEPTANCE=PASS\n'
