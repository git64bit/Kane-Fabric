# Kane Fabric Architecture

## 1. System roles

Kane Fabric separates authority, presentation, logical distribution identity, and physical edge serving.

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
- generate deterministic geographic partition descriptors/manifests;
- publish immutable artifacts and manifests;
- synchronize edge nodes;
- provide explicit geographic contracts to applications such as Mechanical Compiler.

The authoritative GeoPackage and its SQL schema are internal control-plane implementation details. External consumers do not use the database as the Kane Fabric API.

### Browser

The browser is the primary user client.

Responsibilities:

- obtain the required boot application and geographic manifests;
- select geographic scope/partitions;
- validate package identity where required;
- fetch only required component ranges/objects;
- decompress package content where appropriate;
- render geographic context;
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
- package/partition/subscription receipt;
- hash/signature verification;
- activation of manifest generations;
- caching, sharding, or replication;
- optional upstream synchronization through HTTPS, WireGuard, federation, or future transport.

ESP32-S3 is the minimum initial reference implementation, not a permanent platform dependency.

A physical edge node is never the identity of a subscription or geographic partition. The same logical partition may move between nodes or be replicated without changing application semantics.

### External consumption boundary

The durable external interface is compiled geographic publication and explicit subscription/partition contracts, not the internal database or compiler API.

The same immutable baseline must be consumable by:

- web applications;
- microcontrollers and constrained edge devices;
- caches and mirrors;
- independent applications;
- federated peers and synchronization protocols.

Consumers use explicit jurisdiction identity, publication/component format versions, accepted-release descriptors, hashes, lengths, indices, chunks, partition definitions, subscription generations, and manifest/content identities. They must not depend on SQLite table names, migration numbers, CT paths, Python module names, hostnames, SSIDs, or other control-plane/placement internals.

Transport may change without changing the geographic contract. HTTPS, byte-range HTTP, local filesystem/object storage, removable media, edge-node serving, and federated replication may all carry the same publication bytes and identities.

Federation wraps discovery, availability, synchronization, or replication around the publication. It does not define a second geographic schema and does not require peers to share Kane Fabric's internal database implementation.

The normative baseline-consumption contract is `docs/BASELINE_GEOGRAPHY_DISTRIBUTION.md`. The current substrate wire format is `docs/SUBSTRATE_FORMAT_V1.md`. The current partition/subscription direction is `docs/MILESTONE_4_DESIGN.md`.

## 2. Geographic composition

### Shared substrate

The substrate contains geographic context useful to many applications.

The accepted Milestone 3 Kane County v1 substrate contains:

- county boundary/context;
- roads;
- water.

Additional stable layers should be added only when justified by multiple consumers or by a clear geographic contract.

The Milestone 3 county publication remains canonical. Geographic partitions select or reference relevant content from it; they do not create independent authoritative town/township databases.

### Geographic partitions

A geographic partition is a deterministic jurisdiction-scoped description of an area used for selection, composition, storage planning, replication, and serving.

Initial partition classes include:

- whole jurisdiction;
- municipality/incorporated place where an accepted boundary definition exists;
- township/equivalent administrative subdivision where an accepted boundary definition exists;
- explicit bounded region;
- deterministic composite scope where justified.

Municipalities and townships are useful human-facing scopes but are not the only mechanism. Geographic/application objects may cross them.

Partition boundaries are distribution boundaries, not authority or ownership boundaries. A road, water feature, building identity, or subscription object crossing several partitions keeps one logical identity and may be referenced or replicated in each required partition.

Partition identity must not include a physical ESP32 identity, hostname, SSID, network address, or storage path.

### Subscriptions

Subscriptions are independently versioned logical domain datasets layered on top of the substrate.

Initial proof paths:

- Condo;
- Industry / Mechanical Compiler.

Future examples may include Retail or other domain-specific datasets.

Subscriptions may contain:

- relevant site/building geometry;
- classification/state;
- domain metadata;
- references to Fabric geographic identities;
- declared geographic partition coverage;
- rights/license metadata appropriate to the application dataset.

One geographic object may participate in multiple subscriptions independently.

A subscription may cover one partition, many partitions, or a whole jurisdiction. It may fit on one edge node, share a node, span several nodes, or be replicated. Physical placement does not change subscription identity.

