# Milestone 3 Handoff — Compile Shared Substrate

## Status

Current milestone-specific handoff for Milestone 3.

**This file is not a standalone project handoff. A new Assistant must read `docs/HANDOFF.md` first.** That stable handoff contains the repository map, database lifecycle, evidence identities, compatibility nuances, execution model, branch/refspec incident history, testing discipline, and the exact distinction between historical state and current observations.

Then read `docs/DEVELOPMENT_PROCESS.md`. It is authoritative for repository, host, CT, and operational execution boundaries.

Do not use the historical Milestone 2 sentence that the user performs infrastructure commands as an unconditional current operating rule. During MS-1/MS-2 the user did explicitly execute bounded command groups and return output; that is historical fact. Current normal execution, when the capability exists, is Assistant/development access through `srv-b` → `pct exec 102`. If the capability is not exposed in a session, say so and do not fabricate CT102 acceptance.

## Current repository authority

Repository:

```text
git64bit/Kane-Fabric
```

Branch policy:

```text
main
```

Work directly on `main` unless the user explicitly requests another branch/PR workflow.

The MS-2 feature-branch/single-refspec cleanup incident is documented in `docs/HANDOFF.md` and the historical `docs/MILESTONE_2_HANDOFF.md`. Do not recreate it.

Before substantive work, read live `main`. Do not rely on an embedded SHA if the repository has advanced.

The repository snapshot at the start of the handoff repair was:

```text
0c2c5bb636d56da4afc130d05d86fdd0a9ff7092
```

Subsequent handoff/documentation commits moved `main`; this SHA is context, not a current authority token.

## Known CT102 checkout state versus repository state

The last explicitly observed CT102 cleanup state before later Milestone 3 GitHub work was:

```text
branch        main
HEAD          9440c31283a000f0b3ce30e57035446ad45c7ce3
upstream      origin/main
remote refs   origin/main only
working tree  clean
```

After that observation, `main` advanced through GitHub with development-process, civic-infrastructure, multi-county, substrate-format, overview, and handoff work.

Therefore **do not assume CT102 has the current Milestone 3 repository state**. On first live access, discover the actual checkout and synchronize/verify it deliberately. The old MS-2 path `/tmp/kane-fabric-ms2` existed during the cleanup but is not a permanent path contract.

## Execution authority

Reference deployment:

```text
Proxmox host    srv-b
Fabric CT       102
hostname        kane-fabric
```

Normal host-to-CT execution:

```bash
pct status 102
pct exec 102 -- COMMAND ARGUMENTS...
pct exec 102 -- bash -lc '...'
```

Run Proxmox/LXC and host conformance operations on `srv-b`.

Run Kane Fabric tests, tools, database inspection, source work, and substrate compilation inside CT102 through `pct exec`.

Do not substitute an Assistant sandbox for CT102 acceptance.

CT102 is not expected to hold GitHub write credentials. Repository writes use the connected GitHub integration. Do not ask the user to add credentials to CT102 to publish Assistant changes.

## Governing project objectives

Milestone 3 operates under these forward principles:

1. maintain Kane Fabric as authentic public civic infrastructure;
2. preserve the validated authoritative county database pipeline;
3. keep new durable geographic contracts jurisdiction-explicit rather than implicitly Kane-specific;
4. treat ESP32-S3 + ESP-IDF HTTP serving as a first-class format constraint even though completed firmware is a later milestone;
5. keep application/subscription rights and semantics separate from the public civic-infrastructure substrate.

Relevant documents:

- `docs/HANDOFF.md`;
- `docs/DEVELOPMENT_PROCESS.md`;
- `docs/CIVIC_INFRASTRUCTURE_PRINCIPLES.md`;
- `docs/MULTI_COUNTY_DESIGN.md`;
- `docs/ESP32_EDGE_REFERENCE.md`;
- `docs/MILESTONE_3_DESIGN.md`;
- `docs/SUBSTRATE_FORMAT_V1.md`.

## Milestone 3 scope

Initial shared substrate:

- jurisdiction boundary/context;
- roads;
- water.

