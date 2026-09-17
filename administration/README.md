# Kane Fabric Administrative Infrastructure

This directory is the active home for administrative Civic Infrastructure work that is deliberately separate from physical edge firmware.

The governing boundary is `docs/ADMINISTRATIVE_EDGE_BOUNDARY.md`.

## Scope

Administrative infrastructure includes:

- county-wide accepted geography and the county web/map composition;
- category and object-class definitions;
- contracts that bind participant publications to accepted geography;
- visibility/classification semantics used by the web layer;
- conformance rules for independently operated county implementations;
- operator-facing documentation sufficient for another Illinois county to join the Civic Infrastructure without inheriting Kane County private operational state.

The ESP32-S3 is a bounded physical edge. It is not the county database, county web map, category authority, or contract authority.

## Current development target

The immediate target is to define the administrative contract needed for a bounded condominium publication to participate in the county view.

The first reference case is intentionally small enough to reason about concretely:

```text
county base geography
        +
condominium association
        +
unit-level participant data
        =
composed county web view
```

The contract must allow an association-sized edge publication to reference accepted county/building identities without carrying the full county substrate.

The administrative work must distinguish at least:

- county geographic identity;
- participating organization/association identity;
- unit or other participant object identity;
- category/schema identity;
- publication generation identity;
- visibility/classification semantics;
- physical edge identity, which is never any of the identities above.

## Infrastructure constraints

The work must preserve the anti-capture model:

- no required proprietary portal or exclusive hosted datastore;
- no subscription requirement for basic local custody/use;
- open, explicit publication contracts;
- replaceable physical edge and replaceable county operator implementation;
- participant data remains portable and independently retainable;
- online composition does not convert the web operator into the exclusive custodian of participant data;
- another county operator can conform without copying Kane County hostnames, database paths, private keys, or hardware identities.

## Relationship to Milestone 5

MS5-006 physical firmware acceptance is complete and recorded in `docs/CPE_ESP32_MS5_006_DEVICE_RUNTIME_ACCEPTANCE.md`.

The active MS5-007 integration work now depends on this administrative contract: the browser/Wiregate path must integrate a focused participant edge publication with the county web view. The ESP32-S3 is not required to serve the complete MS3 county substrate.

Later MS5-008 through MS5-012 lifecycle and closeout work remains pending, but it does not block administrative county/web/category/contract development.