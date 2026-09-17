# Kane Fabric Roadmap

This roadmap reports milestone status, purpose, and release sequencing. Historical proof belongs in milestone release records. Detailed work-item authority belongs only in the active milestone design document.

The roadmap is expected to change when real consumers expose missing infrastructure. That is normal project evolution. A consumer may reveal a generic Fabric requirement, but application semantics must not be absorbed into Kane Fabric merely because the requirement was discovered there.

## Milestone 0 — Fix the platform contract

**Status: COMPLETE**

Established the browser-first client boundary, county Fabric control-plane/compiler role, replaceable edge role, substrate/subscription model, application ownership boundary, and external operational-data boundary.

## Milestone 1 — Reconstruct Kane County on a clean Fabric node

**Status: RELEASED — 2026-08-18**

Release record: `docs/MILESTONE_1_RELEASE.md`

Proved reconstruction from declared inputs through deterministic candidate replay/comparison and project-building reconciliation. The carried promotion/rollback proof was explicitly completed at Milestone 2 entry rather than silently claimed in Milestone 1.

## Milestone 2 — Extract Kane Fabric geographic core

**Status: RELEASED — 2026-08-20**

Release record: `docs/MILESTONE_2_RELEASE.md`

Kane Fabric owns reusable geographic database migrations, provenance, source contracts, candidate engines, deterministic comparison, persistent building identity, reconciliation, explicit atomic promotion/rollback, and the Kane County bootstrap path without requiring application classification semantics at Fabric runtime.

## Milestone 3 — Compile shared substrate

**Status: RELEASED — 2026-08-20**

Release record: `docs/MILESTONE_3_RELEASE.md`

Frozen wire contract: `docs/SUBSTRATE_FORMAT_V1.md`

Released canonical publication:

```text
county-overview.json
roads-lod.kfs
water-lod.kfs
substrate-manifest.json
```

Accepted substrate identity:

```text
fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc
```

Exit gate: a normal browser can verify, selectively read, decompress, and render the canonical county substrate through bounded byte-range access without application subscription state.

## Milestone 4 — Subscriptions + geographic scoping/partition identity

**Status: RELEASED — 2026-08-22**

Release record: `docs/MILESTONE_4_RELEASE.md`

Historical design authority: `docs/MILESTONE_4_DESIGN.md`

Purpose achieved: applications can publish independently versioned geographic subscriptions layered on the canonical substrate, and content can be addressed through deterministic logical geographic partitions independent of physical edge devices.

Accepted proof identities:

```text
composition_sha256       a58c8398248cee05b7baad9ae289fe0581bdb3624ce1aff3aa8a49721f92ee53
bundle_inventory_sha256  1e109d4621ce738e3e35b93c23ecab0d5c9a0d4166aad5d72f4e2eff397ad0d3
release_proof_sha256      3235cd4f7b7041138fe05708dbb077c07dc3ce8b8ec7a390141489460ac40634
```

Exit gate: **PASSED**. A real browser consumed the accepted Kane substrate and composed two independently versioned subscriptions through two explicit logical partitions. Cross-boundary replication retained logical object identity, and different physical placement metadata did not change logical placement identity.

## Milestone 5 — Reference physical edge architecture + administrative/browser integration

**Status: CURRENT**

Design authority: `docs/MILESTONE_5_DESIGN.md`

Administrative/edge boundary: `docs/ADMINISTRATIVE_EDGE_BOUNDARY.md`

Development-order directive: `docs/BROWSER_FIRST_ONLINE_FIRST_DIRECTIVE.md`

Purpose: prove a real, replaceable ESP32-S3-class bounded participant edge while preserving the authority and identity boundaries needed for the county-wide administrative/browser infrastructure.

MS5 no longer assumes every edge stores the complete Kane County substrate. A participant edge may hold a focused publication such as one condominium association and its unit-level data while referencing accepted county/building identities through explicit contracts.

The ESP32-S3 is intentionally present in the first release to establish a real firmware lifecycle before Kane Fabric matures around a software-only architecture. Its role is deliberately modest: immutable bounded artifact storage, plain-HTTP serving, local provisioning/replacement, fail-closed verification, and a base for later firmware lifecycle responsibilities.

The MS5-006 physical device-runtime gate is accepted. The current priority is administrative/browser integration rather than additional firmware specialization.

The active development order is:

```text
Browser-First product architecture
        +
Online-First implementation order
        ↓
full online Kane County interface
        ↓
categories + participant contracts
        ↓
bounded participant-publication composition
        ↓
shared browser modules/contracts stabilize
        ↓
local/offline browser reduction
```

The online-first order must not become SaaS-first. Participant data remains portable and independently retainable; civic identities do not depend on one hosted account system; and another county operator must be able to conform without inheriting Kane County private operational state.

The security posture is intentionally proportionate to the system:

