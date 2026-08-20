# Milestone 3 Design — Shared Substrate

## Status

Active Milestone 3 design baseline.

Milestone 3 produces the first deterministic browser-consumable Kane Fabric shared substrate for:

- jurisdiction boundary/context;
- roads;
- water.

The frozen v1 wire contract is `docs/SUBSTRATE_FORMAT_V1.md`.

Buildings, categories, classifications, qualifications, workflows, Mechanical Compiler state, and other application/subscription semantics are intentionally outside the shared substrate.

## Governing objectives

Milestone 3 applies three project requirements directly:

1. preserve the accepted geographic database pipeline and its explicit promotion boundary;
2. keep new durable identities jurisdiction-explicit rather than implicitly Kane County-specific;
3. keep the substrate, browser substrate code, and Kane Fabric edge implementation usable as independent civic infrastructure.

The governing documents are:

- `docs/CIVIC_INFRASTRUCTURE_PRINCIPLES.md`;
- `docs/MULTI_COUNTY_DESIGN.md`;
- `docs/ESP32_EDGE_REFERENCE.md`;
- `docs/SUBSTRATE_FORMAT_V1.md`.

Kane County remains the only required operational implementation for this milestone.

## Historical evidence

Kane Condo `0.4` is a regression/design oracle, not a runtime dependency.

Its render work already proved several geographic mechanisms that Milestone 3 should preserve where still applicable:

- a single indexed flat-file component container;
- deterministic overview and LOD generation;
- canonical JSON metadata;
- compressed chunk payloads with lengths, bounds, and hashes;
- deterministic spatial ordering as an internal storage detail;
- package manifests tied to accepted geographic state;
- package content identity independent of creation time;
- staged validation before atomic activation.

Milestone 3 extracts those geographic/package properties without importing Condo application semantics.

## Jurisdiction identity

The current Kane Fabric database uses:

```text
country_code  US
state_code    IL
fips_code     17089
county_key    kane-county-il
name          Kane County
```

For U.S. county/county-equivalent packages, FIPS is the durable geographic code currently available in the Fabric core. `county_key` and `name` remain project/display attributes.

A browser, cache, package, or edge node must not infer jurisdiction from a filename, host, directory, Wi-Fi SSID, or physical device.

## Accepted-state rule

Substrate compilation reads only accepted geographic state.

The package records the accepted release identity, source content SHA-256, and feature count for each required substrate source. Compilation fails when required accepted state is missing, ambiguous, or inconsistent with stored feature inventory.

A candidate never enters the published substrate merely because it is newer.

Substrate generation is read-only with respect to the authoritative GeoPackage.

## Package shape

V1 publishes:

```text
county-overview.json
roads-lod.kfs
water-lod.kfs
substrate-manifest.json
```

Road and water components use the format frozen in `docs/SUBSTRATE_FORMAT_V1.md`: an eight-byte Fabric magic/version, an eight-byte big-endian canonical-index length, a canonical JSON index, and contiguous zlib-compressed canonical JSON chunks.

The package directory is an activation unit. Components are not copied one at a time into active state.

## Kane County source policy versus generic contract

The package contract is generic; source-selection policy may be jurisdiction-specific.

For Kane roads, the accepted source does not retain authoritative functional road class. Milestone 3 therefore reuses the proven deterministic coordinate-length policy for `orientation`, `context`, and `detail` rather than inventing semantics that the source does not contain.

For Kane water, the accepted coordinated Fox River/creek sources do not provide a generic hydrologic importance hierarchy. Milestone 3 therefore reuses the proven deterministic Fox River/creek policy for `overview`, `context`, and `detail`.

Those rules are recorded explicitly as Kane source policy. A future jurisdiction may satisfy the same generic substrate contract using different source semantics.

## ESP32-S3 constraint in Milestone 3

ESP32-S3 serving is not optional to the architecture and does not suddenly become relevant only in Milestone 5.

Milestone 3 **does defer completion of the ESP-IDF firmware and final HTTP edge contract**, but every package-format decision is evaluated against the ESP32-S3 reference edge now.

The format must support:

- bounded reads;
- seek/range access without whole-file RAM residency;
- simple immutable-file/object serving;
- deterministic verification;
- activation without exposing mixed generations;
- browser-side decompression and rendering rather than server-side GIS logic.

The v1 fixed 16-byte prefix and indexed chunk layout are specifically intended to let a browser obtain only the index and selected compressed byte ranges from an ESP-IDF HTTP handler.

Milestone 5 will implement and prove the final reference edge behavior, including the HTTP serving contract, storage layout, activation, recovery, and AP/STA experiments.

## Browser proof

Milestone 3 is not complete when only the Python compiler works.

The browser proof must demonstrate, without any application subscription:

- loading the jurisdiction overview;
- validating required package/component identities;
- selecting and obtaining road/water chunks;
- native zlib/DEFLATE decompression;
- drawing boundary/context, roads, and water;
- useful pan and zoom navigation.

The browser must not need the authoritative GeoPackage or county refresh machinery.

## Rights boundary

The shared substrate is civic infrastructure.

Building categories, qualifications, participant/capability information, workflows, Mechanical Compiler state, and other application/subscription semantics are separate layers with separately determined ownership and licensing.

Serving both layers from one ESP32-S3 or composing both in one browser does not merge those rights boundaries.

## Implementation order

1. **MS3-001 — v1 contract:** freeze jurisdiction identity, canonical JSON, component roles, framing, hashes, and content identity.
2. **MS3-002 — overview:** compile and validate canonical jurisdiction overview from Fabric-owned accepted boundary state.
3. **MS3-003 — road LOD:** extract the proven road generator behind the generic v1 component contract.
4. **MS3-004 — water LOD:** extract coordinated water generation behind the generic v1 contract.
5. **MS3-005 — manifest:** bind all components to one jurisdiction and accepted geographic state.
6. **MS3-006 — compiler/activation:** reproducible staged complete-package build and atomic activation.
7. **MS3-007 — CT102 proof:** compile twice from accepted Kane County state and record deterministic identities and measured component/index/chunk sizes.
8. **MS3-008 — browser loader:** implement selective component/index/chunk loading, validation, and native decompression.
9. **MS3-009 — browser rendering:** prove useful boundary/road/water navigation with no subscription.
10. **MS3-010 — edge-compatibility proof:** exercise the same access pattern with bounded-response behavior representative of the ESP32-S3/ESP-IDF server contract.
11. **MS3-011 — release:** record evidence and close the milestone.

## Explicitly deferred

Milestone 3 does not implement:

- building geometry as shared substrate;
- Condo categories/classifications;
- Mechanical Compiler qualifications/workflows/state;
- subscription contracts;
- completed ESP32-S3 production firmware;
- multi-node sharding/replication;
- nationwide deployment automation;
- a second-county implementation;
- a private registry or permission service;
- County Field Map grids, cells, sectors, or VOID-mask semantics.

The difference is deliberate: completed edge firmware is deferred; **edge compatibility is a current Milestone 3 requirement**.

## Exit gate

Milestone 3 passes when a normal browser can open Kane County and navigate the deterministic shared substrate independently of any application subscription, with reproducible package identities and an access pattern that remains practical for the ESP32-S3 reference edge.
