# Kane Fabric Roadmap

## Milestone 0 — Fix the platform contract

Purpose: establish the architectural boundary before Kane Condo implementation code is adapted.

Initial deliverables:

- project charter;
- architecture;
- data ownership contract;
- county-node reconstruction contract;
- infrastructure baseline;
- roadmap.

Exit gate:

- browser-first client boundary is explicit;
- county Fabric node is authoritative control plane/compiler;
- edge nodes are replaceable distribution resources;
- substrate/subscription model is explicit;
- Mechanical Compiler/application ownership boundary is explicit;
- large operational geographic data remains outside Git.

## Milestone 1 — Reconstruct Kane County on a clean Fabric node

**Status: RELEASED — 2026-08-18**

Release record: `docs/MILESTONE_1_RELEASE.md`

Purpose: prove that the county pipeline can be reproduced from declared inputs rather than copied from hidden orchestrator state.

Milestone 1 was released after clean-node reconstruction through deterministic project-building reconciliation. The promotion/rollback replay originally listed as Batch 009 was not executed before release and is carried forward explicitly as Milestone 2 Entry Gate 001. This scope amendment preserves the unperformed proof rather than claiming it passed.

### Batch 001 — Environment acceptance — COMPLETE

Record and verify two separate layers:

**Host-level conformance**, owned by `srv-b` and asserted by its executable `ct-baseline.sh` check:

- autostart and unprivileged LXC state;
- required LXC features;
- single service-bridge interface and LAN isolation;
- Debian 12;
- generated locale;
- timezone;
- required host-standard tools and admin access;
- no container mail agent and effective SMTP egress block;
- systemd health;
- applicable host firewall and monitoring requirements.

**Kane Fabric-specific environment requirements**:

- data storage and layout;
- Python;
- SQLite runtime and CLI;
- Git;
- reconstruction evidence locations;
- project-specific test gates.

Acceptance: the host-level baseline exits zero for CT102 and all Kane Fabric-specific environment checks pass. Kane Fabric must not maintain a competing definition of host conformance.

Accepted host result on 2026-08-18: CT100, CT101 and CT102 conform with `62 passed, 0 failed, 3 informational`.

### Batch 002 — Reconstruction evidence contract — COMPLETE

Record the immutable Kane County seed, historical reference database, staged candidate evidence, and their SHA-256 identities outside Git.

Acceptance: evidence is distinguishable from active Fabric state and can be verified before use.

### Batch 003 — Historical software reproducibility — COMPLETE

Run the exact Kane Condo `0.4` database test suite on the clean Kane Fabric CT.

Accepted result: 374 tests pass on the reconstructed environment; the historical checkout remains clean.

### Batch 004 — Read-only reference validation — COMPLETE

Use the reconstructed 0.4 toolchain to:

- validate the known-good promoted database;
- inspect its database state;
- validate source profiles;
- perform live lightweight source-status checks;
- prove the reference database hash is unchanged.

Accepted result: all five official source profiles reported `Up to date`; the 649027584-byte historical promoted reference remained at SHA-256 `164200d4d7262874dcc03239c8258446a4d7bb81ce84daf46dc4937d6c97fe86`.

### Batch 005 — Fresh working database reconstruction — COMPLETE

Create a new working database from the immutable accepted seed and declared migrations/import contracts.

Do not install the final Kane Condo database as active Fabric state.

Accepted result: a fresh working database was reconstructed from the immutable donor and passed semantic comparison with the historical seed-import contract.

### Batch 006 — Candidate replay — COMPLETE

Using the staged Kane reconstruction evidence, replay:

- building candidate validation/registration;
- road candidate validation/registration;
- coordinated water candidate validation/registration;
- county boundary candidate validation/registration.

Accepted result: one accepted and one candidate release exist for each of the five datasets. Registration did not promote accepted geography.

Active working database at the end of Batch 006:

```text
/var/lib/kane-fabric/database/kane-county-reconstructed.gpkg
size    355217408 bytes
SHA256  ff67edcb0a732d87f3dc3bb3cf7fda91a03fea4ef8e16fb527f88283894c0a97
```

### Batch 007 — Deterministic comparison replay — COMPLETE

Reproduce accepted-versus-candidate comparison results.

Accepted result: two fresh CT102 comparison runs were byte-for-byte repeatable and matched historical Batch 022 comparison artifacts exactly for buildings, boundary, roads, and coordinated water. The active database remained byte-identical throughout comparison.

### Batch 008 — Geographic identity reconciliation replay — COMPLETE

Reconstruct the building project-identity reconciliation on an external candidate database.

Accepted result:

```text
ready_for_promotion       true
ambiguity_count           0
mapped_source_count       208324
unmapped_source_count     0
continuation mappings     208324
replacement mappings      0
additions                 0
disappearances            0
new project buildings     0
classification changes    0
```

