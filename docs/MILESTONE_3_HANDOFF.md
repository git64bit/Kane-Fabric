# Milestone 3 Handoff — Compile Shared Substrate

## Status

Current handoff for Milestone 3.

Read this file together with `docs/DEVELOPMENT_PROCESS.md`. The development-process document is authoritative for repository, host, CT, and operational execution boundaries.

Do not use the historical Milestone 2 statement that the user performs infrastructure commands as the current operating model. Routine project commands are executed by the Assistant/development process through the authorized `srv-b` → `pct exec 102` path.

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

Before substantive work, re-read current `main`. Do not rely on the commit recorded here if the repository has advanced.

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

Do not ask the user to act as the routine CT102 terminal operator. If an Assistant session lacks the authorized `srv-b` execution capability, state that limitation and leave the execution-dependent gate unverified.

## Checkout rule

The Milestone 2 cleanup historically used:

```text
/tmp/kane-fabric-ms2
```

That is not a permanent checkout-path contract.

On first live access to CT102, discover and verify the current Kane Fabric checkout before running Git operations. Confirm repository identity, `main`, upstream, worktree status, and normal remote fetch refspec before changing it.

Once a stable current checkout path is deliberately established, record it in this handoff or the Milestone 3 release record.

## Governing project objectives

Milestone 3 operates under these forward principles:

1. maintain Kane Fabric as authentic public civic infrastructure;
2. preserve the validated authoritative county database pipeline;
3. keep new durable geographic contracts jurisdiction-explicit rather than implicitly Kane-specific;
4. treat ESP32-S3 + ESP-IDF HTTP serving as a first-class format constraint even though firmware implementation is a later milestone;
5. keep application/subscription rights and semantics separate from the public civic-infrastructure substrate.

Relevant documents:

- `docs/CIVIC_INFRASTRUCTURE_PRINCIPLES.md`;
- `docs/MULTI_COUNTY_DESIGN.md`;
- `docs/ESP32_EDGE_REFERENCE.md`;
- `docs/MILESTONE_3_DESIGN.md`;
- `docs/SUBSTRATE_FORMAT_V1.md`;
- `docs/DEVELOPMENT_PROCESS.md`.

## Milestone 3 scope

Initial shared substrate:

- jurisdiction boundary/context;
- roads;
- water.

Not part of the shared substrate:

- building geometry;
- Condo classifications;
- Mechanical Compiler classifications/qualifications;
- participants/capabilities/workflows;
- other application-owned subscription semantics.

## Implemented repository work

The repository currently contains the initial Milestone 3 contract and overview implementation:

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

The v1 package direction is:

```text
county-overview.json
roads-lod.kfs
water-lod.kfs
substrate-manifest.json
```

Road and water containers use fixed-prefix indexed flat files with canonical JSON metadata and zlib-wrapped DEFLATE chunks. Jurisdiction identity is explicit. FIPS `17089` is the current durable U.S. jurisdiction code for the Kane reference deployment; `county_key` is a project identifier.

The overview generator is designed to open the authoritative database read-only and emit deterministic canonical JSON tied to the exactly-one accepted boundary release.

## Current verification state

Repository review and synthetic regression-test code exist.

The first real CT102 Milestone 3 execution gate has **not yet been accepted in this handoff** unless a later entry below records actual execution from CT102.

Do not claim that the substrate tests, Kane County overview generation, or database immutability proof passed on the real environment merely because the code exists in GitHub or because a sandbox test passes.

The first CT102 gate should prove:

1. current CT102 checkout is synchronized with authoritative `main`;
2. `database/run-tests.sh` still passes;
3. `substrate/run-tests.sh` passes;
4. the overview builds from the current Kane County working/accepted Fabric database;
5. the source database SHA-256 is unchanged by overview compilation;
6. generated overview jurisdiction/release identity matches the actual accepted database state.

The exact current working database path and hash must be observed on CT102 rather than inferred from an old milestone handoff.

## Historical paths and hashes are evidence, not current observations

Historical documents record paths such as:

```text
/var/lib/kane-fabric/database/kane-county-reconstructed.gpkg
```

and multiple historical database hashes from reconstruction, promotion, closeout, and rollback proofs.

Do not call one of those hashes the current active database identity without observing the actual CT102 state.

Immutable evidence identities such as the approved seed and historical oracle remain meaningful where their release records say they are immutable.

## Next implementation sequence after the CT102 gate

Once the current real-environment gate is clean:

1. implement Fabric v1 road LOD/container generation and validation;
2. replay road output on the accepted Kane County road release and measure actual index/chunk/component size;
3. implement coordinated water LOD/container generation and validation;
4. compile the substrate manifest and content identity;
5. build the reproducible staged substrate package and atomic activation path;
6. implement the minimal browser loader/validator/decompressor/renderer;
7. prove selective byte access compatible with the ESP32-S3/ESP-IDF HTTP-serving constraint;
8. record exact Milestone 3 release evidence.

The historical Kane Condo `0.4` renderer remains a regression/design oracle. Port proven geographic mechanics where they still fit; do not import Condo application semantics into the Fabric substrate.

## Promotion and authority discipline

Milestone 3 compilation should consume accepted geography and should not change accepted geographic state.

Candidate registration, reconciliation, and promotion remain separate geographic-maintenance operations.

Do not hide a real accepted-state promotion inside a substrate build or test command.

## Handoff requirement going forward

Every future handoff must distinguish:

- code present in GitHub;
- tests run in synthetic/local environments;
- tests actually run inside CT102;
- real Kane County state observed at that time;
- accepted-state changes deliberately executed;
- work deferred because an execution capability was unavailable.

This distinction is mandatory so a future Assistant cannot mistake repository completion for deployment acceptance.
