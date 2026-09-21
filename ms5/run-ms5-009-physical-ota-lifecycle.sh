#!/usr/bin/env bash
set -euo pipefail

EXPECTED_HOST="fw"
EXPECTED_USER="cpe-build"
EXPECTED_REPO="https://github.com/git64bit/Kane-Fabric.git"
EXPECTED_IDF_HEAD="76f5dedd9950a3012fee8fb7d5586df21fc67802"
EXPECTED_PRETEST_FACTORY_SHA256="6e3c2bbcfb77107898bd96210f85bd49d93621ea057739e86c2914a56f554c96"

PROGRAM="/dev/serial/by-path/pci-0000:00:1a.0-usb-0:1.1.2:1.0"
TERMINAL="/dev/serial/by-path/pci-0000:00:1a.0-usb-0:1.1.3:1.0-port0"

FLASH_BYTES=16777216
NVS_OFFSET=0x9000
NVS_SIZE=0x6000
PHY_OFFSET=0xf000
PHY_SIZE=0x1000
FACTORY_OFFSET=0x10000
FACTORY_SIZE=0x100000
FABRIC_OFFSET=0x110000
FABRIC_SIZE=0x400000
OTADATA_OFFSET=0x510000
OTADATA_SIZE=0x2000
OTA0_OFFSET=0x520000
OTA1_OFFSET=0x620000
OTA_SIZE=0x100000
PARTITION_OFFSET=0x8000

ROOT=$(CDPATH= cd -- "$(dirname -- "$BASH_SOURCE")/.." && pwd)
PROJECT="$ROOT/ms5/esp32_reference"
BUILD="/home/cpe-build/build/Kane-Fabric-ms5-009-esp32_reference"
CPE_ENV="/home/cpe-build/.config/cpe/env.sh"
BASE_EVIDENCE="/home/cpe-build/evidence/Kane-Fabric/ms5-009"
RUN_ID=$(date -u +%Y%m%dT%H%M%SZ)
RUN_DIR="$BASE_EVIDENCE/physical-ota-lifecycle-$RUN_ID"

MUTATED=0
FULL_BACKUP="$RUN_DIR/pretest-full-flash.bin"
RESTORE_READBACK="$RUN_DIR/restore-readback-full-flash.bin"

fail() {
    printf 'MS5_009_PHYSICAL_OTA_LIFECYCLE=FAIL reason=%s\n' "$*" >&2
    exit 1
}

[[ "$(hostname -s)" == "$EXPECTED_HOST" ]] || fail "must run on fw"
[[ "$(id -un)" == "$EXPECTED_USER" ]] || fail "must run as cpe-build"
[[ -e "$PROGRAM" ]] || fail "PROGRAM device missing"
[[ -e "$TERMINAL" ]] || fail "TERMINAL device missing"
[[ "$(git -C "$ROOT" rev-parse --show-toplevel)" == "$ROOT" ]] || fail "unexpected repository root"
[[ "$(git -C "$ROOT" branch --show-current)" == "main" ]] || fail "checkout is not on main"
[[ "$(git -C "$ROOT" remote get-url origin)" == "$EXPECTED_REPO" ]] || fail "origin mismatch"
[[ "$(git -C "$ROOT" status --porcelain)" == "" ]] || fail "worktree is not clean"
[[ "$(git -C "$ROOT" rev-parse HEAD)" == "$(git -C "$ROOT" rev-parse origin/main)" ]] || fail "local main is not exactly origin/main"

[[ -f "$CPE_ENV" ]] || fail "CPE environment file missing"
source "$CPE_ENV"
[[ -v IDF_PATH ]] || fail "IDF_PATH not set"
source "$IDF_PATH/export.sh" >/dev/null
[[ "$(git -C "$IDF_PATH" rev-parse HEAD)" == "$EXPECTED_IDF_HEAD" ]] || fail "ESP-IDF commit drift"

