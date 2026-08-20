# Kane Fabric — Current Handoff

This is the **current operational handoff** for a new Assistant or developer. Start here.

Historical milestone handoffs remain useful evidence, but they are not sufficient onboarding documents and may preserve procedures that are no longer current. When this file conflicts with a historical handoff, this file plus the governing documents named below control current work.

## 1. What this project is

Kane Fabric is public civic infrastructure for maintaining and distributing authoritative county-scale geographic state through a browser-first **substrate + subscriptions** architecture.

Kane County, Illinois is the reference deployment. It is not meant to be baked into reusable wire-format, database, or protocol concepts when those concepts are geographically generic.

The system has three long-lived roles:

```text
County Fabric node
  authoritative geographic control plane/compiler
        ↓
compiled immutable substrate/subscription artifacts
        ↓
replaceable edge nodes
  low-cost HTTP/storage data plane
        ↓
Browser
  durable client: validate, fetch, decompress, render, pan/zoom, compose
```

The shared substrate is civic geographic context. The initial substrate is:

- jurisdiction/county boundary and overview context;
- roads;
- water.

Application-specific state belongs in subscriptions. Buildings may be geographic identities in Fabric, but Condo classifications, Mechanical Compiler qualifications/capabilities/workflows, Retail state, and similar domain semantics are not shared-substrate ownership.

Kane Fabric grew from the frozen Kane Condo `0.4` implementation. Kane Condo is now a historical regression/design oracle only; normal Kane Fabric geographic-core runtime must not depend on the donor checkout.

## 2. Read-order and authority

A new Assistant should read, in this order:

1. `docs/HANDOFF.md` — this current state/mental model;
2. `docs/DEVELOPMENT_PROCESS.md` — execution, repository, CT, operational-state authority;
3. `README.md` — public project/status summary;
4. `docs/PROJECT_CHARTER.md` — fixed project principles;
5. `docs/ARCHITECTURE.md` — system roles and boundaries;
6. `docs/DATA_OWNERSHIP.md` — data/application ownership boundaries;
7. `docs/ROADMAP.md` — milestone sequence and released gates;
8. current milestone documents, presently `docs/MILESTONE_3_DESIGN.md`, `docs/MILESTONE_3_HANDOFF.md`, and `docs/SUBSTRATE_FORMAT_V1.md`;
9. prior release records when exact historical evidence is needed: `docs/MILESTONE_1_RELEASE.md` and `docs/MILESTONE_2_RELEASE.md`.

Do **not** read one old handoff and assume it describes the current execution model.

At the beginning of each session, read the actual current GitHub `main`; do not trust an embedded commit SHA as proof that the repository has not advanced.

At the start of the handoff repair that produced this document, `main` was:

```text
0c2c5bb636d56da4afc130d05d86fdd0a9ff7092
```

This SHA is historical context only. The live `main` ref is authoritative.

## 3. Four separate authorities

Do not collapse these into one machine or one source of truth:

| Authority | Owns |
| --- | --- |
| GitHub `git64bit/Kane-Fabric`, branch `main` | software, migrations, profiles, tests, contracts, documentation, small deterministic manifests |
| Proxmox host `srv-b` | LXC lifecycle, host conformance, host firewall/network policy, host-to-container execution |
| CT102 `kane-fabric` | real Kane Fabric runtime/test/compiler environment |
| `/var/lib/kane-fabric` inside CT102 | operational databases, immutable evidence, staging, rollback, audit, render/substrate artifacts |

An Assistant sandbox is **not CT102**. A sandbox test can find a bug, but it cannot be reported as CT102 acceptance.

The host-owned conformance definition is not in this repository. On `srv-b`, `/usr/local/sbin/ct-baseline.sh` is the executable baseline authority. Kane Fabric must not create a competing host baseline inside the repository.

CT100 and CT101 are Mechanical Compiler infrastructure. Do not repurpose them for Kane Fabric.

## 4. Development execution model

The normal runtime path is:

```bash
pct status 102
pct exec 102 -- COMMAND ...
pct exec 102 -- bash -lc '...'
```

Run Proxmox/LXC and host-policy work on `srv-b`. Run Kane Fabric Git inspection, tests, database tools, source work, and compilation inside CT102 through `pct exec`.

If the current Assistant session exposes an authorized execution channel to `srv-b`, use it. If no such channel is exposed, state that execution capability is missing and do not pretend a sandbox is equivalent.

