# Milestone 3 Release — Compile Shared Substrate

Release acceptance date: 2026-08-20

Status: **RELEASED ON `main`**

Repository publication: `assistant/read-authority-boundary` was fast-forward merged into `main` at `84293aeb381db596f4c3233473c350fda6c5426d` on 2026-08-20. No merge commit was required because the branch was 47 commits ahead and 0 behind.

## Release definition

Milestone 3 establishes the first deterministic Kane Fabric shared geographic substrate and proves that a normal browser can consume it without the authoritative GeoPackage, county refresh machinery, or application/subscription state.

The durable external publication is exactly:

```text
county-overview.json
roads-lod.kfs
water-lod.kfs
substrate-manifest.json
```

The authoritative GeoPackage remains an internal control-plane database and is not the external client contract.

## Authority boundary

Substrate compilation is read-only with respect to accepted geography.

The geographic lifecycle remains:

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
  → read-only substrate compilation
```

Candidate registration, source freshness, comparison, and compilation do not change accepted authority. Only explicit promotion changes accepted geographic state.

## Authoritative database

Accepted Kane County Fabric database:

```text
path    /var/lib/kane-fabric/database/kane-county-fabric.gpkg
bytes   355180544
SHA256  31e362b696a37f1b9c45ae355c5669511a3128c17a651108a62e20d1cedebd67
```

The database remained byte-identical through the accepted Milestone 3 real-environment proofs.

The historical donor-shaped database `/var/lib/kane-fabric/database/kane-county-reconstructed.gpkg` is not Milestone 3 authority.

## Accepted publication identity

Substrate content identity:

```text
fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc
```

Publication components:

```text
county-overview.json
  bytes   1670
  SHA256  f0995177625e28adc39e0ddd842ea22fbc1935239d6d1f7d54f377edde62e942

roads-lod.kfs
  bytes   4014272
  SHA256  4c897db58a55961d76e720d3905b57a76fe199f5396c876b57e56ecaeaaee4d2

water-lod.kfs
  bytes   3183647
  SHA256  dc4786b2904869fc5f910fa0d1b1a5767f1204fda99f34b2745f1ef7088f7f89

substrate-manifest.json
  bytes   1797
  SHA256  1143324ace2dd7c47ad5f79e0763fdf978be5447527095e9e6f96d46b3fd1d13
