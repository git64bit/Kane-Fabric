# Kane Fabric — Current Handoff

Start with `docs/DEVELOPMENT_PROCESS.md`, `docs/CURRENT_STATE.json`, `docs/SESSION_START.md`, then the applicable design authority. `docs/MILESTONE_5_DESIGN.md` remains the sole detailed authority for Milestone 5; `docs/WEB_APPLICATION_DESIGN.md` remains the sole detailed authority for the Web Application workstream.

## Released foundation

Milestones 0–4 are complete. The accepted MS3 substrate identity is `fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc`; the accepted MS4 implementation is `9f6013d1b8b44998047f71e2b3f3e9c55c9ed298`; the accepted MS4 composition identity is `a58c8398248cee05b7baad9ae289fe0581bdb3624ce1aff3aa8a49721f92ee53`.

The byte-identical accepted MS3 reproduction remains at `/var/lib/kane-fabric/render/web-002/ms3-accepted-reproduction`. The accepted MS4 proof remains at `/var/lib/kane-fabric/render/ms4-proof`.

## Web Application closeout

WEB-001 through WEB-005 are complete for the current MS5 edge-requirements purpose. The application implementation remained `73252b6a3c87ba47b7f68f3e3206056607e1e53a`; the later WEB-005 checkpoint `f83dac7ca2ef946edcd285be461a63eec339b59b` changed only status documentation.

WEB-005 evidence:

```text
/var/lib/kane-fabric/render/web-005/browser-closeout-f83dac7
browser evidence SHA256      5d56347b2551481a65cbaa2fc990dd845517aa1b7e20d55176b69914b489d2f9
edge reassessment SHA256     bccff3f369b200737742a7e902b2a8e3a5878b297a5ee9be9e44e08f65ffb488
browser contract stable      true
resume MS5-006               true
```

Those values remain historical accepted WEB-005 evidence. The later transport-architecture correction supersedes the assumption that browser HTTPS terminates on the physical edge; it does not rewrite the historical evidence.

The current UI is sufficient as the reference client/acceptance instrument. UI polish is not required before physical-edge work resumes.

## MS5-006 accepted implementation baseline

The MS5-006 repository implementation remains accepted at:

```text
ef6a08f03a94aabd6c15e9c02f6ed9470c65d3ce
```

CT102 repository acceptance for that implementation:

```text
MS5 authority guard       valid
dependency policy         PASS
Python compileall         PASS
MS5 tests                 42 passed, 1 environment skip
host C compiler           absent on CT102
host C compile            SKIPPED
worktree                  clean
```

The single skip is deliberate environment classification: CT102 has no host C compiler. It is not implementation acceptance evidence. The authoritative C compilation gate remains the pinned ESP-IDF v6.0.3 ESP32-S3 build.

The accepted implementation already provides immutable read-only artifact storage, ordinary GET, exact closed single-range `206` behavior, bounded direct-from-storage reads, CORS/range headers, no device-specific browser API, and no geographic authority at the edge.

## Accepted MS5 transport architecture

The earlier MS5-003/MS5-004 assumption that browser HTTPS terminates on the ESP32-S3 is superseded by the accepted reference topology:

```text
browser -- HTTPS --> Wiregate hub -- HTTP --> ESP32-S3
```

The correction removes `browser-tls-server` from the ESP32 key-provider role set, makes an ESP32-hosted AP non-required, keeps direct ESP32 HTTP as a diagnostic/backend path rather than the browser secure origin, and explicitly prevents WireGuard from becoming a prerequisite for MS5-007. Management/WireGuard remains MS5-008.

The transport/key-role/browser-path correction was accepted in CT102 at:

```text
9cdb0206f4f7280799bec9d228a4f56a326a4ad1
```

Acceptance evidence:

```text
architecture regression scan   PASS
Python compileall               PASS
MS5 authority guard             valid
dependency policy               PASS
MS5 tests                       47 passed, 1 environment skip
host C compiler                 absent on CT102
host C compile                  SKIPPED
worktree                        clean
```

## Residual reconciliation closeout

A repository-wide tracked-file audit then corrected residual older assumptions in the active consumer gate register, the public ESP32 artifact-server header, and a forward-looking Milestone 3 AP/STA statement. The residual reconciliation was accepted in CT102 at:

```text
c43814961cb14d6623ef92e40d6cf4d72f8ef37e
```

Acceptance evidence:

```text
exact stale-assumption guard    PASS
corrected broad drift audit     reviewed; no actionable residual drift
Python compileall               PASS
MS5 tests                       48 passed, 1 environment skip
host C compiler                 absent on CT102
host C compile                  SKIPPED
worktree                        clean
```

The repository transport reconciliation is complete.

## Accepted ESP32-S3 v1 firmware responsibility freeze

The first-release firmware role is now explicitly frozen so later experiments cannot expand v1 merely because ESP-IDF supports additional features.

The accepted boundary has three distinct classes:

1. **core runtime responsibilities:** firmware identity/serial diagnostics, deployment-network client attachment, read-only artifact storage, active-inventory verification, plain HTTP GET/range serving, fail-closed invalid-state behavior, and continued serving of the last valid generation without management connectivity;
2. **required lifecycle responsibilities:** firmware source/build inputs/scripts tracked in Git, exact pinned build, identifiable firmware artifact, reproducible flash/reprovisioning, update/rollback/recovery proof, replacement identity preservation, and device acceptance evidence;
3. **candidate-only capabilities:** WireGuard management transport, managed synchronization, automatic update transport, secure-element use, fleet telemetry, and richer discovery.