PYTHON=$(command -v python)
[[ -n "$PYTHON" ]] || fail "ESP-IDF Python missing"
"$PYTHON" -c 'import serial' || fail "pyserial unavailable in ESP-IDF environment"

mkdir -p "$RUN_DIR"

esptool_cmd() {
    "$PYTHON" -m esptool \
        --chip esp32s3 \
        --port "$PROGRAM" \
        --baud 460800 \
        "$@"
}

start_capture() {
    CAPTURE_LOG="$1"
    CAPTURE_SECONDS="$2"
    "$PYTHON" - "$TERMINAL" "$CAPTURE_SECONDS" "$CAPTURE_LOG" <<'PY' &
import pathlib
import serial
import sys
import time

port = sys.argv[1]
duration = float(sys.argv[2])
output = pathlib.Path(sys.argv[3])

end = time.monotonic() + duration
with serial.Serial(port, 115200, timeout=0.2) as ser, output.open("wb") as fh:
    while time.monotonic() < end:
        data = ser.read(4096)
        if data:
            fh.write(data)
            fh.flush()
PY
    CAPTURE_PID=$!
    sleep 0.5
}

wait_capture() {
    wait "$CAPTURE_PID"
}

make_otadata_entry() {
    BASE_FILE="$1"
    OUTPUT_FILE="$2"
    ENTRY_INDEX="$3"
    ENTRY_SEQ="$4"
    ENTRY_STATE="$5"

    "$PYTHON" - "$BASE_FILE" "$OUTPUT_FILE" "$ENTRY_INDEX" "$ENTRY_SEQ" "$ENTRY_STATE" <<'PY'
import binascii
import pathlib
import struct
import sys

base_path, out_path, index_s, seq_s, state_s = sys.argv[1:]
index = int(index_s, 0)
seq = int(seq_s, 0)
state = int(state_s, 0)

if index not in (0, 1):
    raise SystemExit("invalid otadata entry index")

if base_path == "-":
    data = bytearray(b"\xff" * 0x2000)
else:
    data = bytearray(pathlib.Path(base_path).read_bytes())
    if len(data) != 0x2000:
        raise SystemExit("otadata base must be exactly 0x2000 bytes")

seq_bytes = struct.pack("<I", seq)
crc = binascii.crc32(seq_bytes, 0xFFFFFFFF) & 0xFFFFFFFF
entry = struct.pack("<I20sII", seq, b"\xff" * 20, state, crc)

start = index * 0x1000
data[start:start + len(entry)] = entry
pathlib.Path(out_path).write_bytes(data)
PY
}

clear_second_otadata_sector() {
    BASE_FILE="$1"
    OUTPUT_FILE="$2"
    "$PYTHON" - "$BASE_FILE" "$OUTPUT_FILE" <<'PY'
import pathlib
import sys

data = bytearray(pathlib.Path(sys.argv[1]).read_bytes())
if len(data) != 0x2000:
    raise SystemExit("otadata input must be exactly 0x2000 bytes")
data[0x1000:0x2000] = b"\xff" * 0x1000
pathlib.Path(sys.argv[2]).write_bytes(data)
PY
}

verify_otadata_entry() {
    FILE="$1"
    ENTRY_INDEX="$2"
    EXPECTED_SEQ="$3"
    EXPECTED_STATE="$4"
    "$PYTHON" - "$FILE" "$ENTRY_INDEX" "$EXPECTED_SEQ" "$EXPECTED_STATE" <<'PY'
import binascii
import pathlib
import struct
import sys

path, index_s, seq_s, state_s = sys.argv[1:]
index = int(index_s, 0)
expected_seq = int(seq_s, 0)
expected_state = int(state_s, 0)
data = pathlib.Path(path).read_bytes()
if len(data) != 0x2000:
    raise SystemExit("otadata input must be exactly 0x2000 bytes")

start = index * 0x1000
seq, _label, state, crc = struct.unpack("<I20sII", data[start:start + 32])
expected_crc = binascii.crc32(struct.pack("<I", seq), 0xFFFFFFFF) & 0xFFFFFFFF
print(f"otadata_entry_{index}_seq={seq}")
print(f"otadata_entry_{index}_state={state}")
print(f"otadata_entry_{index}_crc=0x{crc:08x}")

if seq != expected_seq:
    raise SystemExit(f"entry {index} sequence mismatch: {seq} != {expected_seq}")
if state != expected_state:
    raise SystemExit(f"entry {index} state mismatch: {state} != {expected_state}")
if crc != expected_crc:
    raise SystemExit(f"entry {index} CRC mismatch")
PY
}

