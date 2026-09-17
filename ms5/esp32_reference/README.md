# ESP32-S3 Reference Components

This directory contains the default physical-edge implementation used by Milestone 5. It is a reference implementation, not a platform definition. Fabric logical identity, county administration, and the Web Application protocol remain platform-neutral.

The physical build/programming environment is documented in `docs/CIVICVS_PROJECT_ENVIRONMENT.md`. The administrative/edge boundary is `docs/ADMINISTRATIVE_EDGE_BOUNDARY.md`.

## First-release role freeze

The ESP32-S3 is intentionally included in the first Kane Fabric release so the project has a real firmware component, pinned firmware toolchain, physical storage model, provisioning/replacement workflow, and update/recovery path from the beginning.

The firmware source is part of the Kane Fabric repository even though CT102 is not the ESP-IDF build/USB environment. Git tracks the firmware source, CMake/configuration inputs, pinned toolchain/dependency description, host-testable logic, build/flash/acceptance scripts, and documentation. Generated build outputs, flashed binaries, serial captures, and physical-device evidence remain outside Git unless a later release process explicitly publishes them.

The frozen v1 responsibility profile is mirrored in `ms5/tools/kane_fabric_firmware_v1.py`. Normative prose remains in `docs/MILESTONE_5_DESIGN.md`.

### Core runtime responsibilities

The initial firmware is a small deterministic Fabric artifact appliance. Its core runtime responsibilities include serial build/state diagnostics, deployment-network client attachment, read-only bounded participant artifact storage, active-inventory verification, plain HTTP immutable artifact serving, exact closed byte-range behavior, fail-closed invalid-state handling, and continued serving of the last valid generation when management/upstream connectivity is unavailable.

### Required lifecycle responsibilities

V1 also requires an exact pinned build, identifiable firmware artifact, reproducible flash/reprovisioning, firmware authenticity/update/rollback/recovery proof before MS5 closeout, physical replacement without logical-identity change, and retained device acceptance evidence from the dedicated programming workstation.

### Explicitly not v1 firmware responsibilities

The ESP32-S3 does not own browser HTTPS/certificate lifecycle, browser authentication, a browser-facing ESP32 access point, Fabric geographic/release-signing authority, county-database mutation/promotion, county-wide substrate replication, the county web map, category/publication-contract administration, browser GIS/rendering, application membership/person identity, or fleet orchestration.

A participant edge is therefore not expected to hold all Kane County data. It may hold a focused publication such as one condominium association and its unit-level participant artifacts while referencing accepted county/building identities defined by the administrative contracts.

Browser/admin integration remains above the edge:

```text
browser -- HTTPS --> Wiregate / administrative web view
                         |\
                         | +--> accepted county publication
                         |
                         +-- HTTP --> ESP32-S3 bounded participant publication
```

### Candidate-only later capabilities

Candidate-only capabilities include WireGuard management transport, managed artifact synchronization, automatic update transport, an external secure element, remote telemetry, and richer discovery. MS5-008 may retain, reject, or defer WireGuard without making v1 firmware incomplete.

## Acceptance ownership

**CT102 repository acceptance** verifies tracked contracts, tests, documentation, and dependency/work-sequence rules. **CT102 does not build or flash firmware** and does not need ESP-IDF or USB passthrough.

**`fw` / CPE Build and Hardware Workstation acceptance** verifies the exact pinned build, flash/boot behavior, serial firmware identity, read-only storage mounting, active-inventory verification, and real HTTP GET/range/fail-closed behavior on the reference hardware.

**Later MS5 integration acceptance** proves focused participant-publication integration with the administrative web path, management-loss behavior, firmware update/rollback/recovery, physical replacement, and constrained-resource coexistence.

## Accepted physical checkpoint

MS5-006 physical device-runtime acceptance is complete. The accepted firmware implementation head is:

```text
7aa3c836bae470704d051a36a6261a1140e9d3d0
```

The reference board is ESP32-S3 QFN56 revision v0.2 with 8 MB PSRAM and 16 MB flash. The accepted runtime physically proved:

- pinned ESP-IDF v6.0.3 / `esp32s3` build identity;
- PROGRAM and TERMINAL roles;
- 16 MB flash geometry;
- Wi-Fi provisioning and station/DHCP operation;
- read-only Fabric partition mount;
- inventory/artifact verification before serving;
- plain HTTP `200` artifact delivery;
- exact closed byte-range `206` delivery;
- invalid/unsupported range `416` handling;
- traversal rejection;
- deliberate corrupted active storage failing closed before networking/service exposure;
- restoration of the accepted Fabric image and exact artifact SHA-256 recovery.

Detailed evidence is recorded in:

```text
docs/CPE_ESP32_FIRST_FLASH_ACCEPTANCE.md
docs/CPE_ESP32_MS5_006_DEVICE_RUNTIME_ACCEPTANCE.md
```

## Current development state

Firmware is no longer the active workstream. The current probe image remains an MS5-006 physical integration artifact, not a production condominium publication.

The next development work is administrative under `administration/README.md`: define the county-facing categories, participant-publication contract, association/unit identity/reference semantics, visibility classes, web/map composition, and independent-county-operator conformance boundary.

Return to this firmware tree when those contracts are concrete enough to provision the first real bounded participant publication, or when MS5-008 through MS5-011 lifecycle tests require firmware changes.

## MS5-006 components

- `kane_fabric_http`: pure C strict byte-range and artifact-path validation.
- `kane_fabric_artifact_server`: VFS-backed bounded artifact serving for ESP-IDF HTTP.
- `kane_fabric_storage`: read-only raw FAT partition mounting and active inventory verification.
- `kane_fabric_network`: deployment Wi-Fi provisioning and station attachment.
- `host_test`: host compiler tests for the pure HTTP/range core.
- `main`: physical integration application used for the accepted MS5-006 runtime proof.

For the implementation contract, read `docs/MS5_006_STORAGE_HTTP_IMPLEMENTATION.md`.