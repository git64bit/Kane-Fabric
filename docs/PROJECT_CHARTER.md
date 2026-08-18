# Kane Fabric Project Charter

## 1. Purpose

Kane Fabric is a reusable county-scale geographic substrate and subscription platform.

Its first implementation is Kane County, Illinois. The architectural goal is broader: the same reconstruction, acquisition, validation, compilation, publication, and browser-serving model must be capable of being instantiated for many U.S. counties without inventing a new system each time.

## 2. Fixed principles

### Browser-first client

The browser is the enduring user platform. Windows, Linux, Android, and future browser-capable systems should consume Kane Fabric without requiring separate native applications when a standards-based browser implementation is sufficient.

HTTP, HTML, CSS, and JavaScript form the durable user-interface boundary.

### One county Fabric node

A county Fabric deployment begins with one authoritative Debian CT unless a later requirement proves that another service boundary is necessary.

The county Fabric node performs heavy and authoritative work:

- official-source acquisition;
- source-profile validation;
- freshness detection;
- provenance recording;
- candidate harvesting;
- deterministic comparison;
- reconciliation;
- safe promotion and rollback;
- geometry and LOD processing;
- package compilation;
- publication;
- edge-node management and synchronization.

### Replaceable edge nodes

ESP-class hardware is an edge data plane, not the source of geographic truth.

The initial reference hardware is ESP32-S3-class equipment. The architecture must not depend on that specific processor. Faster future devices should satisfy the same contracts without requiring browser or package redesign.

### Substrate plus subscriptions

Kane Fabric separates shared geographic context from application-specific overlays.

The shared substrate may include county boundary, roads, water, and other stable context.

Subscriptions contain domain-specific geographic state such as Condo, Industry, Retail, or later applications.

A subscription is logical data. It is not equivalent to one physical edge node.

### Explicit application boundaries

Kane Fabric owns geographic state.

Applications such as Mechanical Compiler own their own authoritative application state and may reference Kane Fabric geographic identities through explicit contracts.

Neither system silently assumes ownership of the other's authoritative objects.

## 3. Kane Condo inheritance

Kane Condo is frozen at tag `0.4`.

Kane Fabric may inherit proven mechanisms from Kane Condo, including:

- GeoPackage/SQLite provenance and storage;
- official source-profile contracts;
- lightweight update detection;
- candidate harvesting;
- deterministic comparison;
- building identity reconciliation;
- atomic promotion and rollback;
- render-package experiments;
- browser-side validation, decompression, and rendering.

Kane Fabric must not inherit condo-specific assumptions merely because they exist in the donor repository.

## 4. Reconstructability requirement

A county node is not considered reproducible merely because an existing machine can be copied.

The project must demonstrate that the full county pipeline can be reconstructed from declared inputs on a clean supported Debian CT.

Every prerequisite discovered during Kane County reconstruction becomes candidate bootstrap documentation or automation for future counties.

## 5. Data boundary

Large geographic databases and generated operational artifacts remain outside Git.

Git stores:

- source code;
- migrations and schemas;
- source/county profiles;
- tests;
- documentation;
- bootstrap procedures;
- deterministic contracts and small manifests where appropriate.

External storage holds:

- accepted seeds;
- active GeoPackages;
- harvested source evidence;
- staging artifacts;
- reconciliation databases;
- rollback copies;
- compiled render/subscription packages;
- audit bundles too large or unsuitable for source control.

## 6. Initial success condition

The first major success condition is a clean Kane Fabric CT that can independently:

1. validate its environment;
2. validate the inherited Kane County seed and reference evidence;
3. execute the proven database test suite;
4. validate official source profiles;
5. detect current upstream source status;
6. reconstruct an authoritative working database from declared inputs;
7. replay candidate validation, comparison, reconciliation, promotion, and rollback;
8. compile browser-consumable geographic packages;
9. publish those packages through a stable edge/browser contract.

Only after this is demonstrated should Kane-specific procedures be generalized aggressively for other counties.