extract_pretest_regions() {
    "$PYTHON" - "$FULL_BACKUP" "$RUN_DIR" <<'PY'
import pathlib
import sys

source = pathlib.Path(sys.argv[1]).read_bytes()
out = pathlib.Path(sys.argv[2])
if len(source) != 0x1000000:
    raise SystemExit("full flash backup is not 16 MiB")

regions = {
    "pretest-bootloader-region.bin": (0x000000, 0x008000),
    "pretest-partition-table-region.bin": (0x008000, 0x001000),
    "pretest-nvs.bin": (0x009000, 0x006000),
    "pretest-phy-init.bin": (0x00F000, 0x001000),
    "pretest-factory.bin": (0x010000, 0x100000),
    "pretest-fabric.bin": (0x110000, 0x400000),
}
for name, (offset, size) in regions.items():
    (out / name).write_bytes(source[offset:offset + size])
PY
}

restore_pretest_flash() {
    printf '%s\n' '--- automatic predecessor restoration ---' >&2
    esptool_cmd write-flash --flash-size 16MB 0x0 "$FULL_BACKUP" >&2
    esptool_cmd read-flash 0x0 "$FLASH_BYTES" "$RESTORE_READBACK" >&2
    BEFORE=$(sha256sum "$FULL_BACKUP" | awk '{print $1}')
    AFTER=$(sha256sum "$RESTORE_READBACK" | awk '{print $1}')
    printf 'restore_expected_sha256=%s\n' "$BEFORE" >&2
    printf 'restore_readback_sha256=%s\n' "$AFTER" >&2
    if [[ "$BEFORE" == "$AFTER" ]]; then
        printf 'predecessor_full_flash_restore=PASS\n' >&2
    else
        printf 'predecessor_full_flash_restore=FAIL\n' >&2
    fi
}

on_exit() {
    RC=$?
    if [[ "$RC" -ne 0 && "$MUTATED" -eq 1 ]]; then
        set +e
        restore_pretest_flash
        printf 'pretest_backup=%s\n' "$FULL_BACKUP" >&2
        set -e
    fi
    exit "$RC"
}
trap on_exit EXIT

printf 'repository_head=%s\n' "$(git -C "$ROOT" rev-parse HEAD)"
printf 'esp_idf_head=%s\n' "$(git -C "$IDF_PATH" rev-parse HEAD)"
printf 'run_dir=%s\n' "$RUN_DIR"
printf 'program=%s\n' "$PROGRAM"
printf 'terminal=%s\n' "$TERMINAL"

printf '%s\n' '--- exact production build ---'
bash "$ROOT/ms5/run-ms5-009-fw-build-acceptance.sh"

APP_BIN="$BUILD/kane_fabric_ms5_edge_reference.bin"
BOOTLOADER_BIN="$BUILD/bootloader/bootloader.bin"
PARTITION_BIN="$BUILD/partition_table/partition-table.bin"

[[ -f "$APP_BIN" ]] || fail "production app binary missing"
[[ -f "$BOOTLOADER_BIN" ]] || fail "rollback-capable bootloader missing"
[[ -f "$PARTITION_BIN" ]] || fail "partition table binary missing"

