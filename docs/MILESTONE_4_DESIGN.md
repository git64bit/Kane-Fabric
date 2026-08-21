# Milestone 4 Design — Subscriptions and Geographic Partition Identity

## Status

Design baseline for Milestone 4.

Milestone 3 is complete and published to `main`. It established the deterministic county-scale substrate and proved selective browser access to indexed road/water chunks. Milestone 4 does not reopen that format or move ESP-IDF implementation forward from Milestone 5.

## Purpose

Milestone 4 defines how application subscriptions are scoped, identified, composed, and distributed across logical geographic partitions without changing Kane Fabric geographic authority or coupling logical datasets to physical edge devices.

The milestone answers two related questions:

1. how does an application publish domain-specific state as a subscription layered on the public substrate; and
2. how can the substrate and subscriptions be addressed in smaller geographic scopes so constrained edge nodes can carry useful focused subsets rather than an entire county.

The target progression is:

```text
MS-3  county substrate + selective chunks
  ↓
MS-4  subscriptions + geographic scoping/partition identity
  ↓
MS-5  physical edge placement/storage/serving on ESP32-S3
```

## Fixed boundaries

Milestone 4 must preserve these already-accepted constraints:

- the authoritative GeoPackage remains an internal control-plane implementation;
- accepted geographic state changes only through explicit promotion;
- the Milestone 3 four-file substrate publication remains the canonical county baseline;
- substrate compilation and subscription publication do not silently promote geography;
- a subscription is application/domain state layered on geography, not geographic authority;
- a partition is a logical scope/distribution identity, not a physical device;
- ESP32-S3/ESP-IDF implementation remains Milestone 5;
- Kane Fabric-authored code remains under the repository Unlicense;
- retained third-party implementations remain subject to the dependency/vendoring policy.

## Partition model

A **geographic partition** is a deterministic, jurisdiction-scoped description of an area for selection, composition, storage planning, replication, and serving.

A partition does not create a second geographic database and does not alter feature identity. It selects or references content from accepted substrate/subscription generations.

Supported scope classes should include at least:

- whole jurisdiction;
- municipality or other named incorporated place when an accepted boundary definition exists;
- township or equivalent named administrative subdivision when an accepted boundary definition exists;
- explicit bounded region using normalized coordinates;
- deterministic composite scope made from other declared partitions when justified.

Municipality and township are useful human-facing partition types, but they are not the only partition mechanism. Roads, water, buildings, service areas, industrial activity, and other subscription data can cross administrative boundaries.

## Partition identity

Partition identity must be independent of a particular ESP32, hostname, SSID, storage path, or network address.

A partition descriptor should bind at least:

- jurisdiction identity;
- partition format/version;
- scope class;
- normalized scope definition;
- source/accepted-boundary lineage when the scope uses an administrative boundary;
- deterministic partition content/definition hash;
- optional human-readable label that is not itself authority.

A future implementation may derive a stable `partition_key` from the normalized descriptor. The exact key algorithm is an MS4 implementation decision and must be frozen before release.

## Administrative partitions

Named municipalities and townships are convenience scopes, not implicit clipping authority.

When Kane Fabric uses an administrative boundary as a partition definition:

- the boundary must come from an explicit accepted geographic source or declared stable contract;
- the partition records that lineage;
- a boundary update produces a new partition definition/generation rather than silently changing the old partition;
- objects intersecting more than one partition retain the same logical identity;
- the partition mechanism must not require destructive geometry clipping merely to establish placement.

This allows a browser or edge node to request, for example, an Aurora-focused or township-focused subset while preserving cross-boundary roads, water, buildings, and subscription identities.

## Relationship to the Milestone 3 substrate

Milestone 3 produced one canonical Kane County substrate generation:

```text
county-overview.json
roads-lod.kfs
water-lod.kfs
substrate-manifest.json
```

Milestone 4 does not fork that county authority into separate town databases.

Instead, a partition should be able to identify the substrate chunks/ranges relevant to its scope. The already-proven indexed `.kfs` layout and bounding-box chunk selection are the starting mechanism.

A partition descriptor or derived partition manifest may therefore reference:

