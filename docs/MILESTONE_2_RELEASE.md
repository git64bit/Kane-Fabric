# Milestone 2 Release — Kane Fabric Geographic Core Extraction

Release date: 2026-08-20

Status: **Released**

## Release definition

Milestone 2 extracts the reusable Kane Fabric county-geography core from the frozen Kane Condo `0.4` implementation while preserving the deterministic reconstruction, comparison, reconciliation, promotion, and rollback behavior proven during Milestone 1 and Entry Gate 001.

The milestone closes with Kane Fabric-owned migrations, source contracts, database and storage modules, candidate engines, deterministic comparison, durable geographic building identity, reconciliation, promotion/rollback, and verified seed bootstrap. Kane Condo `0.4` remains historical evidence and a regression oracle only; it is not a runtime dependency of the Fabric geographic core.

## Entry Gate 001

The carried promotion/rollback proof from Milestone 1 was completed before behavior-changing extraction proceeded.

Accepted proof included:

- deterministic promotion preparation and validation;
- semantic equivalence with the historical promoted oracle;
- atomic activation;
- automatic recovery after injected post-verification failure;
- explicit rollback to the prior accepted release set;
- retained rollback evidence.

Gate 001 is closed and is not rerun as part of this release.

## Fabric-owned geographic core

Milestone 2 now owns the following implementation under Kane Fabric names and paths:

- GeoPackage database initialization, migrations, validation, and inspection;
- EPSG:4326 geometry normalization and GeoPackage/WKB encoding;
- administrative provenance and release lineage;
- county-boundary storage;
- roads and water storage;
- official-building storage;
- durable geographic building identities and source mappings;
- source-profile registry and source-status inspection;
- building, road, coordinated-water, and boundary candidate acquisition/registration;
- deterministic accepted-versus-candidate comparison;
- building reconciliation;
- atomic promotion and rollback;
- verified import from the immutable Kane County seed.

The obsolete transitional donor compatibility shim was removed before release.

## Application ownership boundary

The Fabric geographic core does not require Kane Condo classification tables or classification semantics.

The release intentionally excludes application ownership of:

- `building_classification_current`;
- `building_classification_event`;
- Condo classification values such as `unclassified`, `other`, `condominium`, and `apartments`.

Application tables may coexist with Fabric state, but they are not required for geographic-core validation or operation.

## Native regression suite

Before the historical closeout replay, the Kane Fabric database suite passed with no donor-runtime test guards:

```text
16 tests passed
0 failures
```

The suite covers:

- Fabric database foundation and migration identity;
- native candidate registration and deterministic comparison;
- native reconciliation without classification tables;
- native atomic promotion, manual rollback, and automatic rollback after injected verification failure;
- native provenance/boundary/map/building storage entry points;
- geometry behavior.

## Historical MS-1 evidence closeout

The decisive closeout replay was executed from the immutable Milestone 1 Kane County evidence through the native Kane Fabric core.

Closeout workspace:

```text
/var/lib/kane-fabric/staging/ms2-closeout-074dc07cd572
```

Closeout report:

```text
/var/lib/kane-fabric/staging/ms2-closeout-074dc07cd572/ms2-closeout.json
```

Closeout report SHA-256:

```text
fee3194b432566fc0cf4af09b8e9e80eb6efd9945e0894e96ecbb2aa22ce9f4c
```

Result:

```text
valid  true
```

### Immutable evidence preservation

Seed before and after:

```text
7fe2198b00b2d0dee9470eda3864b43b6f7b3b0ff3b236ce7c579ddc077f389a
```

Historical promoted oracle before and after:

```text
164200d4d7262874dcc03239c8258446a4d7bb81ce84daf46dc4937d6c97fe86
```

Both remained unchanged.

### Fabric seed bootstrap

Native Fabric seed database:

```text
SHA256  31e362b696a37f1b9c45ae355c5669511a3128c17a651108a62e20d1cedebd67
```

Imported geographic totals:

```text
boundary   1
buildings  208324
roads      27675
water      556
```

Durable geographic building identities:

```text
project buildings             208324
confirmed initial mappings    208324
```

Application tables present:

```text
none
```

### Source-profile registry

The Fabric-owned registry matched the Milestone 1 identity exactly:

```text
e95c9d0486f65035146cb0a2a9580e4148c853a78c4f9e44e2420f59ef654e12
```

### Deterministic comparison replay

The native Fabric comparison results matched every Milestone 1 oracle hash exactly:

```text
buildings
23916019e762740a4ebe773cdfab916ace4c4d505521407fd6c513b382108d28

county boundary
6ffa83d940347e7ffeeb10e3c631625af75de7f12ef95729ab1ebb75b5879f95

roads
7b3bf1ddaef1a40948d57edf0c465199316216510e0a1a78cb2dc0a552f59d3b

water context
a1b0ac3f1504e4e6de199e694f794c83643f02139ed37f9a38c0d65d638f88f3
```

The known roads contract remained intact: 27,675 retained road features with the one declared missing-geometry exclusion preserved.

### Geographic reconciliation replay

Native reconciliation result:

```text
reconciliation key       kane-buildings-reconciliation-20250730-94704f9c0869
reconciliation SHA256    498ee2fa00f7767d9e83437dca6dd330ffd555ca7122c8d5c06ecc36c85991a7
candidate DB SHA256      9236c0d684965c810a4e2fdfc4ac6771471ef234e623e9a7b636a12f68548926
mapped sources           208324
unmapped sources         0
ambiguities              0
continuations            208324
geometry redraws         0
replacements             0
additions                0
disappearances           0
ready for promotion      true
```

No new geographic building identities were required.

### Native promotion and rollback replay

Promotion:

```text
promotion key          kane-fabric-promotion-843b52cd0a19
promotion plan SHA256  843b52cd0a1926bd4ce74c57e889f5ec5a7e726fcac38dce6df6939d82e4509b
promoted DB SHA256     736ab4d1ff357675af9b1e2e358aae12afb617bf7000499171e1f83759e48f98
```

Promoted accepted releases:

```text
buildings          kane-buildings-candidate-20250730-608ac1b48564
county-boundary    kane-county-boundary-candidate-20230509-ecc3b0990d4c
roads              kane-roads-candidate-20250730-c83a588170f3
water-creeks       kane-water-creeks-candidate-20250717-52b859183416
water-fox-river    kane-water-fox-river-candidate-20250717-5efc00d4dfe0
```

Explicit rollback restored the prior accepted releases:

```text
buildings          kane-buildings-20250730-086f09eba5ad
county-boundary    kane-county-boundary-20230509-73cb32426b22
roads              kane-roads-20250730-028e3c1dc7a6
water-creeks       kane-water-creeks-20250717-249c70f01dbc
water-fox-river    kane-water-fox-river-20250717-905d93f928d2
```

Manual rollback proof passed.

## Runtime independence proof

The closeout runtime dependency scan reported:

```text
forbidden_hits  {}
```

The scan covers transitional donor-runtime markers including the removed compatibility module, donor loader calls, donor-tools environment dependency, and the frozen Kane Condo reconstruction-code path.

The frozen Kane Condo `0.4` checkout remains historical evidence only.

## Milestone 2 exit statement

Milestone 2 is released because Kane Fabric can initialize and refresh Kane County through Fabric-owned geographic contracts and entry points while reproducing the exact Milestone 1 deterministic comparison results, preserving durable geographic identity, and proving promotion/rollback safety without requiring Kane Condo application classifications or the historical Kane Condo runtime.

The next milestone is **Milestone 3 — Compile shared substrate**.