Historical nuance: during Milestones 1 and 2 the user explicitly executed bounded command groups on `srv-b` and pasted results back. That was a real workflow used to obtain accepted evidence. It must not be erased from history. For current work, `docs/DEVELOPMENT_PROCESS.md` defines Assistant-executed `srv-b → pct exec 102` as the normal model when that execution capability exists. User command relay is an explicit/manual exception, not something to silently assume.

Do not install Git on the Proxmox host merely to work around repository workflow. Git operations belong in CT102 or through the authorized GitHub integration.

CT102 intentionally does not need GitHub **write** credentials. Repository publication should use the connected GitHub integration. Do not ask the user to enter GitHub credentials in CT102 to clean up Assistant-created branches or to publish routine changes.

## 5. Repository workflow — important incident history

Work directly on `main` unless the user explicitly requests a branch or PR workflow.

Milestone 2 was unnecessarily developed on `ms2/geographic-core-extraction`. That branch choice also left the CT102 checkout configured with a single-branch fetch refspec. After MS-2 was fast-forwarded into `main`, this caused:

- no local `main` branch;
- `git switch main` failure;
- an `origin/main` ref that was initially not recognized as a normal tracking branch because the fetch refspec still only covered MS-2;
- apparent modified/added release documents while the checkout was still based on the older branch commit, even though those files were byte-identical to remote `main`;
- a failed attempt to delete the remote branch from CT102 because CT102 had no GitHub write credential.

The recovery first proved the apparent local changes were byte-identical to `origin/main`, then reset, restored the normal refspec, created local `main`, and removed the merged branch locally/remotely.

The accepted final cleanup state observed on CT102 was:

```text
local branch   main
local HEAD     9440c31283a000f0b3ce30e57035446ad45c7ce3
upstream       origin/main
remote refs    origin/main only
working tree   clean
```

The repository subsequently advanced through GitHub to Milestone 3 commits. Therefore **do not assume CT102 is currently synchronized beyond that last observed checkout state**. Discover it on first live access.

Before changing checkout state, inspect:

```bash
git status --short --branch
git branch -vv
git config --get-all remote.origin.fetch
git remote -v
```

Never discard apparent local work until it has been compared with the intended authoritative ref.

The historical checkout path used during MS-2 was:

```text
/tmp/kane-fabric-ms2
```

It is not a permanent path contract. Discover the actual current checkout on CT102 before using it.

## 6. Repository map

### Geographic database core — `database/`

Kane Fabric owns a native SQLite/GeoPackage geographic core.

Important entry points:

```text
database/kane-fabric-db.sh
database/kane-fabric-provenance.sh
database/kane-fabric-boundary.sh
database/kane-fabric-map-layers.sh
database/kane-fabric-buildings.sh
database/kane-fabric-project-buildings.sh

database/kane-fabric-building-candidate.sh
database/kane-fabric-road-candidate.sh
database/kane-fabric-water-candidate.sh
database/kane-fabric-boundary-candidate.sh

database/kane-fabric-candidate-compare.sh
database/kane-fabric-building-reconcile.sh
database/kane-fabric-promotion.sh

database/kane-fabric-seed-import.sh
database/kane-fabric-ms2-closeout.sh
```

Core Python modules under `database/tools/`:

```text
kane_fabric_db.py                 DB init/migrate/validate/info
kane_fabric_geometry.py           EPSG:4326 geometry + GeoPackage/WKB mechanics
kane_fabric_provenance.py         county/agency/dataset/harvest/file/release lineage
kane_fabric_source_profiles.py    deterministic source-profile registry
kane_fabric_source_status.py      read-only upstream freshness/status inspection
kane_fabric_boundary.py           accepted/candidate boundary storage/validation
kane_fabric_map_layers.py         roads + water storage/validation
kane_fabric_buildings.py          official building footprint storage/validation
kane_fabric_project_buildings.py  durable geographic building identity/mappings
kane_fabric_building_candidate.py building harvest/validate/register
kane_fabric_road_candidate.py     road harvest/validate/register
kane_fabric_water_candidate.py    coordinated water harvest/validate/register
kane_fabric_boundary_candidate.py boundary harvest/validate/register
kane_fabric_candidate_compare.py  deterministic accepted-vs-candidate comparison
kane_fabric_building_reconcile.py building identity continuity/reconciliation
kane_fabric_promotion.py          prepare/validate/promote/rollback
kane_fabric_seed_import.py        verified Fabric-native bootstrap from immutable seed
kane_fabric_ms2_closeout.py       historical MS-1 evidence replay through native core
```