APP_BYTES=$(wc -c < "$APP_BIN" | tr -d ' ')
BOOTLOADER_BYTES=$(wc -c < "$BOOTLOADER_BIN" | tr -d ' ')
PARTITION_BYTES=$(wc -c < "$PARTITION_BIN" | tr -d ' ')
APP_SHA=$(sha256sum "$APP_BIN" | awk '{print $1}')
BOOTLOADER_SHA=$(sha256sum "$BOOTLOADER_BIN" | awk '{print $1}')
PARTITION_SHA=$(sha256sum "$PARTITION_BIN" | awk '{print $1}')

printf '%s\n' '--- build deliberate failed-trial image ---'
FAIL_PROJECT="$RUN_DIR/failed-trial-project"
FAIL_BUILD="$RUN_DIR/failed-trial-build"
mkdir -p "$FAIL_PROJECT/main"
cp "$PROJECT/partitions.fabric-4m.csv" "$FAIL_PROJECT/partitions.fabric-4m.csv"

cat > "$FAIL_PROJECT/CMakeLists.txt" <<'EOF'
cmake_minimum_required(VERSION 3.16)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(kane_fabric_ms5_009_failed_trial)
EOF

cat > "$FAIL_PROJECT/sdkconfig.defaults" <<'EOF'
CONFIG_IDF_TARGET="esp32s3"
CONFIG_ESPTOOLPY_FLASHSIZE_16MB=y
CONFIG_PARTITION_TABLE_CUSTOM=y
CONFIG_PARTITION_TABLE_CUSTOM_FILENAME="partitions.fabric-4m.csv"
CONFIG_PARTITION_TABLE_FILENAME="partitions.fabric-4m.csv"
CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE=y
EOF

cat > "$FAIL_PROJECT/main/CMakeLists.txt" <<'EOF'
idf_component_register(
    SRCS "failed_trial.c"
    INCLUDE_DIRS "."
    REQUIRES esp_system freertos log
)
EOF

cat > "$FAIL_PROJECT/main/failed_trial.c" <<'EOF'
#include "esp_log.h"
#include "esp_system.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "ms5-009-failed-trial";

void app_main(void)
{
    ESP_LOGE(TAG, "MS5_009_FORCED_FAILED_TRIAL=START");
    vTaskDelay(pdMS_TO_TICKS(750));
    esp_restart();
}
EOF

idf.py -C "$FAIL_PROJECT" -B "$FAIL_BUILD" -DSDKCONFIG="$FAIL_BUILD/sdkconfig" build
FAIL_APP="$FAIL_BUILD/kane_fabric_ms5_009_failed_trial.bin"
[[ -f "$FAIL_APP" ]] || fail "failed-trial app binary missing"
FAIL_APP_BYTES=$(wc -c < "$FAIL_APP" | tr -d ' ')
[[ "$FAIL_APP_BYTES" -le "$OTA_SIZE" ]] || fail "failed-trial app exceeds OTA slot"
FAIL_APP_SHA=$(sha256sum "$FAIL_APP" | awk '{print $1}')

printf '%s\n' '--- full pre-test flash backup ---'
esptool_cmd read-flash 0x0 "$FLASH_BYTES" "$FULL_BACKUP"
[[ "$(wc -c < "$FULL_BACKUP" | tr -d ' ')" -eq "$FLASH_BYTES" ]] || fail "full flash backup size mismatch"
FULL_PRETEST_SHA=$(sha256sum "$FULL_BACKUP" | awk '{print $1}')
extract_pretest_regions

PRETEST_FACTORY_SHA=$(sha256sum "$RUN_DIR/pretest-factory.bin" | awk '{print $1}')
PRETEST_NVS_SHA=$(sha256sum "$RUN_DIR/pretest-nvs.bin" | awk '{print $1}')
PRETEST_PHY_SHA=$(sha256sum "$RUN_DIR/pretest-phy-init.bin" | awk '{print $1}')
PRETEST_FABRIC_SHA=$(sha256sum "$RUN_DIR/pretest-fabric.bin" | awk '{print $1}')

