# Kane Fabric Project Charter

## 1. Purpose

Kane Fabric is public civic infrastructure for maintaining and distributing authoritative county-scale geographic state.

Its first implementation is Kane County, Illinois. Kane County is the reference deployment, not the conceptual namespace of the software. New reusable contracts must anticipate operation across U.S. counties and county-equivalent jurisdictions without requiring a redesign for each jurisdiction.

The foundational reconstruction objective has been proven through Milestones 1 and 2. Reconstructability remains mandatory, but the forward objective is now to preserve authentic public-infrastructure properties while maintaining current accepted county geography and building portable substrate, subscription, browser, edge, and federation-facing distribution contracts.

The governing companion documents are:

- `docs/CIVIC_INFRASTRUCTURE_PRINCIPLES.md`;
- `docs/MULTI_COUNTY_DESIGN.md`;
- `docs/BASELINE_GEOGRAPHY_DISTRIBUTION.md`;
- `docs/DEVELOPMENT_PROCESS.md`.

## 2. Fixed principles

### Civic infrastructure

Kane Fabric is deliberately released under the repository `LICENSE` using The Unlicense/public-domain dedication.

The project must remain usable, adaptable, redistributable, independently operable, and available to commerce, government, nonprofit organizations, researchers, communities, and individuals without requiring continuing permission from the original project.

Kane Fabric must not make political, religious, commercial, governmental, philosophical, or intellectual-ideological affiliation a condition of use.

These are architectural objectives, not incidental licensing choices. See `docs/CIVIC_INFRASTRUCTURE_PRINCIPLES.md`.

### Current authoritative geography

Maintaining an up-to-date accepted county geographic database is a primary operational objective.

Freshness does not mean automatically trusting the newest upstream response. Kane Fabric preserves source provenance, detects likely changes, harvests candidates, validates and compares them, reconciles durable geographic identity where required, and changes accepted state only through explicit promotion.

When an upstream source is unavailable or a candidate fails validation, the previously accepted state remains authoritative until a valid replacement is promoted.

### Baseline geography is the durable external interface

Kane Fabric compiles accepted county geography into immutable baseline publications that can be consumed independently of the authoritative database implementation.

The same baseline geography must be usable by:

- web applications;
- microcontrollers and constrained edge nodes;
- local caches and mirrors;
- independent software implementations;
- federated peers and synchronization protocols.

The authoritative GeoPackage, SQL schema, migrations, CT paths, and internal Python APIs are control-plane implementation details. They are not the external Kane Fabric consumer interface.

External consumers depend on explicit jurisdiction, format/version, accepted-release, component, hash, chunk, manifest, and content identities. Transport may vary while those bytes and identities remain stable.

Federation may advertise, locate, synchronize, relay, cache, or replicate baseline geography without requiring every peer to share Kane Fabric's internal database schema. See `docs/BASELINE_GEOGRAPHY_DISTRIBUTION.md`.

### Multi-county design horizon

Kane County remains the sole required operational reference deployment for current work, but new reusable namespaces, database tokens, package identities, manifests, and protocol contracts must not unnecessarily assume Kane County.

Generic concepts should use generic identities. Kane-specific source facts should remain in Kane/source profiles, Kane evidence, or clearly Kane-specific deployment entry points.

No second-county implementation, placeholders, stubs, or speculative national framework are required merely to satisfy this principle. See `docs/MULTI_COUNTY_DESIGN.md`.

### Development execution authority

GitHub `main`, the Proxmox host, CT102, and Kane Fabric operational data have different authority roles and must not be confused.

For the Kane reference deployment:

- GitHub `main` is the software/contracts Single Source of Truth;
- `srv-b` owns Proxmox/LXC control and host conformance;
- CT102 `kane-fabric` is the real Kane Fabric execution environment;
- `/var/lib/kane-fabric` inside CT102 contains operational county state and evidence.

Routine Kane Fabric commands are executed in CT102 through the authorized `srv-b` host-to-LXC path using `pct exec 102 -- ...`. An Assistant sandbox is not a substitute for CT102 acceptance, and the user is not the default terminal relay for routine Assistant-driven development.

The detailed process and capability-failure rules are defined in `docs/DEVELOPMENT_PROCESS.md`.

### Browser-first client

The browser is the enduring user platform. Windows, Linux, Android, and future browser-capable systems should consume Kane Fabric without requiring separate native applications when a standards-based browser implementation is sufficient.

HTTP, HTML, CSS, and JavaScript form the durable user-interface boundary.

The browser consumes compiled Kane Fabric baseline/subscription publications. It does not query the authoritative county database schema directly.

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

An edge node serves, caches, validates, synchronizes, or consumes the same compiled baseline publication contract used elsewhere. It does not require the authoritative GeoPackage implementation merely to participate in distribution.

### Substrate plus subscriptions

Kane Fabric separates shared geographic context from application-specific overlays.

The shared substrate may include county boundary, roads, water, and other stable context.

Subscriptions contain domain-specific geographic state such as Condo, Industry, Retail, or later applications.

A subscription is logical data. It is not equivalent to one physical edge node.

### Explicit application boundaries

Kane Fabric owns geographic state.

Applications such as Mechanical Compiler own their own authoritative application state and may reference Kane Fabric geographic identities through explicit contracts.

Neither system silently assumes ownership of the other's authoritative objects.

Applications consume the published Kane Fabric geographic contract rather than becoming dependent on the control-plane database schema.

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

## 4. Reconstructability — proven foundation

A county node is not considered reproducible merely because an existing machine can be copied.

Milestones 1 and 2 proved the Kane County reconstruction chain from declared inputs and extracted the geographic core into Kane Fabric ownership. The release records are `docs/MILESTONE_1_RELEASE.md` and `docs/MILESTONE_2_RELEASE.md`.

That proof changes the development emphasis; it does not retire the requirement.

Future work must continue to preserve:

- declared inputs rather than hidden orchestrator state;
- immutable seed/reference evidence where applicable;
- deterministic validation and comparison;
- explicit accepted-versus-candidate state;
- safe promotion and rollback;
- the ability to rebuild a supported Fabric node without copying an opaque existing machine.

Reconstruction is now a maintained invariant supporting the broader public-infrastructure objective.

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
- compiled substrate/subscription packages;
- audit bundles too large or unsuitable for source control.

The public-domain status of Kane Fabric software does not automatically determine the legal status of external geographic data. Source provenance and external rights remain separate boundaries.

## 6. Forward development objective

After Milestone 2, new work should be evaluated against four continuing questions:

1. Does it preserve Kane Fabric as authentic, independently usable public infrastructure?
2. Does it strengthen or preserve the ability to maintain current, validated, authoritative county geographic state?
3. Can independent consumers use the compiled baseline without knowledge of the authoritative database internals?
4. If the concept is geographically generic, does its durable namespace and contract avoid unnecessary Kane County coupling?

The project does not need to implement the nation in order to answer the fourth question correctly.

Kane County remains the proving deployment. The architecture should make a future second jurisdiction primarily a matter of jurisdiction/source contracts and evidence where the existing geographic model applies, rather than a fork of the core system.
