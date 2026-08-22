# Kane Fabric

Kane Fabric is public civic infrastructure for maintaining and distributing authoritative county-scale geographic state through a browser-first **substrate + logical partitions + subscriptions** architecture.

Kane County, Illinois is the reference deployment rather than the conceptual namespace of the software. Reusable contracts are intended to remain portable across U.S. counties and county-equivalent jurisdictions without speculative nationwide infrastructure.

Kane Fabric-authored code is released under the repository `LICENSE` using The Unlicense/public-domain dedication. Third-party geographic data, firmware SDKs, and other dependencies retain their own provenance/license boundaries.

## Start here

New Assistants and developers read:

1. `docs/HANDOFF.md`
2. `docs/CURRENT_STATE.json`
3. `docs/SESSION_START.md`
4. `docs/DEVELOPMENT_PROCESS.md`
5. the current milestone reference identified by those documents

Inside CT102, use the recorded checkout and run:

```bash
bash development/kane-fabric-dev-state.sh
```

Use `--deep` only when database hashes/full validation are required.

## Current status

**Milestone 1 — Kane County Reconstruction Proof: RELEASED (2026-08-18).**

See `docs/MILESTONE_1_RELEASE.md`.

**Milestone 2 — Extract Kane Fabric Geographic Core: RELEASED (2026-08-20).**

See `docs/MILESTONE_2_RELEASE.md`.

**Milestone 3 — Compile Shared Substrate: RELEASED (2026-08-20).**

Canonical publication:

```text
county-overview.json
roads-lod.kfs
water-lod.kfs
substrate-manifest.json
```

Accepted substrate content identity:

```text
fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc
```

See `docs/MILESTONE_3_RELEASE.md`.

**Milestone 4 — Subscriptions + Geographic Scoping/Partition Identity: RELEASED (2026-08-22).**

Milestone 4 established deterministic logical partitions, exact substrate-selection references, independently versioned Condo and Industry proof subscriptions, Fabric geographic reference/ownership boundaries, real browser composition, cross-boundary identity preservation, and physical-placement independence.

Accepted proof:

```text
composition_sha256       a58c8398248cee05b7baad9ae289fe0581bdb3624ce1aff3aa8a49721f92ee53
bundle_inventory_sha256  1e109d4621ce738e3e35b93c23ecab0d5c9a0d4166aad5d72f4e2eff397ad0d3
release_proof_sha256      3235cd4f7b7041138fe05708dbb077c07dc3ce8b8ec7a390141489460ac40634
```

See `docs/MILESTONE_4_RELEASE.md`.

**Milestone 5 — Edge Serving Contract: CURRENT.**

Milestone 5 maps the released MS3/MS4 logical identities onto physical constrained-edge storage and HTTP serving. ESP32-S3-class hardware using ESP-IDF remains the initial reference direction. The edge implementation must not redesign partition, subscription, or substrate identities merely to suit a device.

See `docs/ESP32_EDGE_REFERENCE.md` and `docs/ROADMAP.md`.

## Platform model

Kane Fabric separates three long-lived roles:

- **County Fabric node** — authoritative geographic control plane/compiler. It owns source acquisition, provenance, validation, reconciliation, promotion, rollback, and deterministic publication compilation.
- **Browser** — durable client. It verifies, selectively fetches, decompresses, composes, and renders substrate plus subscriptions.
- **Edge nodes** — replaceable storage/HTTP resources. Physical placement is not logical data identity.

The authority flow is:

```text
official geographic sources
        ↓
accepted geographic state
        ↓
canonical county substrate
+ deterministic logical partitions
+ independent subscription generations
        ↓
physical edge placement / replication
        ↓
browser composition
```

## Geographic authority

Accepted geography changes only through explicit promotion. Source status, candidate registration, comparison, partition selection, subscription compilation, and edge placement are not authority-changing operations.

Current Kane County authoritative database:

```text
/var/lib/kane-fabric/database/kane-county-fabric.gpkg
SHA256  31e362b696a37f1b9c45ae355c5669511a3128c17a651108a62e20d1cedebd67
```

The internal GeoPackage schema is not the durable browser/client interface.

## Substrate, partitions, and subscriptions

The Milestone 3 county publication remains canonical. Milestone 4 partitions do not create separate town/township authorities or databases; they deterministically select/reference content from accepted generations.

A partition is a logical jurisdiction-scoped distribution/composition identity. It may be a whole jurisdiction, accepted administrative scope, explicit bounded region, or deterministic composite. Physical node identity, hostname, SSID, IP address, and storage path are excluded from partition identity.

A subscription is independently versioned application/domain state that may reference persistent Fabric geographic identities while retaining its own owner, rights, generation, and payload lifecycle.

Cross-boundary roads, water, buildings, and subscription objects retain one logical identity even when referenced or replicated through several partitions.

## Browser integrity boundary

Browser publication access requires Web Crypto SHA-256 capability. Kane Fabric fails before consuming substrate/publication bytes when the execution context cannot perform the required cryptographic verification. HTTPS is a normal way to obtain a secure browser context; the correctness requirement is the capability, not URL string inference.

## Dependency and licensing boundary

Kane Fabric-authored code remains under the root Unlicense.

Retained third-party project-controlled runtime/build/test/firmware implementations must be reviewed, pinned, and vendored according to `docs/DEPENDENCY_POLICY.md`. Standard browser APIs are contracts, not bundled implementations merely because Kane Fabric uses them.

Node.js and Chromium are development/acceptance tooling. ESP-IDF, if retained for Milestone 5 release, must be explicitly pinned, license-reviewed, and vendored according to project policy.

## Repository boundary

Large county databases, harvests, staging artifacts, rollback copies, render/substrate packages, MS4 proof bundles, and operational evidence remain outside Git under `/var/lib/kane-fabric`.

Git contains software, migrations, source/county contracts, tests, documentation, schemas, small deterministic manifests, and repeatable procedures required to reproduce those external artifacts.
