# Kane Fabric — Current Handoff

Start here, then read:

```text
docs/DEVELOPMENT_PROCESS.md
docs/CURRENT_STATE.json
docs/SESSION_START.md
docs/WEB_APPLICATION_DESIGN.md
docs/MILESTONE_5_DESIGN.md
docs/CONSUMER_INTERFACE_GATES.md
```

`docs/MILESTONE_5_DESIGN.md` remains the sole detailed authority for the Milestone 5 sequence. `docs/WEB_APPLICATION_DESIGN.md` remains the sole detailed authority for the Web Application workstream. Do not duplicate either complete work sequence in status documents.

## Released foundation

Milestones 0–4 are complete.

```text
MS3 substrate identity
fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc

MS4 accepted implementation
9f6013d1b8b44998047f71e2b3f3e9c55c9ed298

MS4 composition identity
a58c8398248cee05b7baad9ae289fe0581bdb3624ce1aff3aa8a49721f92ee53
```

The originally released MS3 package directory was no longer retained when WEB-002 needed it. The deterministic compiler reproduced the exact released four-file publication from the unchanged authoritative database at:

```text
/var/lib/kane-fabric/render/web-002/ms3-accepted-reproduction
```

All released component sizes and SHA-256 identities matched exactly. This is a byte-identical reproduction, not a new geographic release.

## Milestone 5 status

Milestone 5 remains current. `MS5-006` is the next normative MS5 item, but is deliberately deferred while Kane Fabric develops the browser application and other project-controlled components.

Last accepted MS5 implementation checkpoint:

```text
aed812df8c5e37bb1843e022d7a7813dc7e8e862
```

Acceptance remains:

```text
MS5 authority guard     valid
dependency policy       PASS
python compileall       PASS
contract tests          36 passed, 0 failed
worktree                clean
```

ESP32-S3 remains the default reference edge platform, not the architecture. No Fabric logical identity or browser behavior may depend on continued ESP32 availability. Do not rerun accepted MS5-001..005 gates merely because Web Application source advances.

## Web Application accepted work

### WEB-001

Accepted at:

```text
98873196438f87f946796d9b4ffd2ff2a5a135e4
```

Established the dependency-free application shell and platform-neutral artifact-source configuration.

### WEB-002

Accepted at:

```text
ef3c08f77442e1a8cefe6a0567b50e10ce010dd3
```

The new application surface consumed the accepted MS3 publication and accepted MS4 composition in real Chromium through independent ordinary HTTP sources. It visibly rendered two verified subscription objects and preserved bounded MS3 byte-range access.

Durable evidence:

```text
/var/lib/kane-fabric/render/web-002/browser-acceptance-ef3c08f
SHA256 cef970419e4983c845ac19956f4d2f9a7245444d90acb0d81ee917c907090d5a
```

### WEB-003

Accepted at:

```text
b216a3d6e0fd7be51223754c9dc3459229498346
```

Repository gate:

```text
MS5 authority guard     valid
dependency policy       PASS
JavaScript syntax       PASS
Web tests               21 passed, 0 failed
worktree                clean
```

Real Chromium interaction proof established:

```text
zoom control                         PASS
keyboard pan                         PASS
reset control                        PASS
independent substrate visibility     PASS
independent subscription visibility  PASS
verified object inspection           PASS
bounded artifact access              PASS
physical platform assumed            false
```

The selected verified object was `condo-proof-66642827bace7fb1`. Presentation interaction changed only browser state; it did not alter Fabric identities, accepted geography, artifact bytes, partition identity, or subscription generation identity.

Durable evidence:

```text
/var/lib/kane-fabric/render/web-003/browser-acceptance-b216a3d
SHA256 7c0c4afbb2e7ee02586d13a051ded35366501cebf210e716cd9239ba5c05b369
```

## Active Web item

Proceed with:

```text
WEB-004
explicit verification/error/offline behavior visible to the user
```

WEB-004 should make trustworthy application state understandable without weakening the accepted verification boundary. It should distinguish at least successful verification from artifact/network failure, avoid presenting stale or unverified data as accepted, and provide bounded recovery/retry behavior using the same platform-neutral artifact-source contract.

Do not introduce ESP32-specific APIs, application identity/membership semantics, a third-party browser framework, geographic promotion behavior, or hidden fallback that bypasses artifact verification.

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

CT102 was last observed clean at `b216a3d6e0fd7be51223754c9dc3459229498346`, where WEB-003 passed repository and real-browser interaction gates. GitHub may advance through documentation/Web Application commits without invalidating that accepted runtime checkpoint.

## Execution discipline

- Work directly on `main` unless explicitly changed by the operator.
- Accepted geography changes only through explicit promotion.
- CT102 is the real runtime/browser acceptance environment; an Assistant sandbox is not acceptance evidence.
- Large generated/browser evidence stays under `/var/lib/kane-fabric`, not Git.
- Do not rerun accepted gates without an invalidating change.
- Do not install ESP-IDF merely to advance WEB-004.
- For long CT102/srv-b acceptance procedures, create a standalone script file for the operator to upload and run. Keep chat relay commands and output intentionally short.
- MS5-006 resumes when the Web Application establishes concrete physical-edge requirements or WEB-005 reaches the explicit reassessment gate.
