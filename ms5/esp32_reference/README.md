# ESP32-S3 Reference Components

This directory contains the default physical-edge implementation used by
Milestone 5.

It is a reference implementation, not a platform definition. Fabric logical
identity and the Web Application protocol remain platform-neutral.

## First-release role freeze

The ESP32-S3 is intentionally included in the first Kane Fabric release so the
project has a real firmware component, pinned firmware toolchain, physical
storage model, provisioning/replacement workflow, and update/recovery path from
the beginning.

The firmware source is part of the Kane Fabric repository even though CT102 is
not the ESP-IDF build/USB environment. Git tracks the firmware source, CMake and
configuration inputs, pinned toolchain/dependency description, host-testable
logic, build/flash/acceptance scripts, and documentation. Generated build
outputs, flashed binaries, serial captures, and physical-device evidence belong
outside Git unless a later release process explicitly publishes them as release
artifacts.

The frozen v1 responsibility profile is mirrored in
`ms5/tools/kane_fabric_firmware_v1.py`. Normative prose remains in
`docs/MILESTONE_5_DESIGN.md`.

### Core runtime responsibilities

The initial firmware is a small deterministic Fabric artifact appliance. It
must:

- expose firmware build identity and operational state through serial diagnostics;
- attach as a client to a deployment-provided local IP network sufficient for
  Wiregate-to-edge HTTP;
- mount prepared Fabric artifact storage read-only;
- verify the active artifact inventory before serving it;
- serve immutable artifacts by plain HTTP;
- implement the exact closed byte-range behavior required by Kane Fabric;
- fail closed rather than serve an invalid active generation;
- continue serving the last valid activated generation when management/upstream
  connectivity is unavailable.

### Required lifecycle responsibilities

V1 also establishes a durable firmware lifecycle without turning those
lifecycle controls into application features. Kane Fabric must be able to:

- build the tracked source with the exact pinned ESP-IDF/toolchain;
- identify the resulting firmware artifact;
- flash, reprovision, and replace a device reproducibly;
- prove firmware authenticity/update/rollback/recovery behavior before MS5
  closeout;
- replace the physical device without changing Fabric logical identity;
- retain device acceptance evidence from the dedicated ESP programming node.

### Explicitly not v1 firmware responsibilities

The ESP32-S3 v1 reference firmware does not own:

- browser HTTPS termination or browser certificate lifecycle;
- browser authentication;
- an ESP32-hosted browser access point;
- Fabric geographic or release-signing authority;
- county-database mutation, official source acquisition, or candidate promotion;
- browser rendering or GIS processing;
- application membership/person identity;
- fleet orchestration.

Browser TLS remains at the Wiregate hub.

### Candidate-only later capabilities

The following may be evaluated later but are not v1 firmware prerequisites:

- WireGuard management transport;
- managed artifact synchronization;
- automatic update transport;
- an external secure element;
- remote fleet telemetry;
- richer network discovery.

A later MS5 experiment may retain one of these capabilities, reject it, or
defer it. In particular, MS5-008 may conclude that WireGuard is not retained on
the ESP32-S3 without making v1 firmware incomplete.

Reference path:

```text
browser -- HTTPS --> Wiregate hub -- HTTP --> ESP32-S3
```

The Wiregate hub owns browser HTTPS termination and certificate trust. The
ESP32-S3 reference firmware holds no browser TLS private key.

## Acceptance ownership

Acceptance is intentionally split by environment.

**CT102 repository acceptance** verifies the tracked contracts, tests,
documentation, and dependency/work-sequence rules. CT102 does not build or flash
firmware and does not need ESP-IDF or USB passthrough.

**Dedicated ESP programming-node acceptance** verifies the exact pinned build,
flash/boot behavior, serial firmware identity, read-only storage mounting,
active-inventory verification, and real HTTP GET/range/fail-closed behavior on
the reference hardware.

**Later MS5 integration acceptance** proves the Wiregate browser path,
management-loss behavior, firmware update/rollback/recovery, physical
replacement, and constrained-resource coexistence. Candidate capabilities such
as WireGuard are not promoted into the core firmware merely because they are
measured during those later gates.

## MS5-006 components

- `kane_fabric_http`: pure C strict byte-range and artifact-path validation.
- `kane_fabric_artifact_server`: VFS-backed bounded artifact serving for an
  ESP-IDF HTTP server supplied by the caller.
- `kane_fabric_storage`: read-only raw FAT partition mounting for host-generated
  immutable artifact images.
- `host_test`: host compiler tests for the pure HTTP/range core.
- `main`: build-probe application used to ensure the components link under the
  pinned ESP-IDF toolchain.

The current build probe intentionally does not yet start networking or mount a
particular physical partition. Runtime integration later attaches the artifact
component to a plain HTTP server and implements the frozen v1 runtime role.
HTTPS remains at the Wiregate hub.

For the implementation contract, read
`docs/MS5_006_STORAGE_HTTP_IMPLEMENTATION.md`.

## Pinned build target

The accepted MS5 toolchain selection is ESP-IDF v6.0.3 targeting `esp32s3`.

The next physical gate compiles this project with that exact toolchain on the
dedicated ESP programming node. Real browser consumption through the Wiregate
hub belongs to the following Milestone 5 work item.
