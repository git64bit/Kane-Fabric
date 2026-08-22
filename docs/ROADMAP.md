# Kane Fabric Roadmap

This roadmap reports milestone status and purpose. Detailed historical evidence belongs in the milestone release records; detailed work-item authority belongs in the active milestone design/contract document.

## Milestone 0 — Fix the platform contract

**Status: COMPLETE**

Established the browser-first client boundary, county Fabric control plane/compiler role, replaceable edge role, substrate/subscription model, application ownership boundary, and external operational-data boundary.

## Milestone 1 — Reconstruct Kane County on a clean Fabric node

**Status: RELEASED — 2026-08-18**

Release record: `docs/MILESTONE_1_RELEASE.md`

Proved reconstruction from declared inputs through deterministic candidate replay/comparison and project-building reconciliation. The carried promotion/rollback proof was explicitly completed at Milestone 2 entry rather than silently claimed in Milestone 1.

## Milestone 2 — Extract Kane Fabric geographic core

**Status: RELEASED — 2026-08-20**

Release record: `docs/MILESTONE_2_RELEASE.md`

Kane Fabric owns the reusable geographic database migrations, provenance, source contracts, candidate engines, deterministic comparison, persistent building identity, reconciliation, explicit atomic promotion/rollback, and Kane County bootstrap path without requiring Condo classification semantics at Fabric runtime.

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

All normative work items from `MS4-001` through `MS4-011` are complete. The detailed sequence remains defined only in `docs/MILESTONE_4_DESIGN.md`.

Accepted proof identities:

```text
composition_sha256       a58c8398248cee05b7baad9ae289fe0581bdb3624ce1aff3aa8a49721f92ee53
bundle_inventory_sha256  1e109d4621ce738e3e35b93c23ecab0d5c9a0d4166aad5d72f4e2eff397ad0d3
release_proof_sha256      3235cd4f7b7041138fe05708dbb077c07dc3ce8b8ec7a390141489460ac40634
```

Exit gate: **PASSED**. A real browser consumed the accepted Kane substrate and composed two independently versioned subscriptions through two explicit logical partitions. Cross-boundary replication retained logical object identity, and different physical placement metadata did not change logical placement identity.

## Milestone 5 — Edge serving contract

**Status: CURRENT**

Reference boundary: `docs/ESP32_EDGE_REFERENCE.md`

Purpose: map the released MS3 substrate and MS4 partition/subscription identities onto replaceable constrained edge hardware without redesigning logical identity semantics.

Initial reference implementation direction: ESP32-S3-class hardware using ESP-IDF.

Work includes:

- freeze the physical edge serving/storage contract;
- select, pin, license-review, and vendor ESP-IDF/toolchain if retained;
- map logical substrate/partition/subscription generations onto physical storage;
- implement HTTP serving and byte-range behavior;
- define storage layout and capacity limits;
- verify manifests/objects before activation;
- define activation, rollback/recovery, and node replacement behavior;
- prove local browser access under the required WebCrypto secure-context constraints;
- test AP/STA deployment behavior and optional synchronization transport;
- prove focused partition placement makes useful service practical on constrained hardware.

Exit gate: a browser can consume the last activated substrate/partition/subscription generations from reference edge hardware while the county Fabric CT is unavailable, without changing the logical identities established in MS3/MS4.

## Milestone 6 — Multi-node distribution

**Status: PLANNED**

Purpose: prove that logical partitions and subscriptions can be placed, sharded, and replicated across multiple replaceable nodes without changing application semantics or identities.

Exit gate: loss or replacement of one physical node does not force changes to logical partition identity, subscription identity, or browser application semantics.

## Milestone 7 — Generic county bootstrap

**Status: PLANNED**

Purpose: turn the Kane County reference implementation into a repeatable county/county-equivalent deployment model primarily through configuration/profile work rather than forks.

Exit gate: a second county can be brought online without changing core architecture.
