# Kane Fabric Web Application Design

## Status

Retained Web Application design authority and reactivated for administrative participant-publication integration.

The normative Milestone 5 sequence remains in `docs/MILESTONE_5_DESIGN.md`. WEB-001 through WEB-005 established the reference browser application's original consumer requirements and remain accepted. The current administrative/edge boundary is `docs/ADMINISTRATIVE_EDGE_BOUNDARY.md`.

The current development-order authority is `docs/BROWSER_FIRST_ONLINE_FIRST_DIRECTIVE.md`.

## Browser-First, Online-First

Kane Fabric remains **Browser-First**: the browser is the primary human client and its publication/composition/verification contracts are durable platform-neutral interfaces.

The active implementation order is **Online-First**: build the full online county browser/interface first, exercise the administrative/category/participant contracts in that complete interface, and only then reduce the same application into a local/offline form.

This is an implementation-order decision, not a change to the anti-capture architecture.

The intended sequence is:

```text
full online county browser/interface
        ↓
administrative categories + participant contracts
        ↓
online participant-publication composition
        ↓
freeze shared browser modules and browser-visible contracts
        ↓
remove network-only conveniences
        ↓
local/offline browser form
```

The online and offline forms are not separate products. Rendering, validation, identity handling, category interpretation, map composition, and interaction logic should be shared.

## Why browser work resumes now

MS5-006 physically proved the reference ESP32-S3 artifact appliance: build identity, provisioning, read-only storage, active-inventory verification, plain HTTP GET/range behavior, fail-closed invalid storage, and known-good restoration.

That proof removes firmware as the current development bottleneck. The next unresolved contract is administrative: how the county web view composes accepted county geography with bounded participant publications while preserving independent custody and platform neutrality.

The ESP32-S3 is an edge device. It is not the county database, county web map, category authority, contract authority, or person/account system.

The richer online interface is intentionally developed first because it exposes the complete administrative model without forcing early offline constraints to define or narrow that model. Routine browser development should also remain usable from ordinary Windows and Linux workstations.

## Edge-platform boundary

ESP32-S3 is the **default reference edge platform**, not the definition of a Kane Fabric edge.

A conforming physical or software edge may be implemented using:

- another microcontroller family;
- a single-board computer;
- a general-purpose computer or appliance;
- a software-only serving process;
- a future platform not presently selected.

The ESP32-S3 product line, ESP-IDF, specific toolchains, and supporting components are third-party implementations that may evolve, become incompatible, or disappear from the market. Durable Kane Fabric browser/publication contracts must not depend on their continued existence.

The selected ESP-IDF v6.0.3 baseline remains accepted reference groundwork. Its selection does not make ESP-IDF, Espressif hardware identity, Wi-Fi behavior, or any ESP-specific API part of Fabric logical identity or the browser application contract.

A participant edge is not required to carry the complete county substrate. It may carry a bounded publication—such as one condominium association and its unit-level participant data—while referencing accepted county/building identities supplied by the administrative contracts.

## Existing browser foundation

Milestone 3 already proved browser-side:

- immutable substrate manifest verification;
- WebCrypto SHA-256 validation;
- selective HTTP byte-range reads;
- DEFLATE decompression;
- Canvas rendering of accepted Kane County substrate data.

Milestone 4 already proved browser-side:

- deterministic logical partition loading;
- independently versioned subscription loading;
- substrate + subscription composition;
- cross-partition object identity preservation;
- real Canvas composition in a normal browser.

WEB-001 through WEB-005 then established the dependency-free user application shell, platform-neutral source configuration, verified composition, navigation/inspection, explicit failure/offline behavior, and real-browser acceptance.

Those accepted foundations are reused. The administrative re-entry adds participant-publication composition; it does not replace the existing substrate/subscription verification model.

The fact that WEB-004 already models offline/failure state does not require offline-first implementation of the next interface generation. Those semantics remain acceptance requirements that the later reduced local/offline form must preserve.

## Product boundary

The Kane Fabric Web Application is the durable human-facing client for composed Civic Infrastructure.

It may:

- render accepted county substrate geography;
- render and inspect accepted partition/subscription content;
- integrate bounded participant publications under explicit contracts;
- show content/generation identity and verification status;
- show category and visibility/classification state defined by the administrative contracts;
- provide navigation, visibility, inspection, search, discovery, and other geographic interaction;
- expose online conveniences that have no disconnected equivalent, provided those conveniences do not become civic identity or exclusive data custody;
- operate against any artifact-serving path that satisfies the browser-facing contract.

It must not become:

- a geographic promotion authority;
- the exclusive custodian of participant data;
- an identity provider merely because restricted data exists;
- a physical-edge identity authority;
- a Mechanical Compiler-specific frontend;
- an ESP32 management console merely because ESP32-S3 is the default reference edge.

## Administrative composition model

The county-wide map remains an administrative publication. Bounded participant publications are composed into that view rather than forcing the county substrate onto each edge.

Reference model:

```text
accepted county geography
        +
administrative categories/contracts
        +
bounded participant publication
        =
composed county-facing view
```

For a condominium reference case:

```text
accepted Kane County / building context
        +
association publication
        +
unit publications / unit state
        =
condominium contribution visible in the county web view
```

The participant contract must distinguish:

- county geographic identity;
- participating organization/association identity;
- unit or other participant-object identity;
- category/schema identity;
- participant publication generation identity;
- logical references to accepted county/building/partition/subscription identities;
- physical edge identity, which is none of the identities above.

