# Milestone 2 Handoff — Extract Kane Fabric Geographic Core

This document is the starting context for the Assistant taking over Milestone 2.

Read this file first, then read:

1. `docs/MILESTONE_1_RELEASE.md`
2. `docs/ROADMAP.md`
3. `docs/PROJECT_CHARTER.md`
4. `docs/ARCHITECTURE.md`
5. `docs/COUNTY_NODE_RECONSTRUCTION.md`
6. `docs/DATA_OWNERSHIP.md`
7. `docs/INFRASTRUCTURE_BASELINE.md`

Do not restart Kane Condo development. Kane Condo is frozen at tag `0.4` and is historical source/evidence for Kane Fabric extraction.

## Mission

Milestone 2 separates reusable county-geography behavior from Kane Condo application semantics while preserving the reconstruction properties proven in Milestone 1.

The milestone must end with Kane Fabric-owned database migrations, command entry points, source/county contracts, and deterministic tests that can build and refresh Kane County without depending on Condo-specific names or classification semantics.

Before extraction can alter authoritative database behavior, the carried promotion/rollback replay must pass.

## Entry Gate 001 — promotion and rollback replay

This is the original Milestone 1 Batch 009, moved explicitly into Milestone 2 at the Milestone 1 release boundary because it had not yet been executed on CT102.

Do not claim it has passed.

Required proof:

- prepare promotion from the newly reconstructed reconciliation artifact;
- validate the promotion candidate;
- atomically activate the reconstructed county state;
- prove failure/interruption cannot destroy the previously accepted state;
- prove rollback restores the prior accepted release set;
- compare the promoted reconstructed state semantically with the immutable Kane Condo 0.4 promoted reference;
- preserve all historical reconstruction evidence read-only.

Only after this gate passes should extraction modify the database implementation.

## Current CT102 state

Host: `srv-b`

Container:

```text
VMID      102
hostname  kane-fabric
OS        Debian 12
CPU       4 vCPU
RAM       6144 MB
swap      2048 MB
root      20G
state     /var/lib/kane-fabric on separate 20G mount
network   10.20.0.12/24 on vmbr1, gateway 10.20.0.1
onboot    yes
LXC       unprivileged
features  nesting=1,keyctl=1 currently configured
```

Accepted host baseline on 2026-08-18:

```text
62 passed, 0 failed, 3 informational
```

Host conformance is owned by `srv-b` and its `ct-baseline.sh`. Kane Fabric must not create a competing host standard.

## Current active working database

This is the reconstructed, still-unpromoted database containing one accepted and one candidate release for all five datasets:

```text
/var/lib/kane-fabric/database/kane-county-reconstructed.gpkg

size
355217408 bytes

SHA256
ff67edcb0a732d87f3dc3bb3cf7fda91a03fea4ef8e16fb527f88283894c0a97
```

Treat this hash as the Milestone 1 handoff identity unless a deliberate Milestone 2 operation changes it.

## Immutable donor seed

```text
/var/lib/kane-fabric/seed/kane-county.gpkg

size
324886528 bytes

SHA256
7fe2198b00b2d0dee9470eda3864b43b6f7b3b0ff3b236ce7c579ddc077f389a
```

The seed is evidence. Do not modify it.

## Historical reconstruction evidence

Root:

```text
/var/lib/kane-fabric/reconstruction-inputs/kane-condo-data
```

The tree is frozen read-only.

Historical promoted reference:

```text
reconstruction-inputs/kane-condo-data/database/kane-condo.gpkg
size    649027584 bytes
SHA256  164200d4d7262874dcc03239c8258446a4d7bb81ce84daf46dc4937d6c97fe86
```

This reference is an oracle, not active Fabric state.

## Historical software baseline

Checkout:

```text
/var/lib/kane-fabric/reconstruction-code/kane-condo-0.4
```

Identity:

```text
tag     0.4
commit  63582fb05c509d53870835d25612c87b56800d10
```

Milestone 1 result:

```text
374 tests passed
checkout clean
```

Do not edit this checkout while it is serving as historical reconstruction evidence. New Kane Fabric implementation belongs in Kane Fabric-owned source paths/repository work.

## Source profile registry

Milestone 1 validated five historical profiles with registry SHA:

```text
e95c9d0486f65035146cb0a2a9580e4148c853a78c4f9e44e2420f59ef654e12
```

Datasets:

- county-boundary;
- buildings;
- roads;
- water-creeks;
- water-fox-river.

All five reported `Up to date` from CT102 during Milestone 1.

Roads preserve one deliberate exclusion:

```text
source object inventory  27676
retained features         27675
excluded source objects       1
```

The exclusion is contract behavior, not corruption.

## Candidate replay state

The active working database has one accepted and one candidate release for each of the five datasets.

Candidate evidence directories:

