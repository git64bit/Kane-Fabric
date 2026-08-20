# Kane Fabric — Current Handoff

This is the current operational handoff for a new Assistant or developer. Start here.

Historical milestone handoffs and release records remain evidence, but they are not current implementation instructions. When a historical document conflicts with this file, `docs/CURRENT_STATE.json`, or a governing contract, use the current documents.

## 1. What this project is

Kane Fabric is public civic infrastructure for maintaining authoritative county-scale geographic state and distributing it through a browser-first **substrate + subscriptions + logical geographic partitions** architecture.

Kane County, Illinois is the reference deployment. It must not be baked into reusable wire-format, partition, subscription, database, or protocol concepts where those concepts are geographically generic.

The long-lived model is:

```text
official geographic sources
        ↓
County Fabric node
  authoritative geographic control plane/compiler
        ↓
accepted geographic state
        ↓
immutable county substrate
+ logical partition definitions
+ application subscription generations
        ↓
replaceable edge nodes / mirrors / caches
  physical storage and HTTP serving
        ↓
Browser
  validate, selectively fetch, decompress, compose, render
```

The authoritative GeoPackage is an internal control-plane implementation. The compiled publication and explicit partition/subscription contracts are the durable external interface.

## 2. Read order

For current work read:

1. `docs/HANDOFF.md` — current system mental model;
2. `docs/CURRENT_STATE.json` — compact machine-readable current checkpoint;
3. `docs/DEVELOPMENT_PROCESS.md` — execution/repository authority;
4. `README.md` — public project/status summary;
5. `docs/PROJECT_CHARTER.md` — fixed project principles;
6. `docs/ARCHITECTURE.md` — system roles/boundaries;
7. `docs/DATA_OWNERSHIP.md` — geographic/application ownership boundary;
8. `docs/ROADMAP.md` — milestone sequence;
9. `docs/MILESTONE_4_DESIGN.md` — current milestone design;
10. `docs/ESP32_EDGE_REFERENCE.md` — deferred MS-5 hardware boundary.

Use prior release records when exact historical evidence is needed:

- `docs/MILESTONE_1_RELEASE.md`;
- `docs/MILESTONE_2_RELEASE.md`;
- `docs/MILESTONE_3_RELEASE.md`.

Do not reconstruct current state from an old milestone handoff.

## 3. Separate authorities

Do not collapse these into one source of truth:

| Authority | Owns |
| --- | --- |
| GitHub `git64bit/Kane-Fabric`, `main` | software, migrations, profiles, tests, contracts, documentation, small deterministic manifests |
| Proxmox host `srv-b` | LXC lifecycle, host conformance, host firewall/network policy, host-to-container execution |
| CT102 `kane-fabric` | real Kane Fabric runtime/test/compiler environment |
| `/var/lib/kane-fabric` in CT102 | operational databases, immutable evidence, staging, rollback, audit, generated substrate artifacts |

An Assistant sandbox is not CT102 and cannot substitute for CT102 acceptance.

The host-owned conformance definition is `/usr/local/sbin/ct-baseline.sh` on `srv-b`. Kane Fabric must not create a competing repository definition of host conformance.

CT100 and CT101 are Mechanical Compiler infrastructure. Do not repurpose them for Kane Fabric.

## 4. Repository and execution model

Repository:

```text
git64bit/Kane-Fabric
branch: main
```

Normal development is on `main` unless the user explicitly requests a branch/PR workflow.

The Milestone 3 development branch `assistant/read-authority-boundary` was fast-forward merged into `main`; the accepted MS-3 publication entered `main` at:

```text
84293aeb381db596f4c3233473c350fda6c5426d
```

The branch has not been deleted because deletion was not authorized.

Normal runtime path:

```bash
pct status 102
pct exec 102 -- COMMAND ...
pct exec 102 -- bash -lc '...'
```

Run Proxmox/LXC and host-policy work on `srv-b`. Run Kane Fabric tests, database tools, source work, compilation, and real acceptance inside CT102.

CT102 does not need GitHub write credentials. Repository writes use the connected GitHub integration.

The currently recorded checkout path is:

```text
/tmp/kane-fabric-ms2
```

This is an observed deployment path, not an architectural contract. Use `docs/CURRENT_STATE.json` and `development/kane-fabric-dev-state.sh` to verify it before state-changing work.

## 5. Authoritative database and geographic lifecycle

Current authoritative Kane County Fabric database:

```text
/var/lib/kane-fabric/database/kane-county-fabric.gpkg
bytes   355180544
SHA256  31e362b696a37f1b9c45ae355c5669511a3128c17a651108a62e20d1cedebd67
migrations 7
```

Historical donor-shaped database:

