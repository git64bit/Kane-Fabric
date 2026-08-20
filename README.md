# Kane Fabric

Kane Fabric is public civic infrastructure for maintaining and distributing authoritative county-scale geographic state through a browser-first **substrate + subscriptions** system.

Kane County, Illinois is the reference deployment rather than the conceptual namespace of the software. Reusable contracts are intended to remain portable across U.S. counties and county-equivalent jurisdictions without building speculative nationwide infrastructure before it is needed.

Kane Fabric is deliberately released under the repository `LICENSE` using The Unlicense/public-domain dedication. Independent use, adaptation, redistribution, commercial use, government use, and continued operation without permission from the original project are intended properties. The project does not condition use on political, religious, commercial, governmental, philosophical, or intellectual-ideological affiliation. See `docs/CIVIC_INFRASTRUCTURE_PRINCIPLES.md`.

Kane Fabric grew out of Kane Condo 0.4. Kane Condo proved the county-scale browser map, source-profile registry, update detection, candidate harvesting, deterministic comparison, project-identity reconciliation, atomic promotion and rollback, render-package generation, and browser-side rendering model. Kane Condo is frozen at tag `0.4`; Kane Fabric begins from those proven results without remaining condo-specific.

## Start here for current development

**New Assistants and developers start with `docs/HANDOFF.md`, then `docs/CURRENT_STATE.json`, `docs/SESSION_START.md`, and `docs/DEVELOPMENT_PROCESS.md`.**

Current milestone design:

```text
docs/MILESTONE_4_DESIGN.md
```

`docs/HANDOFF.md` is the durable system handoff. `docs/CURRENT_STATE.json` is the compact machine-readable latest observed checkpoint. `docs/SESSION_START.md` defines the low-churn resume path. Stable deployment facts are not rediscovered every session.

Inside CT102, use the recorded checkout path and run:

```bash
bash development/kane-fabric-dev-state.sh
```

Use `--deep` only when database hashes/full validation are actually required.

Historical milestone release records are evidence, not current implementation instructions. Milestone 3 is closed; do not restart MS-3 discovery or implementation unless a concrete regression invalidates its accepted evidence.

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

An Assistant sandbox is not CT102 and cannot substitute for CT102 acceptance.

## Project status

**Milestone 1 — Kane County Reconstruction Proof: RELEASED (2026-08-18).**

A clean Kane Fabric CT independently reconstructed the Kane County pipeline from declared inputs through candidate replay, exact deterministic comparison, and project-building reconciliation. See `docs/MILESTONE_1_RELEASE.md`.

**Milestone 2 — Extract Kane Fabric Geographic Core: RELEASED (2026-08-20).**

Kane Fabric owns the geographic database migrations and implementation, source contracts, seed/bootstrap import, provenance, storage, durable geographic building identity, candidate engines, deterministic comparison, reconciliation, and atomic promotion/rollback. The geographic core operates without Kane Condo classification tables and without the frozen Kane Condo checkout as a runtime dependency. See `docs/MILESTONE_2_RELEASE.md`.

**Milestone 3 — Compile Shared Substrate: RELEASED (2026-08-20).**

Milestone 3 established the deterministic four-file public baseline geography publication:

```text
county-overview.json
roads-lod.kfs
water-lod.kfs
substrate-manifest.json
```

The accepted Kane County substrate is independently browser-consumable, byte-identifiable, selectively readable through indexed byte ranges, decompressible/renderable in a real browser, and compatible with bounded edge-serving access patterns. The authoritative GeoPackage remained unchanged through the accepted build and browser proofs. See `docs/MILESTONE_3_RELEASE.md`.

**Milestone 4 — Subscriptions + Geographic Scoping/Partition Identity: IN PROGRESS.**

Milestone 4 defines how application subscriptions are layered on the public substrate and how substrate/subscription content can be addressed through deterministic logical geographic partitions.

The partition model is intentionally broader than towns or townships. Supported scopes are expected to include whole-jurisdiction, municipality, township/equivalent administrative subdivision, explicit bounded region, and deterministic composite scopes where justified.

A partition is a logical distribution/composition identity, not a physical edge device and not a second geographic authority. Administrative boundaries are convenient named scopes; roads, water, buildings, and application data may cross them without changing feature identity.

The intended progression is:

```text
MS-3  county substrate + selective chunks       COMPLETE
  ↓
MS-4  subscriptions + geographic partitions     CURRENT
  ↓
MS-5  ESP32-S3 placement/storage/HTTP serving   DEFERRED
```

See `docs/MILESTONE_4_DESIGN.md`.

## Platform model