- the county substrate content identity;
- the exact substrate component identities;
- selected component chunks/ranges required for the partition;
- optional neighboring/context chunks required for continuity at the edge of the scope.

The same substrate chunk may legitimately be referenced by several partitions. Duplication at the storage layer does not create new geographic identity.

## Subscription model

A **subscription** is a versioned logical domain dataset that references Kane Fabric geography while retaining its own application ownership and release lifecycle.

Initial proof subscriptions remain:

- Condo, as the historical application extraction path;
- Industry, as the Mechanical Compiler integration path.

A subscription generation should be able to declare:

- subscription identity and version;
- application/domain owner;
- jurisdiction identity;
- substrate generation/content identity it is compatible with;
- geographic scope or partition coverage;
- referenced Fabric geographic identities;
- immutable component/object identities and lengths;
- independent subscription generation identity;
- rights/license metadata appropriate to the subscription;
- dependencies on other subscription or substrate objects only when explicit.

Subscription state must not be stored as an undeclared writable extension of the Fabric control-plane GeoPackage.

## Subscription and partition composition

The browser should be able to compose:

```text
selected substrate scope
+ zero or more selected subscription generations
+ neighboring/context scope where required
```

without requiring every selected subscription to cover the whole county.

A partition may contain:

- only substrate references;
- substrate plus one subscription;
- substrate plus several subscriptions;
- only subscription objects when the substrate is already available from another node/cache.

A subscription may:

- cover one partition;
- cover several partitions;
- cover the whole jurisdiction;
- be replicated across several physical nodes;
- be physically sharded while retaining one logical subscription generation.

## Cross-boundary behavior

Partition boundaries are distribution boundaries, not semantic ownership boundaries.

A feature or subscription object that intersects multiple partitions must retain one logical identity. Implementations may reference or replicate the object in several partition manifests as needed.

The MS4 contract must define deterministic inclusion rules for boundary-touching and boundary-crossing content. Those rules should avoid accidental holes at partition edges and should not make physical storage placement part of object identity.

## Edge-device relationship

Milestone 4 is intentionally hardware-aware but firmware-independent.

The contract must make it practical for future constrained nodes to carry focused subsets such as:

```text
Edge node A
  Aurora-area substrate references
  Industry subscription for that area

Edge node B
  Elgin-area substrate references
  Condo subscription for that area

Edge node C
  township-focused substrate/context
  several smaller subscriptions
```

Those examples describe logical placement only. Milestone 4 does not define ESP-IDF storage APIs, HTTP handlers, flash/SD-card layouts, Wi-Fi configuration, or firmware update behavior.

Milestone 5 maps the logical partition/subscription identities onto actual ESP32-S3 storage and serving implementations.

## Normative implementation order

This section is the single authoritative definition of the detailed Milestone 4 work sequence. Other current documents may report milestone status, identify the current work item, or summarize the milestone, but they must refer here rather than maintain a second complete sequence.

The normative MS4 sequence is:

```text
MS4-001  partition descriptor and deterministic identity contract
MS4-002  administrative/bounded scope normalization and inclusion rules
MS4-003  substrate partition selection manifest/reference model
MS4-004  subscription manifest and independent generation contract
MS4-005  geographic identity references and ownership/rights boundary
MS4-006  Condo proof subscription
MS4-007  Industry / Mechanical Compiler proof subscription
MS4-008  browser composition of substrate + multiple scoped subscriptions
MS4-009  multi-partition / cross-boundary composition proof
MS4-010  edge-placement compatibility proof without ESP-IDF implementation
MS4-011  release evidence and milestone closeout
```

This sequence may be refined as implementation evidence develops, but the scope boundary above is fixed unless explicitly changed.

## Exit gate

Milestone 4 is complete when a browser can consume the accepted Kane substrate and compose at least two independently versioned logical subscriptions while selecting them through explicit geographic partitions, with deterministic partition identities and cross-boundary behavior that do not depend on which physical edge device stores the bytes.

The resulting contracts must be suitable inputs to Milestone 5 ESP32-S3/ESP-IDF placement and serving work without requiring a redesign of subscription or geographic identity semantics.
