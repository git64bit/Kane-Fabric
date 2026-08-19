# Kane Fabric

Kane Fabric is a browser-first distributed geographic substrate and subscription system.

The project begins with Kane County, Illinois, but the architecture is intended to be repeatable across thousands of U.S. counties. A county Fabric node maintains authoritative geographic source state, detects upstream changes, reconstructs and validates county data, compiles browser-consumable packages, and publishes them to replaceable edge-serving devices.

Kane Fabric grew out of Kane Condo 0.4. Kane Condo proved the county-scale browser map, source-profile registry, update detection, candidate harvesting, deterministic comparison, project-identity reconciliation, atomic promotion and rollback, render-package generation, and browser-side rendering model. Kane Condo is frozen at tag `0.4`; Kane Fabric begins from those proven results without remaining condo-specific.

## Project status

**Milestone 1 — Kane County Reconstruction Proof: RELEASED (2026-08-18).**

A clean Kane Fabric CT independently reconstructed the Kane County pipeline from declared inputs through candidate replay, exact deterministic comparison, and project-building reconciliation. The release evidence is recorded in `docs/MILESTONE_1_RELEASE.md`.

The promotion/rollback replay originally planned as Milestone 1 Batch 009 was not executed before that release. It is intentionally carried forward as **Milestone 2 Entry Gate 001** rather than being treated as completed.

**Milestone 2 — Extract Kane Fabric Geographic Core: READY TO START.**

The standalone handoff for the next Assistant is `docs/MILESTONE_2_HANDOFF.md`.

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

## Reconstruction result

Milestone 1 deliberately reconstructed the Kane County pipeline on a clean Debian CT rather than installing the historical promoted database as active state.

Starting inputs included:

- clean conformant Debian CT;
- exact Kane Condo `0.4` software baseline;
- immutable accepted Kane County seed GeoPackage;
- staged source evidence and accepted operational reference artifacts;
- versioned source profiles.

The reconstruction proved that the county node can independently rebuild the required database state, validate and register candidate sources, reproduce historical comparison decisions exactly, and preserve project-building identity through reconciliation without relying on undocumented state left behind on the original orchestrator.

Milestone 2 begins by proving promotion and rollback against that reconstructed state, then extracts the reusable geographic implementation into Kane Fabric ownership.

## Repository boundary

Large county databases, harvests, staging artifacts, rollback copies, render packages, and reconstruction evidence remain outside Git.

Git contains the software, county/source contracts, tests, documentation, schemas, and repeatable procedures required to reproduce those external artifacts.

See `docs/` for the project charter, architecture, reconstruction model, data ownership, infrastructure baseline, release record, Milestone 2 handoff, and roadmap.
