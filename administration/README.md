# Kane Fabric Administrative Infrastructure

This directory is the active home for administrative Civic Infrastructure work that is deliberately separate from physical edge firmware.

The governing boundaries are:

- `docs/ADMINISTRATIVE_EDGE_BOUNDARY.md`
- `docs/BROWSER_FIRST_ONLINE_FIRST_DIRECTIVE.md`

## Scope

Administrative infrastructure includes:

- county-wide accepted geography and the county web/map composition;
- category and object-class definitions;
- contracts that bind participant publications to accepted geography;
- visibility/classification semantics used by the web layer;
- conformance rules for independently operated county implementations;
- operator-facing documentation sufficient for another Illinois county to join the Civic Infrastructure without inheriting Kane County private operational state.

The ESP32-S3 is a bounded physical edge. It is not the county database, county web map, category authority, or contract authority.

## Development order

The project remains **Browser-First**, but the active implementation order is now **Online-First**.

Browser-First means the browser is the durable human client and the browser-visible contracts remain platform-neutral. It does not require the disconnected/offline implementation to be built first.

The current order is:

```text
full online county interface
        ↓
county/category/participant contracts exercised in the real UI
        ↓
bounded participant-publication composition
        ↓
freeze shared browser modules/contracts
        ↓
reduce the same application to local/offline operation
```

The offline browser will be a reduction of the accepted online browser, not a separately designed application.

This ordering is explicitly intended to keep routine web development usable from ordinary Windows and Linux workstations while the complete administrative model is still being discovered.

## Current development target

The immediate target is the **full online Kane County administrative/browser interface** and the contracts needed for a bounded condominium publication to participate in it.

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

The online interface should be used to make these concepts concrete before the reduced offline browser or further ESP32 specialization is attempted.

## Infrastructure constraints

Online-First must not become SaaS-First. The work must preserve the anti-capture model:

- no required proprietary portal or exclusive hosted datastore;
- no subscription requirement for basic local custody/use;
- open, explicit publication contracts;
- replaceable physical edge and replaceable county operator implementation;
- participant data remains portable and independently retainable;
- online composition does not convert the web operator into the exclusive custodian of participant data;
- county, association, unit, category, and publication identities do not depend on one hosted account system;
- public/restricted/private visibility is contractual rather than merely a UI convention;
- another county operator can conform without copying Kane County hostnames, database paths, private keys, or hardware identities.

## Independent county operator target

Administrative development is not complete merely when Kane County renders correctly.

The contracts must be explicit enough that an independent operator can implement another Illinois county without needing Kane County's private operational state.

The future operator should need public/open project contracts, jurisdiction-specific source configuration, and its own deployment infrastructure—not Kane County hostnames, internal filesystem layout, private keys, or proprietary account state.

This requirement is why county categories, participant contracts, web composition, and operator conformance are administrative infrastructure rather than ESP32 firmware features.

## Relationship to Milestone 5

MS5-006 physical firmware acceptance is complete and recorded in `docs/CPE_ESP32_MS5_006_DEVICE_RUNTIME_ACCEPTANCE.md`.

The active MS5-007 integration work now depends on the administrative/web contract: the browser/Wiregate path must integrate a focused participant edge publication with the county web view. The ESP32-S3 is not required to serve the complete MS3 county substrate.

Later MS5-008 through MS5-012 lifecycle and closeout work remains pending, but it does not block online county/web/category/contract development.

Do not return to firmware merely because a web/category/contract question is unresolved. Return to the ESP32 only when the administrative/browser contracts expose a concrete edge requirement or when a later MS5 lifecycle gate is intentionally resumed.