- public Fabric geography and any public participant material remain independently integrity-checked;
- restricted/private participant material, where supported by the administrative contract, does not turn the ESP32 into a person/account authority;
- physical compromise of one edge device is expected to be recoverable and local;
- the ESP32-S3 is replaceable compute/radio/storage, not a permanent root of trust;
- Kane Fabric does not require irreversible eFuse burning, secure-boot fuses, or flash-encryption fuses for the reference edge;
- a separate secure element may be used by a deployment through an explicit key-provider boundary, but is not required by the Fabric format or device identity model;
- authoritative signing, CA, promotion, category, contract, and geographic-release authority never resides on the edge;
- fleet-class firmware/provisioning failures and authority/signing compromise are systemic threats and receive stronger controls than individual physical device loss;
- browser TLS terminates at Wiregate/admin infrastructure and is not an ESP32 device-local role;
- Wiregate/browser TLS, management/WireGuard, optional secure-element, hardware, county, association, unit, category, partition, subscription, and participant-publication identities remain separate.

MS5 owns the reference edge contract and integration proof: storage/activation, Wiregate/browser secure origin, bounded hub-to-edge plain HTTP and byte-range serving, ESP-IDF implementation, management-transport feasibility, firmware authenticity/update/recovery, resource evidence, replacement/reprovisioning, and online browser composition with a focused participant publication.

WireGuard remains a management/synchronization candidate. Runtime operation, recovery, resource cost, and coexistence with Fabric serving remain to be proven. WireGuard is never a Fabric logical identity and is not a prerequisite for the browser path.

Current MS5 integration exit direction: a normal online browser composes accepted Kane County geography with a valid focused participant publication through the administrative/Wiregate path; the participant edge serves only its bounded publication; the browser validates the same logical identities regardless of physical edge replacement; loss of management/upstream connectivity does not silently redefine already activated participant content; later firmware lifecycle/replacement/resource gates pass without moving county/category/contract authority onto the ESP32.

## Milestone 6 — Civic geography extension: parcels + delivery points

**Status: PLANNED**

Purpose: add generic geographic primitives exposed by the first real civic consumer without importing that consumer's participation semantics into Fabric.

Work includes:

- accepted parcel source/profile and persistent parcel references where required;
- accepted deployment-specific parcel classifications as geographic/source data;
- persistent delivery-point identity distinct from building identity, address strings, parcel identifiers, and external corporate identifiers;
- building ↔ parcel ↔ delivery-point relationships;
- witness/source lineage for delivery-point existence and address/unit representation;
- deterministic lifecycle rules for witness changes, continuation, retirement, renumbering, split, merge, and source disagreement;
- candidate/comparison/reconciliation/promotion behavior using the existing Fabric authority model.

A Fabric delivery point is geography. It does not mean a person lives there, has an account, is eligible for a civic program, or holds an active participation credential.

Exit gate: a real Kane County accepted release can expose persistent delivery-point identities and their accepted witnesses/relationships through explicit promotion, including multi-unit cases, without turning building IDs, parcel IDs, postal strings, or third-party identifiers into the persistent Fabric identity.

## Milestone 7 — Managed edge synchronization

**Status: PLANNED**

Purpose: connect replaceable physical edges to county infrastructure for authenticated management and immutable-generation transfer without making transport identity part of Fabric content identity.

Work includes:

- management identity lifecycle separate from Wiregate/browser TLS and logical Fabric identities;
- WireGuard runtime evaluation and adoption if it passes MS5 feasibility;
- provisioning/replacement of management credentials;
- authenticated synchronization of immutable generations;
- resumable transfer and verification;
- activation only after complete validation;
- status/health reporting that does not create geographic authority;
- recovery when management transport is unavailable or credentials are replaced.

Exit gate: a replacement edge can obtain, verify, and activate the same logical participant publication generations through the management plane without changing county, association, unit, category, partition, subscription, or participant-publication identity.

## Milestone 8 — Multi-node distribution

**Status: PLANNED**

Purpose: prove that logical publications can be placed, sharded, and replicated across multiple replaceable nodes without changing browser application semantics or logical identities.

Work includes replication, sharding, overlapping placement, node loss, node replacement, and browser composition across the chosen physical distribution model.

Exit gate: loss or replacement of one physical node does not force changes to county, partition, subscription, participant-publication, or consumer semantics.

## Kane Fabric 1.0 release gate

The first Kane Fabric release is planned after Milestones 0–8 are accepted.

The 1.0 claim is depth before breadth: Kane County operates end-to-end from accepted geographic authority through deterministic publication, administrative/browser composition, bounded participant edges, civic delivery-point geography, managed synchronization, and multi-node distribution.

A second-county deployment is deliberately not a prerequisite for 1.0. The reusable contracts must remain county-generic, but actual second-county proof follows release rather than delaying the first complete Kane County system.

Before 1.0, all project-controlled third-party implementations retained in the build/runtime/firmware/test chain must satisfy the dependency policy: exact pinning, license review, vendoring/offline reproducibility, and retained notices.

## Milestone 9 — Generic county bootstrap

**Status: PLANNED — POST-1.0**

Purpose: prove breadth after Kane County depth is complete.

Work includes separating deployment-specific profiles/data from generic Fabric software, codifying bootstrap inputs, and proving a second county/county-equivalent deployment primarily through configuration/profile work rather than a fork.

Exit gate: a second county can be brought online without changing core architecture.
