# Kane Fabric Architecture

## 1. System roles

Kane Fabric separates authority, administration, presentation, logical publication identity, and physical edge custody/serving.

The governing administrative/edge distinction is `docs/ADMINISTRATIVE_EDGE_BOUNDARY.md`.

### County Fabric node

The Debian CT is the authoritative geographic control plane and compiler for the Kane County reference implementation.

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
- publish immutable geographic artifacts and manifests;
- provide explicit geographic contracts to applications.

The authoritative GeoPackage and its SQL schema are internal control-plane implementation details. External consumers do not use the database as the Kane Fabric API.

### Administrative infrastructure

Administrative infrastructure turns accepted county geography into interoperable Civic Infrastructure without making one hosted service the exclusive custodian of participant data.

Responsibilities include:

- county-wide web/map composition;
- category and object-class definitions;
- participant-publication, reference, visibility, and interoperability contracts;
- rules for attaching participant publications to accepted geographic identities;
- validation of shared contract conformance;
- operator-facing documentation and conformance boundaries sufficient for an independent operator to implement another county.

Administrative infrastructure does not acquire ownership of participant-local data merely because it composes that data into a county-facing view.

### Browser

The browser is the primary user client.

Responsibilities:

- obtain the required boot application and geographic manifests;
- obtain and compose participant publications as permitted by their contracts;
- select geographic scope/partitions;
- validate package identity where required;
- fetch only required component ranges/objects;
- decompress package content where appropriate;
- render geographic context;
- pan and zoom continuously;
- compose substrate, subscriptions, and bounded participant publications;
- perform user interaction defined by consuming applications.

The browser should not need county-wide migration, harvesting, reconciliation, compilation capabilities, ESP32 firmware knowledge, or knowledge of the authoritative database schema.

### Wiregate hub

The Wiregate hub owns the browser secure-origin boundary for the first-release reference topology.

Responsibilities may include:

- terminate browser HTTPS using a browser-trusted certificate;
- expose the browser-facing artifact origin;
- proxy bounded HTTP requests to a physical edge;
- support administrative composition of county publication and participant publication;
- remain separate from Fabric geographic/content identity and from the ESP32's management identity.

The Wiregate hub does not become geographic authority or participant-data owner merely because it terminates HTTPS or presents a composed view.

### Edge nodes

Edge nodes are low-cost replaceable local custody/serving resources for **bounded participant publications**.

Responsibilities may include:

- plain HTTP serving of immutable participant artifacts to a gateway/hub;
- local persistent storage sized for the bounded deployment publication;
- package receipt;
- hash/signature verification;
- activation of manifest generations;
- last-known-good local operation;
- optional upstream synchronization through WireGuard, federation, or future transport.

A participant edge is not required to store the complete county substrate. It may reference accepted county/building/partition/subscription identities while holding only the artifacts needed for its participant scope. A condominium edge, for example, may hold one association and its unit-level publication data rather than a complete Kane County roads/water package.

The first-release ESP32-S3 reference deliberately does **not** terminate browser HTTPS, host the county web map, administer categories/contracts, or own person identity. ESP32-S3 is the initial firmware reference implementation, not a permanent platform dependency, and its first-release responsibility is intentionally modest so the firmware lifecycle exists from the beginning without forcing future administrative roles into v1.

A physical edge node is never the identity of a subscription, geographic partition, association, unit, or participant publication. The same logical participant publication may move to replacement hardware without changing application semantics.

### External consumption boundary

The durable external interface is compiled geographic publication plus explicit subscription, partition, and participant-publication contracts—not the internal database, compiler API, or a proprietary hosted portal.

The same immutable contracts must be consumable by:

- web applications;
- microcontrollers and constrained edge devices where their bounded scope requires them;
- caches and mirrors;
- independent applications;
- federated peers and synchronization protocols;
- independently operated county implementations.

