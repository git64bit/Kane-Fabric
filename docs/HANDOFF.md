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

`docs/DEVELOPMENT_PROCESS.md` defines execution authority and acceptance discipline. `docs/MILESTONE_5_DESIGN.md` remains the sole detailed authority for the Milestone 5 sequence. `docs/WEB_APPLICATION_DESIGN.md` is the detailed authority for the current Web Application priority workstream.

Historical release records remain evidence. They are not current implementation instructions.

## 1. Released foundation

Milestones 0–4 are complete.

Milestone 4 was released on 2026-08-22 and proved deterministic logical geographic partition identity, independently versioned subscriptions, real browser composition of the accepted MS3 substrate plus subscriptions, cross-boundary logical-object identity, physical-placement independence, and unchanged accepted geographic authority.

Accepted MS4 implementation head:

```text
9f6013d1b8b44998047f71e2b3f3e9c55c9ed298
```

Accepted MS3 substrate identity:

```text
fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc
```

MS4 release proof:

```text
3235cd4f7b7041138fe05708dbb077c07dc3ce8b8ec7a390141489460ac40634
```

Do not reopen accepted MS3/MS4 gates without an invalidating implementation/environment change or contradictory observation.

## 2. Active milestone and current priority

Current milestone:

**Milestone 5 — Reference Physical Edge Architecture**

Normative MS5 design/work-sequence authority:

```text
docs/MILESTONE_5_DESIGN.md
```

Hardware/reference boundary:

```text
docs/ESP32_EDGE_REFERENCE.md
```

Current priority workstream:

```text
Kane Fabric Web Application
docs/WEB_APPLICATION_DESIGN.md
```

MS5-006 remains the next normative MS5 work item, but it is deliberately deferred while the Web Application establishes the real browser consumer requirements. This does not renumber, abandon, or redesign Milestone 5.

The priority rule is:

> Continue developing the parts Kane Fabric controls until third-party platform integration becomes necessary to advance the system.

## 3. Accepted MS5 checkpoints

MS5-001 through MS5-003 were originally accepted on CT102 on 2026-09-12 at:

```text
4b9b9d3cbaaff08c90a63a7937fc2ac4efeb6dee
```

with 18 passing contract tests.

A bounded MS5-001/002 cross-contract correction then bound storage activation to the actual edge logical placement and rejected rollback-without-active state. The correction implementation head is:

```text
025b55df42f3cc9d3613a2ae845952ce2bc033c7
```

The corrected contract set was accepted on CT102 on 2026-09-14 at:

```text
762041080fa51e6441546b7ba14bd07792676b9f
```

with a valid authority guard, compileall pass, 20 passing tests, and clean worktree.

MS5-004 added the browser secure-origin plus local AP/STA access contract. It was accepted on CT102 on 2026-09-14 at:

```text
07f4f71f51b538bc1fc5d446691e0bbcfc03cd9c
```

with a valid authority guard, compileall pass, 28 passing tests, and clean worktree.

MS5-005 froze the default reference firmware SDK/toolchain and retained-dependency selection plan. ESP-IDF v6.0.3 is pinned at commit:

```text
76f5dedd9950a3012fee8fb7d5586df21fc67802
```

The submodule-complete release asset is pinned by SHA-256:

```text
748b12484402d8a1cb58ba68b7545d2a1f96d36820ab0145e0332c8348ba5ab7
```

WireGuard remains explicitly unretained until MS5-008 runtime/resource acceptance.

MS5-005 was accepted on CT102 on 2026-09-14 at:

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

This is the last accepted CT102 MS5 implementation checkpoint. Do not rerun MS5-001..005 merely because documentation or Web Application source advances after this head.

## 4. Default edge platform is not the architecture

ESP32-S3 is the **default reference edge platform**. It is not a permanent Kane Fabric platform requirement.

A conforming edge may eventually be another microcontroller, an SBC, a general-purpose appliance, or a software-only server so long as it satisfies the same durable browser/publication and edge-authority contracts.

This is important because ESP32-S3 hardware, the wider ESP32 product line, ESP-IDF, compiler releases, and supporting components are third-party implementations outside Kane Fabric control. They may evolve incompatibly or disappear.

Therefore:

