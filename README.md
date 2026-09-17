# Kane Fabric

Kane Fabric is public civic infrastructure for maintaining and distributing authoritative county-scale geographic state through a browser-first **substrate + subscriptions + logical partitions + replaceable physical edges** architecture.

Kane County, Illinois is the reference deployment rather than the conceptual namespace of the software. Reusable contracts are intended to remain portable to other U.S. counties/county-equivalent jurisdictions without delaying the first complete Kane County system.

Kane Fabric-authored code remains under the repository `LICENSE` using The Unlicense/public-domain dedication. Third-party software and geographic data retain their own rights/notice boundaries.

## Current development

Start with:

1. `docs/HANDOFF.md`
2. `docs/CURRENT_STATE.json`
3. `docs/BROWSER_FIRST_ONLINE_FIRST_DIRECTIVE.md`
4. `administration/README.md`
5. `docs/WEB_APPLICATION_DESIGN.md`
6. `docs/DEVELOPMENT_PROCESS.md`
7. `docs/ROADMAP.md`
8. active milestone design: `docs/MILESTONE_5_DESIGN.md`
9. CPE/environment authority: `docs/CIVICVS_PROJECT_ENVIRONMENT.md`

Current milestone:

**Milestone 5 — Reference Physical Edge Architecture**

The physical ESP32-S3 MS5-006 runtime gate is accepted. Firmware is no longer the active development bottleneck.

The active priority workstream is now **Administrative County/Web/Category/Contract Development**.

Kane Fabric remains **Browser-First**, but the implementation order is now **Online-First**:

```text
full online Kane County browser/interface
        ↓
county categories + participant contracts
        ↓
bounded participant-publication composition
        ↓
freeze shared browser modules/contracts
        ↓
reduce the same application to local/offline operation
```

The offline browser is a later reduction of the same application, not a separate product or schema.

The full directive is `docs/BROWSER_FIRST_ONLINE_FIRST_DIRECTIVE.md`.

## Current architecture boundary

The ESP32-S3 is a bounded edge device, not a miniature county server.

A participant edge may hold a focused publication such as one condominium association and its unit-level data. It is not required to carry the complete Kane County substrate.

The county-wide geography, web/map composition, category/object definitions, participant-publication contracts, visibility semantics, and independent-county/operator conformance model are administrative infrastructure.

The online county interface may provide discovery, aggregation, search, administrative workflows, current availability, and authentication needed for restricted material. Those conveniences must not become civic identity, exclusive data custody, or a proprietary SaaS prerequisite.

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

## MS5 accepted physical edge checkpoint

MS5-006 physically proved the ESP32-S3 reference artifact appliance on the dedicated `fw` workstation.

Accepted behavior includes:

- pinned ESP-IDF/toolchain build identity;
- first flash and cold boot;
- 16 MB reference flash geometry;
- Wi-Fi provisioning and deployment-network attachment;
- read-only Fabric storage mount;
- active-inventory verification before serving;
- plain HTTP full GET;
- exact closed byte-range serving;
- invalid range and traversal rejection;
- fail-closed behavior on deliberately corrupted active storage;
- restoration of known-good storage and resumed serving.

Accepted firmware source:

```text
7aa3c836bae470704d051a36a6261a1140e9d3d0
```

Acceptance record:

```text
docs/CPE_ESP32_MS5_006_DEVICE_RUNTIME_ACCEPTANCE.md
```

The reference edge remains deliberately replaceable. Browser HTTPS terminates at Wiregate/admin infrastructure rather than on the ESP32-S3.

Later MS5 lifecycle work remains pending, including management-transport evaluation, firmware update/rollback/recovery, physical replacement/reprovisioning proof, constrained-resource acceptance, and final closeout. Those gates do not block the current online administrative/browser development.

## Administrative / participant direction

The immediate reference participant is a condominium association with unit-level data.

Reference composition:

```text
accepted county geography
        +
administrative categories/contracts
        +
bounded association/unit publication
        =
full online county-facing browser view
```

The administrative work must distinguish at least:

- county geographic identity;
- association/participating-organization identity;
- unit or participant-object identity;
- category/schema identity;
- participant publication-generation identity;
- public/restricted/private visibility semantics;
- physical edge identity, which is none of the identities above.

This work must become explicit enough that a future independent operator can implement another Illinois county without inheriting Kane County hostnames, filesystem paths, private keys, database internals, accounts, or proprietary service state.

## Infrastructure rather than SaaS

Online-First changes development order, not the anti-capture architecture.

Kane Fabric must preserve:

- browser-first access;
- portable/open publication contracts;
- independent participant data custody;
- replaceable edge implementations;
- replaceable county operator implementations;
- no hosted-account definition of civic identity;
- no proprietary portal as the sole datastore;
- source-neutral browser loaders/adapters;
- local/offline operation as a later reduction of the same browser application.

## Forward release plan

```text
MS5  reference physical edge architecture + administrative/browser integration
MS6  civic geography extension: parcels + delivery points
MS7  managed edge synchronization
MS8  multi-node distribution
 ↓
Kane Fabric 1.0
MS9  generic second-county bootstrap (post-1.0)
```

The first release remains **depth before breadth**: complete the Kane County end-to-end infrastructure and public contracts before requiring a second-county proof.

## Core architecture

```text
official geographic sources
        ↓
County Fabric node
(authority, validation, explicit promotion, compilation)
        ↓
accepted county geographic state
        ↓
administrative categories/contracts
        ↓
full online browser/interface
        ↑
        +--- bounded participant publications
                 ↑
          replaceable edge nodes
          (ESP32-S3 or other source)
```

Wiregate/admin web infrastructure provides the browser secure origin. Physical edges serve or retain bounded participant publications without becoming county geographic or category authority.

The internal GeoPackage is a control-plane implementation. Compiled publications and explicit logical contracts are the durable external interface.

Physical replacement of an edge must not change county, association, unit, category, partition, subscription, or participant-publication identity.

## Development boundary

GitHub `main` is software/documentation authority. Real Kane Fabric runtime/compiler acceptance occurs in CT102 (`kane-fabric`) under `/var/lib/kane-fabric`; an Assistant sandbox is not a substitute.

Physical firmware build/programming and ESP32 acceptance occur on `fw`. The accepted firmware should remain unchanged during current administrative/browser development unless a concrete contract requirement or later MS5 lifecycle gate requires returning to it.

Large county databases, harvests, staging artifacts, rollback copies, render packages, and release evidence stay outside Git.

See `docs/HANDOFF.md` for the current checkpoint and `docs/ROADMAP.md` for milestone sequencing.
