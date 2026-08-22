# Kane Fabric — Current Handoff

This is the current operational handoff for a new Assistant or developer. Start here.

Historical milestone handoffs and release records remain evidence, not current implementation instructions. When a historical document conflicts with this file, `docs/CURRENT_STATE.json`, or a governing contract, use the current documents.

## 1. What Kane Fabric is

Kane Fabric is public civic infrastructure for maintaining authoritative county-scale geographic state and distributing it through a browser-first architecture:

```text
official geographic sources
        ↓
County Fabric node
  authoritative control plane/compiler
        ↓
accepted geographic state
        ↓
canonical county substrate
+ logical geographic partitions
+ independently versioned application subscriptions
        ↓
replaceable physical edge nodes / mirrors / caches
        ↓
Browser
  verify, selectively fetch, decompress, compose, render
```

Kane County, Illinois is the reference deployment. Reusable wire formats, partition identities, subscription contracts, and edge-serving contracts must remain geographically generic where possible.

The authoritative GeoPackage is an internal control-plane implementation. Compiled publications and explicit contracts are the durable external interface.

## 2. Current read order

1. `docs/HANDOFF.md`
2. `docs/CURRENT_STATE.json`
3. `docs/DEVELOPMENT_PROCESS.md`
4. `README.md`
5. `docs/PROJECT_CHARTER.md`
6. `docs/ARCHITECTURE.md`
7. `docs/DATA_OWNERSHIP.md`
8. `docs/ROADMAP.md`
9. `docs/MILESTONE_4_RELEASE.md` for the released partition/subscription identities
10. `docs/MILESTONE_4_DESIGN.md` as the historical normative MS4 work-sequence authority
11. `docs/ESP32_EDGE_REFERENCE.md` for the Milestone 5 starting boundary

Historical release evidence:

- `docs/MILESTONE_1_RELEASE.md`
- `docs/MILESTONE_2_RELEASE.md`
- `docs/MILESTONE_3_RELEASE.md`
- `docs/MILESTONE_4_RELEASE.md`

## 3. Separate authorities

| Authority | Owns |
| --- | --- |
| GitHub `git64bit/Kane-Fabric`, `main` | software, migrations, tests, contracts, documentation, small deterministic manifests |
| Proxmox host `srv-b` | LXC lifecycle, host conformance, host firewall/network policy, host-to-container execution |
| CT102 `kane-fabric` | real Kane Fabric runtime/test/compiler environment |
| `/var/lib/kane-fabric` in CT102 | operational databases, immutable evidence, staging, rollback, audit, generated publications |

An Assistant sandbox is not CT102 and cannot substitute for CT102 acceptance.

CT100 and CT101 are Mechanical Compiler infrastructure. Do not repurpose them.

Normal development is directly on `main` unless the user explicitly requests a branch/PR workflow.

Recorded CT102 checkout:

```text
/tmp/kane-fabric-ms2
```

This is an observed deployment path, not an architectural contract.

## 4. Geographic authority lifecycle

Accepted geography changes only through explicit promotion:

```text
source profile
  → source status
  → candidate harvest
  → candidate validation
  → candidate registration
  → deterministic comparison
  → reconciliation where required
  → promotion preparation + validation
  → explicit atomic promotion
  → accepted geographic state
  → read-only publication / partition / subscription compilation
```

Source freshness, candidate registration, comparison, partition selection, subscription generation, edge placement, and browser composition do not silently change geographic authority.

Current authoritative database:

```text
/var/lib/kane-fabric/database/kane-county-fabric.gpkg
bytes   355180544
SHA256  31e362b696a37f1b9c45ae355c5669511a3128c17a651108a62e20d1cedebd67
migrations 7
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

Road provenance correction remains binding: the accepted road release and accepted harvest inventory both contain 27,675 objects. A later live source inventory exposed 27,676 and correctly triggered `new_source_detected`. Do not revive the disproven missing-geometry explanation.

Water provenance remains coordinated across `water-creeks` and `water-fox-river`.

## 5. Durable building identity and application ownership

Kane Fabric owns persistent geographic building identity because applications need references that survive source refreshes.

Physical compatibility tables may retain donor-era names such as `project_building` and `project_building_source_mapping`; those records remain Fabric geography, not Condo application state.

Application classifications and domain payloads belong to applications/subscriptions. Industry / Mechanical Compiler state is not Kane Fabric authority merely because it references a Fabric building.

## 6. Milestone 3 — released substrate

Milestone 3 is released and must not be reopened without a concrete invalidating observation.

Canonical publication:

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
county-overview.json   1670 bytes     f0995177625e28adc39e0ddd842ea22fbc1935239d6d1f7d54f377edde62e942
roads-lod.kfs          4014272 bytes  4c897db58a55961d76e720d3905b57a76fe199f5396c876b57e56ecaeaaee4d2
water-lod.kfs          3183647 bytes  dc4786b2904869fc5f910fa0d1b1a5767f1204fda99f34b2745f1ef7088f7f89
substrate-manifest     1797 bytes     1143324ace2dd7c47ad5f79e0763fdf978be5447527095e9e6f96d46b3fd1d13
```

