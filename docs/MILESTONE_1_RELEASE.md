# Milestone 1 Release — Kane County Reconstruction Proof

Release date: 2026-08-18

Status: **Released**

## Release definition

Milestone 1 proves that the Kane County authoritative geographic database pipeline can be reconstructed on a clean, conformant Kane Fabric node from declared software, immutable evidence, and versioned contracts rather than from hidden orchestrator state.

This release freezes the reconstruction proof through deterministic project-building reconciliation on CT102.

At release, the originally planned promotion/rollback replay had **not** been executed against the reconstructed CT102 state. Rather than claim an unperformed test, that work is carried forward as the mandatory Milestone 2 entry gate. The original Milestone 1 Batch 009 intent is therefore preserved, but its execution belongs to Milestone 2.

Milestone 1 does **not** claim that the reconstructed candidate was promoted into the active CT102 database.

## Accepted reconstruction chain

The following sequence was independently reproduced on CT102:

1. host and Fabric-specific environment acceptance;
2. immutable reconstruction evidence contract;
3. exact Kane Condo `0.4` historical software checkout and test suite;
4. read-only validation of the accepted historical reference database and current official source status;
5. fresh working database creation from the immutable donor seed;
6. staged candidate validation and registration for buildings, roads, coordinated water, and county boundary;
7. deterministic accepted-versus-candidate comparison replay;
8. project-building identity reconciliation on an external candidate database.

The active working database remained separate from immutable reference evidence and from the external reconciliation candidate.

## Infrastructure acceptance

Host-level conformance is owned by `srv-b`, not by Kane Fabric.

Accepted host result on 2026-08-18:

```text
scope      srv-b, CT 100, CT 101, CT 102
result     62 passed, 0 failed, 3 informational
```

CT102 is the Kane Fabric node. Kane Fabric-specific requirements are additive to the host standard and do not redefine it.

## Historical software reproducibility

Historical source:

```text
Kane Condo tag:       0.4
Kane Condo commit:    63582fb05c509d53870835d25612c87b56800d10
```

On CT102:

```text
374 tests passed
historical checkout clean
systemd running
0 failed units
```

## Immutable evidence identities

Original donor seed:

```text
Path:    /var/lib/kane-fabric/seed/kane-county.gpkg
Size:    324886528 bytes
SHA256:  7fe2198b00b2d0dee9470eda3864b43b6f7b3b0ff3b236ce7c579ddc077f389a
```

Historical promoted reference:

```text
Size:    649027584 bytes
SHA256:  164200d4d7262874dcc03239c8258446a4d7bb81ce84daf46dc4937d6c97fe86
```

Source-profile registry:

```text
Profiles: 5
SHA256:   e95c9d0486f65035146cb0a2a9580e4148c853a78c4f9e44e2420f59ef654e12
```

The historical reference remained byte-identical during read-only validation.

## Source-status acceptance

All five official source profiles reported `Up to date` from CT102 during Batch 004:

- county boundary;
- buildings;
- roads;
- creeks;
- Fox River.

The road source preserves the known inventory distinction of 27,676 source object IDs and 27,675 retained features because one source object is excluded by the declared missing-geometry policy.

## Fresh working database

A new active working database was constructed from the immutable donor rather than copied from the historical promoted database.

After all candidate registrations and before reconciliation/promotion:

```text
Path:    /var/lib/kane-fabric/database/kane-county-reconstructed.gpkg
Size:    355217408 bytes
SHA256:  ff67edcb0a732d87f3dc3bb3cf7fda91a03fea4ef8e16fb527f88283894c0a97
```

At the end of candidate replay it contained exactly one accepted and one candidate release for each dataset:

- buildings;
- county-boundary;
- roads;
- water-creeks;
- water-fox-river.

Candidate registration did not promote candidate geography.

## Deterministic comparison proof

Two fresh CT102 comparison runs were byte-for-byte repeatable and matched the historical Batch 022 comparison artifacts exactly.

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

Comparison conclusions:

- county boundary: 1 unchanged;
- buildings: 208,324 unchanged;
- roads: 27,675 unchanged retained features;
- creeks: 555 unchanged;
- Fox River: 1 unchanged.

The active database remained byte-identical during comparison.

## Reconciliation proof

A new external building reconciliation candidate was constructed and validated on CT102:

```text
Reconciliation key:
kane-buildings-reconciliation-20250730-2bfb38f11c7d

Directory:
/var/lib/kane-fabric/staging/reconciliation/kane-buildings-reconciliation-20250730-2bfb38f11c7d

Candidate database SHA256:
9e59c2ad2bd6d6962894faebd98ffc31620b48f711b091f0c376e2707c488ae9

Reconciliation SHA256:
1d81b3287cee5c0ed47f6aa5092d8dee2b7aab382095749494f630f601a06a62
```

Accepted reconciliation result:

```text
continuation mappings      208324
geometry redraws                 0
replacements                      0
additions                         0
disappearances                    0
ambiguities                       0
unmapped candidate sources        0
new project buildings             0
classification changes            0
ready_for_promotion            true
```

Project-building identity and state hashes were identical before and after. Classification current/history snapshots were also identical before and after.

## Frozen operational rules

The following rules are part of the reconstruction evidence and carry into Milestone 2:

- the immutable seed is not modified;
- historical reconstruction evidence remains read-only;
- active Fabric state is not replaced by the historical promoted database;
- large operational geographic artifacts remain outside Git;
- host conformance belongs to the host executable baseline;
- `nesting=1` is a shared srv-b Debian 12 unprivileged-LXC requirement;
- `keyctl=1` is workload-specific, not a universal Kane Fabric requirement;
- containers on srv-b do not originate mail;
- cross-machine large-file transfer uses Webmin tarball upload/download plus local SHA verification, not SCP;
- shell strict mode must be wrapped in a subshell when commands are supplied for an interactive root session;
- Mechanical Compiler remains a separate application and authoritative application-state owner; no current interface is assumed.

## Milestone 1 exit statement

Milestone 1 is released because Kane County has been independently reconstructed from declared inputs through deterministic comparison and project-identity reconciliation on CT102.

The remaining promotion/rollback proof is intentionally visible, not hidden: it is Milestone 2 Entry Gate 001 and must pass before geographic-core extraction changes authoritative database behavior.