Consumers use explicit jurisdiction identity, publication/component format versions, accepted-release descriptors, hashes, lengths, indices, chunks, partition definitions, subscription generations, participant publication generations, category definitions, visibility semantics, and manifest/content identities. They must not depend on SQLite table names, migration numbers, CT paths, Python module names, hostnames, SSIDs, hardware serials, or other control-plane/placement internals.

Transport may change without changing the geographic or participant-publication contract. HTTPS, byte-range HTTP, local filesystem/object storage, removable media, edge-node serving, and federated replication may all carry the same publication bytes and identities.

Federation wraps discovery, availability, synchronization, or replication around the publication. It does not define a second geographic schema and does not require peers to share Kane Fabric's internal database implementation.

The normative baseline-consumption contract is `docs/BASELINE_GEOGRAPHY_DISTRIBUTION.md`. The current substrate wire format is `docs/SUBSTRATE_FORMAT_V1.md`. The current partition/subscription direction is `docs/MILESTONE_4_DESIGN.md`. The administrative/edge boundary is `docs/ADMINISTRATIVE_EDGE_BOUNDARY.md`.

## 2. Geographic composition

### Shared substrate

The substrate contains geographic context useful to many applications.

The accepted Milestone 3 Kane County v1 substrate contains:

- county boundary/context;
- roads;
- water.

Additional stable layers should be added only when justified by multiple consumers or by a clear geographic contract.

The Milestone 3 county publication remains canonical. Geographic partitions select or reference relevant content from it; bounded participant edges may reference it without replicating all of its bytes.

### Geographic partitions

A geographic partition is a deterministic jurisdiction-scoped description of an area used for selection, composition, storage planning, replication, and serving.

Initial partition classes include:

- whole jurisdiction;
- municipality/incorporated place where an accepted boundary definition exists;
- township/equivalent administrative subdivision where an accepted boundary definition exists;
- explicit bounded region;
- deterministic composite scope where justified.

Municipalities and townships are useful human-facing scopes but are not the only mechanism. Geographic/application objects may cross them.

Partition boundaries are distribution boundaries, not authority or ownership boundaries. A road, water feature, building identity, subscription object, or participant reference crossing several partitions keeps one logical identity and may be referenced or replicated in each required partition.

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

A subscription may cover one partition, many partitions, or a whole jurisdiction. Its logical identity does not require one physical edge to carry the whole subscription.

### Participant publications

Participant publications are bounded, independently retained publications contributed by organizations or other participating entities through administrative contracts.

A participant publication may contain association/unit or other domain records, category assignments, visibility classifications, and references to accepted Fabric geographic identities. It does not become accepted county geography merely because it appears on the county web map.

Participant-publication identity must remain independent of the ESP32, IP address, Wiregate origin, account provider, or county operator implementation that happens to carry it.

## 3. Authority boundaries

Kane Fabric owns geographic truth and geographic release state for the reference county implementation.

Administrative contracts own the shared interoperability semantics by which participant publications are composed with that geography.

A consuming application or participant owns its own application/participant state unless a separate explicit contract says otherwise.

For Mechanical Compiler, this means:

- Kane Fabric may own geographic site/building identities and geometry;
- Mechanical Compiler may own participant, qualification, capability, workflow, and federation state;
- Mechanical Compiler references Kane Fabric identities through an explicit interface;
- neither database is silently treated as a writable extension of the other.

For a condominium publication, this means the county can provide accepted geographic/building context while the participant publication carries association/unit information under the administrative contract. Online composition does not make the county web operator the exclusive custodian of that participant publication.

The application consumes published Kane Fabric contracts. It does not become coupled to the control-plane GeoPackage schema merely because it references Fabric geography.

A partition also does not become geographic authority. It is a deterministic selection/distribution contract over accepted geography and publication generations.

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

Administrative development adds bounded participant-publication contracts that may reference those canonical identities without copying the complete county substrate into each participant package.

