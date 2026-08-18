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

Purpose: prove that the county pipeline can be reproduced from declared inputs rather than copied from hidden orchestrator state.

### Batch 001 — Environment acceptance

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

Known accepted host result on 2026-08-18: CT100, CT101 and CT102 conform with `62 passed, 0 failed, 3 informational`.

### Batch 002 — Reconstruction evidence contract

Record the immutable Kane County seed, historical reference database, staged candidate evidence, and their SHA-256 identities outside Git.

Acceptance: evidence is distinguishable from active Fabric state and can be verified before use.

### Batch 003 — Historical software reproducibility

Run the exact Kane Condo `0.4` database test suite on the clean Kane Fabric CT.

Known initial result: 374 tests pass on the reconstructed environment.

Acceptance: exact historical baseline is reproducible and the checkout remains clean.

### Batch 004 — Read-only reference validation

Use the reconstructed 0.4 toolchain to:

- validate the known-good promoted database;
- inspect its database state;
- validate source profiles;
- perform live lightweight source-status checks;
- prove the reference database hash is unchanged.

Acceptance: current Kane County endpoints can be evaluated from the new CT without mutating accepted evidence.

### Batch 005 — Fresh working database reconstruction

Create a new working database from the immutable accepted seed and declared migrations/import contracts.

Do not install the final Kane Condo database as active Fabric state.

Acceptance: the reconstructed database represents the expected accepted starting county state and passes database validation.

### Batch 006 — Candidate replay

Using the staged Kane reconstruction evidence, replay:

- boundary candidate validation/registration;
- building candidate validation/registration;
- road candidate validation/registration;
- coordinated water candidate validation/registration.

Acceptance: staged evidence validates independently on the new node and accepted state is unchanged merely by registration.

### Batch 007 — Deterministic comparison replay

Reproduce accepted-versus-candidate comparison results.

Acceptance: semantic comparison outputs agree with the historical reference audit for all source groups.

### Batch 008 — Geographic identity reconciliation replay

Reconstruct the building project-identity reconciliation on an external candidate database.

Acceptance: stable identities and historical application-relevant mappings are preserved according to the donor contract, with no unexplained ambiguity.

### Batch 009 — Promotion and rollback replay

Prepare, validate, and atomically promote the reconstructed county state; prove rollback behavior.

Acceptance:

- failed/interrupted promotion cannot destroy accepted state;
- reconstructed promoted state is semantically equivalent to the historical 0.4 reference;
- rollback restores the prior accepted release set.

Milestone 1 exit gate: Kane County's complete authoritative database refresh pipeline has been reproduced on CT102 from declared inputs.

## Milestone 2 — Extract Kane Fabric geographic core

Purpose: separate reusable county geography from Kane Condo application semantics.

Work includes:

- rename/generalize county data concepts;
- separate stable geographic identity from Condo-specific project identity where necessary;
- define generic source/county profiles;
- retain proven provenance, candidate, comparison, promotion, and rollback behavior;
- preserve deterministic tests;
- create Kane Fabric-owned database migrations and command entry points.

Exit gate: Kane Fabric can build/refresh Kane County without depending on Kane Condo names or classification semantics.

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