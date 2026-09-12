# Kane Fabric — Current Handoff

Start here, then read:

```text
docs/CURRENT_STATE.json
docs/MILESTONE_5_DESIGN.md
docs/CONSUMER_INTERFACE_GATES.md
```

Historical release records remain evidence. They are not current implementation instructions.

## 1. Released foundation

Milestones 0–4 are complete.

Milestone 4 was released on 2026-08-22 and proved:

- deterministic logical geographic partition identity;
- independently versioned Condo and Industry proof subscriptions;
- browser composition of the accepted MS3 substrate plus both subscriptions;
- cross-boundary logical-object identity;
- physical-placement independence;
- unchanged accepted geographic authority.

Accepted MS4 implementation head:

```text
9f6013d1b8b44998047f71e2b3f3e9c55c9ed298
```

MS4 release proof:

```text
3235cd4f7b7041138fe05708dbb077c07dc3ce8b8ec7a390141489460ac40634
```

Historical MS4 design authority:

```text
docs/MILESTONE_4_DESIGN.md
```

Accepted MS3 substrate identity:

```text
fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc
```

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

## 3. Accepted MS5 work

MS5-001 through MS5-003 were accepted on CT102 on 2026-09-12 at:

```text
4b9b9d3cbaaff08c90a63a7937fc2ac4efeb6dee
```

Acceptance evidence from CT102:

```text
python compileall: PASS
MS5 contract tests: 18 passed, 0 failed
worktree: clean
MS5 authority guard: valid
```

The accepted contracts establish:

- a physical edge is replaceable and cannot acquire Fabric authority;
- no irreversible ESP32 eFuse security operation is required;
- an external secure element is optional rather than the definition of a node;
- logical placement identity survives physical replacement;
- storage inventory identity is independent of storage location;
- activation selects a fully verified inventory rather than exposing mixed generations;
- rollback/recovery retain a previously verified generation;
- artifact hashing/verification supports bounded streaming;
- TLS and management keys are distinct replaceable device-local roles;
- authority/release-signing and civic-anchor keys are rejected from the edge-device key contract;
- software and external key providers are substitutable.

Current work item:

```text
MS5-004
browser secure-origin plus local AP/STA access contract
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

External feasibility work established compile-level support on ESP32-S3. Runtime tunnel behavior remains an MS5 proof obligation.

MS5-008 must measure:

- real handshake;
- routed management traffic;
- NAT/persistent keepalive;
- Wi-Fi interruption/recovery;
- repeated reconnect;
- memory/flash/task/socket/CPU cost;
- coexistence with AP/STA, storage, browser serving, and update operations.

The existing `wg-pk` estate hub may be used as controlled feasibility infrastructure. It is **not** automatically the production fleet topology. Peer lifecycle, scale, ownership, and failure isolation belong to the managed-edge architecture.

Failure of management connectivity must not invalidate already activated public Fabric artifacts.

## 6. Consumer pressure and the Mechanical Compiler

A current Mechanical Compiler identity contract was reviewed on 2026-09-12.

Its useful architectural shape is:

```text
membership / identity system
        ↓
Mechanical Compiler CT101 reverse proxy
        ↓ authorization verdict + minimum identity headers
Mechanical Compiler application
```

The Mechanical Compiler intentionally does **not** want to know:

- building geography;
- membership levels/groups;
- membership roll contents;
- eligibility rules.

That reinforces the Kane Fabric boundary: future Fabric geography may be consumed upstream by a membership system, while the application receives only the consumer-owned authorization result.

The current contract creates **no direct Kane Fabric authentication API requirement**.

The following cross-project issues are deliberately unresolved and recorded in:

```text
docs/CONSUMER_INTERFACE_GATES.md
```

Most important:

1. Kane Fabric must not become the identity provider merely because the Mechanical Compiler currently uses `kane-fabric/oidc` as an example method string.
2. Mechanical Compiler's persistent email-as-author identity must be reconciled with any address-bound/epoch-unlinkable civic membership design before those systems integrate.
3. Building-oriented membership wording must eventually reconcile with planned persistent delivery-point geography without teaching the compiler geography.
4. Kane-specific request-header/domain assumptions require review before claiming generic multi-county reuse.
5. Existing WireGuard estate topology is test infrastructure, not a fleet contract.
6. Mechanical Compiler's central TLS/reverse-proxy path does not solve MS5's offline/local browser secure-origin problem.

These are interface gates, not instructions to implement Mechanical Compiler semantics in Kane Fabric.

## 7. Consumer-exposed geography

A real civic consumer exposed generic geographic requirements that did not exist in the original roadmap:

- accepted parcel/classification source data;
- persistent delivery-point identity distinct from building identity;
- building/parcel/delivery-point geographic relationships.

These are planned as:

**Milestone 6 — Civic geography extension: parcels + delivery points**

Fabric may own:

- accepted parcel geography/classification;
- persistent delivery-point geography;
- source witnesses;
- building/parcel/delivery-point relationships;
- candidate/comparison/reconciliation/promotion lifecycle.

Fabric does not own:

- person/email authentication;
- postal challenge/anchor epochs;
- civic participation credentials;
- affected-set membership/assertion semantics;
- application authorization/ACLs;
- mail aliases or economic/application semantics.

A delivery point is geography, not evidence that a particular person lives there or participates in anything.

## 8. Forward roadmap

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

The 1.0 plan is depth before breadth: finish a complete Kane County system before making a second-county deployment a release prerequisite.

## 9. Stable operational authorities

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

The database was re-read in read-only mode at MS5 entry and still reported the five accepted releases.

GitHub `main` is software/documentation authority. CT102 is the real compiler/runtime/acceptance environment. An Assistant sandbox is not CT102.

## 10. Development discipline

- Normal development is directly on `main` unless explicitly changed by the operator.
- Do not reopen accepted MS3/MS4 gates without an invalidating change or contradiction.
- Compilation, serving, provisioning, synchronization, or consumer demand never silently promote geography.
- Use CT102 for real acceptance.
- Keep large operational artifacts outside Git under `/var/lib/kane-fabric`.
- Batch documentation at material checkpoints.
- Do not turn consumer application rules into generic Fabric semantics.
- Do not burn ESP32 eFuses as a Kane Fabric reference-edge requirement.
- Do not make WireGuard, TLS, secure-element, device, person, or membership identity into Fabric logical identity.
- Treat `docs/CONSUMER_INTERFACE_GATES.md` as a gate register, not as a backlog that Kane Fabric owns.

## 11. Next safe action

Proceed with:

```text
MS5-004
browser secure-origin plus local AP/STA access contract
```

The contract must preserve these additional cross-project constraints:

- browser/TLS device identity is not person or membership identity;
- local secure-origin operation cannot depend on Mechanical Compiler's central reverse-proxy/TLS arrangement;
- no application authentication headers become a Kane Fabric protocol;
- future delivery-point geography remains outside the browser-serving device identity.

After MS5-004, continue in the normative order defined only by `docs/MILESTONE_5_DESIGN.md`.