The released browser path requires Web Crypto SHA-256 capability before publication access. Capability is authoritative; URL/scheme inference is not. Loopback HTTP was proven trustworthy in Chromium; ordinary LAN HTTP without WebCrypto failed before any substrate publication request. Do not weaken integrity verification or add a fallback hash implementation.

The normative project zlib compile/runtime pin remains `1.2.13`. Historical observed values are evidence only, not authority.

## 7. Milestone 4 — released partitions and subscriptions

Milestone 4 is **RELEASED — 2026-08-22**.

Release record:

```text
docs/MILESTONE_4_RELEASE.md
```

Accepted implementation head:

```text
9f6013d1b8b44998047f71e2b3f3e9c55c9ed298
```

Accepted proof bundle:

```text
/var/lib/kane-fabric/render/ms4-proof
composition SHA256      a58c8398248cee05b7baad9ae289fe0581bdb3624ce1aff3aa8a49721f92ee53
bundle inventory SHA256 1e109d4621ce738e3e35b93c23ecab0d5c9a0d4166aad5d72f4e2eff397ad0d3
```

Release evidence:

```text
/var/lib/kane-fabric/render/ms4-evidence/ms4-011-release-proof.json
SHA256  3235cd4f7b7041138fe05708dbb077c07dc3ce8b8ec7a390141489460ac40634
```

Released logical partition identities:

```text
west  kfp1-489f4340fc2fa2652dfa5bf4eac4b0e1
east  kfp1-3047abaf4fef374f57fb59b9c76902f6
```

Released proof subscription generations:

```text
condo     kfsg1-4804b03fc48ffb4b9882fdd71ce39689
industry  kfsg1-f6efa4be24e65db0f6b78b99c3ec3a37
```

The final proof established two partitions, two subscriptions, four cross-partition object appearances, two unique logical objects, preserved cross-boundary identity, physical-placement independence, and unchanged accepted geographic authority.

Partition boundaries are distribution boundaries, not ownership or geographic authority boundaries. Municipalities/townships are convenience scopes only. Cross-boundary features retain one logical identity. A partition identity never depends on ESP32 serial/device identity, hostname, SSID, IP address, or physical storage path.

The Industry proof is a synthetic contract-shape proof unless Mechanical Compiler later supplies an actual geographic/service interface.

## 8. Milestone 5 — current work

Current milestone:

**Milestone 5 — Edge serving contract**

Milestone 5 maps already-released MS3/MS4 logical identities onto physical edge hardware. ESP32-S3-class hardware with ESP-IDF remains the initial reference direction.

Milestone 5 owns physical/runtime decisions including:

- selection, pinning, license review, and vendoring of ESP-IDF/toolchain if retained;
- physical storage layout and capacity planning;
- HTTP serving and byte-range behavior;
- package/partition/subscription activation;
- local browser access and secure-context implications;
- AP/STA deployment behavior;
- synchronization transport where required;
- node replacement and recovery.

Milestone 5 must not redesign MS3 substrate identity, MS4 partition identity, subscription generation identity, or cross-boundary object identity merely to suit one device.

## 9. Dependency and licensing policy

Kane Fabric-authored code remains under the repository Unlicense.

A dependency is unacceptable if it forces Kane Fabric-authored code to change license. Retained project-controlled third-party runtime/build/test/firmware implementations must be pinned and vendored before final release according to `docs/DEPENDENCY_POLICY.md`.

Node.js and Chromium are development/acceptance tooling, not published runtime dependencies merely because they were used for proofs.

## 10. Testing and evidence discipline

Make claims only at the level actually tested:

```text
repository/static review
  → synthetic/unit tests
  → full regression tests in CT102
  → real Kane County read-only/derived-data proof
  → explicit authority-changing gate when required
  → release evidence with exact identities
```

Accepted gates are not rerun merely because a new Assistant arrived. Rerun when implementation, environment, dependency, or contradictory evidence invalidates the prior result.

## 11. Shell and operational discipline

Never inject bare `set -euo pipefail` into the interactive `srv-b` root shell. Use strict mode only inside bounded child commands such as `pct exec 102 -- bash -lc '...'`.

For user-relayed CT102 work, issue one bounded command group at a time and wait for output before the next state-changing group.

Large operational GeoPackages and generated proof/publication artifacts remain outside Git.

## 12. Next safe action

Milestones 1–4 are released.

Begin Milestone 5 by defining how the released MS3 substrate and MS4 partition/subscription identities map to physical ESP32-S3-class storage, HTTP serving, activation, replacement, and recovery. Preserve the existing logical identities and authority boundaries while doing so.
