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

The accepted implementation already provides the useful storage/range behavior: immutable read-only artifact storage, ordinary GET, exact closed single-range `206` behavior, bounded direct-from-storage reads, CORS/range headers, no device-specific browser API, and no geographic authority at the edge.

## Accepted MS5 transport architecture

The earlier MS5-003/MS5-004 assumption that browser HTTPS terminates on the ESP32-S3 is superseded by the accepted reference topology:

```text
browser -- HTTPS --> Wiregate hub -- HTTP --> ESP32-S3
```

The correction removes `browser-tls-server` from the ESP32 key-provider role set, makes an ESP32-hosted AP non-required, keeps direct ESP32 HTTP as a diagnostic/backend path rather than the browser secure origin, and explicitly prevents WireGuard from becoming a prerequisite for MS5-007. Management/WireGuard remains MS5-008.

The ESP32-S3 remains in the first release primarily to establish a real firmware lifecycle early. Its initial role is intentionally modest: immutable storage, bounded plain-HTTP serving, provisioning/replacement, and a base for later firmware responsibilities.

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

A repository-wide tracked-file audit then found three residual areas carrying older assumptions: the active consumer gate register, the public ESP32 artifact-server header, and a forward-looking Milestone 3 AP/STA statement. Those were corrected in one bounded commit and protected by a regression test.

The residual reconciliation was accepted in CT102 at:

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

The remaining AP/TLS/WireGuard strings in tracked files are accepted-topology statements, explicit negations, historical annotations, or negative tests. In particular, `local-ap-http` remains only in a negative browser-access test that verifies such a transport is rejected; the active browser transport is `wiregate-hub-proxy`.

The repository reconciliation review is therefore complete. No further actionable browser-TLS, local-AP, WireGuard-ordering, or overstated first-release ESP32-role drift was identified in that pass.

## ESP32-S3 v1 firmware responsibility freeze

Before physical work resumes, the first-release firmware role is being frozen explicitly rather than allowing the existing implementation or later experiments to define the product by accident.

The candidate boundary defines three distinct classes:

1. **core runtime responsibilities:** firmware identity/serial diagnostics, deployment-network client attachment, read-only artifact storage, active-inventory verification, plain HTTP GET/range serving, fail-closed invalid-state behavior, and continued serving of the last valid generation without management connectivity;
2. **required lifecycle responsibilities:** firmware source/build inputs/scripts tracked in Git, exact pinned build, identifiable firmware artifact, reproducible flash/reprovisioning, update/rollback/recovery proof, replacement identity preservation, and device acceptance evidence;
3. **candidate-only capabilities:** WireGuard management transport, managed synchronization, automatic update transport, secure-element use, fleet telemetry, and richer discovery.

Browser TLS/certificate lifecycle, browser authentication, ESP32-hosted browser AP behavior, geographic/release-signing authority, county-database/source-promotion work, browser GIS/rendering, membership/person identity, and fleet orchestration are explicitly outside the v1 firmware responsibility boundary.

The executable mirror is `ms5/tools/kane_fabric_firmware_v1.py`; normative prose remains in `docs/MILESTONE_5_DESIGN.md`.

The candidate also freezes acceptance ownership:

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

MS5-008 is explicitly allowed to retain, reject, or defer WireGuard. A result of "do not retain WireGuard on ESP32-S3" does not make v1 firmware incomplete.

This firmware-role freeze is a **published repository candidate pending CT102 acceptance**. Physical execution remains paused until the candidate contract and tests pass in CT102 and a material acceptance checkpoint is recorded.

## Hardware execution status

Physical ESP32-S3 execution is **paused pending acceptance of the firmware v1 responsibility freeze**.

Do **not** install ESP-IDF in CT102 and do **not** add Proxmox USB passthrough. CT102 remains the repository/browser/contract acceptance environment. After the role freeze is accepted, the dedicated ESP programming node will own pinned ESP-IDF verification, build, flash, serial/device diagnostics, and physical storage/range evidence.

Current hardware evidence remains:

```text
pinned ESP-IDF v6.0.3 compile    PENDING after firmware-role freeze
device storage/range evidence    PENDING after firmware-role freeze
```

Firmware source remains in the GitHub repository even though firmware compilation/USB work does not occur in CT102. Generated build/device evidence remains outside Git unless a later release process explicitly publishes selected firmware binaries as release artifacts.

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

CT102 was last observed clean at `58faa54638b60c50a688d4de3f23d211917cd525` after synchronizing the transport-reconciliation closeout. The accepted MS5-006 implementation baseline remains `ef6a08f03a94aabd6c15e9c02f6ed9470c65d3ce`; the accepted transport architecture is `9cdb0206f4f7280799bec9d228a4f56a326a4ad1`; the residual reconciliation acceptance head is `c43814961cb14d6623ef92e40d6cf4d72f8ef37e`.

## Next safe action

Synchronize clean CT102 to the published firmware-role candidate and run only the invalidated repository gates: Python compileall, the MS5 work-sequence authority check, and the MS5 test suite. Do not begin ESP-IDF build/flash/device work until the role freeze is accepted and checkpointed.

## Execution discipline

Work directly on `main` unless the operator changes policy. CT102 is the repository/browser/contract acceptance environment; the dedicated ESP programming node is the MS5 reference firmware build/flash/device-test environment. The Assistant sandbox is not acceptance evidence. Do not rerun accepted gates without an invalidating change. Large generated/device/browser evidence stays under `/var/lib/kane-fabric`, not Git. Long manual acceptance procedures must be delivered as standalone script files with only a short relay command and compact successful output in chat.