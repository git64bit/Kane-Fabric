# Kane Fabric — Current Handoff

Start with `docs/DEVELOPMENT_PROCESS.md`, `docs/CURRENT_STATE.json`, `docs/SESSION_START.md`, then the applicable design authority. `docs/MILESTONE_5_DESIGN.md` remains the sole detailed authority for Milestone 5; `docs/WEB_APPLICATION_DESIGN.md` remains the sole detailed authority for the Web Application workstream.

## Released foundation

Milestones 0–4 are complete. The accepted MS3 substrate identity is `fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc`; the accepted MS4 implementation is `9f6013d1b8b44998047f71e2b3f3e9c55c9ed298`; the accepted MS4 composition identity is `a58c8398248cee05b7baad9ae289fe0581bdb3624ce1aff3aa8a49721f92ee53`.

The byte-identical accepted MS3 reproduction remains at `/var/lib/kane-fabric/render/web-002/ms3-accepted-reproduction`. The accepted MS4 proof remains at `/var/lib/kane-fabric/render/ms4-proof`.

## Web Application closeout

WEB-001 through WEB-004 established the dependency-free platform-neutral browser application, verified MS3/MS4 composition, navigation/layer inspection, and explicit fail-closed verification/offline/retry behavior.

WEB-005 passed on CT102 on 2026-09-14. The application implementation remained `73252b6a3c87ba47b7f68f3e3206056607e1e53a`; the later checkpoint `f83dac7ca2ef946edcd285be461a63eec339b59b` changed only status documentation.

WEB-005 evidence:

```text
/var/lib/kane-fabric/render/web-005/browser-closeout-f83dac7
browser evidence SHA256      5d56347b2551481a65cbaa2fc990dd845517aa1b7e20d55176b69914b489d2f9
edge reassessment SHA256     bccff3f369b200737742a7e902b2a8e3a5878b297a5ee9be9e44e08f65ffb488
browser contract stable      true
resume MS5-006               true
```

The Web Application is sufficient as the reference client/acceptance instrument for this stage. No UI-polish work is required before the physical-edge work proceeds.

## Active work

Milestone 5 is current. MS5-005 remains the last fully accepted MS5 implementation checkpoint at `aed812df8c5e37bb1843e022d7a7813dc7e8e862`. The active normative item is now **MS5-006**, the ESP32-S3 immutable artifact storage and HTTP byte-range reference implementation.

WEB-005 froze the edge-facing requirements needed now: immutable released MS3/MS4 bytes, ordinary GET for small files, exact closed single-range `206` serving for `.kfs`, explicit `Content-Length`/`Content-Range`/`Accept-Ranges`, rejection of unsupported range forms, browser CORS support, bounded direct-from-storage reads, and no device-specific browser API or geographic authority. Physical browser access must still satisfy the MS5-004 browser-trusted HTTPS secure-origin contract.

Throughput/concurrency limits remain later measurement work. WireGuard runtime, firmware update mechanics, and physical replacement remain their existing later MS5 gates.

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

CT102 was last observed clean at `f83dac7ca2ef946edcd285be461a63eec339b59b` after WEB-005 closeout. Repository-side MS5-006 work must be accepted there before pinned ESP-IDF/device evidence is attempted.

## Execution discipline

Work directly on `main` unless the operator changes policy. CT102 is the real acceptance environment; the Assistant sandbox is not acceptance evidence. Do not rerun accepted gates without an invalidating change. Large generated/device/browser evidence stays under `/var/lib/kane-fabric`, not Git. Long srv-b/CT102 procedures must be delivered as standalone script files with only a short relay command and compact successful output in chat.
