# Kane Fabric

Kane Fabric is public civic infrastructure for maintaining and distributing authoritative county-scale geographic state through a browser-first substrate and subscription system.

The project begins with Kane County, Illinois, but Kane County is the reference deployment rather than the conceptual namespace of the software. New reusable contracts are intended to remain portable across U.S. counties and county-equivalent jurisdictions without building speculative nationwide infrastructure before it is needed.

Kane Fabric is deliberately released under the repository `LICENSE` using The Unlicense/public-domain dedication. Independent use, adaptation, redistribution, commercial use, government use, and continued operation without permission from the original project are intended properties. The project does not condition use on political, religious, commercial, governmental, philosophical, or intellectual-ideological affiliation. See `docs/CIVIC_INFRASTRUCTURE_PRINCIPLES.md`.

Kane Fabric grew out of Kane Condo 0.4. Kane Condo proved the county-scale browser map, source-profile registry, update detection, candidate harvesting, deterministic comparison, project-identity reconciliation, atomic promotion and rollback, render-package generation, and browser-side rendering model. Kane Condo is frozen at tag `0.4`; Kane Fabric begins from those proven results without remaining condo-specific.

## Start here for current development

**New Assistants and developers start with `docs/HANDOFF.md`, then `docs/CURRENT_STATE.json`, `docs/SESSION_START.md`, and `docs/DEVELOPMENT_PROCESS.md`.**

`docs/HANDOFF.md` is the durable system handoff: architecture, database lifecycle, evidence identities, compatibility nuances, and milestone context.

`docs/CURRENT_STATE.json` is the compact machine-readable latest observed checkpoint: current CT checkout path/state, accepted test gates, operational database identity when established, and the exact next safe action.

`docs/SESSION_START.md` defines the low-churn resume path. Stable deployment facts are not rediscovered every session. Use the recorded checkout path first and run:

```bash
bash development/kane-fabric-dev-state.sh
```

inside CT102. Use `--deep` only when database hashes/full validation are actually required.

Do not reconstruct current state from historical milestone handoffs alone. `docs/MILESTONE_1_RELEASE.md` and `docs/MILESTONE_2_RELEASE.md` are release evidence; `docs/MILESTONE_2_HANDOFF.md` is historical; `docs/MILESTONE_3_HANDOFF.md` is milestone-specific.

Accepted CT tests are not rerun merely because a new Assistant arrived. Rerun only after an invalidating implementation/environment change or contradictory live observation. Documentation/state updates are batched at material checkpoints rather than committed after every command group.

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

An Assistant sandbox is not CT102 and cannot substitute for CT102 acceptance. If a session does not expose an authorized execution channel to `srv-b`, that is an execution-capability gap and must be stated explicitly; real-environment gates remain unverified unless the user explicitly accepts a bounded manual relay exception.

Historical milestone handoffs preserve historical procedures but do not override `docs/DEVELOPMENT_PROCESS.md` when their execution instructions conflict with it.

## Project status

**Milestone 1 — Kane County Reconstruction Proof: RELEASED (2026-08-18).**

A clean Kane Fabric CT independently reconstructed the Kane County pipeline from declared inputs through candidate replay, exact deterministic comparison, and project-building reconciliation. The release evidence is recorded in `docs/MILESTONE_1_RELEASE.md`.

**Milestone 2 — Extract Kane Fabric Geographic Core: RELEASED (2026-08-20).**

Kane Fabric now owns the geographic database migrations and implementation, source contracts, seed/bootstrap import, provenance, storage, durable geographic building identity, candidate engines, deterministic comparison, reconciliation, and atomic promotion/rollback. The geographic core operates without Kane Condo classification tables and without the frozen Kane Condo checkout as a runtime dependency.

The decisive historical closeout replay reproduced all Milestone 1 comparison hashes, reconciled all 208,324 building identities with zero ambiguities, promoted and rolled back the five-dataset refresh, and left the immutable seed and historical promoted oracle unchanged. The release evidence is recorded in `docs/MILESTONE_2_RELEASE.md`.

Reconstructability is therefore a proven foundation and remains a required invariant rather than the principal forward development objective.

**Milestone 3 — Compile Shared Substrate: IN PROGRESS.**

The v1 substrate wire contract and deterministic jurisdiction-overview implementation are present. CT102 has now accepted the current database regression suite (16/16) and substrate regression suite (19/19) at the recorded checkpoint in `docs/CURRENT_STATE.json`. The remaining first real-data gate is to identify the live accepted/working Kane County database, compile the overview from it, validate jurisdiction/release identity, and prove the source database is byte-unchanged.

Road/water LOD components, manifest/package activation, browser loading/rendering, and edge-compatibility proof remain ahead. See `docs/CURRENT_STATE.json` and `docs/MILESTONE_3_HANDOFF.md` for the exact boundary.

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

See `docs/HANDOFF.md` for the durable system context, `docs/CURRENT_STATE.json` for the latest operational checkpoint, `docs/SESSION_START.md` for the fast resume path, and `docs/DEVELOPMENT_PROCESS.md` for execution rules. Then read the current milestone design/handoff and roadmap as needed.
