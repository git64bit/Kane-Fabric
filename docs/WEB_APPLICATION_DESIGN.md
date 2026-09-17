# Kane Fabric Web Application Design

## Status

Retained Web Application design authority and reactivated for administrative participant-publication integration.

The normative Milestone 5 sequence remains in `docs/MILESTONE_5_DESIGN.md`. WEB-001 through WEB-005 established the reference browser application's original consumer requirements and remain accepted. The current administrative/edge boundary is `docs/ADMINISTRATIVE_EDGE_BOUNDARY.md`.

## Why browser work resumes now

MS5-006 physically proved the reference ESP32-S3 artifact appliance: build identity, provisioning, read-only storage, active-inventory verification, plain HTTP GET/range behavior, fail-closed invalid storage, and known-good restoration.

That proof removes firmware as the current development bottleneck. The next unresolved contract is administrative: how the county web view composes accepted county geography with bounded participant publications while preserving independent custody and platform neutrality.

The ESP32-S3 is an edge device. It is not the county database, county web map, category authority, contract authority, or person/account system.

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

## Product boundary

The Kane Fabric Web Application is the durable human-facing client for composed Civic Infrastructure.

It may:

- render accepted county substrate geography;
- render and inspect accepted partition/subscription content;
- integrate bounded participant publications under explicit contracts;
- show content/generation identity and verification status;
- show category and visibility/classification state defined by the administrative contracts;
- provide navigation, visibility, inspection, and other geographic interaction;
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

## Visibility and identity boundary

Visibility classification and human authentication are separate concerns.

A publication contract may classify fields or artifacts as public, restricted, or private. The browser may use higher-layer credentials to decide whether restricted content can be obtained or rendered. The ESP32-S3 v1 firmware does not become a person/account membership system.

A county operator or web operator likewise must not become the logical owner of participant content merely because it supplies authentication, discovery, or presentation services.

## Infrastructure rather than SaaS

The web layer remains Civic Infrastructure only when independently controlled data can move between conforming implementations.

Therefore:

- participant publications use explicit portable contracts;
- county and participant identities do not depend on one hosted account system;
- a participant publication can remain locally retained if the online service is unavailable;
- another county operator can implement the same contracts without cloning Kane County hostnames, database schema, hardware identities, or private operational state;
- web composition must not require a proprietary portal to be the sole datastore of participant state.

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

Before the first real condominium edge publication is provisioned, administrative development must define enough of the following to be testable:

- category/object model;
- association and unit identity/reference semantics;
- participant publication manifest/generation contract;
- references to accepted county/building identities;
- public/restricted/private classification semantics;
- web composition rules;
- independent county-operator conformance boundary.

Only after those contracts are concrete should the web application add their loader/composition code and the ESP32 replace the synthetic MS5-006 probe with a real bounded participant publication.

## Acceptance discipline

Repository/static tests validate application configuration, contract parsing, and dependency boundaries.

A claim that the Web Application actually integrates a participant edge publication requires a real-browser gate using accepted county geography plus a valid bounded participant publication. That proof belongs to MS5-007.

MS5-007 no longer means storing or serving the complete accepted county substrate from the ESP32-S3. It means integrating a focused participant edge publication with the administrative county/web view while preserving the immutable identities and authority boundaries already established by MS3/MS4.