```text
/var/lib/kane-fabric/database/kane-county-reconstructed.gpkg
```

is not current authority.

The geographic lifecycle is fundamental:

```text
source profile
  ↓
source status
  ↓
candidate harvest
  ↓
candidate validation
  ↓
candidate registration
  ↓
deterministic comparison
  ↓
reconciliation where required
  ↓
promotion preparation + validation
  ↓
EXPLICIT atomic promotion
  ↓
accepted geographic state
  ↓
READ-ONLY publication/subscription/partition compilation
```

Consequences:

- source status is read-only;
- candidate registration is not acceptance;
- a newer source is not automatically authoritative;
- comparison is not acceptance;
- reconciliation is not acceptance;
- compilation/partitioning must never promote geography;
- explicit promotion is the authority-changing operation.

## 6. Accepted Kane County reference state

Jurisdiction:

```text
country_code  US
state_code    IL
fips_code     17089
county_key    kane-county-il
name          Kane County
```

Accepted releases:

```text
buildings          208324
county boundary         1
roads                 27675
water creeks            555
Fox River                 1
water total              556
```

### Road source-status correction

The accepted road release contains 27,675 features and the accepted harvest object inventory is also 27,675.

A later live official source inventory exposed 27,676 object IDs. That correctly produces `new_source_detected` because the live inventory changed.

Do **not** repeat the earlier explanation that the accepted release deliberately removed one of 27,676 objects for missing geometry. That explanation was disproven by the accepted harvest inventory.

Water provenance remains coordinated across `water-creeks` and `water-fox-river`; do not invent a single upstream water source identity.

## 7. Durable building identity and application ownership

Kane Fabric owns persistent geographic building identity because applications need references that survive official-source refreshes.

For behavior-preserving compatibility, physical tables still include donor-era names such as:

```text
project_building
project_building_source_mapping
```

Those names do not make the records Condo application state.

Kane Fabric geographic operation does not require application classification tables such as:

```text
building_classification_current
building_classification_event
```

Mechanical Compiler remains a separate application. An Industry subscription may reference Fabric geography; Kane Fabric does not become authoritative for Mechanical Compiler participant, qualification, capability, workflow, or federation state.

## 8. Milestone 3 — released baseline substrate

Milestone 3 is complete and must not be reopened as routine discovery.

Canonical external publication:

```text
county-overview.json
roads-lod.kfs
water-lod.kfs
substrate-manifest.json
```

Accepted substrate content SHA-256:

```text
fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc
```

Component identities:

```text
county-overview.json
  1670 bytes
  f0995177625e28adc39e0ddd842ea22fbc1935239d6d1f7d54f377edde62e942

roads-lod.kfs
  4014272 bytes
  4c897db58a55961d76e720d3905b57a76fe199f5396c876b57e56ecaeaaee4d2

water-lod.kfs
  3183647 bytes
  dc4786b2904869fc5f910fa0d1b1a5767f1204fda99f34b2745f1ef7088f7f89

substrate-manifest.json
  1797 bytes
  1143324ace2dd7c47ad5f79e0763fdf978be5447527095e9e6f96d46b3fd1d13
```

Milestone 3 proved:

- deterministic real Kane County publication bytes;
- selective indexed `.kfs` byte-range access;
- browser SHA-256 validation;
- browser DEFLATE decompression;
- real Chromium Canvas rendering;
- no application subscription data required for baseline rendering;
- bounded reference-server reads compatible with constrained-edge design;
- authoritative database byte identity unchanged by compilation/render proof.

See `docs/MILESTONE_3_RELEASE.md` for exact evidence.

## 9. Milestone 4 — exact current boundary

Current milestone:

**Milestone 4 — Subscriptions + Geographic Scoping/Partition Identity**

Design authority:

```text
docs/MILESTONE_4_DESIGN.md
```

The new architectural progression is:

```text
MS-3  county substrate + selective chunks       COMPLETE
  ↓
MS-4  subscriptions + geographic partitions     CURRENT
  ↓
MS-5  ESP32-S3 physical edge implementation     DEFERRED
```

A geographic partition is a deterministic jurisdiction-scoped area used for selection, composition, storage planning, replication, and serving.

Initial partition classes:

- whole jurisdiction;
- municipality/incorporated place when an accepted boundary definition exists;
- township/equivalent administrative subdivision when an accepted boundary definition exists;
- explicit bounded region;
- deterministic composite scope where justified.

Municipalities and townships are useful named scopes but are not the only mechanism. Roads, water, buildings, service areas, and domain data may cross them.

Partition boundaries are distribution boundaries, not authority or ownership boundaries. Cross-boundary objects retain one logical identity and may be referenced/replicated in several partitions.