```

Total publication byte length:

```text
7201386
```

## Accepted source state

The substrate is bound to accepted Kane County geography:

```text
county-boundary    1
roads              27675
water-creeks       555
water-fox-river    1
```

Buildings remain accepted Fabric geography but are deliberately outside the v1 shared-substrate component set.

### Road source-status clarification

The accepted road release contains 27,675 features and its accepted harvest metadata records 27,675 source objects. The live official source later exposed 27,676 object IDs, which correctly caused `new_source_detected` source status.

Do not describe the accepted release as deliberately dropping a 27,676th missing-geometry object. That earlier explanation was disproven by the accepted harvest inventory.

## V1 container contract

Road and water containers use:

```text
8 bytes   magic/version
8 bytes   unsigned big-endian canonical-index byte length
N bytes   canonical UTF-8 JSON index
...       contiguous zlib-compressed canonical JSON chunks
```

Magic values:

```text
roads  KFSR001\n
water  KFSW001\n
```

The publication uses canonical JSON, zlib level 9 payloads, deterministic ordering, contiguous offsets, per-chunk compressed hashes, and canonical record hashes.

## Milestone work acceptance

### MS3-001 — v1 substrate contract

Accepted. Jurisdiction identity, component roles, canonical JSON, framing, hashes, compression, and substrate content identity were frozen.

### MS3-002 — county overview

Accepted. The deterministic overview is compiled from the exactly-one accepted county boundary and is independently browser-consumable.

### MS3-003 — road LOD

Accepted real CT102 proof:

```text
feature_count   27675
chunk_count     170
orientation     2862
context         12402
detail          27675
bytes           4014272
SHA256          4c897db58a55961d76e720d3905b57a76fe199f5396c876b57e56ecaeaaee4d2
```

Two independent real builds were byte-identical and the authoritative database was unchanged.

### MS3-004 — water LOD

Accepted real CT102 proof:

```text
feature_count   556
chunk_count     5
overview        1
context         145
detail          556
bytes           3183647
SHA256          dc4786b2904869fc5f910fa0d1b1a5767f1204fda99f34b2745f1ef7088f7f89
```

Two independent real builds were byte-identical and preserved coordinated Fox River/creek accepted lineage.

### MS3-005 — manifest

Accepted. The canonical manifest binds the four-component publication to one jurisdiction, the authoritative database audit identity, and the accepted source releases.

### MS3-006 — package compiler / activation

Accepted. Complete package builds were byte-identical, validation passed, activation recovery/rollback behavior was exercised, and no mixed-generation component set was accepted.

The implementation uses complete-directory rename/backup behavior; it does not claim a single-syscall directory exchange.

### MS3-007 — deterministic real evidence

Accepted evidence:

```text
/var/lib/kane-fabric/render/ms3-evidence/ms3-007-substrate-proof.json
SHA256  8093011b62d169388cbe264bc7cb4b7b9903d56e2f768c0249dc26107ed7680c
```

The evidence records two real byte-identical packages, exact content identity, expected component/chunk structure, and unchanged authoritative database identity.

### MS3-008 — browser selective loader

Accepted real compatibility evidence:

```text
/var/lib/kane-fabric/render/ms3-evidence/ms3-008-browser-proof.json
SHA256  42339593d8598dda52ec61356177837ce2a9152809b6620d62c510ca7d87fcd5
```

The loader uses no npm dependencies. It validates the manifest/overview, fetches only the fixed `.kfs` prefix, canonical index, and selected payload ranges, validates SHA-256 with WebCrypto, and uses `DecompressionStream("deflate")`.

Observed selective fractions in the accepted MS3-008 probe:

```text
roads  0.01685760207579357
water  0.017101770391001265
```

### MS3-009 — real browser rendering

Accepted real Chromium Canvas proof:

```text
/var/lib/kane-fabric/render/ms3-evidence/ms3-009-browser-render-proof.json
SHA256  75c85fff2ba5e56616697b5f31c3442619943673c95e0ba44af0d1772d2e6cc5
```

Observed acceptance facts:

```text
non-white canvas pixels   407773
road features rendered    2862
water features rendered   1
roads selected fraction   0.044927448862458745
water selected fraction   0.017101770391001265
subscription_data_used    false
```

Accepted screenshot:

```text
/var/lib/kane-fabric/render/ms3-evidence/ms3-009-browser-render.png
SHA256  dd96e3e155391201073ffdd635653985f6d5be7c2ad149d6e37bb5414c32d151
```

### MS3-010 — edge compatibility

Accepted. A real browser consumed the same substrate through the bounded reference range server. Every road/water access remained selective; no whole `.kfs` file residency was required by the serving pattern; server reads were bounded to 64 KiB per read/send step.

This is an edge-compatibility proof only. It does not claim completed ESP-IDF firmware or freeze the final Milestone 5 HTTP implementation.

Evidence path:

```text
/var/lib/kane-fabric/render/ms3-evidence/ms3-010-edge-compatibility-proof.json
```

Its exact SHA-256 is retained in the external MS3-011 release proof. It is intentionally not guessed into this repository record because the final command excerpt supplied to this development session contained only the successful closeout marker.

### MS3-011 — release closeout

Accepted on CT102 at candidate head:

```text
a3a24268f8bba6088206e63a420a214761c7c679
```

Final marker:

```text
=== MS3-011 MILESTONE 3 CLOSEOUT PASSED ===
pct_exec_rc=0
```

Release evidence path:

```text
/var/lib/kane-fabric/render/ms3-evidence/ms3-011-release-proof.json
```

The closeout compiler verifies the authoritative database SHA-256, exact four-file publication inventory and hashes, substrate content identity, accepted MS3-007/008/009 evidence identities, and MS3-010 contract semantics before producing the release proof.

## Browser / edge dependency boundary

The browser loader and renderer have no npm dependency graph.

Node.js and Chromium were used only as development/acceptance runtimes on CT102 and are recorded in `third_party/manifest.json` plus observation records. They are not runtime dependencies of the published substrate, browser code, or future edge node merely because they were used for testing.

The repository root Unlicense remains unchanged. Third-party software retained in the final Kane Fabric distribution remains subject to the project vendoring policy and its own notices/licenses.

## Milestone 3 exit statement

Milestone 3 is accepted because Kane Fabric can compile the accepted Kane County geographic state into a deterministic four-file publication, reproduce its byte identities, selectively read and validate its indexed compressed chunks, render county boundary/roads/water in a real browser without application subscription state, and serve the same browser access pattern with bounded reads representative of the ESP32-S3 edge constraint.

Completed ESP32-S3/ESP-IDF firmware remains a Milestone 5 responsibility.

The next development milestone is **Milestone 4 — Subscription contract**.
