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

Milestone 4 proved deterministic logical geographic partition identity, independently versioned subscriptions, real browser composition of the accepted MS3 substrate plus subscriptions, cross-boundary logical-object identity, physical-placement independence, and unchanged accepted geographic authority.

Do not reopen accepted MS3/MS4 gates without an invalidating implementation/environment change or contradictory observation.

## 2. Active milestone and current priority

Current milestone:

**Milestone 5 — Reference Physical Edge Architecture**

Normative MS5 authority:

```text
docs/MILESTONE_5_DESIGN.md
```

Default hardware/reference boundary:

```text
docs/ESP32_EDGE_REFERENCE.md
```

Current priority workstream:

```text
Kane Fabric Web Application
docs/WEB_APPLICATION_DESIGN.md
```

MS5-006 remains the next normative MS5 item, but is deliberately deferred while the Web Application establishes the real browser consumer requirements. This is a sequencing decision, not abandonment or renumbering of MS5.

Priority rule:

> Continue developing the parts Kane Fabric controls until third-party platform integration becomes necessary to advance the system.

## 3. Accepted MS5 checkpoints

MS5-001 through MS5-003 were originally accepted at:

```text
4b9b9d3cbaaff08c90a63a7937fc2ac4efeb6dee
```

A bounded MS5-001/002 cross-contract correction was implemented at:

```text
025b55df42f3cc9d3613a2ae845952ce2bc033c7
```

and accepted on CT102 at:

```text
762041080fa51e6441546b7ba14bd07792676b9f
```

with 20 passing contract tests.

MS5-004 browser secure-origin/AP+STA access contract was accepted on CT102 at:

```text
07f4f71f51b538bc1fc5d446691e0bbcfc03cd9c
```

with 28 passing contract tests.

MS5-005 froze the default reference firmware SDK/toolchain and retained-dependency selection plan. ESP-IDF v6.0.3 is pinned at commit:

```text
76f5dedd9950a3012fee8fb7d5586df21fc67802
```

The submodule-complete release asset SHA-256 is:

```text
748b12484402d8a1cb58ba68b7545d2a1f96d36820ab0145e0332c8348ba5ab7
```

MS5-005 was accepted on CT102 at:

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

Do not rerun MS5-001..005 merely because documentation or Web Application source advances after that implementation head.

## 4. Default edge platform is not the architecture

ESP32-S3 is the **default reference edge platform**, not a permanent Kane Fabric platform requirement.

A conforming edge may eventually be another microcontroller, an SBC, a general-purpose appliance, or a software-only server if it satisfies the same durable browser/publication and edge-authority contracts.

ESP32-S3 hardware, the wider ESP32 line, ESP-IDF, compiler releases, and supporting components are third-party implementations outside Kane Fabric control. They may evolve incompatibly or disappear. Kane Fabric logical identity and browser semantics must remain valid if that occurs.

Therefore:

- no Fabric logical identity depends on ESP32 identity or continued ESP32 availability;
- the Web Application must not require an ESP32-specific JavaScript API or device RPC protocol;
- the accepted ESP-IDF/toolchain selection remains reference groundwork, not architectural lock-in;
- hardware-specific implementation resumes when consumer-facing requirements make it necessary.

## 5. Web Application workstream

The repository already contains accepted browser primitives rather than only server-side code.

MS3 proved immutable substrate verification, WebCrypto SHA-256, selective byte-range fetch, decompression, and Canvas rendering.

MS4 proved deterministic partition/subscription loading and verified browser composition. The existing proof pages are verification harnesses, not a durable user application.

WEB-001 introduced the first application shell with a platform-neutral artifact-source boundary, explicit loading/verification/failure states, responsive Canvas presentation, substrate identity display, subscription-generation display, and no third-party JavaScript/CSS dependency graph.

WEB-001 was accepted on CT102 on 2026-09-14 at:

```text
98873196438f87f946796d9b4ffd2ff2a5a135e4
```

Acceptance evidence:

```text
MS5 work-sequence authority guard: valid
dependency policy: PASS
JavaScript syntax: PASS
Web unit tests: 8 passed, 0 failed
worktree: clean
```

This is now the last observed accepted CT102 checkout head.

The next Web item is:

```text
WEB-002
accepted MS3/MS4 map composition as a user-facing vertical slice
```

WEB-002 should reuse the accepted browser modules and accepted Kane County artifacts rather than duplicate their validation or rendering logic.

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

CT102 was last observed clean at `98873196438f87f946796d9b4ffd2ff2a5a135e4`, where WEB-001 passed its repository acceptance gate. The last accepted MS5 implementation checkpoint remains `aed812df8c5e37bb1843e022d7a7813dc7e8e862` with 36 passing MS5 contract tests. These are separate accepted claims and neither should be conflated with the other.

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
WEB-002
accepted MS3/MS4 map composition as a user-facing vertical slice
```

Use the existing accepted MS3/MS4 browser modules and accepted Kane County artifacts. WEB-002 should prove that the new application surface—not merely the older proof pages—can present verified accepted Fabric data in a normal browser while keeping its artifact-source boundary platform-neutral.

Do **not** install ESP-IDF or begin MS5-006 merely to advance WEB-002. MS5-006 resumes when the Web Application establishes concrete serving/storage requirements or reaches its explicit reassessment gate.
