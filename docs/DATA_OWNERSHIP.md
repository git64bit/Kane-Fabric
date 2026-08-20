# Kane Fabric Data Ownership

## 1. Purpose

Kane Fabric separates authoritative geographic state, external source evidence, compiled distribution artifacts, logical geographic partition definitions, and application-owned subscription state.

This contract exists to prevent a county refresh, application change, partition change, edge-node failure, or package rebuild from silently transferring ownership between layers.

## 2. Official source data

Official county or agency services remain external authorities for their published datasets.

Kane Fabric records:

- source agency identity;
- dataset identity;
- source profile;
- source endpoint contract;
- harvest metadata;
- source file/evidence hashes;
- accepted and candidate release identities.

A live upstream response does not become authoritative Kane Fabric state merely because it is newer. It must pass the applicable validation and promotion process.

## 3. Accepted geographic state

The county Fabric node owns the currently accepted geographic release state used to compile substrate, partition references, and geographic portions of subscription packages.

Accepted state changes only through an explicit validated promotion process.

A failed or partial candidate must not silently alter accepted state.

Partition selection, subscription publication, rendering, caching, and physical edge placement do not themselves alter accepted geographic authority.

## 4. Seed evidence

Seed GeoPackages or initial acquisition bundles are immutable reconstruction evidence.

They are not active mutable databases.

A working county database is derived from a seed through documented migration/import/reconstruction procedures.

## 5. Candidate and staging evidence

Harvested candidates are external staged evidence until promoted.

Candidate storage may include:

- layer metadata;
- object-ID inventories;
- source GeoJSON or equivalent complete acquisition evidence;
- excluded/null-geometry inventories where the profile requires them;
- manifests;
- deterministic comparison outputs;
- reconciliation databases and reports;
- promotion artifacts.

Registration of candidate provenance does not itself mean acceptance.

## 6. Geographic identities

Kane Fabric may own project-level geographic identities that survive changes in official source identifiers.

Examples include persistent building/site identities needed to bridge official source refreshes.

Such identities must be reconciled explicitly when official geometry or identifiers change.

Geographic identity does not change merely because an object appears in several partitions or subscriptions.

## 7. Shared substrate

The shared substrate is Kane Fabric-owned compiled geographic context.

The accepted Milestone 3 v1 components are:

- county boundary/context;
- roads;
- water.

The authoritative source of these compiled artifacts remains the accepted county database and associated release metadata, not an edge-device copy.

The county-wide Milestone 3 publication remains canonical. A later geographic partition may select/reference only part of the publication without creating a second geographic authority.

## 8. Geographic partitions

A geographic partition is a logical Kane Fabric distribution/composition definition over a declared jurisdictional area.

Partition examples include:

- whole jurisdiction;
- municipality/incorporated place;
- township/equivalent administrative subdivision;
- explicit bounded region;
- deterministic composite scope.

A partition may identify which substrate chunks/ranges and subscription objects are relevant to a focused area.

A partition does **not** own or replace:

- accepted geographic authority;
- source provenance;
- feature identity;
- subscription business/domain ownership;
- physical edge-node identity.

Administrative boundaries used to define a partition must carry explicit accepted lineage when applicable. A changed administrative boundary produces a new partition definition/generation rather than silently mutating an old one.

Objects crossing partition boundaries retain one logical identity and may be referenced or replicated in several partitions.

## 9. Subscriptions

A subscription is an independently versioned logical distribution dataset layered on the shared substrate.

Subscription packages may contain geographic references, geometry, classification, and domain metadata required for a consumer.

Ownership of domain/business state remains with the application where appropriate.

Example: an Industry subscription may carry site geometry and stable geographic references for Mechanical Compiler, while Mechanical Compiler remains authoritative for participant identity, capability, qualification, workflow, and federation state.

A subscription may cover one partition, several partitions, or a whole jurisdiction. Its logical identity does not change because its bytes are moved, replicated, cached, or sharded across physical edge devices.

A proprietary, restricted, private, or commercially licensed subscription does not acquire ownership of the underlying public Kane Fabric substrate or partition definitions merely because the artifacts are composed together or co-located on one device.

## 10. Browser state

Browser-local state is not county authority unless an explicit application contract says otherwise.

Caching, decompression buffers, selected partitions, visual selections, and transient UI state may be discarded and reconstructed.

Future offline write journals, if introduced, must have an explicit ownership and reconciliation contract before implementation.

## 11. Edge-node state

Edge nodes hold replaceable distribution copies and placement configuration.

An edge node may store:

- immutable objects/components;
- substrate manifests/generations;
- geographic partition descriptors/manifests;
- subscription manifests/generations;
- selected chunk/range copies;
- caches;
- replication/shard copies;
- local placement/serving configuration.

Loss or replacement of an edge node must not destroy authoritative county state or require a change to logical partition/subscription identity.

Physical device identity, hostname, SSID, IP address, and storage path are placement/runtime state rather than partition/subscription authority.

## 12. Rollback and audit

Rollback artifacts and append-only promotion/audit records are part of the county Fabric node's operational evidence.

They may be retained according to policy, but they are not active accepted state unless an explicit rollback operation restores them.

## 13. Git boundary

Git owns versioned implementation and contracts, not large operational geographic data.

Do not commit:

- production GeoPackages;
- harvest GeoJSON;
- candidate databases;
- rollback databases;
- large generated substrate/partition/subscription packages;
- reconstruction bundles;
- secrets or private deployment credentials.

Do commit:

- schemas and migrations;
- source/county profiles;
- partition/subscription schemas and small deterministic manifests when appropriate;
- tests;
- scripts;
- documentation;
- bootstrap and validation procedures.