Not part of the shared substrate:

- building geometry as a default shared layer;
- Condo classifications;
- Mechanical Compiler classifications/qualifications;
- participants/capabilities/workflows;
- other application-owned subscription semantics.

Kane Fabric still owns durable geographic building identity in the database core; that does not make building geometry part of the initial shared substrate.

## Database pipeline invariant relevant to MS-3

Substrate compilation sits **after** geographic acceptance. It does not participate in source promotion.

The geographic lifecycle remains:

```text
source status
  → candidate harvest
  → candidate validation
  → candidate registration
  → deterministic comparison
  → building reconciliation where required
  → promotion prepare/validate
  → explicit atomic promotion
```

MS-3 compilation then reads the accepted database state read-only.

A candidate must never enter a published substrate merely because it is newer. A substrate build/test must not implicitly promote geography.

The full module/path map and the deliberate `project_building` compatibility naming are documented in `docs/HANDOFF.md`.

## Kane reference invariants relevant to substrate work

Jurisdiction identity:

```text
country_code  US
state_code    IL
fips_code     17089
county_key    kane-county-il
name          Kane County
```

Historical accepted counts used as regression evidence:

```text
boundary          1
buildings     208324
roads          27675
water-creeks     555
Fox River          1
```

The road source deliberately retains 27,675 of 27,676 source objects because one source object has missing geometry. That exclusion is an accepted source-contract behavior, not an error to repair casually.

Water provenance remains coordinated across `water-creeks` and `water-fox-river`; do not invent a single upstream source identity.

## Implemented repository work

The repository currently contains the Milestone 3 contract primitives and overview implementation:

```text
docs/SUBSTRATE_FORMAT_V1.md
substrate/README.md
substrate/run-tests.sh
substrate/kane-fabric-overview.sh
substrate/tools/kane_fabric_substrate.py
substrate/tools/kane_fabric_overview.py
substrate/tests/test_substrate_contract.py
substrate/tests/test_overview.py
```

The frozen v1 package direction is:

```text
county-overview.json
roads-lod.kfs
water-lod.kfs
substrate-manifest.json
```

Road and water containers use fixed-prefix indexed flat files with canonical JSON metadata and zlib-wrapped DEFLATE chunks. Jurisdiction identity is explicit. FIPS `17089` is the current durable U.S. jurisdiction code for the Kane reference deployment; `county_key` is a project identifier.

The overview generator opens the authoritative database read-only and emits deterministic canonical JSON tied to the exactly-one accepted boundary release.

Current implementation boundary:

```text
MS3-001 v1 contract primitives       repository implementation present
MS3-002 county overview              repository implementation present
MS3-003 road LOD/container           not yet implemented
MS3-004 water LOD/container          not yet implemented
MS3-005 manifest                     not yet implemented
MS3-006 package compiler/activation  not yet implemented
MS3-007 real deterministic proof     not yet accepted
MS3-008 browser selective loader     not yet implemented
MS3-009 browser rendering            not yet implemented
MS3-010 edge compatibility proof     not yet accepted
MS3-011 release                      not reached
```

Design text for a future component is not proof that the component exists.

## Current verification state

Repository review and synthetic regression-test code exist.

The first real CT102 Milestone 3 execution gate has **not yet been accepted**.

Do not claim that substrate tests, Kane County overview generation, or database immutability proof passed on the real environment merely because the code exists in GitHub or because a sandbox test passes.

The first CT102 gate must prove:

1. CT102 is running;
2. the actual Kane Fabric checkout is found and understood;
3. checkout repo identity, `main`, upstream, worktree, and fetch refspec are sane;
4. checkout is synchronized/verified against current GitHub `main` without discarding unexplained state;
5. `bash database/run-tests.sh` passes inside CT102;
6. `bash substrate/run-tests.sh` passes inside CT102;
7. the actual current Kane County working/accepted Fabric database is identified from live CT state;
8. its SHA-256 is recorded before compilation;
9. `county-overview.json` is built from that real database;
10. overview jurisdiction and accepted-boundary release identity match the database;
11. the database SHA-256 is unchanged after compilation.

