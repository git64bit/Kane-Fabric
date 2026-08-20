# Kane Fabric Architecture

## 1. System roles

Kane Fabric separates authority, presentation, and edge serving.

### County Fabric node

The Debian CT is the authoritative control plane and compiler.

Responsibilities:

- maintain the authoritative geographic database;
- preserve provenance and accepted source-release state;
- validate county/source profiles;
- poll official upstream services for likely changes;
- harvest complete candidates when needed;
- compare accepted and candidate releases deterministically;
- reconcile project-owned geographic identity where required;
- promote validated state atomically;
- retain rollback state;
- generate substrate and subscription packages;
- publish immutable artifacts and manifests;
- synchronize edge nodes;
- provide explicit geographic contracts to applications such as Mechanical Compiler.

The authoritative GeoPackage and its SQL schema are internal control-plane implementation details. External consumers do not use the database as the Kane Fabric API.

### Browser

The browser is the primary user client.

Responsibilities:

- obtain the required boot application and geographic manifests;
- validate package identity where required;
- decompress package content where appropriate;
- render county-scale geographic context;
- pan and zoom continuously;
- compose substrate and one or more subscriptions;
- perform user interaction defined by consuming applications.

The browser should not need county-wide migration, harvesting, reconciliation, compilation capabilities, or knowledge of the authoritative database schema.

### Edge nodes

Edge nodes are low-cost replaceable storage/serving resources.

Responsibilities may include:

- HTTP serving;
- local Wi-Fi access;
- persistent bulk storage;
- package receipt;
- hash/signature verification;
- activation of a manifest generation;
- caching, sharding, or replication;
- optional upstream synchronization through HTTPS, WireGuard, federation, or future transport.

ESP32-S3 is the minimum initial reference implementation, not a permanent platform dependency.

### External consumption boundary

The durable external interface is the compiled baseline geography publication, not the internal database or compiler API.

The same immutable baseline must be consumable by:

- web applications;
- microcontrollers and constrained edge devices;
- caches and mirrors;
- independent applications;
- federated peers and synchronization protocols.

Consumers use explicit jurisdiction identity, publication/component format versions, accepted-release descriptors, hashes, lengths, indices, chunks, and manifest/content identities. They must not depend on SQLite table names, migration numbers, CT paths, Python module names, or other control-plane internals.

Transport may change without changing the geographic contract. HTTPS, byte-range HTTP, local filesystem/object storage, removable media, edge-node serving, and federated replication may all carry the same publication bytes and identities.

Federation wraps discovery, availability, synchronization, or replication around the baseline publication. It does not define a second geographic schema and does not require peers to share Kane Fabric's internal database implementation.

The normative external-consumption contract is `docs/BASELINE_GEOGRAPHY_DISTRIBUTION.md`. The current substrate wire format is `docs/SUBSTRATE_FORMAT_V1.md`.

## 2. Geographic composition

### Shared substrate

The substrate contains geographic context useful to many applications.

Initial Kane County substrate candidates:

- county boundary/context;
- roads;
- water.

Additional stable layers should be added only when justified by multiple consumers or by a clear geographic contract.

### Subscriptions

Subscriptions are logical domain datasets layered on top of the substrate.

Examples:

- Condo;
- Industry;
- Retail.

Subscriptions may contain:

- relevant site/building geometry;
- classification/state;
- domain metadata;
- references to substrate identities.

One object may participate in multiple subscriptions independently.

A subscription may fit on one edge node, share a node with other subscriptions, span several nodes, or be replicated.

## 3. Authority boundaries

Kane Fabric owns geographic truth and geographic release state.

A consuming application owns its own business/application state.

For Mechanical Compiler, this means:

- Kane Fabric may own geographic site/building identities and geometry;
- Mechanical Compiler may own participant, qualification, capability, workflow, and federation state;
- Mechanical Compiler references Kane Fabric identities through an explicit interface;
- neither database is silently treated as a writable extension of the other.

The application consumes published Kane Fabric geographic contracts. It does not become coupled to the control-plane GeoPackage schema merely because it references Fabric geography.

## 4. Package direction

The architecture evolves toward immutable, verifiable package generations.

The Milestone 3 substrate v1 contract freezes the first concrete baseline publication shape:

```text
county-overview.json
roads-lod.kfs
water-lod.kfs
substrate-manifest.json
```

Content-addressed object storage may be used underneath or around those publication identities, for example:

```text
objects/<prefix>/<sha256>
manifests/<generation>.json
```

A manifest can identify:

- county/substrate generation;
- subscription generations;
- object hashes;
- sizes;
- compression;
- dependencies;
- signatures or trust metadata.

Object-storage layout is a transport/storage choice. It must preserve the publication bytes and identities defined by the current wire contract.

## 5. Transport boundary

Local browser operation must not depend on an upstream control-plane connection.

Possible transports between county Fabric nodes, edge nodes, mirrors, federated peers, and consumers include:

- HTTPS;
- byte-range HTTP;
- WireGuard-carried services;
- filesystem or object synchronization;
- federated discovery/replication protocols;
- future transports satisfying the same publication contract.

WireGuard is optional infrastructure, not a browser requirement.

No transport is allowed to silently change the meaning or content identity of the baseline geography it carries.

## 6. Failure model

The design should preserve useful operation through common failures:

- upstream county source unavailable -> existing accepted geographic state remains valid;
- candidate validation failure -> accepted database remains active;
- interrupted promotion -> prior accepted database remains recoverable;
- Fabric node temporarily unavailable -> edge nodes may continue serving the last activated generation;
- one edge node lost -> subscriptions may be restored, relocated, or replicated without changing logical identities;
- one transport unavailable -> another transport may carry the same immutable publication;
- browser platform changes -> standards-based HTTP/browser contract limits client-specific rebuilding;
- federated peer implementation differs internally -> interoperability remains possible at the publication boundary.

## 7. Non-goals of the initial architecture

The initial architecture does not require:

- one CT per internal subsystem;
- one ESP per subscription;
- a native Android application;
- a native Windows application;
- PostgreSQL/PostGIS solely for architectural fashion;
- Docker as a prerequisite;
- exposing the authoritative GeoPackage schema as an external API;
- requiring federated peers to run Kane Fabric's internal database implementation;
- a revival of the old Kane Condo/County Field Map grid or VOID workflow.

Any such dependency must be justified by a concrete later requirement.