The Milestone 3 county publication remains canonical. MS-4 does not create separate authoritative town databases. Partitions select/reference relevant substrate chunks/ranges and subscription objects.

A partition identity must not depend on:

- ESP32 serial/device identity;
- hostname;
- SSID;
- IP address;
- physical storage path.

## 10. Milestone 4 implementation order

Current planned order:

```text
MS4-001  partition descriptor and deterministic identity contract
MS4-002  administrative/bounded scope normalization and inclusion rules
MS4-003  substrate partition selection manifest/reference model
MS4-004  subscription manifest and independent generation contract
MS4-005  geographic identity references and ownership/rights boundary
MS4-006  Condo proof subscription
MS4-007  Industry / Mechanical Compiler proof subscription
MS4-008  browser composition of substrate + multiple scoped subscriptions
MS4-009  multi-partition / cross-boundary composition proof
MS4-010  edge-placement compatibility proof without ESP-IDF implementation
MS4-011  release evidence and milestone closeout
```

Do not mark an item complete merely because its design text exists.

## 11. ESP32-S3 / ESP-IDF boundary

ESP32-S3 remains the minimum initial edge reference, but actual ESP-IDF integration remains Milestone 5.

Milestone 4 is hardware-aware but firmware-independent. It must define logical partitions/subscriptions that make focused edge placement practical without implementing:

- ESP-IDF firmware;
- ESP-IDF HTTP handlers;
- flash/SD-card layout;
- Wi-Fi AP/STA behavior;
- firmware update/recovery.

Milestone 5 owns those physical/runtime decisions and maps MS-3/MS-4 logical identities onto actual devices.

If ESP-IDF is retained for release, the exact SDK/toolchain must be license-reviewed, pinned, and vendored according to the dependency policy.

## 12. Dependency and licensing policy

Kane Fabric-authored code must remain under the repository's existing Unlicense.

A dependency is not acceptable if it forces Kane Fabric-authored code to change license.

Third-party implementations retained as project-controlled runtime/build/test/firmware dependencies must be pinned and vendored before final release. Browser Web APIs and ordinary target-platform interfaces are contracts, not automatically bundled project implementations.

Node.js and Chromium used for Milestone 3 acceptance are currently development-only tooling. Their use does not make them runtime dependencies of the substrate or edge node.

See:

```text
docs/DEPENDENCY_POLICY.md
third_party/manifest.json
```

## 13. Testing and evidence discipline

Make claims only at the level actually tested:

```text
repository/static review
  ↓
synthetic/unit tests
  ↓
full regression tests in CT102
  ↓
real Kane County read-only/derived-data proof
  ↓
explicit authority-changing gate when required
  ↓
release evidence with exact identities
```

Accepted gates are not rerun merely because a new Assistant arrived. Rerun when an implementation/environment/dependency change invalidates the prior evidence or a contradictory observation appears.

Large operational artifacts remain outside Git under `/var/lib/kane-fabric`.

## 14. Shell and operational discipline

Never inject bare:

```bash
set -euo pipefail
```

into the user's interactive `srv-b` root shell. It can terminate the interactive shell after an assertion failure.

Strict mode is safe inside a bounded child command, for example:

```bash
pct exec 102 -- bash -lc '
  set -euo pipefail
  ...
'
```

When the user is explicitly performing a manual command relay, give one bounded command group at a time and wait for its output before issuing the next state-changing group.

Do not copy large operational GeoPackages into Git.

## 15. What not to do

Do not:

- revive Kane Condo as an active project/runtime dependency;
- expose the internal GeoPackage schema as the durable external client interface;
- silently promote candidate geography during source status, comparison, compilation, subscription work, or partition work;
- make a town/township partition its own geographic authority;
- make physical edge placement part of partition or subscription identity;
- clip/change feature identity merely because a feature crosses a partition boundary;
- move ESP-IDF implementation into Milestone 4 without an explicit project scope decision;
- repeat the disproven 27,676-to-27,675 missing-geometry road explanation;
- collapse the two accepted water source datasets into fake single-source provenance;
- treat `project_building` physical names as application ownership;
- require the frozen donor checkout at normal Fabric runtime;
- claim CT102 acceptance from an Assistant sandbox;
- repurpose CT100/CT101;
- create feature branches unless requested;
- delete historical branches without authorization;
- change the root Unlicense to accommodate a dependency.

## 16. Next safe action

Milestone 3 is released on `main`.

The next implementation item is:

```text
MS4-001
partition descriptor and deterministic identity contract
```

Begin from `docs/MILESTONE_4_DESIGN.md` after the normal live checkout preconditions are verified. Do not start ESP-IDF firmware work; that remains Milestone 5.
