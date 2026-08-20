# Milestone 2 Database Extraction Inventory

Status: **complete — Milestone 2 released 2026-08-20**

Source oracle: `git64bit/kane-condo` tag `0.4`, commit `63582fb05c509d53870835d25612c87b56800d10`.

Release record: `docs/MILESTONE_2_RELEASE.md`

Entry Gate 001 is complete. The reconstructed Kane County state was prepared, semantically compared with the immutable Kane Condo promoted reference, atomically promoted, and explicitly rolled back with retained audit evidence before behavior-changing extraction proceeded.

## Extraction rule

Kane Fabric owns county-scale geographic state and the mechanisms required to acquire, validate, compare, reconcile, promote, roll back, bootstrap, and preserve durable geographic references. Application classifications and business semantics do not belong in the geographic core.

Milestone 2 followed a behavior-preserving extraction strategy: proven donor algorithms were first isolated behind Fabric entry points, then copied into Fabric-owned modules, then the donor runtime compatibility layer was removed. The final historical replay reproduced the Milestone 1 deterministic evidence through native Fabric code.

## Final geographic-core ownership

| Historical donor responsibility | Fabric-owned implementation |
| --- | --- |
| `kane_geometry.py` | `database/tools/kane_fabric_geometry.py` |
| `kane_db.py` | `database/tools/kane_fabric_db.py` plus Fabric migrations |
| `kane_provenance.py` | `database/tools/kane_fabric_provenance.py` |
| `kane_boundary.py` | `database/tools/kane_fabric_boundary.py` |
| `kane_map_layers.py` | `database/tools/kane_fabric_map_layers.py` |
| `kane_buildings.py` | `database/tools/kane_fabric_buildings.py` |
| `kane_source_profiles.py` | `database/tools/kane_fabric_source_profiles.py` plus `database/source-profiles/` |
| `kane_source_status.py` | `database/tools/kane_fabric_source_status.py` |
| `kane_building_candidate.py` | `database/tools/kane_fabric_building_candidate.py` |
| `kane_road_candidate.py` | `database/tools/kane_fabric_road_candidate.py` |
| `kane_water_candidate.py` | `database/tools/kane_fabric_water_candidate.py` |
| `kane_boundary_candidate.py` | `database/tools/kane_fabric_boundary_candidate.py` |
| `kane_candidate_compare.py` | `database/tools/kane_fabric_candidate_compare.py` |
| `kane_project_buildings.py` | `database/tools/kane_fabric_project_buildings.py` |
| `kane_building_reconcile.py` | `database/tools/kane_fabric_building_reconcile.py` |
| `kane_promotion.py` | `database/tools/kane_fabric_promotion.py` |
| `kane_seed_import.py` | `database/tools/kane_fabric_seed_import.py` plus Fabric-owned seed contract |

The transitional `database/tools/kane_fabric_compat.py` shim was deleted before release.

## Resolved transitional items

### Database and migrations

The donor database validator required Condo classification tables and Kane Condo identifiers. Fabric now owns its migration ledger, GeoPackage identifiers, required geographic tables, validation, and initialization. Application tables are optional and are not part of core validity.

### Durable building identity

The deterministic identity algorithm and mapping lifecycle were retained as geographic behavior. Fabric owns the durable building identity implementation and GeoPackage registrations. The existing physical `project_building` and `project_building_source_mapping` table names remain transitional naming debt only; their runtime ownership is Fabric and they do not imply application-state ownership.

### Reconciliation

Geographic reconciliation is Fabric-owned. Continuation, reappearance, exact-geometry replacement, split/merge ambiguity detection, lifecycle updates, deterministic report hashing, and mapping completeness checks remain intact. Condo classification tables are not required.

### Promotion and rollback

Atomic promotion and rollback are Fabric-owned. The proven backup, SHA recheck, atomic `os.replace`, directory fsync, post-verification rollback, retained promoted-state copy, and rollback receipts remain intact. Application classifications are not required for promotion validity.

### Verified seed/bootstrap import

Fabric owns verified import from the immutable Kane County seed using the frozen seed contract. The importer copies only accepted geographic/provenance state into a freshly initialized Fabric database, seeds durable geographic building identities, verifies the donor seed hash remains unchanged, and requires no application classification tables.

## Application-specific ownership

| Historical donor module | Ownership |
| --- | --- |
| `kane_classifications.py` | Kane Condo/application layer only. It hard-codes `unclassified`, `other`, `condominium`, and `apartments` plus classification/correction/undo history. It is not required by the Fabric geographic core. |

The same boundary applies to donor classification migrations and any future subscription-specific business state. Mechanical Compiler remains a separate application and future Industry subscription use case.

## Fabric naming and layout

Internal Python modules use the `kane_fabric_*` prefix. Shell entry points use `kane-fabric-*`. Large operational data, GeoPackages, candidate evidence, reconciliation artifacts, promotion artifacts, and rollback evidence remain outside Git under `/var/lib/kane-fabric/`.

Fabric-owned Kane County source contracts live under:

```text
database/source-profiles/
```

The source-profile registry identity reproduced Milestone 1 exactly:

```text
e95c9d0486f65035146cb0a2a9580e4148c853a78c4f9e44e2420f59ef654e12
```

## Completed extraction order

1. Isolated geometry support and direct tests — complete.
2. Fabric-owned GeoPackage foundation and migration split — complete.
3. Administrative provenance — complete.
4. Boundary, roads/water, and official-building storage — complete.
5. Generic source profile schema and Kane County profiles — complete.
6. Candidate acquisition/registration — complete.
7. Deterministic comparison — complete.
8. Durable geographic building identity and reconciliation — complete.
9. Atomic promotion/rollback without classification dependency — complete.
10. Reproduce MS-1 deterministic reconstruction evidence through Kane Fabric entry points — complete.
11. Retain Kane Condo `0.4` only as a regression oracle, not a runtime dependency — complete.
12. Verified Kane County seed/bootstrap import under Fabric ownership — complete.

## Final closeout evidence

The historical closeout replay produced:

```text
valid                     true
closeout SHA256           fee3194b432566fc0cf4af09b8e9e80eb6efd9945e0894e96ecbb2aa22ce9f4c
runtime forbidden hits    {}
```

It reproduced the exact Milestone 1 comparison hashes for buildings, boundary, roads, and coordinated water; mapped all 208,324 building identities with zero ambiguity and zero unmapped sources; promoted the five-dataset candidate set; explicitly rolled back to the prior accepted set; and left both the immutable seed and historical promoted oracle byte-identical.

## Non-goals preserved

- No redesign of the proven candidate lifecycle.
- No PostgreSQL/PostGIS introduction.
- No Docker requirement.
- No application classification model in the Fabric core.
- No Mechanical Compiler database coupling.
- No large GeoPackages, harvests, rollback databases, or staging evidence in Git.
