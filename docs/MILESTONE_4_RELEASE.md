# Milestone 4 Release — Subscriptions + Geographic Scoping/Partition Identity

Release acceptance date: 2026-08-22

Status: **RELEASED ON `main`**

Accepted implementation head:

```text
9f6013d1b8b44998047f71e2b3f3e9c55c9ed298
```

This release record is a documentation closeout after the CT102 exit gate. The accepted implementation was already on `main`; no feature branch or pull request was required.

## Release definition

Milestone 4 establishes deterministic logical geographic partitions and independently versioned application subscriptions layered on the canonical Milestone 3 Kane County substrate.

The durable architectural progression is now:

```text
MS-3  canonical county substrate + selective chunks       RELEASED
MS-4  subscriptions + logical geographic partitions       RELEASED
MS-5  physical ESP32-S3 placement/storage/HTTP serving    NEXT
```

Milestone 4 does not create town/township geographic authorities, does not change accepted geography, and does not make a partition or subscription identity depend on a physical device.

## Authority boundary

The accepted geographic control-plane database remained:

```text
/var/lib/kane-fabric/database/kane-county-fabric.gpkg
SHA256  31e362b696a37f1b9c45ae355c5669511a3128c17a651108a62e20d1cedebd67
```

The accepted Milestone 3 substrate remained:

```text
substrate_content_sha256
fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc
```

MS4 compilation was read-only with respect to the authoritative GeoPackage and the accepted MS3 publication. The final exit proof verified that accepted authority was unchanged.

Buildings remain accepted Fabric geography but are deliberately outside the four-file MS3 substrate. MS4 subscription references to buildings are therefore validated against the accepted building release in the authoritative GeoPackage rather than incorrectly requiring a building entry in the MS3 substrate manifest.

## Implemented contract

### MS4-001 — partition descriptor and deterministic identity

Accepted. Logical partition identity is derived from a canonical normalized definition and is independent of labels and physical placement metadata.

The v1 partition key is:

```text
kfp1- + first 128 bits of the partition definition SHA-256
```

### MS4-002 — scope normalization and inclusion

Accepted. Whole-jurisdiction, bounded-region, administrative, and deterministic composite scopes are supported. WGS84 coordinates are normalized to fixed decimal text. Boundary-touching and boundary-crossing objects/chunks are included rather than destructively clipped.

### MS4-003 — substrate selection manifest

Accepted. A partition selection binds one logical partition to the canonical substrate content identity and exact selected substrate chunk/range references. The county-wide MS3 substrate remains canonical.

### MS4-004 — subscription manifest and generation identity

Accepted. Subscription generations are independently versioned and content-addressed. Application changes do not create new Fabric geographic identity.

### MS4-005 — geographic references and ownership/rights

Accepted. Subscription objects may reference persistent Fabric geographic identities with accepted-release lineage while application ownership, license/rights, and application payload state remain application-owned.

### MS4-006 — Condo proof subscription

Accepted. A deterministic Condo proof generation references one real accepted persistent Fabric building identity without reintroducing Kane Condo runtime ownership into Kane Fabric.

### MS4-007 — Industry / Mechanical Compiler proof subscription

Accepted. A synthetic Industry/Mechanical Compiler contract-shape generation references the same Fabric geographic identity while retaining independent application/domain ownership. This is a contract proof, not a claim that an external Mechanical Compiler service interface was integrated.

### MS4-008 — browser composition

Accepted in Node and real Chromium. The browser consumed the accepted MS3 substrate and both scoped subscription generations through the MS4 composition contract.

### MS4-009 — cross-boundary composition

Accepted. Two overlapping logical partitions produced four object appearances but only two unique subscription objects. Replication across partition boundaries preserved logical object identity.

### MS4-010 — edge-placement compatibility

Accepted. Two different physical placement descriptions produced the same logical placement identity. Device/node label, network address, and storage path are not part of the logical partition/subscription identity.