```text
buildings
/var/lib/kane-fabric/reconstruction-inputs/kane-condo-data/staging/buildings/kane-buildings-candidate-20250730-608ac1b48564

roads
/var/lib/kane-fabric/reconstruction-inputs/kane-condo-data/staging/roads/kane-roads-candidate-20250730-c83a588170f3

water
/var/lib/kane-fabric/reconstruction-inputs/kane-condo-data/staging/water/kane-water-context-candidate-20250717-25d02c084002

boundary
/var/lib/kane-fabric/reconstruction-inputs/kane-condo-data/staging/boundary/kane-county-boundary-candidate-20230509-ecc3b0990d4c
```

Registration changed provenance only; accepted geography remained unchanged.

## Deterministic comparison oracle

Fresh CT102 comparison runs repeated byte-for-byte and matched historical Batch 022 exactly.

```text
buildings
23916019e762740a4ebe773cdfab916ace4c4d505521407fd6c513b382108d28

boundary
6ffa83d940347e7ffeeb10e3c631625af75de7f12ef95729ab1ebb75b5879f95

roads
7b3bf1ddaef1a40948d57edf0c465199316216510e0a1a78cb2dc0a552f59d3b

water
a1b0ac3f1504e4e6de199e694f794c83643f02139ed37f9a38c0d65d638f88f3
```

All retained geographic features were unchanged between accepted and candidate releases.

## Reconciliation artifact to promote

Milestone 1 created this new reconciliation artifact from the reconstructed CT102 database:

```text
/var/lib/kane-fabric/staging/reconciliation/kane-buildings-reconciliation-20250730-2bfb38f11c7d
```

Candidate database:

```text
SHA256
9e59c2ad2bd6d6962894faebd98ffc31620b48f711b091f0c376e2707c488ae9
```

Reconciliation report:

```text
SHA256
1d81b3287cee5c0ed47f6aa5092d8dee2b7aab382095749494f630f601a06a62
```

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

Project state before and after reconciliation is identical. Classification current/history snapshots are identical.

## Milestone 2 extraction boundary

After Entry Gate 001, extract the Kane Fabric geographic core without collapsing application ownership boundaries.

Kane Fabric owns geographic state:

- county/source profiles;
- source acquisition;
- provenance;
- candidate lifecycle;
- comparison;
- geographic identity where generic;
- reconciliation mechanisms required to preserve geographic references;
- promotion and rollback;
- later substrate compilation/publication.

Kane Fabric does not silently become the Mechanical Compiler application database or a generic owner of application classifications.

Mechanical Compiler is a future Industry subscription/use case. No interface between the projects is currently assumed merely because both run on `srv-b`.

## Likely extraction order

After Entry Gate 001:

1. inventory Kane Condo 0.4 database modules and classify each concept as geographic core, application-specific, or transitional compatibility;
2. define Kane Fabric package/module naming without changing behavior;
3. define generic county/source profile schema;
4. create Kane Fabric-owned migrations reproducing the geographic/provenance state model;
5. port candidate validation/registration;
6. port deterministic comparison;
7. port promotion/rollback;
8. isolate project-building/classification semantics behind an application-facing reference boundary instead of baking Condo into the geographic core;
9. reproduce Milestone 1 deterministic tests against Kane Fabric entry points;
10. only then retire dependence on the historical Kane Condo checkout for normal operation.

Prefer behavior-preserving extraction over redesign. Milestone 1 artifacts are the regression oracle.

## Operational discipline

The user performs infrastructure commands on `srv-b` and returns output.

Work one controlled step at a time. Do not automate a path before the manual baseline works.

### Shell safety

Never issue unwrapped strict mode into the interactive root shell.

Safe form:

```bash
(
  set -euo pipefail
  ...
)
```

Historical project scripts may contain their own `set -euo pipefail`; that is acceptable because they run in their own noninteractive shell.

### File transfer

Do not prescribe SCP/SSH-based cross-machine artifact transfer unless the user explicitly requests it.

For large cross-machine artifacts the established workflow is:

```text
create tarball
→ download with Webmin
→ upload with Webmin
→ verify locally by SHA-256
```

`git clone` over HTTPS is fine.

### Host/platform boundaries

Do not repurpose Mechanical Compiler CT100 or CT101.

Do not duplicate `srv-b`'s `ct-baseline.sh` into Kane Fabric.

`nesting=1` is a proven shared requirement for Debian 12 unprivileged CTs on this host.

`keyctl=1` is not a universal platform requirement; retain it only when the workload justifies it.

Containers do not send mail. SMTP egress is blocked at the host.

## Milestone 2 completion condition

Milestone 2 is complete when:

- Entry Gate 001 promotion/rollback replay has passed;
- Kane Fabric owns its geographic database implementation and migrations;
- Kane County can be initialized/refreshed through Kane Fabric names and entry points;
- provenance, candidate, comparison, promotion and rollback behavior remains deterministic;
- application classifications are not required to operate the geographic core;
- historical Kane Condo 0.4 remains a regression reference rather than a runtime dependency.