- no Fabric logical identity may depend on ESP32 identity or continued ESP32 availability;
- the Web Application must not require an ESP32-specific JavaScript API or device RPC protocol;
- the accepted ESP-IDF v6.0.3/toolchain selection remains useful reference groundwork, not architectural lock-in;
- hardware-specific implementation resumes when consumer-facing requirements make it necessary.

## 5. Web Application foundation already available

The repository already contains meaningful browser infrastructure.

MS3 browser modules have proved immutable substrate verification, WebCrypto SHA-256, selective byte-range fetch, decompression, and Canvas rendering.

MS4 browser modules have proved deterministic partition/subscription loading and verified browser composition. The existing `substrate/browser/render.html` and `ms4/browser/proof.html` are proof harnesses, not a user application.

The current task is therefore to build a durable human-facing application shell around accepted browser primitives, not to rewrite the substrate/partition logic.

The first Web work item is named only here by status; the detailed Web sequence lives only in `docs/WEB_APPLICATION_DESIGN.md`:

```text
WEB-001 application shell + platform-neutral artifact-source configuration
```

## 6. Approved physical-edge security position

These points remain settled unless explicitly invalidated:

- no irreversible ESP32 security eFuse operation is required;
- physical compromise of one edge is local/recoverable;
- fleet-class firmware/provisioning failure and authority/signing compromise are systemic threats;
- geographic promotion authority, Fabric release-signing authority, and CA/issuing authority never live on an edge;
- software-held replaceable device keys are acceptable for the default reference edge;
- an external secure element is optional and substitutable;
- TLS, management/WireGuard, secure-element, hardware, storage, substrate, partition, and subscription identities remain distinct;
- firmware authenticity protects normal fleet operation but does not make one physical device authoritative.

## 7. WireGuard and consumer boundaries

WireGuard is a preferred management/synchronization candidate, not an accepted Fabric dependency and not logical identity. Compile feasibility exists; runtime handshake/recovery/resource/coexistence proof remains MS5-008 work.

Mechanical Compiler remains a relying party behind its own authorization boundary. Kane Fabric must not implement Mechanical Compiler authentication, membership, OIDC, proxy ACL, or request-header semantics.

Cross-project issues remain tracked in:

```text
docs/CONSUMER_INTERFACE_GATES.md
```

Generic future geography exposed by real consumers remains planned for MS6: accepted parcel/classification data, persistent delivery-point identity, and building/parcel/delivery-point geographic relationships. Fabric owns geography, not person/account/participation semantics.

## 8. Stable operational authorities

Repository:

```text
git64bit/Kane-Fabric
branch: main
```

Execution:

```text
Proxmox host: srv-b
Kane Fabric container: CT102 / kane-fabric
operational root: /var/lib/kane-fabric
checkout: /tmp/kane-fabric-ms2
```

Authoritative database:

```text
/var/lib/kane-fabric/database/kane-county-fabric.gpkg
SHA256 31e362b696a37f1b9c45ae355c5669511a3128c17a651108a62e20d1cedebd67
```

GitHub `main` is software/documentation authority. CT102 is the real runtime/compiler/acceptance environment. An Assistant sandbox is not CT102 evidence.

CT102 was last observed clean at `aed812df8c5e37bb1843e022d7a7813dc7e8e862`, where MS5-005 and the prior MS5 contracts passed the 36-test acceptance gate. GitHub may advance by documentation/Web Application work without invalidating that accepted MS5 implementation gate.

## 9. Development discipline

- Work directly on `main` unless explicitly changed by the operator.
- Accepted geography changes only through explicit promotion.
- Use CT102 for real application/browser acceptance when such a claim is made.
- Keep large operational artifacts outside Git under `/var/lib/kane-fabric`.
- Do not introduce third-party browser dependencies for convenience; use `docs/DEPENDENCY_POLICY.md`.
- Do not turn consumer rules into generic Fabric semantics.
- Do not make a default hardware platform into Fabric logical identity.
- Do not rerun accepted gates without an invalidating change.

## 10. Next safe action

Proceed with:

```text
WEB-001
application shell + platform-neutral artifact-source configuration
```

Use the existing accepted MS3/MS4 browser modules. Build a dependency-free browser application shell with a platform-neutral artifact-source boundary and explicit loading/verification/failure states.

Do **not** install ESP-IDF or begin MS5-006 merely to advance the Web Application. MS5-006 resumes when the Web Application establishes concrete serving/storage requirements or the Web workstream reaches its explicit reassessment gate.