Content-addressed object storage may be used underneath or around those publication identities, for example:

```text
objects/<prefix>/<sha256>
manifests/<generation>.json
```

A manifest can identify:

- jurisdiction/substrate generation;
- partition definition/generation;
- subscription generations;
- participant publication generation;
- object/component hashes;
- selected chunk/range references;
- sizes;
- compression;
- dependencies;
- visibility/classification metadata;
- signatures or trust metadata.

Object-storage layout is a transport/storage choice. It must preserve the publication bytes and logical identities defined by the current contracts.

## 5. Milestone boundary: logical administration versus ESP-IDF

Milestone 4 defines:

- deterministic geographic scope/partition identity;
- substrate selection/reference behavior for a partition;
- subscription manifests and independent generations;
- cross-boundary inclusion/composition rules;
- browser composition of scoped substrate plus subscriptions;
- device-independent placement semantics.

Milestone 5 defines:

- actual ESP32-S3/ESP-IDF firmware;
- ESP-IDF plain-HTTP artifact behavior behind the Wiregate hub;
- physical storage layout/capacity decisions for bounded participant publications;
- firmware provisioning/replacement and later network-management behavior;
- activation/recovery on reference hardware;
- integration proof between a bounded edge publication and the administrative county/web layer.

The county-wide map, categories, participant-publication semantics, and independent-operator conformance rules are administrative infrastructure. They are deliberately developed outside ESP-IDF and then consumed by the edge integration contract.

This keeps hardware implementation from contaminating logical dataset identity while still making constrained devices a first-class design constraint.

## 6. Transport boundary

Useful local participant operation must not depend on an upstream county control-plane connection. The county-facing web experience may be online, but the participant publication must remain independently retainable and movable.

Possible transports between county Fabric nodes, edge nodes, mirrors, federated peers, gateways, and consumers include:

- HTTPS;
- byte-range HTTP;
- WireGuard-carried services;
- filesystem or object synchronization;
- federated discovery/replication protocols;
- future transports satisfying the same publication contract.

WireGuard is optional infrastructure, not a browser requirement.

No transport is allowed to silently change the meaning or content identity of baseline geography, partition definitions, subscriptions, categories, or participant publications it carries.

## 7. Failure model

The design should preserve useful operation through common failures:

- upstream county source unavailable -> existing accepted geographic state remains valid;
- candidate validation failure -> accepted database remains active;
- interrupted promotion -> prior accepted database remains recoverable;
- county web service temporarily unavailable -> participant publication remains independently retained at its edge/operator custody boundary;
- management path unavailable -> edge may continue serving its last valid activated bounded publication;
- one edge node lost -> participant publication may be restored or relocated without changing logical identities;
- a partition's administrative boundary is updated -> a new partition definition/generation is produced rather than silently changing the old definition;
- one transport unavailable -> another transport may carry the same immutable publication;
- browser platform changes -> standards-based HTTP/browser contract limits client-specific rebuilding;
- federated peer or independent county implementation differs internally -> interoperability remains possible at the publication/administrative contract boundary.

## 8. Non-goals of the current architecture

The architecture does not require:

- one CT per internal subsystem;
- one ESP per subscription or partition;
- a complete county substrate on every ESP32 edge;
- treating a town/township partition as its own geographic authority;
- destructive clipping of cross-boundary objects merely for edge placement;
- an ESP32-hosted browser access point;
- browser TLS termination on the ESP32-S3;
- county web-map hosting on the ESP32-S3;
- category/contract administration on the ESP32-S3;
- a native Android application;
- a native Windows application;
- PostgreSQL/PostGIS solely for architectural fashion;
- Docker as a prerequisite;
- exposing the authoritative GeoPackage schema as an external API;
- requiring federated peers or independent county operators to run Kane Fabric's internal database implementation;
- a revival of the old Kane Condo/County Field Map grid or VOID workflow.

Any such dependency must be justified by a concrete later requirement.