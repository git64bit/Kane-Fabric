# Kane Fabric

Kane Fabric is a browser-first distributed geographic substrate and subscription system.

The project begins with Kane County, Illinois, but the architecture is intended to be repeatable across thousands of U.S. counties. A county Fabric node maintains authoritative geographic source state, detects upstream changes, reconstructs and validates county data, compiles browser-consumable packages, and publishes them to replaceable edge-serving devices.

Kane Fabric grew out of Kane Condo 0.4. Kane Condo proved the county-scale browser map, source-profile registry, update detection, candidate harvesting, deterministic comparison, project-identity reconciliation, atomic promotion and rollback, render-package generation, and browser-side rendering model. Kane Condo is frozen at tag `0.4`; Kane Fabric begins from those proven results without remaining condo-specific.

## Project status

**Milestone 1 — Kane County Reconstruction Proof: RELEASED (2026-08-18).**

A clean Kane Fabric CT independently reconstructed the Kane County pipeline from declared inputs through candidate replay, exact deterministic comparison, and project-building reconciliation. The release evidence is recorded in `docs/MILESTONE_1_RELEASE.md`.

**Milestone 2 — Extract Kane Fabric Geographic Core: RELEASED (2026-08-20).**

Kane Fabric now owns the geographic database migrations and implementation, source contracts, seed/bootstrap import, provenance, storage, durable geographic building identity, candidate engines, deterministic comparison, reconciliation, and atomic promotion/rollback. The geographic core operates without Kane Condo classification tables and without the frozen Kane Condo checkout as a runtime dependency.

The decisive historical closeout replay reproduced all Milestone 1 comparison hashes, reconciled all 208,324 building identities with zero ambiguities, promoted and rolled back the five-dataset refresh, and left the immutable seed and historical promoted oracle unchanged. The release evidence is recorded in `docs/MILESTONE_2_RELEASE.md`.

**Milestone 3 — Compile Shared Substrate: NEXT.**

Milestone 3 defines and compiles the first deterministic browser-consumable shared Kane County substrate for county boundary/context, roads, and water.

## Platform model

Kane Fabric separates three roles:

- **County Fabric node** — authoritative control plane and compiler. It owns source acquisition, provenance, validation, reconciliation, promotion, rollback, package compilation, publication, and edge-node synchronization.
- **Browser** — durable user client. It validates, decompresses, renders, pans, zooms, composes substrate plus subscriptions, and provides interaction without requiring a native operating-system application.
- **Edge nodes** — replaceable low-cost HTTP/storage devices. ESP32-S3 is the initial minimum reference implementation, not a permanent architectural dependency.

## Geographic model

A county is divided into a stable shared substrate and logical subscriptions.

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

See `docs/` for the project charter, architecture, reconstruction model, data ownership, infrastructure baseline, Milestone 1 and Milestone 2 release records, historical handoff, and roadmap.