The old donor compatibility shim was removed. Do not reintroduce donor runtime loading as a shortcut.

Migrations are `database/migrations/0001` through `0007`:

```text
0001_geopackage_core.sql
0002_administrative_provenance.sql
0003_county_boundary.sql
0004_roads_water_storage.sql
0005_official_building_storage.sql
0006_geographic_building_identity.sql
0007_refresh_promotion.sql
```

Source contracts are under `database/source-profiles/` and currently cover exactly:

```text
county-boundary
buildings
roads
water-creeks
water-fox-river
```

The source-profile registry identity reproduced from MS-1 is:

```text
e95c9d0486f65035146cb0a2a9580e4148c853a78c4f9e44e2420f59ef654e12
```

Database regression entry point:

```bash
bash database/run-tests.sh
```

The accepted MS-2 native suite result before closeout was 16 tests passed, 0 failures.

### Milestone 3 substrate — `substrate/`

Current repository implementation contains:

```text
substrate/README.md
substrate/run-tests.sh
substrate/kane-fabric-overview.sh
substrate/tools/kane_fabric_substrate.py
substrate/tools/kane_fabric_overview.py
substrate/tests/test_substrate_contract.py
substrate/tests/test_overview.py
```

Substrate regression entry point:

```bash
bash substrate/run-tests.sh
```

Overview compiler entry point:

```bash
bash substrate/kane-fabric-overview.sh build DATABASE county-overview.json
```

As of the repository state audited for this handoff, **the generic v1 contract primitives and county overview compiler exist, but road LOD, water LOD, manifest/package compiler/activation, browser loader/renderer, and edge-compatibility proof are not yet complete implementations**.

Do not infer completion from the fact that `docs/SUBSTRATE_FORMAT_V1.md` already specifies those future components.

## 7. Geographic database lifecycle — mental model

This sequence is fundamental:

```text
official source profile
        ↓
read-only source-status check
        ↓
complete candidate harvest
        ↓
offline candidate validation
        ↓
register candidate provenance
        ↓
deterministic accepted-vs-candidate comparison
        ↓
building identity reconciliation where required
        ↓
promotion preparation + validation
        ↓
explicit atomic promotion
        ↓
rollback evidence retained
```

Important consequences:

- **Source status is read-only.** It detects likely upstream change; it does not update accepted geography.
- **Harvested evidence is not accepted state.** A candidate can exist externally and/or be registered in provenance without becoming authoritative.
- **Registration is not promotion.** It records candidate lineage only.
- **Comparison is deterministic and read-oriented.** It must not silently promote.
- **Building reconciliation is separate from comparison.** It determines continuity of durable geographic building identities when official source identifiers/geometry change.
- **Promotion is the authority-changing step.** It is explicit, preconditioned, backed up, atomically replaced, post-verified, and automatically restored on verification failure.
- **Rollback is explicit and audited.**
- **Substrate compilation consumes accepted geography read-only.** It must never hide a geographic promotion inside a build.

This pipeline is a core project invariant, not a historical implementation detail.

## 8. Durable building identity nuance

Kane Fabric owns persistent geographic building identity because applications need references that survive official source refreshes.

For behavior-preserving MS-2 compatibility, the physical schema still uses donor-era table names:

```text
project_building
project_building_source_mapping
```

Those names do **not** mean the records are Condo application state. Migration `0006_geographic_building_identity.sql` explicitly defines them as Kane Fabric geographic identities and records that the old table names were retained for compatibility.

Current building keys retain the historical deterministic form:

```text
kcb-<64 lowercase hex characters>
identity algorithm: sha256-release-feature-v1
```

Lifecycle values:

```text
active
inactive
retired
```

Mapping relationships include:

```text
initial
continuation
replacement
split
merge
reappearance
manual
```

Do not rename this physical schema casually. A neutral naming cleanup was intentionally deferred during behavior-preserving extraction.

## 9. Classification/application boundary

Kane Fabric geographic operation does **not** require the Kane Condo application-classification tables:

```text
building_classification_current
building_classification_event
```

Nor does the core own Condo classification values such as:

