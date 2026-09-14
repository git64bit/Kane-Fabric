# Kane Fabric

Kane Fabric is public civic infrastructure for maintaining and distributing authoritative county-scale geographic state through a browser-first **substrate + subscriptions + logical partitions + replaceable physical edges** architecture.

Kane County, Illinois is the reference deployment rather than the conceptual namespace of the software. Reusable contracts are intended to remain portable to other U.S. counties/county-equivalent jurisdictions without delaying the first complete Kane County system.

Kane Fabric-authored code remains under the repository `LICENSE` using The Unlicense/public-domain dedication. Third-party software and geographic data retain their own rights/notice boundaries.

## Current development

Start with:

1. `docs/HANDOFF.md`
2. `docs/CURRENT_STATE.json`
3. `docs/DEVELOPMENT_PROCESS.md`
4. `docs/ROADMAP.md`
5. active milestone design: `docs/MILESTONE_5_DESIGN.md`
6. hardware boundary: `docs/ESP32_EDGE_REFERENCE.md`

Current milestone:

**Milestone 5 — Reference Physical Edge Architecture**

Milestones 1–4 are released. MS5 maps the accepted MS3/MS4 logical contracts onto a real, replaceable ESP32-S3-class edge without making hardware identity, network identity, cryptographic keys, or storage location part of Fabric logical identity.

The ESP32-S3 is intentionally present in the first release to establish Kane Fabric's firmware lifecycle early. Its initial role is modest: immutable artifact storage, bounded plain-HTTP serving, physical provisioning/replacement, and a foundation for later edge responsibilities. Browser HTTPS terminates at the Wiregate hub rather than on the ESP32-S3.

## Released foundation

### Milestone 1 — Kane County reconstruction proof

**RELEASED — 2026-08-18**

See `docs/MILESTONE_1_RELEASE.md`.

### Milestone 2 — Geographic core

**RELEASED — 2026-08-20**

Kane Fabric owns the geographic database/source/candidate/comparison/reconciliation/promotion lifecycle and persistent building identity without requiring application classification semantics.

See `docs/MILESTONE_2_RELEASE.md`.

### Milestone 3 — Shared substrate

**RELEASED — 2026-08-20**

Canonical four-file publication:

```text
county-overview.json
roads-lod.kfs
water-lod.kfs
substrate-manifest.json
```

Accepted content identity:

```text
fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc
```

See `docs/MILESTONE_3_RELEASE.md`.

### Milestone 4 — Subscriptions + geographic partitions

**RELEASED — 2026-08-22**

MS4 established deterministic logical partitions, independent subscription generations, real browser composition, cross-boundary identity preservation, and physical-placement independence.

See `docs/MILESTONE_4_RELEASE.md`.

## MS5 security direction

The reference ESP32-S3 edge is deliberately replaceable.

Kane Fabric does **not** require irreversible ESP32 security eFuse burning as part of the reference design. The project does not attempt to make one household edge physically unextractable.

Instead:

- public Fabric data remains independently integrity-checked;
- individual device compromise is local/recoverable;
- fleet-class firmware/provisioning failures are treated as systemic;
- authoritative signing/CA/promotion keys never live on the edge;
- firmware/update authenticity protects normal fleet operation;
- software-held replaceable device keys are allowed where appropriate;
- an external secure element is optional through a replaceable key-provider boundary;
- browser TLS terminates at the Wiregate hub; the ESP32-S3 reference edge serves plain HTTP and holds no browser TLS private key;
- Wiregate/browser TLS, management/WireGuard, hardware, secure-element, substrate, partition, and subscription identities remain separate.

WireGuard is a preferred management candidate under evaluation. Compile feasibility has been observed externally; runtime/resource acceptance on ESP32-S3 remains MS5 work.

## First-consumer feedback

The first real civic consumer exposed generic geographic capabilities that Kane Fabric did not yet have:

- accepted parcel/classification source data;
- persistent delivery-point identity distinct from building identity.

These are planned for Milestone 6. Kane Fabric will own the geographic primitives and authority lifecycle, not consumer participation/account/credential semantics.

## Forward release plan

```text
MS5  reference physical edge architecture
MS6  civic geography extension: parcels + delivery points
MS7  managed edge synchronization
MS8  multi-node distribution
 ↓
Kane Fabric 1.0
MS9  generic second-county bootstrap (post-1.0)
```

The first release is intentionally **depth before breadth**: complete the Kane County end-to-end infrastructure before requiring a second-county proof.

## Core architecture

```text
official geographic sources
        ↓
County Fabric node
(authority, validation, explicit promotion, compilation)
        ↓
accepted geographic state
        ↓
MS3 substrate + MS4 partitions/subscriptions
        ↓
replaceable edge nodes
(storage, plain HTTP serving, firmware lifecycle)
        ↓
Wiregate hub
(HTTPS termination / browser origin)
        ↓
browser
(validation, selective fetch, decompression, composition, rendering)
```

The internal GeoPackage is a control-plane implementation. The compiled publication and explicit logical contracts are the durable external interface.

Physical replacement of an edge must not change geographic, substrate, partition, or subscription identity.

## Development boundary

GitHub `main` is software/documentation authority. Real Kane Fabric runtime/compiler acceptance occurs in CT102 (`kane-fabric`) under `/var/lib/kane-fabric`; an Assistant sandbox is not a substitute.

Large county databases, harvests, staging artifacts, rollback copies, render packages, and release evidence stay outside Git.

See `docs/HANDOFF.md` for the current checkpoint and `docs/ROADMAP.md` for milestone sequencing.