Browser TLS/certificate lifecycle, browser authentication, ESP32-hosted browser AP behavior, geographic/release-signing authority, county-database/source-promotion work, browser GIS/rendering, membership/person identity, and fleet orchestration are outside the v1 firmware responsibility boundary.

The executable mirror is `ms5/tools/kane_fabric_firmware_v1.py`; normative prose remains in `docs/MILESTONE_5_DESIGN.md`.

Acceptance ownership is frozen as:

```text
CT102
  repository contracts/tests/work-sequence only
  no ESP-IDF build
  no USB/flash

Dedicated ESP programming node
  exact pinned ESP-IDF build
  flash/boot
  serial firmware identity
  storage/inventory/device HTTP evidence

Later MS5 integration
  Wiregate browser path
  management-loss behavior
  firmware update/recovery
  physical replacement
  constrained-resource coexistence
```

MS5-008 may retain, reject, or defer WireGuard. A result of "do not retain WireGuard on ESP32-S3" does not make v1 firmware incomplete.

The firmware-role freeze was accepted in CT102 at:

```text
5d45fd600468060104341166adf23bb6465393d2
```

Acceptance evidence:

```text
firmware-v1 structural guard    PASS
MS5 work-sequence authority     valid
Python compileall               PASS
MS5 tests                       54 passed, 1 environment skip
host C compiler                 absent on CT102
host C compile                  SKIPPED
worktree                        clean
```

The single skip remains deliberate: CT102 has no host C compiler. It does not replace the authoritative pinned ESP-IDF build on the dedicated programming node.

## Firmware source and execution ownership

Firmware source belongs in GitHub even though CT102 remains outside the firmware build/USB path.

Git tracks the firmware source, CMake/configuration inputs, pinned toolchain/dependency description, host-testable logic, build/flash/acceptance scripts, and documentation. Generated build outputs, serial captures, device logs, and physical acceptance evidence remain outside Git under the operational evidence tree unless a later release process explicitly publishes selected firmware artifacts.

CT102 remains the repository/browser/contract acceptance environment. It must not acquire ESP-IDF merely to validate repository state, and it must not receive Proxmox USB passthrough for the reference firmware workflow.

## Hardware execution status

Physical ESP32-S3 execution has not yet restarted, but it is no longer blocked by repository reconciliation or firmware-role definition. It may resume when the operator chooses.

The dedicated ESP programming node owns pinned ESP-IDF verification, build, flash, serial/device diagnostics, and physical storage/range evidence.

Current hardware evidence remains:

```text
pinned ESP-IDF v6.0.3 compile    PENDING
device storage/range evidence    PENDING
```

The first physical action is to verify the exact pinned ESP-IDF v6.0.3/toolchain environment. Only after that verification should the tracked `ms5/esp32_reference` firmware be compiled. Flash/storage/network/device integration follows only after a clean pinned build.

Candidate-only capabilities must not be added to the core v1 runtime during this work. In particular, do not add WireGuard merely to support MS5-006 or MS5-007.

Native Linux/macOS/Windows distribution support remains an independent, undecided product/distribution concern.

## Stable operational authorities

```text
repository          git64bit/Kane-Fabric
branch              main
Proxmox host        srv-b
container           CT102 / kane-fabric
checkout            /tmp/kane-fabric-ms2
operational root    /var/lib/kane-fabric
authoritative DB    /var/lib/kane-fabric/database/kane-county-fabric.gpkg
DB SHA256           31e362b696a37f1b9c45ae355c5669511a3128c17a651108a62e20d1cedebd67
```

CT102 was last observed clean at `5d45fd600468060104341166adf23bb6465393d2` after accepting the firmware-v1 role freeze. The accepted MS5-006 implementation baseline remains `ef6a08f03a94aabd6c15e9c02f6ed9470c65d3ce`; the accepted transport architecture is `9cdb0206f4f7280799bec9d228a4f56a326a4ad1`; the residual reconciliation acceptance head is `c43814961cb14d6623ef92e40d6cf4d72f8ef37e`; the firmware-v1 role acceptance head is `5d45fd600468060104341166adf23bb6465393d2`.

## Next safe action

MS5-006 physical execution may resume when the operator chooses. Use the dedicated ESP programming node with direct USB access, verify the exact pinned ESP-IDF v6.0.3/toolchain first, then compile the tracked `ms5/esp32_reference` firmware. Do not begin flash/storage/network/device integration until the pinned build is clean, and do not promote candidate-only capabilities into the core v1 runtime without their later explicit MS5 acceptance gate.

## Execution discipline

Work directly on `main` unless the operator changes policy. CT102 is the repository/browser/contract acceptance environment; the dedicated ESP programming node is the MS5 reference firmware build/flash/device-test environment. The Assistant sandbox is not acceptance evidence. Do not rerun accepted gates without an invalidating change. Large generated/device/browser evidence stays under `/var/lib/kane-fabric`, not Git. Long manual acceptance procedures must be delivered as standalone script files with only a short relay command and compact successful output in chat.
