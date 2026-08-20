# Kane Fabric

Kane Fabric is public civic infrastructure for maintaining and distributing authoritative county-scale geographic state through a browser-first substrate and subscription system.

The project begins with Kane County, Illinois, but Kane County is the reference deployment rather than the conceptual namespace of the software. New reusable contracts are intended to remain portable across U.S. counties and county-equivalent jurisdictions without building speculative nationwide infrastructure before it is needed.

Kane Fabric is deliberately released under the repository `LICENSE` using The Unlicense/public-domain dedication. Independent use, adaptation, redistribution, commercial use, government use, and continued operation without permission from the original project are intended properties. The project does not condition use on political, religious, commercial, governmental, philosophical, or intellectual-ideological affiliation. See `docs/CIVIC_INFRASTRUCTURE_PRINCIPLES.md`.

Kane Fabric grew out of Kane Condo 0.4. Kane Condo proved the county-scale browser map, source-profile registry, update detection, candidate harvesting, deterministic comparison, project-identity reconciliation, atomic promotion and rollback, render-package generation, and browser-side rendering model. Kane Condo is frozen at tag `0.4`; Kane Fabric begins from those proven results without remaining condo-specific.

## Start here for current development

**New Assistants and developers must start with `docs/HANDOFF.md`.**

That file is the stable current operational handoff. It contains the repository map, geographic database lifecycle, execution environment, external evidence/state layout, MS-1/MS-2 regression identities, compatibility nuances, current Milestone 3 implementation boundary, real-environment verification state, and the exact next safe development action.

Do not try to reconstruct current state from a historical milestone handoff alone. `docs/MILESTONE_1_RELEASE.md` and `docs/MILESTONE_2_RELEASE.md` are release evidence; `docs/MILESTONE_2_HANDOFF.md` is historical; `docs/MILESTONE_3_HANDOFF.md` is milestone-specific. `docs/HANDOFF.md` is the maintained cross-milestone entry point.

## Development and execution process

`docs/DEVELOPMENT_PROCESS.md` is the current authority for how project work is executed.

The critical execution boundary is:

```text
GitHub main
software/contracts SSOT
        ↓
srv-b
Proxmox/LXC control plane
        ↓
pct exec 102 -- ...
        ↓
CT102 kane-fabric
real Kane Fabric execution environment
        ↓
/var/lib/kane-fabric
operational county state and evidence
```

Routine Kane Fabric commands are executed inside CT102 through the authorized `srv-b` host-to-LXC path. The user's role is not to serve as the normal terminal relay for Assistant-driven development.

An Assistant sandbox is not CT102 and cannot substitute for CT102 acceptance. If a session does not expose an authorized execution channel to `srv-b`, that is an execution-capability gap and must be stated explicitly; real-environment gates remain unverified rather than being delegated to the user by default.

Historical milestone handoffs preserve historical procedures but do not override `docs/DEVELOPMENT_PROCESS.md` when their execution instructions conflict with it.

## Project status

**Milestone 1 — Kane County Reconstruction Proof: RELEASED (2026-08-18).**

A clean Kane Fabric CT independently reconstructed the Kane County pipeline from declared inputs through candidate replay, exact deterministic comparison, and project-building reconciliation. The release evidence is recorded in `docs/MILESTONE_1_RELEASE.md`.

**Milestone 2 — Extract Kane Fabric Geographic Core: RELEASED (2026-08-20).**

Kane Fabric now owns the geographic database migrations and implementation, source contracts, seed/bootstrap import, provenance, storage, durable geographic building identity, candidate engines, deterministic comparison, reconciliation, and atomic promotion/rollback. The geographic core operates without Kane Condo classification tables and without the frozen Kane Condo checkout as a runtime dependency.

The decisive historical closeout replay reproduced all Milestone 1 comparison hashes, reconciled all 208,324 building identities with zero ambiguities, promoted and rolled back the five-dataset refresh, and left the immutable seed and historical promoted oracle unchanged. The release evidence is recorded in `docs/MILESTONE_2_RELEASE.md`.

Reconstructability is therefore a proven foundation and remains a required invariant rather than the principal forward development objective.

**Milestone 3 — Compile Shared Substrate: NEXT.**

Milestone 3 defines and compiles the first deterministic browser-consumable shared Kane County substrate for county boundary/context, roads, and water. New durable package, manifest, database, and protocol identities must distinguish generic Fabric concepts from Kane County-specific source facts. See `docs/MULTI_COUNTY_DESIGN.md`.

## Governing forward objectives

After Milestone 2, new work is evaluated against three continuing objectives:

1. preserve Kane Fabric as authentic, independently usable public infrastructure;
2. maintain current, validated, authoritative county geographic state without bypassing provenance, candidate validation, comparison, reconciliation, promotion, or rollback safeguards;
3. avoid unnecessary Kane County coupling in new reusable namespaces and durable contracts so that a future jurisdiction does not require a redesign of the core.

Kane County remains the sole required operational reference deployment for current work. No second-county stubs or speculative nationwide framework are required.

## Platform model

Kane Fabric separates three roles:

- **County Fabric node** — authoritative control plane and compiler. It owns source acquisition, provenance, validation, reconciliation, promotion, rollback, package compilation, publication, and edge-node synchronization.
- **Browser** — durable user client. It validates, decompresses, renders, pans, zooms, composes substrate plus subscriptions, and provides interaction without requiring a native operating-system application.
- **Edge nodes** — replaceable low-cost HTTP/storage devices. ESP32-S3 is the initial minimum reference implementation, not a permanent architectural dependency.

## Geographic model

A county or county-equivalent jurisdiction is divided into a stable shared substrate and logical subscriptions.

The initial substrate is expected to contain:

- county boundary/context;
- roads;
- water;
- other future stable geographic context as justified.

Subscriptions provide application-specific geographic state. Initial examples include:

- Condo;
- Industry / Mechanical Compiler;
- Retail;
- future domain-specific datasets.

A subscription is a logical dataset, not a physical device. One edge node may carry several subscriptions; one subscription may be sharded or replicated across several nodes.

## Reconstruction and extraction result

Milestone 1 deliberately reconstructed the Kane County pipeline on a clean Debian CT rather than installing the historical promoted database as active state.

Starting inputs included:

- clean conformant Debian CT;
- exact Kane Condo `0.4` software baseline;
- immutable accepted Kane County seed GeoPackage;
- staged source evidence and accepted operational reference artifacts;
- versioned source profiles.

Milestone 2 then extracted those proven geographic behaviors into Kane Fabric ownership and replayed the immutable Milestone 1 evidence through the native core. Kane Condo `0.4` remains a historical regression oracle rather than an operational dependency.

## Repository boundary

Large county databases, harvests, staging artifacts, rollback copies, render packages, and reconstruction evidence remain outside Git.

Git contains the software, county/source contracts, tests, documentation, schemas, and repeatable procedures required to reproduce those external artifacts.

The public-domain status of Kane Fabric software does not automatically determine the legal status of third-party geographic data. External source provenance remains a separate boundary.

See `docs/HANDOFF.md` first for current development state, then `docs/DEVELOPMENT_PROCESS.md`, the project charter, civic infrastructure principles, multi-county design horizon, architecture, reconstruction model, data ownership, infrastructure baseline, milestone release records, current milestone design/handoff, and roadmap.
