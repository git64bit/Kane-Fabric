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

The current UI is sufficient as the reference client/acceptance instrument. UI polish is not required before physical-edge work proceeds.

## MS5-006 status

MS5-006 is active. The repository implementation is accepted at:

```text
ef6a08f03a94aabd6c15e9c02f6ed9470c65d3ce
```

CT102 repository acceptance:

```text
MS5 authority guard       valid
dependency policy         PASS
Python compileall         PASS
MS5 tests                 42 passed, 1 environment skip
host C compiler           absent on CT102
host C compile            SKIPPED
worktree                  clean
```

The single skip is deliberate environment classification: CT102 has no host C compiler. It is not implementation acceptance evidence. The authoritative C compilation gate is the pinned ESP-IDF v6.0.3 ESP32-S3 build and remains pending.

The repository implementation preserves the WEB-005 edge contract: immutable read-only artifact storage, ordinary GET, exact closed single-range `206` behavior, bounded direct-from-storage reads, CORS/range headers, no device-specific browser API, and no geographic authority at the edge. The artifact component registers onto a caller-owned HTTP/HTTPS server so MS5-006 does not weaken the already accepted MS5-004 browser-trusted HTTPS requirement.

Current remaining MS5-006 evidence:

```text
pinned ESP-IDF v6.0.3 compile    PENDING
device storage/range evidence    PENDING
```

Native Linux/macOS/Windows distribution support is not part of the MS5-006 browser-facing contract and remains an independent, undecided product/distribution concern.

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

CT102 was last observed clean at `ef6a08f03a94aabd6c15e9c02f6ed9470c65d3ce` after corrected MS5-006 repository acceptance.

## Execution discipline

Work directly on `main` unless the operator changes policy. CT102 is the real acceptance environment; the Assistant sandbox is not acceptance evidence. Do not rerun accepted gates without an invalidating change. Large generated/device/browser evidence stays under `/var/lib/kane-fabric`, not Git. Long srv-b/CT102 procedures must be delivered as standalone script files with only a short relay command and compact successful output in chat.