printf 'pretest_full_flash_sha256=%s\n' "$FULL_PRETEST_SHA"
printf 'pretest_factory_sha256=%s\n' "$PRETEST_FACTORY_SHA"
printf 'pretest_nvs_sha256=%s\n' "$PRETEST_NVS_SHA"
printf 'pretest_phy_init_sha256=%s\n' "$PRETEST_PHY_SHA"
printf 'pretest_fabric_sha256=%s\n' "$PRETEST_FABRIC_SHA"

[[ "$PRETEST_FACTORY_SHA" == "$EXPECTED_PRETEST_FACTORY_SHA256" ]] || \
    fail "physical predecessor factory partition is not the accepted restored image"

printf '%s\n' '--- migrate bootloader / partition table / factory app ---'
MUTATED=1
esptool_cmd write-flash \
    --flash-mode dio \
    --flash-size 16MB \
    --flash-freq 80m \
    0x0 "$BOOTLOADER_BIN" \
    "$PARTITION_OFFSET" "$PARTITION_BIN" \
    "$FACTORY_OFFSET" "$APP_BIN"

FACTORY_BOOT_LOG="$RUN_DIR/factory-after-migration.log"
start_capture "$FACTORY_BOOT_LOG" 45
esptool_cmd erase-region "$OTADATA_OFFSET" "$OTADATA_SIZE"
wait_capture

grep -aFq "MS5-007 HTTP artifact server ready" "$FACTORY_BOOT_LOG" || \
    fail "migrated factory app did not recover the provisioned network/artifact path"
grep -aFq "MS5-009 factory image healthy; OTA confirmation not required" "$FACTORY_BOOT_LOG" || \
    fail "factory lifecycle health marker missing"

printf '%s\n' '--- healthy OTA trial in ota_0 ---'
esptool_cmd write-flash "$OTA0_OFFSET" "$APP_BIN"

HEALTHY_NEW_OTADATA="$RUN_DIR/otadata-ota0-new.bin"
make_otadata_entry "-" "$HEALTHY_NEW_OTADATA" 0 1 0

HEALTHY_LOG="$RUN_DIR/healthy-ota0-trial.log"
start_capture "$HEALTHY_LOG" 45
esptool_cmd write-flash "$OTADATA_OFFSET" "$HEALTHY_NEW_OTADATA"
wait_capture

grep -aFq "MS5-007 HTTP artifact server ready" "$HEALTHY_LOG" || \
    fail "healthy ota_0 trial did not reach artifact-serving health boundary"
grep -aFq "MS5-009 OTA trial image confirmed healthy" "$HEALTHY_LOG" || \
    fail "healthy ota_0 trial was not confirmed"

HEALTHY_OTADATA_READ="$RUN_DIR/otadata-after-healthy-trial.bin"
esptool_cmd read-flash "$OTADATA_OFFSET" "$OTADATA_SIZE" "$HEALTHY_OTADATA_READ"
verify_otadata_entry "$HEALTHY_OTADATA_READ" 0 1 2

printf '%s\n' '--- deliberate failed OTA trial in ota_1 ---'
esptool_cmd write-flash "$OTA1_OFFSET" "$FAIL_APP"

FAILED_NEW_OTADATA="$RUN_DIR/otadata-ota1-new.bin"
make_otadata_entry "$HEALTHY_OTADATA_READ" "$FAILED_NEW_OTADATA" 1 2 0

FAILED_LOG="$RUN_DIR/failed-ota1-trial-and-rollback.log"
start_capture "$FAILED_LOG" 55
esptool_cmd write-flash "$OTADATA_OFFSET" "$FAILED_NEW_OTADATA"
wait_capture

grep -aFq "MS5_009_FORCED_FAILED_TRIAL=START" "$FAILED_LOG" || \
    fail "deliberate failed trial did not execute"
