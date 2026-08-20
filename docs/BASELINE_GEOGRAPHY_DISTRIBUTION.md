# Kane Fabric Baseline Geography Distribution

## Status

Normative architecture contract for external consumption of Kane Fabric baseline geography.

This document defines the boundary between the authoritative county control plane and every external consumer of Kane Fabric geography.

## Purpose

Kane Fabric exists to maintain authoritative county-scale geographic state and distribute a stable baseline that can be consumed by unrelated software and hardware without access to the authoritative database implementation.

The durable system shape is:

```text
official sources
      ↓
Kane Fabric authoritative control plane
  provenance / validation / accepted state
      ↓
deterministic compiler
      ↓
immutable baseline geography publication
      ↓
logical geographic partition/reference layer
      ↓
┌──────────────┬─────────────────┬─────────────────┬──────────────────┐
│ web apps     │ microcontrollers│ caches / mirrors│ federated peers  │
└──────────────┴─────────────────┴─────────────────┴──────────────────┘
```

The GeoPackage, migrations, source tables, reconciliation tables, and compiler-internal Python interfaces are control-plane implementation details. They are not the public Kane Fabric consumer API.

## One logical baseline, many transports and scopes

A Kane Fabric baseline publication has one logical identity regardless of how its bytes reach a consumer or which geographic subset a consumer selects.

For the current v1 substrate the publication is composed of:

```text
county-overview.json
roads-lod.kfs
water-lod.kfs
substrate-manifest.json
```

The manifest, jurisdiction identity, accepted-release lineage, component hashes, and substrate content identity define the publication. A transport or partition selector must not reinterpret or regenerate those identities.

The same publication may be delivered through:

- ordinary HTTPS;
- local HTTP from an ESP32-S3-class edge node;
- byte-range HTTP;
- a filesystem, removable medium, object store, or local cache;
- synchronization between Kane Fabric nodes or mirrors;
- a federated protocol that advertises, requests, relays, or replicates the publication;
- future transports that preserve the same bytes and identities.

Transport metadata may wrap the publication. It must not silently rewrite component bytes, jurisdiction identity, accepted-release identity, or content hashes.

A geographic partition may select/reference only the ranges/chunks required for a focused area. That selection does not create a new authoritative baseline or change the identity of the underlying publication.

## Consumer contract

External consumers depend on the compiled publication contract, not on the authoritative database schema.

A consumer may assume only documented publication semantics such as:

- explicit jurisdiction identity;
- format/version identity;
- immutable component bytes;
- content hashes and lengths;
- accepted source-release descriptors;
- deterministic component framing;
- indexed chunks and byte ranges where defined;
- documented geographic record semantics;
- substrate content identity;
- atomic publication generations;
- explicit partition/subscription descriptors when consuming scoped application data.

A consumer must not need to know:

- SQLite or GeoPackage table names;
- migration numbers;
- source-release primary keys;
- CT102 paths;
- Kane County database filenames;
- harvesting or reconciliation internals;
- Python module names;
- compiler implementation details;
- which physical edge device currently stores a logical partition/subscription.

Changing those internal details must not require changes to conforming external consumers when the publication contract remains unchanged.

## Web applications

A web application consumes baseline geography as immutable published data.

The browser should be able to:

1. obtain a manifest and jurisdiction overview;
2. validate format, jurisdiction, release, length, and hash identities;
3. inspect a component prefix and canonical index;
4. choose a viewport or declared geographic partition;
5. request only needed compressed byte ranges;
6. validate and decompress selected chunks;
7. render baseline geography;
8. compose application-specific subscriptions without modifying the baseline.

No web application should require direct access to the authoritative GeoPackage.

## Geographic partition relationship

Milestone 4 adds deterministic geographic partition/scoping identity above the baseline publication.

A partition is a logical selection/distribution definition, not a second baseline and not a physical device.

Expected scope classes include:

- whole jurisdiction;
- municipality/incorporated place where an accepted boundary definition exists;
- township/equivalent administrative subdivision where an accepted boundary definition exists;
- explicit bounded region;
- deterministic composite scope where justified.

A partition descriptor may reference:

- the baseline substrate content identity;
- exact component identities;
- selected component chunks/ranges;
- neighboring/context chunks required for continuity;
- subscription objects/generations relevant to the same scope.

The same baseline chunk may be referenced by multiple partitions. Storage duplication does not create new geographic identity.

Administrative partition boundaries are distribution boundaries, not semantic ownership boundaries. Roads, water, buildings, and subscription objects crossing a boundary retain one logical identity.

The partition identity must remain independent of ESP32 identity, hostname, SSID, IP address, and storage path.