## 3. Authority boundaries

Kane Fabric owns geographic truth and geographic release state.

A consuming application owns its own business/application state.

For Mechanical Compiler, this means:

- Kane Fabric may own geographic site/building identities and geometry;
- Mechanical Compiler may own participant, qualification, capability, workflow, and federation state;
- Mechanical Compiler references Kane Fabric identities through an explicit interface;
- neither database is silently treated as a writable extension of the other.

The application consumes published Kane Fabric geographic contracts. It does not become coupled to the control-plane GeoPackage schema merely because it references Fabric geography.

A partition also does not become geographic authority. It is a deterministic selection/distribution contract over accepted geography and subscription generations.

## 4. Package direction

The architecture uses immutable, verifiable package generations.

Milestone 3 froze the first concrete baseline publication shape:

```text
county-overview.json
roads-lod.kfs
water-lod.kfs
substrate-manifest.json
```

Milestone 4 adds logical partition and subscription descriptors/manifests without changing the fact that the county substrate above is canonical.

Content-addressed object storage may be used underneath or around those publication identities, for example:

```text
objects/<prefix>/<sha256>
manifests/<generation>.json
```

A manifest can identify:

- jurisdiction/substrate generation;
- partition definition/generation;
- subscription generations;
- object/component hashes;
- selected chunk/range references;
- sizes;
- compression;
- dependencies;
- signatures or trust metadata.

Object-storage layout is a transport/storage choice. It must preserve the publication bytes and logical identities defined by the current contracts.

## 5. Milestone boundary: logical partitioning versus ESP-IDF

Milestone 4 defines:

- deterministic geographic scope/partition identity;
- substrate selection/reference behavior for a partition;
- subscription manifests and independent generations;
- cross-boundary inclusion/composition rules;
- browser composition of scoped substrate plus subscriptions;
- device-independent placement semantics.

Milestone 5 defines:

- actual ESP32-S3/ESP-IDF firmware;
- ESP-IDF HTTP behavior;
- physical storage layout/capacity decisions;
- partition/subscription placement on devices;
- Wi-Fi/AP/STA behavior;
- activation/recovery on reference hardware.

This keeps hardware implementation from contaminating logical dataset identity while still making constrained devices a first-class design constraint.

## 6. Transport boundary

Local browser operation must not depend on an upstream control-plane connection.

Possible transports between county Fabric nodes, edge nodes, mirrors, federated peers, and consumers include:

- HTTPS;
- byte-range HTTP;
- WireGuard-carried services;
- filesystem or object synchronization;
- federated discovery/replication protocols;
- future transports satisfying the same publication contract.

WireGuard is optional infrastructure, not a browser requirement.

No transport is allowed to silently change the meaning or content identity of baseline geography, partition definitions, or subscriptions it carries.

## 7. Failure model

The design should preserve useful operation through common failures:

- upstream county source unavailable -> existing accepted geographic state remains valid;
- candidate validation failure -> accepted database remains active;
- interrupted promotion -> prior accepted database remains recoverable;
- Fabric node temporarily unavailable -> edge nodes may continue serving the last activated generations;
- one edge node lost -> partitions/subscriptions may be restored, relocated, or replicated without changing logical identities;
- a partition's administrative boundary is updated -> a new partition definition/generation is produced rather than silently changing the old definition;
- one transport unavailable -> another transport may carry the same immutable publication;
- browser platform changes -> standards-based HTTP/browser contract limits client-specific rebuilding;
- federated peer implementation differs internally -> interoperability remains possible at the publication boundary.

## 8. Non-goals of the current architecture

The architecture does not require:

- one CT per internal subsystem;
- one ESP per subscription or partition;
- treating a town/township partition as its own geographic authority;
- destructive clipping of cross-boundary objects merely for edge placement;
- ESP-IDF implementation during Milestone 4;
- a native Android application;
- a native Windows application;
- PostgreSQL/PostGIS solely for architectural fashion;
- Docker as a prerequisite;
- exposing the authoritative GeoPackage schema as an external API;
- requiring federated peers to run Kane Fabric's internal database implementation;
- a revival of the old Kane Condo/County Field Map grid or VOID workflow.

Any such dependency must be justified by a concrete later requirement.