### MS4-011 — release evidence and closeout

Accepted. The final CT102 marker was:

```text
=== MS4 EXECUTION EXIT GATE PASSED ===
```

The durable release proof was then read back successfully with:

```text
release_evidence_readback=PASS
=== MS4 RELEASE IDENTITIES COMPLETE ===
```

## Accepted real proof identities

Proof bundle:

```text
/var/lib/kane-fabric/render/ms4-proof
```

Composition SHA-256:

```text
a58c8398248cee05b7baad9ae289fe0581bdb3624ce1aff3aa8a49721f92ee53
```

Bundle inventory SHA-256:

```text
1e109d4621ce738e3e35b93c23ecab0d5c9a0d4166aad5d72f4e2eff397ad0d3
```

Logical partitions:

```text
west
  partition_key     kfp1-489f4340fc2fa2652dfa5bf4eac4b0e1
  selection_sha256  2996001d7d55ee50522262048d467cbb4fedd5cb418656586fc13b62113cd8f1

east
  partition_key     kfp1-3047abaf4fef374f57fb59b9c76902f6
  selection_sha256  7bf705f5cee7749a29bc39ced9cb77d96ea0b88c00ba4f65dcb8d64c12a095ba
```

Subscription generations:

```text
condo
  generation_key  kfsg1-4804b03fc48ffb4b9882fdd71ce39689
  objects_sha256  bad11f7cb03b3ed1f73ed86defdd5c3b0e58d2d524747aa82bb292e184262dac

industry
  generation_key  kfsg1-f6efa4be24e65db0f6b78b99c3ec3a37
  objects_sha256  7832aba2497a24a0397bb78e54372b8804e1959202e23cc88833c05bcc4f3b2b
```

Logical edge-placement identity:

```text
51c07aead7369e5fbc94971b083afdc674ff67cd1bd40f5669cf1f54c36b3cff
```

## Accepted composition result

The final proof established:

```text
partition_count                    2
subscription_count                 2
object_appearances                 4
unique_objects                     2
cross_boundary_identity_preserved  true
physical_placement_independent     true
accepted_authority_unchanged       true
```

The accepted real browser runtime was:

```text
Chromium 151.0.7922.137 built on Debian GNU/Linux 12 (bookworm)
```

The browser proof rendered accepted substrate geometry and composed both independently versioned subscriptions through explicit logical partitions.

## Test evidence

The post-correction CT102 Milestone 4 repository suite passed before real proof compilation:

```text
Python contract tests  33 passed
Node browser tests       5 passed
failures                 0
```

The real proof then compiled against the authoritative GeoPackage and accepted MS3 package, the generated bundle validated, the Node composition probe passed, the real Chromium composition proof passed, and the accepted authority hashes remained unchanged.

## Durable evidence

Release evidence root:

```text
/var/lib/kane-fabric/render/ms4-evidence
```

Release proof:

```text
/var/lib/kane-fabric/render/ms4-evidence/ms4-011-release-proof.json
SHA256  3235cd4f7b7041138fe05708dbb077c07dc3ce8b8ec7a390141489460ac40634
```

The evidence root also contains the accepted Node composition result, browser composition result, request log, and Chromium version observation generated by the exit gate.

## Milestone 4 exit statement

Milestone 4 is accepted because Kane Fabric now has deterministic logical geographic partition identities, deterministic substrate-selection references, independently versioned Condo and Industry proof subscriptions, explicit application/geographic ownership boundaries, real browser composition of substrate plus multiple subscriptions, deterministic cross-boundary identity behavior, and physical-placement independence.

The logical contracts are now suitable inputs to Milestone 5. Milestone 5 owns actual ESP32-S3/ESP-IDF storage, HTTP serving, activation, recovery, networking, and device placement. It must map the already-released MS3/MS4 logical identities onto physical edge hardware without redesigning those identities.
