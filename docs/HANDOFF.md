# Kane Fabric — Current Handoff

This is the current operational handoff. Start here, then read `docs/CURRENT_STATE.json` and the active milestone design.

Historical release records remain evidence. They are not current implementation instructions.

## 1. Current checkpoint

Milestones 0–4 are complete. Milestone 4 was released on 2026-08-22 and proved:

- deterministic logical geographic partition identity;
- independently versioned Condo and Industry proof subscriptions;
- browser composition of accepted MS3 substrate plus both subscriptions;
- cross-boundary logical-object identity;
- physical placement independence;
- unchanged accepted geographic authority.

Accepted MS4 implementation head:

```text
9f6013d1b8b44998047f71e2b3f3e9c55c9ed298
```

MS4 release proof:

```text
3235cd4f7b7041138fe05708dbb077c07dc3ce8b8ec7a390141489460ac40634
```

The repository was deliberately paused after the MS4 documentation closeout. The pre-MS5-redesign `main` head was:

```text
3adf081791943c8fc1552580abf34068388f4c89
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

Current work item:

```text
MS5-001
physical-edge threat model, trust boundary, and replaceability contract
```

Do not recreate a second MS5 work sequence in another current document.

## 3. Why MS5 was redesigned

The old roadmap treated MS5 mostly as an ESP32 HTTP-serving exercise.

Two later developments invalidated that simplification:

1. the first real consumer exposed missing generic Fabric primitives, especially persistent delivery-point geography and accepted parcel classification;
2. ESP32-S3 WireGuard feasibility work showed that managed edge connectivity is plausible, but also made physical-device identity/provisioning/replacement a first-class concern.

The resulting decision is that the physical edge must be treated as disposable infrastructure rather than as a permanent root of trust.

## 4. Approved physical-edge security position

These points are settled unless explicitly changed:

- **Do not require irreversible ESP32 security eFuse burning.**
- The ESP32-S3 is replaceable compute/radio/storage.
- Physical compromise of one edge is tolerated as a local/recoverable failure.
- The project protects strongly against fleet-class firmware/provisioning failure and authority/signing compromise.
- Geographic promotion authority, release-signing authority, and CA/issuing authority never live on an edge.
- Software-held device keys are acceptable for the reference edge where the deployment threat model permits them.
- A separate external secure element may be supported through a key-provider boundary, but it is optional and never defines Fabric logical identity.
- TLS identity, management/WireGuard identity, optional secure-element identity, hardware identity, storage location, partition identity, subscription identity, and substrate identity are distinct.
- Normal firmware-update authenticity is useful; physical inability of an owner to reflash one ESP32 is not an MS5 goal.

## 5. WireGuard position

WireGuard is a preferred management/synchronization candidate, not an accepted Fabric dependency and not logical identity.

External feasibility evidence established that a maintained WireGuard component could compile for ESP32-S3 against the then-current ESP-IDF development environment. Runtime tunnel operation on the ESP32 was not yet proven.

MS5 owns the runtime feasibility proof:

- real handshake;
- NAT/persistent keepalive;
- Wi-Fi interruption/recovery;
- repeated reconnect;
- memory/flash/task/socket/CPU cost;
- coexistence with AP/STA, storage, browser serving, and update operations.

If WireGuard fails that proof, Kane Fabric chooses another management transport without changing MS3/MS4 identities.

## 6. Consumer-exposed geography

The first real civic consumer exposed two generic geographic requirements that did not exist in the original roadmap:

- accepted parcel/classification source data;
- persistent delivery-point identity distinct from building identity.

These are planned as **Milestone 6 — Civic geography extension: parcels + delivery points**.

The Fabric boundary is strict:

Fabric may own:

- accepted parcel geography/classification;
- persistent delivery-point geography;
- building/parcel/delivery-point relationships;
- source witnesses and promotion/reconciliation lifecycle.

Fabric does not own:

- postal challenge/anchor epochs;
- person or participant identity;
- civic participation credentials;
- affected-set assertions;
- consumer accounts/mail aliases/economic semantics.

A delivery point is geography, not proof that a particular person lives there or participates in anything.

## 7. Forward roadmap

```text
MS0–MS4   logical Fabric foundation                   COMPLETE
MS5       reference physical edge architecture        CURRENT
MS6       parcels + persistent delivery-point geography
MS7       managed edge synchronization
MS8       multi-node distribution
           ↓
Kane Fabric 1.0
MS9       generic second-county bootstrap             POST-1.0
```

The 1.0 plan is depth before breadth: finish a complete Kane County system before making a second-county deployment a release prerequisite.

## 8. Stable authorities

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
last recorded checkout: /tmp/kane-fabric-ms2
```

Authoritative database last verified during MS4:

```text
/var/lib/kane-fabric/database/kane-county-fabric.gpkg
SHA256 31e362b696a37f1b9c45ae355c5669511a3128c17a651108a62e20d1cedebd67
```

Accepted MS3 substrate:

```text
fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc
```

GitHub `main` is software/documentation authority. CT102 is the real compiler/runtime/acceptance environment. An Assistant sandbox is not CT102.

## 9. Development discipline

- Normal development is directly on `main` unless explicitly changed by the operator.
- Do not reopen accepted MS3/MS4 gates without an invalidating change or contradiction.
- Compilation, serving, edge provisioning, or synchronization never silently promote geography.
- Use the recorded CT102 checkout first; verify it before state-changing work.
- Keep large operational artifacts outside Git under `/var/lib/kane-fabric`.
- Batch documentation at material checkpoints rather than after every command.
- Do not turn the first consumer's application rules into generic Fabric semantics.
- Do not burn ESP32 eFuses as a Kane Fabric reference-edge requirement.

## 10. Next safe action

1. Verify the recorded CT102 checkout is clean and points at the expected repository.
2. Fast-forward it to current GitHub `main` only if the normal preconditions pass.
3. Begin **MS5-001** from `docs/MILESTONE_5_DESIGN.md`.
4. Do not begin firmware implementation until the MS5-001/002/003 contracts make the physical trust, storage, activation, and key-provider boundaries explicit.
