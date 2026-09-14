# Kane Fabric Web Application Design

## Status

Active priority workstream while Milestone 5 remains current.

The next normative Milestone 5 item remains `MS5-006` in `docs/MILESTONE_5_DESIGN.md`, but implementation of that third-party-platform-specific item is deliberately deferred while Kane Fabric develops the browser application and other components it controls directly.

This document is the single detailed authority for the Web Application workstream. It does not renumber or replace the Milestone 5 sequence.

## Why this work comes now

MS5-001 through MS5-005 established the physical-edge trust boundary, immutable-storage/activation contract, cryptographic role separation, browser secure-origin contract, and a pinned default ESP32-S3 toolchain plan.

That is enough groundwork to protect later edge implementation.

Continuing immediately into MS5-006 would spend substantial effort against a third-party hardware/SDK ecosystem before the real browser application has established the concrete consumer requirements for serving, storage, navigation, failure handling, and interaction.

Kane Fabric therefore follows this priority rule:

> Continue developing the parts Kane Fabric controls until third-party platform integration becomes necessary to advance the system.

This is a sequencing decision, not abandonment of physical-edge work.

## Edge-platform boundary

ESP32-S3 is the **default reference edge platform**, not the definition of a Kane Fabric edge.

A conforming physical or software edge may be implemented using:

- another microcontroller family;
- a single-board computer;
- a general-purpose computer or appliance;
- a software-only serving process;
- a future platform not presently selected.

The ESP32-S3 product line, ESP-IDF, specific toolchains, and supporting components are third-party implementations that may evolve, become incompatible, or disappear from the market. Durable Kane Fabric browser/publication contracts must not depend on their continued existence.

The selected ESP-IDF v6.0.3 baseline remains useful and accepted reference groundwork. Its selection does not make ESP-IDF, Espressif hardware identity, Wi-Fi behavior, or any ESP-specific API part of Fabric logical identity or the browser application contract.

## Existing browser foundation

The Web Application begins from already accepted browser work rather than from a blank UI stack.

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

The existing proof pages are verification harnesses, not a user application. Their browser modules are reusable foundations.

## Product boundary

The Kane Fabric Web Application is the durable human-facing client for public Fabric geography.

It may:

- render accepted substrate geography;
- render and inspect accepted partition/subscription content;
- show content/generation identity and verification status;
- provide navigation, visibility, inspection, and other geographic interaction;
- operate against any artifact-serving edge that satisfies the browser-facing contract.

It must not become:

- a geographic promotion authority;
- an identity provider;
- a person/account membership system;
- a proxy ACL engine;
- a Mechanical Compiler-specific frontend;
- an ESP32 management console merely because ESP32-S3 is the default reference edge.

## Browser-to-edge contract

The application consumes Fabric artifacts through ordinary browser interfaces:

```text
Web Application
      |
      | HTTPS / fetch / bounded byte ranges
      v
Fabric artifact source
      |
      +-- development/software source
      +-- ESP32-S3 reference source
      +-- other MCU/SBC/software source
```

The application must not need to know which implementation is underneath that artifact source.

No ESP32-specific JavaScript API, custom device RPC protocol, hardware serial number, management key, or platform identity may be required merely to read and validate Fabric geography.

During development, source locations may be supplied explicitly to the application. That development configuration is not itself geographic identity and must not be embedded into immutable Fabric content identities.

## Dependency posture

The Web Application initially uses:

- standard HTML;
- standard CSS;
- browser ES modules;
- existing Kane Fabric browser modules;
- standard Web APIs already covered by the dependency/platform policy.

No npm dependency graph is required for the initial application shell. A new third-party browser framework or library must satisfy `docs/DEPENDENCY_POLICY.md` before introduction.

## Work sequence

This section is the single detailed work sequence for the current Web Application priority workstream.

```text
WEB-001  application shell + platform-neutral artifact-source configuration
WEB-002  accepted MS3/MS4 map composition as a user-facing vertical slice
WEB-003  geographic navigation, layer/subscription visibility, and inspection interaction
WEB-004  explicit verification/error/offline behavior visible to the user
WEB-005  real-browser acceptance against accepted Kane County artifacts and reassessment of edge requirements
```

Do not duplicate this complete list in current status documents. They may name only the active Web item.

## WEB-001 boundary

WEB-001 establishes a real application surface without pretending to solve the whole UI.

It must provide:

- a browser application page rather than a proof-only page;
- responsive map/canvas presentation;
- platform-neutral configuration of substrate/composition source locations;
- an explicit partition reference for the first vertical slice;
- human-readable loading, verified, and failure states;
- display of the verified substrate identity and loaded subscription generations when available;
- no third-party JavaScript/CSS dependency graph;
- unit-testable configuration normalization separate from DOM code.

The initial source configuration may use query parameters as a development adapter. Later work may replace that with discovery/configuration without changing the renderer or introducing device-specific application semantics.

## Acceptance discipline

Repository/static tests can validate application configuration and dependency boundaries.

A claim that the Web Application actually consumes accepted Kane County artifacts requires a real-browser gate in CT102 using accepted MS3/MS4 artifacts. Existing MS3/MS4 proof evidence remains accepted but does not automatically prove new application code.

Do not install ESP-IDF or begin firmware implementation merely to test WEB-001 through WEB-004.

## Resume condition for MS5-006

Resume MS5-006 when Web Application work has produced concrete browser-facing requirements that make physical edge implementation necessary, or when WEB-005 explicitly concludes that the current browser contract is sufficiently stable for hardware implementation.

At that point the ESP32-S3 remains the default reference implementation. The implementation must satisfy the same browser/artifact contract that a software server, another microcontroller, or an SBC could satisfy.