```text
unclassified
other
condominium
apartments
```

Application tables may coexist with Fabric state, but they are not prerequisites for geographic DB validation, reconciliation, promotion, or seed bootstrap.

Mechanical Compiler remains a separate application. A future Industry subscription may reference Fabric geography; it does not make Kane Fabric the authoritative owner of Mechanical Compiler participant, qualification, capability, workflow, or federation state.

## 10. Kane County reference-data invariants

Reference jurisdiction identity currently used by the Fabric core:

```text
country_code  US
state_code    IL
fips_code     17089
county_key    kane-county-il
name          Kane County
```

Retained accepted geographic counts proven by MS-1/MS-2 evidence:

```text
county boundary     1
buildings       208324
roads            27675
water creeks       555
Fox River             1
water total          556
```

Roads have a deliberate source exclusion:

```text
source object inventory  27676
retained                 27675
excluded                     1
reason: missing geometry
```

That exclusion is contract behavior. Do not “fix” the count to 27,676 unless the upstream evidence and source contract intentionally change.

Water is coordinated across two accepted datasets (`water-creeks` and `water-fox-river`); do not collapse provenance into an invented single source.

## 11. Milestone 1 and 2 immutable/regression evidence

Immutable accepted seed:

```text
/var/lib/kane-fabric/seed/kane-county.gpkg
size    324886528 bytes
SHA256  7fe2198b00b2d0dee9470eda3864b43b6f7b3b0ff3b236ce7c579ddc077f389a
```

Historical promoted Kane Condo oracle:

```text
/var/lib/kane-fabric/reconstruction-inputs/kane-condo-data/database/kane-condo.gpkg
size    649027584 bytes
SHA256  164200d4d7262874dcc03239c8258446a4d7bb81ce84daf46dc4937d6c97fe86
```

Historical donor software reference:

```text
/var/lib/kane-fabric/reconstruction-code/kane-condo-0.4
tag     0.4
commit  63582fb05c509d53870835d25612c87b56800d10
```

MS-1 proved 374 donor tests passed on the clean reconstruction environment. Do not edit the frozen donor checkout when using it as historical evidence.

Historical staged candidates used as regression evidence:

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

Exact deterministic comparison hashes reproduced by Fabric native code:

```text
buildings  23916019e762740a4ebe773cdfab916ace4c4d505521407fd6c513b382108d28
boundary   6ffa83d940347e7ffeeb10e3c631625af75de7f12ef95729ab1ebb75b5879f95
roads      7b3bf1ddaef1a40948d57edf0c465199316216510e0a1a78cb2dc0a552f59d3b
water      a1b0ac3f1504e4e6de199e694f794c83643f02139ed37f9a38c0d65d638f88f3
```

## 12. Milestone 2 closeout — decisive proof

MS-2 native historical closeout workspace:

```text
/var/lib/kane-fabric/staging/ms2-closeout-074dc07cd572
```

Final report:

```text
/var/lib/kane-fabric/staging/ms2-closeout-074dc07cd572/ms2-closeout.json
closeout SHA256  fee3194b432566fc0cf4af09b8e9e80eb6efd9945e0894e96ecbb2aa22ce9f4c
valid            true
```

Fabric-native seed bootstrap produced:

```text
SHA256  31e362b696a37f1b9c45ae355c5669511a3128c17a651108a62e20d1cedebd67
boundary 1
buildings 208324
roads 27675
water 556
confirmed initial building mappings 208324
application classification tables none
```

Native reconciliation result:

```text
reconciliation key       kane-buildings-reconciliation-20250730-94704f9c0869
reconciliation SHA256    498ee2fa00f7767d9e83437dca6dd330ffd555ca7122c8d5c06ecc36c85991a7
candidate DB SHA256      9236c0d684965c810a4e2fdfc4ac6771471ef234e623e9a7b636a12f68548926
mapped sources           208324
unmapped                 0
ambiguities              0
continuations            208324
redraws/replacements/additions/disappearances 0
ready for promotion      true
```

Native promotion/rollback proof:

```text
promotion key          kane-fabric-promotion-843b52cd0a19
promotion plan SHA256  843b52cd0a1926bd4ce74c57e889f5ec5a7e726fcac38dce6df6939d82e4509b
promoted DB SHA256     736ab4d1ff357675af9b1e2e358aae12afb617bf7000499171e1f83759e48f98
manual rollback        proved
```