grep -aFq "MS5-007 HTTP artifact server ready" "$FAILED_LOG" || \
    fail "device did not return to the accepted artifact-serving runtime after failed trial"
grep -aFq "MS5-009 OTA image already confirmed valid" "$FAILED_LOG" || \
    fail "rollback did not return to previously confirmed ota_0"

FAILED_OTADATA_READ="$RUN_DIR/otadata-after-failed-trial.bin"
esptool_cmd read-flash "$OTADATA_OFFSET" "$OTADATA_SIZE" "$FAILED_OTADATA_READ"
verify_otadata_entry "$FAILED_OTADATA_READ" 0 1 2
verify_otadata_entry "$FAILED_OTADATA_READ" 1 2 4

printf '%s\n' '--- remove failed-trial residue and establish stable ota_0 baseline ---'
esptool_cmd erase-region "$OTA1_OFFSET" "$OTA_SIZE"

CLEAN_OTADATA="$RUN_DIR/otadata-final-clean.bin"
clear_second_otadata_sector "$FAILED_OTADATA_READ" "$CLEAN_OTADATA"

FINAL_BOOT_LOG="$RUN_DIR/final-stable-ota0.log"
start_capture "$FINAL_BOOT_LOG" 45
esptool_cmd write-flash "$OTADATA_OFFSET" "$CLEAN_OTADATA"
wait_capture

grep -aFq "MS5-007 HTTP artifact server ready" "$FINAL_BOOT_LOG" || \
    fail "final stable ota_0 did not recover provisioned artifact-serving runtime"
grep -aFq "MS5-009 OTA image already confirmed valid" "$FINAL_BOOT_LOG" || \
    fail "final ota_0 is not confirmed valid"

FINAL_OTADATA_READ="$RUN_DIR/otadata-final-readback.bin"
esptool_cmd read-flash "$OTADATA_OFFSET" "$OTADATA_SIZE" "$FINAL_OTADATA_READ"
verify_otadata_entry "$FINAL_OTADATA_READ" 0 1 2

"$PYTHON" - "$FINAL_OTADATA_READ" <<'PY'
import pathlib
import sys
data = pathlib.Path(sys.argv[1]).read_bytes()
if data[0x1000:0x2000] != b"\xff" * 0x1000:
    raise SystemExit("second otadata sector is not erased")
print("otadata_second_sector_erased=PASS")
PY

printf '%s\n' '--- final physical preservation/readback checks ---'
FINAL_FACTORY="$RUN_DIR/final-factory-app.bin"
FINAL_OTA0="$RUN_DIR/final-ota0-app.bin"
FINAL_OTA1_HEAD="$RUN_DIR/final-ota1-head.bin"
FINAL_PARTITION="$RUN_DIR/final-partition-table.bin"
FINAL_BOOTLOADER="$RUN_DIR/final-bootloader.bin"
FINAL_NVS="$RUN_DIR/final-nvs.bin"
FINAL_PHY="$RUN_DIR/final-phy-init.bin"
FINAL_FABRIC="$RUN_DIR/final-fabric.bin"

esptool_cmd read-flash "$FACTORY_OFFSET" "$APP_BYTES" "$FINAL_FACTORY"
esptool_cmd read-flash "$OTA0_OFFSET" "$APP_BYTES" "$FINAL_OTA0"
esptool_cmd read-flash "$OTA1_OFFSET" 0x1000 "$FINAL_OTA1_HEAD"
esptool_cmd read-flash "$PARTITION_OFFSET" "$PARTITION_BYTES" "$FINAL_PARTITION"
esptool_cmd read-flash 0x0 "$BOOTLOADER_BYTES" "$FINAL_BOOTLOADER"
esptool_cmd read-flash "$NVS_OFFSET" "$NVS_SIZE" "$FINAL_NVS"
esptool_cmd read-flash "$PHY_OFFSET" "$PHY_SIZE" "$FINAL_PHY"
esptool_cmd read-flash "$FABRIC_OFFSET" "$FABRIC_SIZE" "$FINAL_FABRIC"

