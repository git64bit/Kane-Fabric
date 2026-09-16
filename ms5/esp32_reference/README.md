# ESP32-S3 Reference Components

This directory contains the default physical-edge implementation used by Milestone 5. It is a reference implementation, not a platform definition. Fabric logical identity and the Web Application protocol remain platform-neutral.

The physical build/programming environment is documented in `docs/CIVICVS_PROJECT_ENVIRONMENT.md`.

## First-release role freeze

The ESP32-S3 is intentionally included in the first Kane Fabric release so the project has a real firmware component, pinned firmware toolchain, physical storage model, provisioning/replacement workflow, and update/recovery path from the beginning.

The firmware source is part of the Kane Fabric repository even though CT102 is not the ESP-IDF build/USB environment. Git tracks the firmware source, CMake/configuration inputs, pinned toolchain/dependency description, host-testable logic, build/flash/acceptance scripts, and documentation. Generated build outputs, flashed binaries, serial captures, and physical-device evidence remain outside Git unless a later release process explicitly publishes them.

The frozen v1 responsibility profile is mirrored in `ms5/tools/kane_fabric_firmware_v1.py`. Normative prose remains in `docs/MILESTONE_5_DESIGN.md`.

### Core runtime responsibilities

The initial firmware is a small deterministic Fabric artifact appliance. Its core runtime responsibilities include serial build/state diagnostics, deployment-network client attachment, read-only artifact storage, active-inventory verification, plain HTTP immutable artifact serving, exact closed byte-range behavior, fail-closed invalid-state handling, and continued serving of the last valid generation when management/upstream connectivity is unavailable.

### Required lifecycle responsibilities

V1 also requires an exact pinned build, identifiable firmware artifact, reproducible flash/reprovisioning, firmware authenticity/update/rollback/recovery proof before MS5 closeout, physical replacement without logical-identity change, and retained device acceptance evidence from the dedicated programming workstation.

### Explicitly not v1 firmware responsibilities

The ESP32-S3 does not own browser HTTPS/certificate lifecycle, browser authentication, a browser-facing ESP32 access point, Fabric geographic/release-signing authority, county-database mutation/promotion, browser GIS/rendering, application membership/person identity, or fleet orchestration.

Browser TLS remains at the Wiregate hub:

```text
browser -- HTTPS --> Wiregate hub -- HTTP --> ESP32-S3
```

### Candidate-only later capabilities

Candidate-only capabilities include WireGuard management transport, managed artifact synchronization, automatic update transport, an external secure element, remote telemetry, and richer discovery. MS5-008 may retain, reject, or defer WireGuard without making v1 firmware incomplete.

## Acceptance ownership

**CT102 repository acceptance** verifies tracked contracts, tests, documentation, and dependency/work-sequence rules. **CT102 does not build or flash firmware** and does not need ESP-IDF or USB passthrough.

**`fw` / CPE Build and Hardware Workstation acceptance** verifies the exact pinned build, flash/boot behavior, serial firmware identity, read-only storage mounting, active-inventory verification, and real HTTP GET/range/fail-closed behavior on the reference hardware.

**Later MS5 integration acceptance** proves the Wiregate browser path, management-loss behavior, firmware update/rollback/recovery, physical replacement, and constrained-resource coexistence.

## Current physical checkpoint

`fw` is the accepted build/programming workstation at CPE address `10.110.0.4/22`.

The exact pinned ESP-IDF v6.0.3 `esp32s3` build has succeeded there:

```text
firmware image            kane_fabric_ms5_edge_reference.bin
binary size               0x28180
smallest app partition    0x100000
free                      84%
```

The reference build defaults now explicitly pin:

```text
CONFIG_IDF_TARGET="esp32s3"
CONFIG_ESPTOOLPY_FLASHSIZE_16MB=y
```

The fixed USB roles are accepted:

```text
CPE-USB-1 / branch 1.1.2 / PROGRAM  / Espressif 303a:1001
CPE-USB-2 / branch 1.1.3 / TERMINAL / Silicon Labs CP2102 10c4:ea60
```

The clean reference board is ESP32-S3 revision v0.2 with 8 MB PSRAM, MAC `b8:f8:62:e2:d5:2c`, 16 MB flash, Security Flags `0x00000000`, Secure Boot disabled, and Flash Encryption disabled.

The first controlled Kane Fabric flash and subsequent cold boot are accepted. The initial boot exposed a 2 MB image-header default against the 16 MB physical flash; that reproducibility defect was corrected at Kane-Fabric commit:

```text
d26ec418751b7b2f82a8814297204e1b62bceda4
```

After regenerating the effective `sdkconfig`, the corrected flash command used `--chip esp32s3 --flash-size 16MB`. A corrective reflash passed written-data hash verification for bootloader, partition table, and application. The following PROGRAM-to-TERMINAL power transition produced a real cold boot:

```text
rst:0x1 (POWERON)
SPI Flash Size : 16MB
App version: d26ec41
```

The previous 16 MB physical / 2 MB image-header warning was absent. Detailed evidence is recorded in `docs/CPE_ESP32_FIRST_FLASH_ACCEPTANCE.md`.

Current runtime connection:

```text
PROGRAM / CPE-USB-1    OFF
TERMINAL / CPE-USB-2   ON
```

Switch back to PROGRAM only when another firmware flash is actually required.

## MS5-006 components

- `kane_fabric_http`: pure C strict byte-range and artifact-path validation.
- `kane_fabric_artifact_server`: VFS-backed bounded artifact serving for an ESP-IDF HTTP server supplied by the caller.
- `kane_fabric_storage`: read-only raw FAT partition mounting for host-generated immutable artifact images.
- `host_test`: host compiler tests for the pure HTTP/range core.
- `main`: build-probe application used to ensure the components link under the pinned ESP-IDF toolchain.

The current build probe intentionally does not yet start networking or mount a particular physical partition. Runtime integration next attaches prepared read-only artifact storage, verifies the active inventory, and then starts the plain HTTP artifact server. HTTPS remains at the Wiregate hub.

For the implementation contract, read `docs/MS5_006_STORAGE_HTTP_IMPLEMENTATION.md`.
