# Kane Fabric Data Ownership

## 1. Purpose

Kane Fabric separates authoritative geographic state, external source evidence, compiled distribution artifacts, and application-owned subscription state.

This contract exists to prevent a county refresh, application change, edge-node failure, or package rebuild from silently transferring ownership between layers.

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

The county Fabric node owns the currently accepted geographic release state used to compile substrate and subscription packages.

Accepted state changes only through an explicit validated promotion process.

A failed or partial candidate must not silently alter accepted state.

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

## 7. Shared substrate

The shared substrate is Kane Fabric-owned compiled geographic context.

Initial expected components include:

- county boundary/context;
- roads;
- water.

The authoritative source of these compiled artifacts remains the accepted county database and associated release metadata, not an edge-device copy.

## 8. Subscriptions

A subscription is a logical Kane Fabric distribution dataset layered on the shared substrate.

Subscription packages may contain geographic identity, geometry, classification, and domain metadata required for a consumer.

Ownership of domain/business state remains with the application where appropriate.

Example: an Industry subscription may carry site geometry and stable geographic references for Mechanical Compiler, while Mechanical Compiler remains authoritative for participant identity, capability, qualification, workflow, and federation state.

## 9. Browser state

Browser-local state is not county authority unless an explicit application contract says otherwise.

Caching, decompression buffers, visual selections, and transient UI state may be discarded and reconstructed.

Future offline write journals, if introduced, must have an explicit ownership and reconciliation contract before implementation.

## 10. Edge-node state

Edge nodes hold replaceable distribution copies.

An edge node may store:

- immutable objects;
- manifests;
- substrate generations;
- subscription generations;
- caches;
- replication/shard copies.

Loss of an edge node must not destroy authoritative county state.

## 11. Rollback and audit

Rollback artifacts and append-only promotion/audit records are part of the county Fabric node's operational evidence.

They may be retained according to policy, but they are not active accepted state unless an explicit rollback operation restores them.

## 12. Git boundary

Git owns versioned implementation and contracts, not large operational geographic data.

Do not commit:

- production GeoPackages;
- harvest GeoJSON;
- candidate databases;
- rollback databases;
- render packages;
- reconstruction bundles;
- secrets or private deployment credentials.

Do commit:

- schemas and migrations;
- source/county profiles;
- small deterministic manifests when appropriate;
- tests;
- scripts;
- documentation;
- bootstrap and validation procedures.