FINAL_FACTORY_SHA=$(sha256sum "$FINAL_FACTORY" | awk '{print $1}')
FINAL_OTA0_SHA=$(sha256sum "$FINAL_OTA0" | awk '{print $1}')
FINAL_PARTITION_SHA=$(sha256sum "$FINAL_PARTITION" | awk '{print $1}')
FINAL_BOOTLOADER_SHA=$(sha256sum "$FINAL_BOOTLOADER" | awk '{print $1}')
FINAL_NVS_SHA=$(sha256sum "$FINAL_NVS" | awk '{print $1}')
FINAL_PHY_SHA=$(sha256sum "$FINAL_PHY" | awk '{print $1}')
FINAL_FABRIC_SHA=$(sha256sum "$FINAL_FABRIC" | awk '{print $1}')

[[ "$FINAL_FACTORY_SHA" == "$APP_SHA" ]] || fail "factory app readback hash mismatch"
[[ "$FINAL_OTA0_SHA" == "$APP_SHA" ]] || fail "ota_0 app readback hash mismatch"
[[ "$FINAL_PARTITION_SHA" == "$PARTITION_SHA" ]] || fail "partition table readback hash mismatch"
[[ "$FINAL_BOOTLOADER_SHA" == "$BOOTLOADER_SHA" ]] || fail "bootloader readback hash mismatch"
[[ "$FINAL_PHY_SHA" == "$PRETEST_PHY_SHA" ]] || fail "phy_init changed"
[[ "$FINAL_FABRIC_SHA" == "$PRETEST_FABRIC_SHA" ]] || fail "Fabric partition changed"

"$PYTHON" - "$FINAL_OTA1_HEAD" <<'PY'
import pathlib
import sys
data = pathlib.Path(sys.argv[1]).read_bytes()
if data != b"\xff" * len(data):
    raise SystemExit("ota_1 was not erased after failed-trial proof")
print("ota_1_erased_after_test=PASS")
PY

[[ "$(git -C "$ROOT" status --porcelain)" == "" ]] || fail "repository worktree changed during physical gate"

printf 'production_application_bytes=%s\n' "$APP_BYTES"
printf 'production_application_sha256=%s\n' "$APP_SHA"
printf 'rollback_bootloader_sha256=%s\n' "$BOOTLOADER_SHA"
printf 'partition_table_sha256=%s\n' "$PARTITION_SHA"
printf 'failed_trial_application_sha256=%s\n' "$FAIL_APP_SHA"
printf 'healthy_trial_confirmed=PASS\n'
printf 'failed_trial_executed=PASS\n'
printf 'automatic_rollback_to_previous_valid_ota=PASS\n'
printf 'final_factory_application=PASS\n'
printf 'final_ota0_application=PASS\n'
printf 'final_ota1_erased=PASS\n'
printf 'final_otadata_ota0_valid=PASS\n'
printf 'fabric_byte_identical=PASS\n'
printf 'phy_init_byte_identical=PASS\n'
printf 'provisioning_state_functional_preservation=PASS\n'
printf 'nvs_sha256_before=%s\n' "$PRETEST_NVS_SHA"
printf 'nvs_sha256_after=%s\n' "$FINAL_NVS_SHA"
if [[ "$PRETEST_NVS_SHA" == "$FINAL_NVS_SHA" ]]; then
    printf 'nvs_byte_identical=YES\n'
else
    printf 'nvs_byte_identical=NO lifecycle_metadata_may_have_been_added=YES\n'
fi
printf 'release_signing_activated=NO\n'
printf 'wireguard_required=NO\n'
printf 'pretest_full_flash_backup=%s\n' "$FULL_BACKUP"
printf 'final_runtime=ota_0_confirmed-valid\n'
printf 'worktree_clean=PASS\n'
printf 'MS5_009_PHYSICAL_OTA_LIFECYCLE=PASS\n'
