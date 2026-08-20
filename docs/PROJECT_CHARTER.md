# Kane Fabric Project Charter

## 1. Purpose

Kane Fabric is public civic infrastructure for maintaining and distributing authoritative county-scale geographic state.

Its first implementation is Kane County, Illinois. Kane County is the reference deployment, not the conceptual namespace of the software. New reusable contracts must anticipate operation across U.S. counties and county-equivalent jurisdictions without requiring a redesign for each jurisdiction.

The foundational reconstruction objective has been proven through Milestones 1 and 2. Milestone 3 proved the deterministic public county substrate and selective browser-consumption model. Reconstructability remains mandatory, but the forward objective is now to preserve authentic public-infrastructure properties while maintaining current accepted geography and building portable substrate, geographic-partition, subscription, browser, edge, and federation-facing contracts.

The governing companion documents are:

- `docs/CIVIC_INFRASTRUCTURE_PRINCIPLES.md`;
- `docs/MULTI_COUNTY_DESIGN.md`;
- `docs/BASELINE_GEOGRAPHY_DISTRIBUTION.md`;
- `docs/DEVELOPMENT_PROCESS.md`;
- `docs/MILESTONE_4_DESIGN.md`.

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

Compilation, partition selection, subscription publication, rendering, caching, and edge placement do not silently change accepted geographic authority.

### Baseline geography is the durable external interface

Kane Fabric compiles accepted county geography into immutable baseline publications that can be consumed independently of the authoritative database implementation.

The same baseline geography must be usable by:

- web applications;
- microcontrollers and constrained edge nodes;
- local caches and mirrors;
- independent software implementations;
- federated peers and synchronization protocols.

The authoritative GeoPackage, SQL schema, migrations, CT paths, and internal Python APIs are control-plane implementation details. They are not the external Kane Fabric consumer interface.

External consumers depend on explicit jurisdiction, format/version, accepted-release, component, hash, chunk, manifest, and content identities. Transport and physical storage placement may vary while those bytes and identities remain stable.

Federation may advertise, locate, synchronize, relay, cache, or replicate baseline geography without requiring every peer to share Kane Fabric's internal database schema. See `docs/BASELINE_GEOGRAPHY_DISTRIBUTION.md`.

### Geographic partitions are logical distribution identities

Kane Fabric may define deterministic geographic partitions so consumers and constrained edge devices can work with focused subsets smaller than the whole jurisdiction.

A partition is a logical jurisdiction-scoped distribution/composition identity. It is not:

- a second geographic authority;
- a separate authoritative town/township database;
- a physical ESP32 identity;
- a hostname, SSID, IP address, or storage path;
- semantic ownership of objects within the boundary.

Useful partition scopes may include whole jurisdiction, municipality/incorporated place, township/equivalent subdivision, explicit bounded region, and deterministic composite scopes where justified.

Administrative terms are jurisdiction-specific conveniences, not universal assumptions. Cross-boundary roads, water, buildings, and subscription objects retain one logical identity and may be referenced or replicated in several partitions.

The canonical county substrate remains the underlying public geographic publication. Partition contracts select/reference it rather than replacing it.

### Multi-county design horizon

Kane County remains the sole required operational reference deployment for current work, but new reusable namespaces, database tokens, package identities, partition identities, manifests, and protocol contracts must not unnecessarily assume Kane County.

Generic concepts should use generic identities. Kane-specific source facts and administrative-boundary choices should remain in Kane/source profiles, Kane evidence, or clearly Kane-specific deployment entry points.

No second-county implementation, placeholders, stubs, or speculative national framework are required merely to satisfy this principle. See `docs/MULTI_COUNTY_DESIGN.md`.

### Development execution authority

GitHub `main`, the Proxmox host, CT102, and Kane Fabric operational data have different authority roles and must not be confused.

For the Kane reference deployment:

- GitHub `main` is the software/contracts Single Source of Truth;
- `srv-b` owns Proxmox/LXC control and host conformance;
- CT102 `kane-fabric` is the real Kane Fabric execution environment;
- `/var/lib/kane-fabric` inside CT102 contains operational county state and evidence.

Routine Kane Fabric commands are executed in CT102 through the authorized `srv-b` host-to-LXC path using `pct exec 102 -- ...`. An Assistant sandbox is not a substitute for CT102 acceptance.

