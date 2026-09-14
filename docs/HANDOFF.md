# Kane Fabric — Current Handoff

Start here, then read:

```text
docs/DEVELOPMENT_PROCESS.md
docs/CURRENT_STATE.json
docs/SESSION_START.md
docs/MILESTONE_5_DESIGN.md
docs/CONSUMER_INTERFACE_GATES.md
```

`docs/DEVELOPMENT_PROCESS.md` defines how work is executed, which system owns each kind of state, how CT102 acceptance differs from GitHub publication, when the user may act as a bounded terminal relay, and when accepted gates must or must not be rerun. Read it before issuing infrastructure commands or changing the repository.

Historical release records remain evidence. They are not current implementation instructions.

## 1. Released foundation

Milestones 0–4 are complete.

Milestone 4 was released on 2026-08-22 and proved deterministic logical geographic partition identity, independently versioned Condo and Industry proof subscriptions, browser composition of the accepted MS3 substrate plus both subscriptions, cross-boundary logical-object identity, physical-placement independence, and unchanged accepted geographic authority.

Accepted MS4 implementation head:

```text
9f6013d1b8b44998047f71e2b3f3e9c55c9ed298
```

MS4 release proof:

```text
3235cd4f7b7041138fe05708dbb077c07dc3ce8b8ec7a390141489460ac40634
```

Accepted MS3 substrate identity:

```text
fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc
```

Do not reopen accepted MS3/MS4 gates without an invalidating change or contradiction.

## 2. Active milestone

Current milestone:

**Milestone 5 — Reference Physical Edge Architecture**

Normative design/work-sequence authority:

```text
docs/MILESTONE_5_DESIGN.md
```

Hardware/reference boundary:

```text
docs/ESP32_EDGE_REFERENCE.md
```

Cross-project non-normative gate register:

```text
docs/CONSUMER_INTERFACE_GATES.md
```

Do not recreate a second complete MS5 work sequence in another current document.

## 3. Accepted MS5 checkpoints

MS5-001 through MS5-003 were originally accepted on CT102 on 2026-09-12 at:

```text
4b9b9d3cbaaff08c90a63a7937fc2ac4efeb6dee
```

with 18 passing contract tests.

A later handoff review identified one bounded cross-contract gap: the edge descriptor and storage inventory each carried a `logical_placement_sha256`, but activation did not enforce equality between them. It also identified an undefined activation state in which rollback existed while no active inventory existed.

The bounded correction was implemented at:

```text
025b55df42f3cc9d3613a2ae845952ce2bc033c7
```

The correction:

- requires activation to receive and validate the actual edge descriptor;
- rejects a candidate inventory whose logical placement differs from the edge logical placement;
- rejects activation state with rollback inventory but no active inventory;
- adds regression tests for both cases.

This is a join/enforcement correction to the existing MS5-001/002 contracts. It does **not** redesign MS5, MS3/MS4 identity, or the roadmap.

The corrected MS5-001 through MS5-003 contract set was accepted on CT102 on 2026-09-14 at checkout head:

```text
762041080fa51e6441546b7ba14bd07792676b9f
```

Acceptance evidence:

```text
MS5 work-sequence authority guard: valid
python compileall: PASS
MS5 contract tests: 20 passed, 0 failed
worktree: clean
```

MS5-004 then added the browser secure-origin plus local AP/STA access contract. It requires a physical edge access profile that is bound to the actual edge instance and browser-TLS key provider, uses HTTPS rather than arbitrary LAN HTTP, preserves the boundary between browser/TLS identity and Fabric geography, and keeps AP+STA shared-radio/channel behavior as an explicit measurement obligation rather than an assumption.

MS5-004 was accepted on CT102 on 2026-09-14 at:

```text
07f4f71f51b538bc1fc5d446691e0bbcfc03cd9c
```

Acceptance evidence:

```text
MS5 work-sequence authority guard: valid
python compileall: PASS
MS5 contract tests: 28 passed, 0 failed
worktree: clean
```

MS5-005 froze the reference firmware SDK/toolchain and retained-dependency plan. The selected SDK is ESP-IDF v6.0.3 at commit `76f5dedd9950a3012fee8fb7d5586df21fc67802`, with the submodule-complete release asset pinned by SHA-256. The ESP32-S3 Xtensa compiler is pinned by the selected ESP-IDF tool manifest. WireGuard remains explicitly unretained until MS5-008 runtime/resource acceptance.

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

This checkpoint is accepted. Do not rerun or reopen MS5-001..005 merely because documentation advances after this accepted head. Rerun only if an implementation, dependency, environment change, or contradictory live observation invalidates an accepted gate.

The next normative work item is now:

```text
MS5-006
ESP32-S3 immutable artifact storage and HTTP byte-range implementation
```

## 4. Approved physical-edge security position

These points are settled unless explicitly changed:

- Do not require irreversible ESP32 security eFuse burning.
- ESP32-S3 is replaceable compute/radio/storage.
- Physical compromise of one edge is a local/recoverable failure.
- Fleet-class firmware/provisioning failure and authority/signing compromise are systemic threats.
- Geographic promotion authority, Fabric release-signing authority, and CA/issuing authority never live on an edge.
- Software-held replaceable device keys are acceptable for the reference edge where appropriate.
- A separate external secure element may implement a key-provider role, but it is optional and never defines Fabric logical identity.
- TLS identity, management/WireGuard identity, optional secure-element identity, hardware identity, storage location, partition identity, subscription identity, and substrate identity remain distinct.
- Firmware-update authenticity is useful; preventing a determined owner from reflashing one ESP32 is not an MS5 objective.

## 5. WireGuard position

WireGuard is a preferred management/synchronization candidate, not an accepted Fabric dependency and not logical identity.

External feasibility work established compile-level support on ESP32-S3. Runtime tunnel behavior remains an MS5 proof obligation in MS5-008: real handshake, routed management traffic, NAT/persistent keepalive, Wi-Fi interruption and reconnect behavior, repeated disconnect/reconnect, flash/RAM/task/socket/CPU cost, and coexistence with AP/STA, storage, browser serving, and update operations.

The existing `wg-pk` estate hub may be used as controlled feasibility infrastructure. It is not automatically the production fleet topology. Failure of management connectivity must not invalidate already activated public Fabric artifacts.

## 6. Consumer pressure and Mechanical Compiler

Mechanical Compiler is currently a relying party behind its own authorization boundary. It intentionally does not want building geography, membership groups, membership-roll contents, or eligibility rules in the application.

That reinforces the Fabric boundary:

```text
accepted Fabric geography
        ↓
consumer-owned membership / eligibility system
        ↓
minimal authorization result
        ↓
Mechanical Compiler
```

The current Mechanical Compiler contract creates no direct Kane Fabric authentication API requirement.

Cross-project issues are tracked only in:

```text
docs/CONSUMER_INTERFACE_GATES.md
```

Important unresolved issues include persistent email authorship versus any epoch-unlinkable civic membership model, building-oriented membership wording versus future delivery-point geography, existing WireGuard estate topology versus future fleet lifecycle, and the fact that Mechanical Compiler central TLS does not solve MS5's local/offline browser secure-origin requirement.

One previously identified issue is resolved: Mechanical Compiler removed its earlier Kane-specific trusted-header naming and made that relying-party interface deployment-neutral. Kane Fabric intentionally records no consumer-owned header syntax.

Do not implement Mechanical Compiler authentication, membership, OIDC, proxy ACL, or request-header semantics inside Kane Fabric.

## 7. Consumer-exposed geography and forward roadmap

A real civic consumer exposed generic future Fabric requirements:

- accepted parcel/classification source data;
- persistent delivery-point identity distinct from building identity;
- building/parcel/delivery-point geographic relationships.

These remain planned for MS6. Fabric owns geography and source/promotion/reconciliation lifecycle, not person identity, civic participation credentials, application authorization, mail aliases, or economic semantics.

Forward roadmap:

```text
MS0–MS4   logical Fabric foundation                    COMPLETE
MS5       reference physical edge architecture         CURRENT
MS6       parcels + persistent delivery-point geography
MS7       managed edge synchronization
MS8       multi-node distribution
           ↓
Kane Fabric 1.0
MS9       generic second-county bootstrap              POST-1.0
```

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

GitHub `main` is software/documentation authority. CT102 is the real compiler/runtime/acceptance environment. An Assistant sandbox is not CT102.

CT102 was last observed clean at `aed812df8c5e37bb1843e022d7a7813dc7e8e862`, where MS5-005 and the previously accepted MS5 contracts passed the 36-test acceptance gate. GitHub `main` may be ahead by documentation-only material-checkpoint commits; that alone does not invalidate the accepted implementation gate.

## 9. Development discipline

- Normal development is directly on `main` unless explicitly changed by the operator.
- Compilation, serving, provisioning, synchronization, or consumer demand never silently promote geography.
- Use CT102 for real acceptance.
- Keep large operational artifacts outside Git under `/var/lib/kane-fabric`.
- Batch documentation at material checkpoints.
- Do not turn consumer application rules into generic Fabric semantics.
- Do not burn ESP32 eFuses as a Kane Fabric reference-edge requirement.
- Do not make WireGuard, TLS, secure-element, device, person, or membership identity into Fabric logical identity.
- Treat `docs/CONSUMER_INTERFACE_GATES.md` as a gate register, not a backlog that Kane Fabric owns.
- Do not reopen MS5-001..005 unless a later implementation, dependency, environment change, or contradictory observation invalidates an accepted contract.

## 10. Next safe action

Proceed with:

```text
MS5-006
ESP32-S3 immutable artifact storage and HTTP byte-range implementation
```

Use `docs/MILESTONE_5_DESIGN.md` as the sole detailed work-sequence authority. MS5-006 must implement bounded immutable artifact access and HTTP single-byte-range behavior for the ESP32-S3 reference edge while preserving the accepted storage/activation identity contracts and browser-facing publication semantics.

Do not rerun the accepted MS5-001..005 gate merely because this handoff/current-state checkpoint advances documentation beyond the CT102 acceptance head.

After MS5-006, continue in the normative order defined only by `docs/MILESTONE_5_DESIGN.md`.