Kane Fabric separates three long-lived roles:

- **County Fabric node** — authoritative control plane and compiler. It owns source acquisition, provenance, validation, reconciliation, promotion, rollback, package compilation, publication, and edge synchronization.
- **Browser** — durable user client. It validates, fetches, decompresses, renders, pans, zooms, and composes substrate plus subscriptions.
- **Edge nodes** — replaceable low-cost HTTP/storage devices. ESP32-S3 is the initial minimum reference implementation, not a permanent architectural dependency.

Physical edge placement is deliberately separated from logical data identity. A subscription or geographic partition may fit on one node, share a node with others, span several nodes, or be replicated without changing its logical identity.

## Geographic model

Kane Fabric distinguishes three layers:

### Authoritative geography

The county Fabric node maintains accepted geographic state through explicit provenance, candidate validation, comparison, reconciliation where required, and promotion. Source freshness, candidate registration, comparison, compilation, and partition selection do not silently change accepted authority.

### Shared substrate

The public substrate contains geographic context useful to many applications. The Milestone 3 v1 baseline contains:

- county boundary/context;
- roads;
- water.

The county-wide publication remains canonical. Milestone 4 partitioning selects/references relevant substrate chunks and context rather than creating independent town databases or new geographic authorities.

### Subscriptions and partitions

Subscriptions provide application-specific geographic state. Initial proof paths are:

- Condo;
- Industry / Mechanical Compiler.

A subscription is a logical dataset with its own generation and ownership boundary. It may reference Kane Fabric geographic identities without acquiring ownership of the public substrate.

A geographic partition is a deterministic jurisdiction-scoped area used for selection, composition, storage planning, replication, and serving. Examples include a municipality, township, explicit bounded region, or whole county.

A road, water feature, building identity, or subscription object crossing a partition boundary retains one logical identity. Partition boundaries are distribution boundaries, not semantic ownership boundaries.

## Edge direction

ESP32-S3 + ESP-IDF remains the Milestone 5 reference edge implementation.

Milestone 4 is hardware-aware but firmware-independent: its partition and subscription contracts must make it practical for constrained devices to carry focused subsets, but it does not define ESP-IDF HTTP handlers, storage APIs, flash/SD layouts, Wi-Fi behavior, or firmware updates.

A future arrangement may therefore look like:

```text
edge A  Aurora-area substrate + Industry subscription
edge B  Elgin-area substrate + Condo subscription
edge C  township-focused context + several small subscriptions
```

Those placements do not become part of partition or subscription identity.

## Governing forward objectives

New work is evaluated against continuing objectives:

1. preserve Kane Fabric as authentic, independently usable public civic infrastructure;
2. maintain current, validated, authoritative county geographic state without bypassing provenance, candidate validation, comparison, reconciliation, promotion, or rollback safeguards;
3. keep the compiled publication—not the internal GeoPackage schema—as the durable external geographic interface;
4. keep subscriptions independent of shared-substrate ownership;
5. keep geographic partition identity independent of physical edge hardware;
6. avoid unnecessary Kane County coupling in reusable namespaces and durable contracts.

Kane County remains the sole required operational reference deployment for current work. No speculative nationwide framework or fake second-county implementation is required.

## Dependency and licensing boundary

Kane Fabric-authored code remains under the root Unlicense.

Third-party implementations retained by the final project must be explicitly reviewed, pinned, and vendored according to `docs/DEPENDENCY_POLICY.md`. Platform contracts such as standard browser APIs are not treated as bundled project implementations merely because Kane Fabric depends on those interfaces.

Node.js and Chromium were used as development-only acceptance runtimes during Milestone 3 and are not dependencies of the public substrate or future edge nodes.

ESP-IDF remains a future project-controlled firmware SDK/toolchain and must be pinned/licensed/vendored before Kane Fabric firmware release if retained.

## Repository boundary

Large county databases, harvests, staging artifacts, rollback copies, render/substrate packages, and reconstruction evidence remain outside Git.

Git contains software, county/source contracts, tests, documentation, schemas, deterministic small manifests, and repeatable procedures required to reproduce those external artifacts.

The public-domain status of Kane Fabric software does not automatically determine the legal status of third-party geographic data. External source provenance remains a separate boundary.

See `docs/HANDOFF.md` for durable system context, `docs/CURRENT_STATE.json` for the latest operational checkpoint, `docs/ROADMAP.md` for milestone sequencing, `docs/MILESTONE_4_DESIGN.md` for the current milestone contract, and `docs/ESP32_EDGE_REFERENCE.md` for the deferred Milestone 5 edge implementation boundary.