The exact working database path and hash must be observed on CT102 rather than inferred from an old milestone handoff.

If the Assistant session lacks an execution channel to `srv-b`, record that capability gap. Repository work can continue only where it does not depend on pretending this gate passed.

## Historical evidence versus current observations

Historical release documents record important immutable/regression identities, including:

```text
seed SHA256
7fe2198b00b2d0dee9470eda3864b43b6f7b3b0ff3b236ce7c579ddc077f389a

historical promoted oracle SHA256
164200d4d7262874dcc03239c8258446a4d7bb81ce84daf46dc4937d6c97fe86

MS-2 closeout SHA256
fee3194b432566fc0cf4af09b8e9e80eb6efd9945e0894e96ecbb2aa22ce9f4c
```

Those remain regression evidence where the release documents define them as immutable.

A historical working DB such as:

```text
/var/lib/kane-fabric/database/kane-county-reconstructed.gpkg
ff67edcb0a732d87f3dc3bb3cf7fda91a03fea4ef8e16fb527f88283894c0a97
```

must **not** be called the current active database identity until it is observed live.

## Package and edge constraints

V1 publishes:

```text
county-overview.json
roads-lod.kfs
water-lod.kfs
substrate-manifest.json
```

`.kfs` framing is:

```text
8 bytes  magic/version
8 bytes  unsigned big-endian canonical-index length
N bytes  canonical JSON index
...      contiguous zlib-compressed canonical JSON chunks
```

The format must support bounded reads, seek/range access without whole-file RAM residency, immutable-file serving, deterministic verification, and browser-side decompression/rendering.

The ESP32-S3 reference edge matters now as a format constraint. Final production firmware and final HTTP contract are deferred to a later milestone.

## Kane-specific source policy versus generic contract

The wire contract is generic; source-selection policy may be jurisdiction-specific.

For Kane roads, authoritative functional road class is not retained. The design therefore uses deterministic coordinate-length membership for `orientation`, `context`, and `detail` rather than inventing unavailable semantics.

For Kane water, accepted coordinated Fox River/creek sources do not expose a generic hydrologic importance hierarchy. The design therefore uses explicit Kane Fox River/creek policy for `overview`, `context`, and `detail`.

Do not turn either Kane source policy into a universal Fabric semantic.

## Next implementation sequence after the CT102 baseline gate

Once the real environment baseline is accepted:

1. implement v1 road LOD/container generation and validation;
2. replay road output on the accepted Kane County road release and measure actual index/chunk/component size;
3. implement coordinated water LOD/container generation and validation;
4. compile the substrate manifest and content identity;
5. build the reproducible staged substrate package and atomic activation path;
6. implement the minimal browser loader/validator/decompressor/renderer;
7. prove selective byte access compatible with the ESP32-S3/ESP-IDF HTTP-serving constraint;
8. record exact Milestone 3 release evidence.

The historical Kane Condo `0.4` renderer remains a regression/design oracle. Port proven geographic mechanics where they still fit; do not import Condo application semantics into the Fabric substrate.

## Testing discipline

Do not churn already accepted tests without a concrete reason. Once a bounded implementation slice passes its defined acceptance gate, accept it and continue unless a later change invalidates the evidence.

A synthetic test can catch defects but does not replace CT102 execution when the claim is about the real Kane Fabric environment or Kane County state.

Promotion/rollback tests must use disposable or deliberately prepared state; substrate work must not alter accepted geography.

## Handoff requirement going forward

At every material MS-3 boundary, update **both**:

- `docs/HANDOFF.md` — stable cross-milestone current state;
- this file — Milestone 3-specific implementation/acceptance state.

Every update must distinguish:

- code present in GitHub;
- tests run only in synthetic/local environments;
- tests actually run inside CT102;
- real Kane County state observed at that time;
- accepted-state changes deliberately executed;
- work deferred because an execution capability was unavailable;
- exact next safe development action.

A future Assistant should not need private chat history to discover any of those facts.
