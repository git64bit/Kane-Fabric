# Kane Fabric Web Application

This directory is the human-facing Kane Fabric browser application workstream defined by `docs/WEB_APPLICATION_DESIGN.md`.

It is distinct from the historical proof harnesses under `substrate/browser/` and `ms4/browser/`. Those accepted verification/rendering modules remain the foundation and are reused rather than copied or weakened.

The active administrative/edge boundary is `docs/ADMINISTRATIVE_EDGE_BOUNDARY.md`. The current administrative workstream is `administration/README.md`. The active development-order directive is `docs/BROWSER_FIRST_ONLINE_FIRST_DIRECTIVE.md`.

## Development order

Kane Fabric remains **Browser-First**, but implementation is now **Online-First**.

The current target is the full online Kane County browser/interface. The reduced offline/local browser will be derived later from the same application architecture by removing or substituting network-only conveniences.

Do not create a separate offline application or a second civic schema.

Shared browser logic must remain reusable across both forms:

- publication validation;
- county/participant composition;
- category interpretation;
- logical identity handling;
- visibility/classification semantics;
- rendering and interaction.

Source acquisition belongs behind adapters so the same publication can come from the online administrative origin, Wiregate, a participant edge, a development server, or local/offline storage without changing its identity.

## Accepted foundation

WEB-001 established the dependency-free application shell and platform-neutral artifact-source configuration.

WEB-002 established the verified user-facing composition vertical slice against accepted MS3/MS4 artifacts in real Chromium.

WEB-003 established browser-side navigation, independent substrate/subscription visibility, and inspection of verified subscription objects without changing Fabric identity or the browser-to-edge wire contract.

WEB-004 made verification, failure, connectivity, and recovery state explicit to the user.

WEB-005 completed real-browser acceptance and the original edge-requirements reassessment.

Those gates remain accepted. The return to web development does not reopen them.

## Active online administrative integration

The next browser work is not "put the county map on the ESP32" and it is not "build the offline page first."

The county base geography remains an administrative publication. The online browser must first learn to compose that county view with bounded participant publications supplied under explicit administrative contracts.

Reference direction:

```text
accepted county publication
        +
bounded participant publication
        |
        +-- association data
        +-- unit data
        +-- category assignments
        +-- visibility/classification metadata
        =
full online county-facing web view
```

A participant publication may arrive through an ESP32-S3 edge, another edge platform, or a software source. The web application must remain platform-neutral.

The immediate contract work must establish how the browser recognizes and composes:

- county geographic identity;
- participating organization/association identity;
- unit or other participant-object identity;
- category/schema identity;
- participant publication generation identity;
- references from participant objects to accepted county/building identities;
- public/restricted/private classification semantics.

The browser application does not make the ESP32 a person/account service. Human authentication/authorization, when required by a visibility class, remains above the physical edge firmware boundary.

## Online features versus civic authority

The online reference interface may use conveniences that have no disconnected equivalent, such as county-wide discovery, current source availability, richer search, administrative workflows, aggregation, and authentication for restricted content.

Those capabilities must not become:

- civic identity;
- exclusive participant-data custody;
- a proprietary account prerequisite for locally retained civic data;
- a Kane-specific requirement that prevents an independent county operator from conforming.

Online-First is an implementation order, not a SaaS dependency.

## Development source configuration

The existing application accepts source configuration through query parameters:

```text
substrate=<directory URL>
composition=<directory URL>
partition=<partition reference>
label=<optional human-readable source label>
```

`ms4=` remains a temporary alias for `composition=` for compatibility with existing proof layouts.

These parameters remain development adapters. The administrative participant-publication contract may add a platform-neutral publication source/discovery mechanism; it must not introduce an ESP32-specific JavaScript API or hardware identity into Fabric logical identity.

## Later offline/local reduction

After the online interface and administrative contracts stabilize, the local/offline browser will be produced by reducing the same application.

That later work must retain the same:

- logical identities;
- category and visibility semantics;
- publication validation;
- county/participant composition rules for locally available material;
- reusable rendering and interaction modules.

Offline operation remains part of the Civic Infrastructure direction, but it is no longer the first implementation surface.

## Infrastructure boundary

The county web application is Civic Infrastructure only if it can compose independently retained participant publications without becoming their exclusive datastore.

Accordingly the web layer must not require:

- a proprietary portal as the only source of participant state;
- a physical ESP32 identity as participant identity;
- Kane County private database paths or hostnames in the publication contract;
- one central SaaS account merely to preserve participant data;
- another county operator to clone Kane County's internal implementation.

## Tests

Run:

```bash
bash web/run-tests.sh
```

Existing unit tests cover source normalization, verified composition presentation, projection, navigation, visibility, inspection, failure classification, verification-state presentation, fail-closed recovery status, and platform neutrality.

New administrative integration tests will be added only after the participant/category/visibility contract is frozen enough to test rather than guessed from firmware.
