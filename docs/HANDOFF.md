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

`docs/MILESTONE_5_DESIGN.md` remains the sole detailed authority for the Milestone 5 sequence. `docs/WEB_APPLICATION_DESIGN.md` is the sole detailed authority for the current Web Application workstream.

## Released foundation

Milestones 0–4 are complete.

Accepted MS3 substrate identity:

```text
fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc
```

Accepted MS4 implementation head:

```text
9f6013d1b8b44998047f71e2b3f3e9c55c9ed298
```

Accepted MS4 composition identity:

```text
a58c8398248cee05b7baad9ae289fe0581bdb3624ce1aff3aa8a49721f92ee53
```

Do not reopen accepted MS3/MS4 gates without an invalidating implementation/environment change or contradictory observation.

## Current priority

Milestone 5 remains current, with `MS5-006` the next normative MS5 item. It is deliberately deferred while Kane Fabric develops the browser application and other project-controlled components.

Priority rule:

> Continue developing the parts Kane Fabric controls until third-party platform integration becomes necessary to advance the system.

ESP32-S3 is the default reference edge platform, not the definition of a Kane Fabric edge. Other microcontrollers, SBCs, appliances, or software-only implementations may satisfy the same durable browser/publication and authority contracts. No Fabric logical identity or Web Application behavior may depend on continued ESP32 availability.

## Accepted MS5 checkpoint

MS5-005 remains the last accepted MS5 implementation checkpoint:

```text
aed812df8c5e37bb1843e022d7a7813dc7e8e862
```

Acceptance evidence:

```text
MS5 work-sequence authority guard: valid
dependency policy: PASS
python compileall: PASS
MS5 contract tests: 36 passed, 0 failed
worktree: clean
```

ESP-IDF v6.0.3 is pinned as default-reference groundwork. WireGuard remains unretained pending MS5-008 runtime/resource proof. Do not rerun MS5-001..005 merely because Web Application source advances.

## Web Application accepted work

### WEB-001

Accepted on CT102 at:

```text
98873196438f87f946796d9b4ffd2ff2a5a135e4
```

It established the dependency-free application shell, platform-neutral artifact-source configuration, responsive Canvas presentation, and explicit loading/verification/failure states. Eight Web unit tests passed.

### WEB-002

Accepted on CT102 at:

```text
ef3c08f77442e1a8cefe6a0567b50e10ce010dd3
```

Repository gate:

```text
MS5 work-sequence authority guard: valid
dependency policy: PASS
JavaScript/Python syntax: PASS
Web unit tests: 13 passed, 0 failed
worktree: clean
```

The originally released MS3 package directory was no longer retained. This was not treated as a new release. The existing deterministic MS3 compiler reproduced the exact released four-file publication from the unchanged authoritative database at:

```text
/var/lib/kane-fabric/render/web-002/ms3-accepted-reproduction
```

The reproduced files matched every released byte length and SHA-256 exactly, totaling `7201386` bytes. The authoritative GeoPackage remained byte-identical.

WEB-002 then passed a real Chromium application gate using three independent ordinary HTTP origins for application code, MS3 substrate, and MS4 composition. This directly exercised the platform-neutral artifact-source boundary.

Observed browser result:

```text
browser                 Chromium 151.0.7922.137
partition               west
subscription objects    2
visible overlays         2
MS3 bounded range reads PASS
MS4 verified reads      PASS
physical platform       not assumed
```

Durable evidence:

```text
/var/lib/kane-fabric/render/web-002/browser-acceptance-ef3c08f
SHA256 cef970419e4983c845ac19956f4d2f9a7245444d90acb0d81ee917c907090d5a
```

The new Web Application surface—not the historical MS3/MS4 proof pages—therefore consumes and visibly composes the accepted Kane County artifacts in a normal browser.

## Active Web item

Proceed with:

```text
WEB-003
geographic navigation, layer/subscription visibility, and inspection interaction
```

WEB-003 should add human interaction on top of the accepted verified composition result without moving verification logic out of the existing MS3/MS4 browser modules. Expected scope includes geographic navigation, visibility controls for substrate/subscription presentation, and inspection of verified objects/identities.

Do not introduce an ESP32-specific JavaScript API, hardware management semantics, a third-party browser framework, application identity/membership semantics, or geographic promotion behavior.

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

CT102 was last observed clean at `ef3c08f77442e1a8cefe6a0567b50e10ce010dd3`, where WEB-002 passed its repository and real-browser gates. GitHub may advance by documentation/Web Application commits without invalidating that accepted runtime checkpoint.

## Development discipline

- Work directly on `main` unless explicitly changed by the operator.
- Accepted geography changes only through explicit promotion.
- CT102 is the real runtime/browser acceptance environment; an Assistant sandbox is not acceptance evidence.
- Large generated/browser evidence remains under `/var/lib/kane-fabric`, not Git.
- Do not rerun accepted gates without an invalidating change.
- Do not install ESP-IDF merely to advance WEB-003 or WEB-004.
- MS5-006 resumes when Web Application work establishes concrete physical-edge requirements or WEB-005 reaches the explicit reassessment gate.
