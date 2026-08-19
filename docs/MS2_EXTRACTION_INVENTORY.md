# Milestone 2 Database Extraction Inventory

Status: active MS-2 engineering record

Source oracle: `git64bit/kane-condo` tag `0.4`, commit `63582fb05c509d53870835d25612c87b56800d10`.

Entry Gate 001 is complete. The reconstructed Kane County state has been prepared, semantically compared with the immutable Kane Condo promoted reference, atomically promoted, and explicitly rolled back with retained audit evidence. MS-2 now moves from reconstruction proof to behavior-preserving extraction.

## Extraction rule

Kane Fabric owns county-scale geographic state and the mechanisms required to acquire, validate, compare, reconcile, promote, roll back, and preserve durable geographic references. Application classifications and business semantics do not belong in the geographic core.

The donor implementation is classified below before renaming or refactoring. A module marked **transitional compatibility** contains behavior that must survive extraction, but its current Kane Condo names or application coupling must not become the final Fabric contract.

## Geographic core

| Donor module | Fabric responsibility |
| --- | --- |
| `kane_geometry.py` | Strict EPSG:4326 normalization plus GeoPackage/WKB encode/decode support. Isolated first extraction target. |
| `kane_provenance.py` | County, agency, dataset, harvest, source-file, and release lineage. |
| `kane_boundary.py` | County-boundary storage, validation, bounds, and lineage. |
| `kane_map_layers.py` | Road and water geometry storage and validation. |
| `kane_buildings.py` | Official building footprint storage, identity, geometry, and lineage. |
| `kane_source_profiles.py` | Source-contract validation and deterministic profile registry mechanics. Kane-specific contracts remain configuration, not hard-coded architecture. |
| `kane_source_status.py` | Read-only source freshness/update detection against accepted releases. |
| `kane_building_candidate.py` | Complete staged building acquisition, offline validation, and provenance-only candidate registration. |
| `kane_road_candidate.py` | Complete road acquisition including declared null-geometry exclusion evidence. |
| `kane_water_candidate.py` | Coordinated water-context acquisition and atomic candidate registration. |
| `kane_boundary_candidate.py` | Boundary acquisition with county identity and gross-bounds guards. |
| `kane_candidate_compare.py` | Offline deterministic accepted-versus-candidate comparison. |

## Transitional compatibility

| Donor module | Why transitional | Required destination |
| --- | --- | --- |
| `kane_db.py` | GeoPackage/migration engine is core, but the donor validator requires Condo classification tables and Kane Condo identifiers. | Split Fabric geographic schema requirements from application schema requirements. |
| `kane_project_buildings.py` | Durable building identity and source mappings are geographic-core concepts, but donor names use `project_building`, `kcb-*`, and Kane Condo identifiers. | Preserve identity behavior while defining application-neutral geographic building identity names/contracts. |
| `kane_building_reconcile.py` | Reconciliation and identity continuity are core, but the donor directly imports classification logic and proves classification preservation. | Preserve geographic reconciliation behavior; move application-state preservation behind an explicit compatibility/reference boundary. |
| `kane_promotion.py` | Atomic promotion/rollback is core, but snapshots and validation directly include Condo classification tables. | Preserve exact promotion safety semantics while removing classifications as a prerequisite for Fabric geographic operation. |
| `kane_seed_import.py` | Verified seed import is useful for reconstruction/bootstrap, but donor identity and schema assumptions are Kane Condo-specific. | Keep as bootstrap/reconstruction compatibility until Fabric-owned migrations and seed contract replace it. |

## Application-specific

| Donor module | Ownership |
| --- | --- |
| `kane_classifications.py` | Kane Condo/application layer. It hard-codes `unclassified`, `other`, `condominium`, and `apartments` plus classification/correction/undo history. It must not be required for Kane Fabric geographic operation. |

The same boundary applies to migration `0007_classification_history.sql`: it is application-specific. Migration `0006_project_building_identity.sql` contains a geographic identity concept but requires neutral naming/ownership. Migration `0008_refresh_promotion.sql` is geographic-core behavior with compatibility naming to be addressed during extraction.

## Initial Fabric naming direction

The extraction will initially preserve the donor `database/` layout to minimize behavioral change while replacing Kane Condo ownership names at module boundaries.

Internal Python modules use the `kane_fabric_*` prefix. Shell entry points, once introduced, use `kane-fabric-*`. Large operational data remains outside Git under `/var/lib/kane-fabric/`.

The first extracted module is therefore:

```text
database/tools/kane_fabric_geometry.py
```

It is intentionally copied behavior-first from donor `kane_geometry.py`; only ownership wording changes in the first extraction. Refactoring is deferred until regression coverage exists under Kane Fabric entry points.

## Extraction order

1. Isolated geometry support and direct tests.
2. Fabric-owned GeoPackage foundation and migration split.
3. Administrative provenance.
4. Boundary, roads/water, and official-building storage.
5. Generic source profile schema and Kane County profiles.
6. Candidate acquisition/registration.
7. Deterministic comparison.
8. Durable geographic building identity and reconciliation.
9. Atomic promotion/rollback without classification dependency.
10. Reproduce MS-1 deterministic reconstruction tests through Kane Fabric entry points.
11. Retain Kane Condo `0.4` only as a regression oracle, not a runtime dependency.

## Non-goals for this extraction

- No redesign of the proven candidate lifecycle.
- No PostgreSQL/PostGIS introduction.
- No Docker requirement.
- No application classification model in the Fabric core.
- No Mechanical Compiler database coupling.
- No large GeoPackages, harvests, rollback databases, or staging evidence in Git.
