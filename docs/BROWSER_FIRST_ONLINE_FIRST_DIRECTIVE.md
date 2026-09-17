# Browser-First / Online-First Development Directive

## Status

Current development directive for the Kane Fabric human-facing interface and administrative web work.

This document defines implementation order. It does not replace the authority boundaries in `docs/ARCHITECTURE.md`, `docs/ADMINISTRATIVE_EDGE_BOUNDARY.md`, or the active Milestone 5 design.

## Browser-First remains the product directive

Kane Fabric remains **Browser-First**.

Browser-First means:

- the browser is the primary human client;
- browser-visible publication, identity, category, composition, verification, and interaction contracts are durable project interfaces;
- the system must not require a native Windows, Android, Linux, or Apple application merely to use the civic infrastructure;
- physical edge implementations remain replaceable behind browser/publication contracts.

Browser-First does **not** require the disconnected/offline browser form to be implemented before the online browser form.

## Online-First is the implementation order

The current implementation order is **Online-First**.

Kane Fabric will first build the full-featured online county browser/interface, then reduce that accepted browser application into a local/offline form using the same core modules and contracts.

Reference order:

```text
accepted county geography
        +
administrative categories/contracts
        +
full online county browser/interface
        +
bounded participant-publication composition
        ↓
freeze shared browser-visible contracts and reusable modules
        ↓
remove network-only conveniences
        ↓
local/offline browser form
```

The offline browser is therefore a **reduction of the online browser**, not an independently designed application.

## Why this order is deliberate

The online interface is the better place to discover and stabilize the complete administrative model:

- county map composition;
- categories and object classes;
- condominium association and unit relationships;
- public/restricted/private visibility semantics;
- participant publication discovery and composition;
- operator-facing administrative workflows;
- interoperability requirements needed before an independent operator can implement another Illinois county.

Developing the richer interface first also keeps routine browser development accessible from ordinary Windows or Linux workstations without making the development sequence depend on repeated offline-environment switching.

Offline constraints remain important acceptance constraints, but they should not prematurely define or narrow the administrative data model.

## One application architecture

Online-first must not produce a SaaS-only application and offline work must not become a rewrite.

The browser architecture must preserve these rules:

1. **Shared core modules.** Rendering, map composition, category interpretation, publication validation, identity handling, and interaction logic are shared between online and offline forms.
2. **Source adapters.** County publications and participant publications may come from an online HTTP origin, Wiregate, a bounded edge, local files/storage, or another conforming source without changing their logical identities.
3. **Subtractive offline reduction.** Offline/local operation removes network-dependent conveniences; it does not redefine the publication or category contracts.
4. **Portable data custody.** The online operator is not the exclusive datastore or logical owner of participant data.
5. **No account-defined civic identity.** County, association, unit, category, publication-generation, and geographic identities do not depend on one hosted account system.
6. **Visibility is contractual.** Public/restricted/private classification is represented by portable administrative/publication contracts, not merely by hiding UI controls.
7. **Edge neutrality.** ESP32-S3 remains one bounded edge implementation. The browser contract does not depend on ESP32-specific APIs or hardware identity.

## Infrastructure, not SaaS

Online-First changes development order, not the anti-capture architecture.

The full online interface may provide useful network services such as:

- county-wide aggregation and discovery;
- current participant availability;
- richer search and navigation;
- administrative update workflows;
- authentication needed to obtain restricted material;
- live status that cannot exist when disconnected.

Those services must remain conveniences around portable civic contracts. Loss of the hosted interface must not erase the participant's independently retained publication or redefine its civic identity.

A conforming alternate county operator must be able to implement the same public contracts without inheriting Kane County hostnames, filesystem paths, private keys, database schema, accounts, or proprietary service state.

## Current implementation target

The active work is the **full online Kane County administrative/browser interface**.

Before returning to ESP32 specialization or building the reduced offline browser, this work should make the following concrete and testable:

- county-facing category/object model;
- association identity and unit identity/reference semantics;
- participant publication manifest/generation contract;
- references to accepted county/building identities;
- public/restricted/private visibility classification;
- online composition of participant publications into the county map;
- source-neutral browser loaders/adapters;
- cross-county/operator conformance requirements.

The first concrete participant reference case remains a condominium association with unit-level data.

## Offline acceptance later

When the online interface and contracts are stable enough, the offline/local browser form must prove that the same core application can operate with network-only capabilities removed.

That later acceptance should demonstrate at least:

- the same logical identities and category semantics;
- the same immutable publication validation;
- the same participant/county composition rules for locally available material;
- no dependency on a proprietary account or hosted datastore for locally retained data;
- no second divergent application schema.

Offline capability remains a required property of the Civic Infrastructure direction. It is simply no longer the first implementation surface.
