# Milestone 3 Handoff — Historical Closeout

## Status

Milestone 3 — Compile Shared Substrate — is **accepted** as of 2026-08-20.

This file is now a historical milestone handoff. The release record is:

```text
docs/MILESTONE_3_RELEASE.md
```

The current project checkpoint is `docs/CURRENT_STATE.json`. New work should not restart Milestone 3 discovery or implementation.

## Accepted release boundary

Milestone 3 established the durable public baseline geography publication:

```text
county-overview.json
roads-lod.kfs
water-lod.kfs
substrate-manifest.json
```

External consumers do not depend on the GeoPackage schema, migrations, CT102 paths, Python modules, source harvesting, comparison, reconciliation, or promotion internals.

The control-plane sequence remains:

```text
official geographic sources
  ↓
Kane Fabric authoritative control plane
  ↓
explicit accepted geographic state
  ↓
read-only deterministic compiler
  ↓
immutable four-file substrate publication
  ↓
browser / caches / mirrors / future edge nodes
```

Compilation never promotes geography.

## Authoritative Kane County database

```text
/var/lib/kane-fabric/database/kane-county-fabric.gpkg
SHA256  31e362b696a37f1b9c45ae355c5669511a3128c17a651108a62e20d1cedebd67
bytes   355180544
migrations 7
```

The historical donor-shaped database `/var/lib/kane-fabric/database/kane-county-reconstructed.gpkg` is not Milestone 3 authority.

## Publication identity

Substrate content SHA-256:

```text
fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc
```

Components:

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

Total publication size: `7201386` bytes.

## Road source-status correction

The accepted road release contains 27,675 features and accepted harvest metadata records 27,675 source objects.

A later live official inventory exposed 27,676 road object IDs, correctly producing `new_source_detected` because the upstream inventory changed.

The earlier statement that the accepted release deliberately dropped one of 27,676 source objects because of missing geometry is false and must not be repeated.

## Accepted Milestone 3 gates

```text
MS3-001  v1 contract                         accepted
MS3-002  county overview                     accepted
MS3-003  road LOD/container                  accepted
MS3-004  water LOD/container                 accepted
MS3-005  manifest                            accepted
MS3-006  package compiler/activation         accepted
MS3-007  deterministic real evidence         accepted
MS3-008  browser selective loader            accepted
MS3-009  real browser rendering              accepted
MS3-010  edge-compatibility proof            accepted
MS3-011  release closeout                    accepted
```

Final MS3-011 closeout marker:

```text
=== MS3-011 MILESTONE 3 CLOSEOUT PASSED ===
pct_exec_rc=0
```

Closeout candidate head:

```text
a3a24268f8bba6088206e63a420a214761c7c679
```

## Evidence

External evidence root:

```text
/var/lib/kane-fabric/render/ms3-evidence
```

Known accepted evidence identities:

```text
ms3-007-substrate-proof.json
8093011b62d169388cbe264bc7cb4b7b9903d56e2f768c0249dc26107ed7680c

ms3-008-browser-proof.json
42339593d8598dda52ec61356177837ce2a9152809b6620d62c510ca7d87fcd5

ms3-009-browser-render-proof.json
75c85fff2ba5e56616697b5f31c3442619943673c95e0ba44af0d1772d2e6cc5

ms3-009-browser-render.png
dd96e3e155391201073ffdd635653985f6d5be7c2ad149d6e37bb5414c32d151
```

Additional accepted evidence files:

```text
ms3-010-edge-compatibility-proof.json
ms3-011-release-proof.json
```

Their exact SHA-256 values are retained by the machine-generated external closeout evidence. They are not guessed into this handoff because the final pasted closeout excerpt contained only the success marker.

## Browser implementation boundary

The browser loader/renderer:

- consumes only the public four-file publication;
- uses no npm dependencies;
- selectively fetches `.kfs` prefix/index/chunk ranges;
- verifies selected bytes with WebCrypto SHA-256;
- decompresses zlib-wrapped DEFLATE with `DecompressionStream("deflate")`;
- renders county boundary, roads, and water with Canvas 2D;
- does not use application/subscription data.

MS3-009 real-browser acceptance rendered:

```text
non-white pixels  407773
road features      2862
water features     1
subscription data  false
```

## Edge boundary

MS3-010 proved the same browser access pattern through bounded HTTP range serving representative of the ESP32-S3 constraint.

It did **not** implement completed ESP-IDF firmware and did **not** freeze the final edge HTTP implementation. Those remain Milestone 5 work.

## Dependency / licensing boundary

The repository root Unlicense remains a hard invariant.

Node.js and Chromium were used as development-only acceptance runtimes and are recorded in `third_party/manifest.json` and observation records. The browser loader itself has no npm dependency graph.

Any third-party implementation retained in the final Kane Fabric build/runtime/toolchain remains subject to the vendoring policy in `docs/DEPENDENCY_POLICY.md`.

## Repository state boundary

Milestone 3 implementation and closeout were performed on:

```text
assistant/read-authority-boundary
```

No pull request, merge, or write to `main` is implied by this historical milestone acceptance. Repository publication remains a separate authorized action.

## Next development work

The next milestone is:

```text
Milestone 4 — Subscription contract
```

Do not reopen Milestone 3 implementation unless a regression, contract change, or explicit user instruction invalidates an accepted gate.