The closeout verified the immutable seed and historical oracle were byte-identical before/after and reported zero forbidden donor-runtime references.

This is why MS-2 is closed. Do not rerun it as routine acceptance and do not reintroduce Kane Condo runtime dependencies.

## 13. Operational-state paths

Inside CT102, `/var/lib/kane-fabric/` is external operational state:

```text
seed/                    immutable seed evidence
reconstruction-inputs/   frozen historical evidence
reconstruction-code/     frozen historical software reference
database/                active/working Fabric databases
staging/                 candidate/reconciliation/promotion/closeout work
rollback/                rollback evidence
audit/                   audit reports
render/                   generated rendering/substrate artifacts
```

Large GeoPackages, harvested source data, staging directories, rollback DBs, and generated packages do not belong in Git.

A historically recorded working database was:

```text
/var/lib/kane-fabric/database/kane-county-reconstructed.gpkg
SHA256  ff67edcb0a732d87f3dc3bb3cf7fda91a03fea4ef8e16fb527f88283894c0a97
```

That is a historical identity, **not a guaranteed current observation**. Before MS-3 compiles real data, inspect CT102 and determine the actual current accepted/working database path and hash.

## 14. Milestone 3 — exact current boundary

Milestone 3 goal: compile a deterministic, browser-consumable shared substrate for boundary/context, roads, and water, independently of any application subscription.

The frozen v1 package shape is:

```text
county-overview.json
roads-lod.kfs
water-lod.kfs
substrate-manifest.json
```

The `.kfs` road/water containers use:

```text
8-byte magic/version
8-byte big-endian canonical-index length
canonical JSON index
contiguous zlib-wrapped DEFLATE chunks
```

Important current design constraints:

- deterministic bytes for identical accepted state + format/profile versions;
- explicit jurisdiction identity; never infer jurisdiction from filename, host, SSID, or physical device;
- accepted-release provenance in every relevant artifact;
- compilation opens the authoritative GeoPackage read-only;
- browser performs validation/decompression/rendering;
- package/index/chunk access must remain practical for ESP32-S3 + ESP-IDF HTTP serving;
- bounded reads/selective byte-range access are a format constraint now, even though final edge firmware is a later milestone;
- buildings and application semantics are excluded from the shared substrate.

Kane-specific LOD policy is source policy, not a universal Fabric rule:

- roads: orientation/context/detail use deterministic coordinate-length thresholds because authoritative functional class is not retained;
- water: overview/context/detail use coordinated Fox River/creek policy because no generic hydrologic importance hierarchy is available from the accepted sources.

## 15. Milestone 3 verification status — do not overclaim

At the time this handoff was repaired, repository code and synthetic tests existed for the v1 contract primitives and overview generator.

**No accepted record yet proves the current Milestone 3 repository state was synchronized and executed inside CT102.**

The next real-environment gate is therefore not “keep coding until road/water are finished.” First establish the real baseline:

1. access `srv-b` and verify CT102 is running;
2. discover the actual Kane Fabric checkout inside CT102;
3. inspect repo identity, branch, upstream, worktree, and fetch refspec;
4. synchronize/verify it against current GitHub `main` without discarding unexplained local state;
5. run `bash database/run-tests.sh` inside CT102;
6. run `bash substrate/run-tests.sh` inside CT102;
7. identify the actual current accepted/working Kane County Fabric database;
8. hash it before overview compilation;
9. build `county-overview.json` from that real database;
10. validate overview jurisdiction/release identity against the database;
11. hash the DB afterward and prove it was unchanged.

Only after that gate is accepted should MS3-003 road LOD work proceed as real-environment-backed development.

If the current Assistant has no `srv-b` execution channel, say so and leave these steps unverified. Do not convert repository-only work into a false CT acceptance result.

## 16. Milestone 3 implementation order

The active design order is:

```text
MS3-001  v1 contract                     present in repository
MS3-002  jurisdiction overview           implementation present; CT102 gate not yet accepted
MS3-003  road LOD/container              next after real baseline gate
MS3-004  coordinated water LOD/container
MS3-005  substrate manifest
MS3-006  reproducible compiler + atomic package activation
MS3-007  repeated real Kane County deterministic build/measurement proof
MS3-008  browser selective loader/validator/decompressor
MS3-009  browser boundary/road/water rendering + navigation
MS3-010  bounded edge-access compatibility proof
MS3-011  release evidence and milestone closeout
```

