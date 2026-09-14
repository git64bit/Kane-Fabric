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

The exact released MS3 publication is available as a byte-identical deterministic reproduction at:

```text
/var/lib/kane-fabric/render/web-002/ms3-accepted-reproduction
```

This is not a new geographic release.

## Milestone 5 status

Milestone 5 remains current. `MS5-006` is the next normative MS5 item, but it remains deferred until WEB-005 explicitly reassesses the stable browser/edge serving contract.

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

ESP32-S3 remains the default reference edge platform, not the architecture. No Fabric logical identity or browser behavior may depend on continued ESP32 availability.

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

The application consumed accepted MS3/MS4 artifacts in real Chromium through independent ordinary HTTP sources, rendered verified composition, and preserved bounded byte-range access.

Evidence:

```text
/var/lib/kane-fabric/render/web-002/browser-acceptance-ef3c08f
SHA256 cef970419e4983c845ac19956f4d2f9a7245444d90acb0d81ee917c907090d5a
```

### WEB-003

Accepted at:

```text
b216a3d6e0fd7be51223754c9dc3459229498346
```

It proved real-browser navigation, independent layer/subscription visibility, verified object inspection, and bounded artifact access without changing Fabric identities.

Evidence:

```text
/var/lib/kane-fabric/render/web-003/browser-acceptance-b216a3d
SHA256 7c0c4afbb2e7ee02586d13a051ded35366501cebf210e716cd9239ba5c05b369
```

### WEB-004

Accepted at:

```text
73252b6a3c87ba47b7f68f3e3206056607e1e53a
```

Repository gate:

```text
MS5 authority guard     valid
dependency policy       PASS
JavaScript syntax       PASS
Web tests               28 passed, 0 failed
worktree                clean
```

Real Chromium failure/recovery proof established:

```text
verified data survives connectivity loss without new artifact fetch   PASS
corrupt artifact bytes fail verification                              PASS
failed verification clears accepted presentation                      PASS
o connectivity before verification fails closed                       PASS
connection-restored retry prompt                                       PASS
explicit retry recovery                                                PASS
physical platform assumed                                              false
```

A verified browser may continue displaying data that was already verified before connectivity loss, but no new fetch or verification claim is made while offline. Before verification, offline/network/integrity failures remain visibly not verified.

Evidence:

```text
/var/lib/kane-fabric/render/web-004/browser-acceptance-73252b6
SHA256 f9054cb884568e8503a8e7f416065aa5ea97bcd5b8082494a5ade00cb4db4b50
```

## Active Web item

Proceed with:

```text
WEB-005
real-browser acceptance against accepted Kane County artifacts and reassessment of edge requirements
```

WEB-005 is primarily a consolidation and decision gate, not an invitation to redesign the accepted browser application. It should determine which concrete serving/storage properties are now actually required from a physical edge and whether those requirements are stable enough to resume `MS5-006` against the default ESP32-S3 reference implementation.

The accepted browser contract already requires ordinary browser fetch semantics, exact byte-range support for flat substrate components, immutable accepted artifact identities, WebCrypto-capable secure browser context at the physical edge, and no device-specific JavaScript or hardware identity semantics.

Do not weaken or alter those accepted contracts merely to make the reference hardware implementation easier.

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

CT102 was last observed clean at `73252b6a3c87ba47b7f68f3e3206056607e1e53a`, where WEB-004 passed repository and real-browser failure/recovery gates. GitHub may advance through documentation commits without invalidating that accepted runtime checkpoint.

## Execution discipline

- Work directly on `main` unless explicitly changed by the operator.
- Accepted geography changes only through explicit promotion.
- CT102 is the real runtime/browser acceptance environment; an Assistant sandbox is not acceptance evidence.
- Large generated/browser evidence stays under `/var/lib/kane-fabric`, not Git.
- Do not rerun accepted gates without an invalidating change.
- For long CT102/srv-b acceptance procedures, create a standalone script file for the operator to upload and run. Keep chat relay commands and successful output intentionally short.
- Resume `MS5-006` only after WEB-005 explicitly concludes that the browser-facing serving/storage contract is stable enough for physical-edge implementation.