The detailed process and capability-failure rules are defined in `docs/DEVELOPMENT_PROCESS.md`.

### Browser-first client

The browser is the enduring user platform. Windows, Linux, Android, and future browser-capable systems should consume Kane Fabric without requiring separate native applications when a standards-based browser implementation is sufficient.

HTTP, HTML, CSS, and JavaScript form the durable user-interface boundary.

The browser consumes compiled Kane Fabric baseline, partition, and subscription publications. It does not query the authoritative county database schema directly.

### One county Fabric node

A county Fabric deployment begins with one authoritative Debian CT unless a later requirement proves another service boundary is necessary.

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
- partition/subscription compilation;
- publication;
- edge-node management and synchronization.

### Replaceable edge nodes

ESP-class hardware is an edge data plane, not the source of geographic truth.

The initial reference hardware is ESP32-S3-class equipment. The architecture must not depend on that specific processor. Faster future devices should satisfy the same contracts without requiring browser, package, partition, or subscription redesign.

An edge node serves, caches, validates, synchronizes, or consumes compiled public artifacts. It does not require the authoritative GeoPackage implementation merely to participate in distribution.

Physical placement is separate from logical identity. One node may carry several partitions/subscriptions; one partition/subscription may span or be replicated across several nodes.

Actual ESP32-S3/ESP-IDF implementation is a Milestone 5 responsibility. Earlier milestones may impose compatibility constraints but must not silently pull hardware/runtime identity into logical data contracts.

### Substrate plus subscriptions

Kane Fabric separates shared geographic context from application-specific overlays.

The shared substrate includes county boundary, roads, water, and other stable context justified by broad use.

Subscriptions contain independently versioned domain-specific geographic/application state such as Condo, Industry, Retail, or later applications.

A subscription is logical data. It is not equivalent to one physical edge node.

Subscriptions may be whole-jurisdiction or scoped through one or more logical geographic partitions.

### Explicit application boundaries

Kane Fabric owns geographic state.

Applications such as Mechanical Compiler own their own authoritative application state and may reference Kane Fabric geographic identities through explicit contracts.

Neither system silently assumes ownership of the other's authoritative objects.

Applications consume the published Kane Fabric geographic contract rather than becoming dependent on the control-plane database schema.

A proprietary, restricted, private, or commercially licensed application subscription does not acquire ownership of the public Kane Fabric substrate or partition definitions merely because the artifacts are composed together or served from the same device.

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

Milestones 1 and 2 proved the Kane County reconstruction chain from declared inputs and extracted the geographic core into Kane Fabric ownership. Milestone 3 proved the reproducible browser-consumable county publication.

Those proofs change development emphasis; they do not retire the requirements.

Future work must continue to preserve:

- declared inputs rather than hidden orchestrator state;
- immutable seed/reference evidence where applicable;
- deterministic validation and comparison;
- explicit accepted-versus-candidate state;
- safe promotion and rollback;
- deterministic publication/partition/subscription identities;
- the ability to rebuild a supported Fabric node without copying an opaque existing machine.

Reconstruction is a maintained invariant supporting the broader public-infrastructure objective.

## 5. Data boundary

Large geographic databases and generated operational artifacts remain outside Git.

Git stores:

- source code;
- migrations and schemas;
- source/county profiles;
- partition/subscription schemas and contracts;
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
- compiled substrate/partition/subscription packages;
- audit bundles too large or unsuitable for source control.

The public-domain status of Kane Fabric software does not automatically determine the legal status of external geographic data or separately owned application subscription state. Source provenance and external rights remain separate boundaries.

## 6. Forward development objective

New work should be evaluated against these continuing questions:

1. Does it preserve Kane Fabric as authentic, independently usable public infrastructure?
2. Does it strengthen or preserve the ability to maintain current, validated, authoritative county geographic state?
3. Can independent consumers use the compiled baseline without knowledge of authoritative database internals?
4. Can subscriptions reference public geography without collapsing application ownership into Kane Fabric?
5. Can geographic partitions focus distribution without becoming new authorities or physical-device identities?
6. If the concept is geographically generic, does its durable namespace and contract avoid unnecessary Kane County coupling?

The project does not need to implement the nation to answer the sixth question correctly.

Kane County remains the proving deployment. The architecture should make a future second jurisdiction primarily a matter of jurisdiction/source/administrative-boundary contracts and evidence where the existing geographic model applies, rather than a fork of the core system.