Some participant fields may be intentionally public. Other fields may be restricted or private. The contract must express visibility/classification semantics independently of a particular ESP32, web host, or account vendor.

## Online reference interface

The online county interface is now the primary implementation surface for administrative development.

It may use online-only conveniences such as discovery, county-wide aggregation, richer search, current source availability, administrative workflows, and authentication needed to obtain restricted material.

Those conveniences must surround rather than define the civic contracts. The online interface must consume the same portable county, category, participant, publication-generation, and visibility semantics that a later local/offline browser will consume.

The online operator may cache, index, aggregate, or present participant content, but must not silently become its exclusive custodian or logical owner.

## Browser-to-edge contract

The application consumes Fabric artifacts through ordinary browser interfaces. In the first-release reference topology the browser never terminates TLS on the ESP32-S3:

```text
Web Application / browser
      |
      | HTTPS / fetch / bounded byte ranges
      v
Wiregate / administrative web origin
      |\
      | +--> accepted county publication
      |
      | plain HTTP when reading a bounded edge publication
      v
participant artifact source
      |
      +-- ESP32-S3 reference source
      +-- development/software source
      +-- other MCU/SBC/software source
```

The Wiregate/admin origin owns the browser secure origin and browser-trusted certificate. The ESP32-S3 reference source owns plain-HTTP bounded artifact/range serving only. Direct browser-to-ESP32 HTTP is not the reference secure-origin path.

The application must not need to know which implementation is underneath the participant artifact-source boundary.

No ESP32-specific JavaScript API, custom device RPC protocol, hardware serial number, management key, TLS key, or platform identity may be required merely to read and validate a participant publication.

During development, source locations may be supplied explicitly to the application. That development configuration is not itself geographic or participant identity and must not be embedded into immutable Fabric content identities.

## Source-adapter rule

The application must keep source acquisition separate from content semantics.

A publication may be obtained through:

- the online administrative origin;
- Wiregate;
- a bounded participant edge;
- a development/software server;
- local/offline files or storage;
- another conforming source.

Changing source adapters must not change publication identity, category identity, participant identity, or validation behavior.

This rule is the main mechanism by which the online-first implementation can later be reduced to offline/local use without a second application architecture.

## Visibility and identity boundary

Visibility classification and human authentication are separate concerns.

A publication contract may classify fields or artifacts as public, restricted, or private. The browser may use higher-layer credentials to decide whether restricted content can be obtained or rendered. The ESP32-S3 v1 firmware does not become a person/account membership system.

A county operator or web operator likewise must not become the logical owner of participant content merely because it supplies authentication, discovery, aggregation, or presentation services.

## Infrastructure rather than SaaS

The web layer remains Civic Infrastructure only when independently controlled data can move between conforming implementations.

Therefore:

- participant publications use explicit portable contracts;
- county and participant identities do not depend on one hosted account system;
- a participant publication can remain locally retained if the online service is unavailable;
- another county operator can implement the same contracts without cloning Kane County hostnames, database schema, hardware identities, or private operational state;
- web composition must not require a proprietary portal to be the sole datastore of participant state.

Online-First does not weaken any of these requirements.

## Dependency posture

The Web Application initially uses:

- standard HTML;
- standard CSS;
- browser ES modules;
- existing Kane Fabric browser modules;
- standard Web APIs already covered by the dependency/platform policy.

No npm dependency graph is required for the initial application shell. A new third-party browser framework or library must satisfy `docs/DEPENDENCY_POLICY.md` before introduction.

## Accepted Web Application work

The existing workstream remains accepted:

```text
WEB-001  application shell + platform-neutral artifact-source configuration
WEB-002  accepted MS3/MS4 map composition as a user-facing vertical slice
WEB-003  geographic navigation, layer/subscription visibility, and inspection interaction
WEB-004  explicit verification/error/offline behavior visible to the user
WEB-005  real-browser acceptance against accepted Kane County artifacts and reassessment of edge requirements
```

These identifiers record completed browser foundation. They are not a replacement work sequence for Milestone 5.

## Active administrative development

The next work is defined under `administration/README.md`, not by inventing another firmware feature first.

Before the first real condominium edge publication is provisioned or the reduced offline browser is built, administrative development must define enough of the following to be testable in the full online interface:

- category/object model;
- association and unit identity/reference semantics;
- participant publication manifest/generation contract;
- references to accepted county/building identities;
- public/restricted/private classification semantics;
- online web composition rules;
- source-neutral browser loaders/adapters;
- independent county-operator conformance boundary.

Only after those contracts are concrete should the ESP32 replace the synthetic MS5-006 probe with a real bounded participant publication.

## Offline/local reduction

The reduced offline browser is a later derivative of the accepted online application.

The reduction should remove or substitute network-only capabilities while retaining:

- the same logical identities;
- the same category and visibility semantics;
- the same publication validation;
- the same county/participant composition rules for locally available material;
- the same reusable rendering and interaction modules;
- independent local custody of available data.

The project must not fork a second schema or second civic contract merely to support offline operation.

## Acceptance discipline

Repository/static tests validate application configuration, contract parsing, source neutrality, and dependency boundaries.

A claim that the Online Reference Interface actually integrates a participant publication requires a real-browser gate using accepted county geography plus a valid bounded participant publication.

A later claim of offline/local support requires a separate gate proving the accepted online application can be reduced to local sources without changing the civic contracts or logical identities.

MS5-007 no longer means storing or serving the complete accepted county substrate from the ESP32-S3. It means integrating a focused participant edge publication with the administrative county/web view while preserving the immutable identities and authority boundaries already established by MS3/MS4.