## Microcontrollers and constrained edge devices

An ESP32-S3-class node is a replaceable data-plane participant, not a geographic authority.

A constrained device may:

- store exact publication files or selected immutable ranges/objects;
- store partition descriptors and subscription manifests;
- validate hashes during receipt or activation;
- advertise available publication/partition/subscription identities;
- serve manifests, overview data, indices, and selected byte ranges;
- cache or relay exact immutable objects;
- synchronize newer complete generations before atomic activation.

The device must not need SQLite, GeoPackage interpretation, source harvesting, reconciliation, or county-specific GIS logic merely to serve baseline geography.

A future microcontroller that actively consumes geography rather than only serving it still consumes the same publication/partition contracts.

Actual ESP32-S3/ESP-IDF implementation remains a Milestone 5 responsibility. Milestone 4 defines only the hardware-independent logical partition/subscription semantics required for focused placement.

## Federated protocols

Federation is a transport and discovery concern around the publication contract, not a second geographic schema.

A federated peer may exchange information such as:

- jurisdiction identity;
- substrate format/version;
- substrate content SHA-256;
- manifest identity or locator;
- partition identity/definition;
- subscription generation identity;
- component descriptors;
- availability/capability metadata;
- replication or synchronization hints.

The peer then obtains or relays the exact publication/subscription bytes defined by the relevant manifests.

Federation must not require every peer to share Kane Fabric's authoritative database schema. A peer can interoperate at the publication boundary even if its internal storage and implementation are entirely different.

Application federation and baseline-geography federation are also separate concerns. Mechanical Compiler, Condo, Retail, or another application may federate its own state while referencing the same Kane Fabric baseline jurisdiction/content/partition identities.

## Authority and publication lifecycle

Only accepted geographic state enters a baseline publication.

The lifecycle is:

```text
candidate source state
      ↓ validate / compare / reconcile as required
accepted authoritative state
      ↓ deterministic compile
complete staged baseline publication
      ↓ validate / reproduce
atomic activation
      ↓
immutable consumer-visible generation
      ↓
partition/subscription selection and composition
```

Consumers never infer authority from recency alone. A newer candidate is not baseline geography until it has crossed the accepted-state and publication boundaries.

Partition generation/selection is downstream of accepted geography and must never act as implicit promotion.

## Identity

Jurisdiction identity is explicit and independent of host, path, transport, partition placement, or physical device.

For the current Kane County reference deployment:

```text
country_code  US
state_code    IL
fips_code     17089
county_key    kane-county-il
name          Kane County
```

A publication also carries accepted-release identities and a deterministic substrate content identity. Those identities allow a browser, microcontroller, mirror, or federated peer to determine whether two copies represent the same baseline without knowing how either copy was produced.

A partition adds a deterministic scope identity while preserving the baseline and feature identities it references.

## Substrate and subscriptions

Baseline geography is shared civic context. Application-specific state is layered separately.

The baseline may be consumed by many applications simultaneously. An application may reference baseline geographic identities or spatial context without acquiring ownership of the baseline or extending the authoritative geographic database.

Subscriptions may be whole-jurisdiction or geographically scoped to one or more logical partitions. Physical placement does not become subscription identity.

Likewise, application-specific categories, qualifications, workflows, participant state, or federation state do not become baseline geography merely because they are displayed on the same map or served by the same device.

## Internal compiler boundary

The compiler requires a tested internal read interface to authoritative accepted state. That interface exists to prevent compiler modules from duplicating SQL and GeoPackage validation logic.

It is deliberately not a public consumer contract.

The intended internal flow is:

```text
GeoPackage
   ↓
Fabric database/storage validation
   ↓
Fabric read-side API
   ↓
baseline compiler
   ↓
consumer-facing immutable publication
   ↓
partition/subscription manifests and selection
```

External consumers begin at the publication/partition/subscription boundary, not at the Fabric read-side API.

## Compatibility rule

A change to database schema, migration layout, internal Python APIs, or compiler implementation is an internal change unless it changes published bytes or semantics.

A change to required baseline publication files, framing, record semantics, identity, compression, validation rules, or required consumer behavior is a substrate publication-contract change and must follow substrate versioning rules.

A change to partition descriptor semantics or subscription manifest semantics is an MS-4 logical-contract change and must be versioned independently rather than silently changing the Milestone 3 baseline.

## Design test

For every new Kane Fabric feature, ask:

> Can an independent web application, constrained device, mirror, or federated implementation consume the baseline and declared partitions/subscriptions using only the documented external contracts, with no knowledge of authoritative database internals or physical device placement?

If the answer is no, the external interface is incomplete or the implementation has crossed the authority boundary.