Do not mark an item complete merely because its design text exists.

## 17. Testing/acceptance discipline

Use the least expensive useful test first, but make claims only at the level actually run:

```text
repository/static review
        ↓
synthetic unit tests
        ↓
full regression tests inside CT102
        ↓
real Kane County read-only/derived-data gate in CT102
        ↓
explicit candidate/reconciliation/promotion gate when required
        ↓
release evidence with exact hashes/counts
```

Avoid repeated verification churn. Once a concrete implementation slice has passed its defined acceptance gate, accept it and move to the next slice unless a later change invalidates that evidence.

Do not add gratuitous source-level/synthetic closeout tests when real milestone evidence already proves the required behavior.

When a real test fails, diagnose the exact failure and patch the repository; do not fall back to donor wrappers or bypass the authority model.

## 18. Shell and operational discipline

Do not inject bare `set -euo pipefail` into an interactive root shell. Put strict mode inside a bounded subprocess, for example:

```bash
pct exec 102 -- bash -lc '
  set -euo pipefail
  ...
'
```

When the user is explicitly performing a manual command relay, give one bounded command group at a time and wait for its output before issuing the next destructive/state-changing group.

For large cross-machine artifacts, the established transfer workflow is:

```text
create tarball
→ Webmin download/upload
→ verify SHA-256 locally
→ extract/use
```

Do not prescribe SCP/SSH transfer as the default unless the user explicitly asks or the deployment policy changes.

Containers do not send mail in the host model; SMTP egress is blocked at the host. Do not treat lack of a container MTA as a project defect.

`nesting=1` is a proven shared requirement for the Debian unprivileged CT pattern on this host. `keyctl=1` is not a universal Kane Fabric architectural requirement; retain it only where the workload justifies it.

## 19. Public-infrastructure and multi-county forward constraints

New work after MS-2 must preserve three broad objectives:

1. Kane Fabric remains authentic independently usable public civic infrastructure;
2. accepted county geography remains current only through the explicit provenance/candidate/comparison/reconciliation/promotion safeguards;
3. new durable generic identities avoid unnecessary Kane County coupling.

Kane Fabric is released under the repository `LICENSE` using The Unlicense/public-domain dedication. That software status does not automatically make third-party geographic source data public domain; provenance/rights remain separate.

Kane County is the only required current operational jurisdiction. Do not create speculative nationwide infrastructure or fake second-county stubs merely to claim portability.

ESP32-S3 is the current minimum reference edge. It constrains package/access design now but does not define the permanent architecture.

## 20. What not to do

A new Assistant should not:

- revive Kane Condo development;
- require the frozen donor checkout at Fabric runtime;
- silently import Condo classification semantics into geographic core/substrate;
- treat `project_building` physical names as proof of application ownership;
- “fix” the deliberate one-road exclusion without new authoritative evidence;
- collapse two water source datasets into fake single-source provenance;
- assume a historical database hash is the current active DB without observing CT102;
- assume `/tmp/kane-fabric-ms2` is the current checkout;
- create a feature branch unless the user requested one;
- restrict `remote.origin.fetch` to one branch without an explicit reason;
- ask for GitHub write credentials in CT102 merely to publish or clean up Assistant changes;
- run Git on `srv-b` as a substitute for the CT/repository model;
- claim CT102 tests passed when only a sandbox test ran;
- hide accepted-state promotion inside a test, source-status check, or substrate compilation;
- repurpose CT100/CT101;
- copy large operational GeoPackages into Git;
- duplicate the host-owned `ct-baseline.sh` as a repository authority;
- keep rerunning already accepted gates without a concrete invalidating change.

## 21. Definition of a good future handoff

This file must be maintained as the stable current handoff path.

At every milestone boundary, update it to state:

- current milestone and exact implementation boundary;
- current repository module map if it changed materially;
- which gates actually ran inside CT102 and their accepted evidence;
- last **observed** CT102 checkout/path/state, clearly distinguished from repository `main`;
- last observed active/working database path/hash when relevant, clearly distinguished from historical evidence;
- new invariants, deliberate exceptions, and deferred compatibility names;
- any execution capability that was unavailable;
- the exact next safe development action.

A successor should be able to understand the system and resume safely from this file plus the named governing documents without needing private conversation memory.