Reconciliation artifact:

```text
/var/lib/kane-fabric/staging/reconciliation/kane-buildings-reconciliation-20250730-2bfb38f11c7d
candidate DB SHA256  9e59c2ad2bd6d6962894faebd98ffc31620b48f711b091f0c376e2707c488ae9
reconciliation SHA256 1d81b3287cee5c0ed47f6aa5092d8dee2b7aab382095749494f630f601a06a62
```

### Original Batch 009 — Promotion and rollback replay — CARRIED TO MILESTONE 2

This proof was part of the original Milestone 1 plan but was not executed before the Milestone 1 release.

It is now Milestone 2 Entry Gate 001 and remains mandatory before extraction changes authoritative database behavior.

Milestone 1 exit statement: Kane County's authoritative database pipeline has been independently reconstructed from declared inputs through deterministic comparison and project-identity reconciliation on CT102. Promotion/rollback replay remains explicitly pending as the next milestone's entry gate.

## Milestone 2 — Extract Kane Fabric geographic core

**Status: READY TO START**

Handoff: `docs/MILESTONE_2_HANDOFF.md`

Purpose: first close the carried promotion/rollback proof, then separate reusable county geography from Kane Condo application semantics.

### Entry Gate 001 — Promotion and rollback replay

Carry forward the original Milestone 1 Batch 009 against the newly reconstructed reconciliation artifact.

Acceptance:

- prepare and validate promotion from the reconstructed reconciliation candidate;
- atomically promote the reconstructed county state;
- failed/interrupted promotion cannot destroy accepted state;
- reconstructed promoted state is semantically equivalent to the historical 0.4 reference;
- rollback restores the prior accepted release set;
- immutable reconstruction evidence remains unchanged.

Do not begin behavior-changing geographic-core extraction until this gate passes.

### Core extraction work

Work includes:

- rename/generalize county data concepts;
- separate stable geographic identity from Condo-specific project identity where necessary;
- define generic source/county profiles;
- retain proven provenance, candidate, comparison, promotion, and rollback behavior;
- preserve deterministic tests;
- create Kane Fabric-owned database migrations and command entry points.

Exit gate: Kane Fabric can build/refresh Kane County without depending on Kane Condo names or classification semantics, and promotion/rollback behavior remains proven under Kane Fabric ownership.

## Milestone 3 — Compile shared substrate

Purpose: produce the first Kane Fabric shared geographic distribution.

Initial substrate:

- county boundary/context;
- roads;
- water.

Work includes:

- define deterministic substrate package format;
- define LOD strategy;
- define package identity/hash rules;
- compile Kane County substrate;
- validate browser-side loading, decompression, and rendering.

Exit gate: a browser can open Kane County and navigate the shared substrate independently of any one application subscription.

## Milestone 4 — Subscription contract

Purpose: define how applications add domain-specific geographic data without owning the substrate.

Initial subscriptions:

- Condo as historical proof/application extraction;
- Industry as the Mechanical Compiler integration path.

Work includes:

- subscription manifest contract;
- geographic identity references;
- independent generations;
- composition with substrate;
- application ownership boundaries;
- filtering/visibility semantics.

Exit gate: one browser session can compose the Kane substrate with at least two independently defined logical subscriptions.

## Milestone 5 — Edge serving contract

Purpose: move compiled geographic distribution onto replaceable low-cost edge hardware.

Initial reference implementation: ESP32-S3-class device.

Work includes:

- HTTP serving contract;
- storage layout;
- manifest/object verification;
- package activation;
- local browser access;
- AP/STA deployment experiments;
- optional upstream synchronization transport;
- node replacement/recovery.

Exit gate: the browser can consume the last activated Kane substrate/subscription generation from edge hardware while the county Fabric CT is unavailable.

## Milestone 6 — Multi-node distribution

Purpose: prove that logical datasets are independent of individual edge devices.

Experiments:

- multiple subscriptions on one node;
- one subscription sharded across nodes;
- replication of critical objects;
- coordinator/proxy versus direct multi-origin browser fetching;
- CORS/CSP implications;
- node discovery and replacement.

Exit gate: loss or replacement of one physical edge node does not force a change to logical subscription identity or browser application semantics.

## Milestone 7 — Generic county bootstrap

Purpose: turn Kane County lessons into a repeatable county deployment model.

Work includes:

- separate county-specific profile/data from generic Fabric software;
- declare required initial source contracts;
- codify infrastructure bootstrap while allowing each deployment host to own its own executable conformance standard;
- automate only after manual reconstruction is proven;
- produce deterministic acceptance reports;
- test a second county without changing core architecture.

Target model:

```text
conformant supported CT
+ Kane Fabric software
+ county/source profile
+ accepted seed or initial harvest
= reproducible county Fabric node
```

Exit gate: a second county can be brought online primarily through configuration/profile work rather than a forked implementation.
