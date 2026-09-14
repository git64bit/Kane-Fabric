# Kane Fabric Web Application Design

## Status

Completed for the current Milestone 5 edge-requirements purpose and retained as the Web Application design authority.

The normative Milestone 5 sequence remains in `docs/MILESTONE_5_DESIGN.md`. WEB-001 through WEB-005 established the reference browser application's consumer requirements and are not a replacement work sequence for MS5.

## Why this work came before physical implementation

MS5-001 through MS5-005 established the physical-edge trust boundary, immutable-storage/activation contract, cryptographic role separation, browser secure-origin contract, and a pinned default ESP32-S3 toolchain plan.

That was enough groundwork to protect later edge implementation, but the actual browser application still needed to establish the concrete consumer requirements for serving, storage, navigation, failure handling, and interaction before the reference firmware was allowed to hard-code platform assumptions.

Kane Fabric therefore followed this priority rule:

> Continue developing the parts Kane Fabric controls until third-party platform integration becomes necessary to advance the system.

WEB-005 completed that reassessment. The later correction that places browser HTTPS on the Wiregate hub and plain HTTP on the ESP32-S3 refines the transport topology without changing the browser's immutable-artifact validation semantics.

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
- operate against any artifact-serving path that satisfies the browser-facing contract.

It must not become:

- a geographic promotion authority;
- an identity provider;
- a person/account membership system;
- a proxy ACL engine;
- a Mechanical Compiler-specific frontend;
- an ESP32 management console merely because ESP32-S3 is the default reference edge.

## Browser-to-edge contract

The application consumes Fabric artifacts through ordinary browser interfaces. In the first-release reference topology the browser never terminates TLS on the ESP32-S3:

```text
Web Application / browser
      |
      | HTTPS / fetch / bounded byte ranges
      v
Wiregate hub
      |
      | plain HTTP
      v
Fabric artifact source
      |
      +-- ESP32-S3 reference source
      +-- development/software source
      +-- other MCU/SBC/software source
```

The Wiregate hub owns the browser secure origin and browser-trusted certificate. The ESP32-S3 reference source owns plain-HTTP artifact/range serving only. Direct browser-to-ESP32 HTTP is not the reference secure-origin path.

The application must not need to know which implementation is underneath the Wiregate/artifact-source boundary.

No ESP32-specific JavaScript API, custom device RPC protocol, hardware serial number, management key, TLS key, or platform identity may be required merely to read and validate Fabric geography.

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

This section records the Web Application workstream that produced the current reference client:

```text
WEB-001  application shell + platform-neutral artifact-source configuration
WEB-002  accepted MS3/MS4 map composition as a user-facing vertical slice
WEB-003  geographic navigation, layer/subscription visibility, and inspection interaction
WEB-004  explicit verification/error/offline behavior visible to the user
WEB-005  real-browser acceptance against accepted Kane County artifacts and reassessment of edge requirements
```

These items are complete for the current MS5 edge-requirements purpose.

## WEB-001 boundary

WEB-001 established a real application surface without pretending to solve the whole UI.

It provides:

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

Repository/static tests validate application configuration and dependency boundaries.

A claim that the Web Application actually consumes accepted Kane County artifacts requires a real-browser gate in CT102 using accepted MS3/MS4 artifacts. Existing MS3/MS4 proof evidence remains accepted but does not automatically prove new application code.

The corrected MS5 reference topology adds a separate physical proof: the browser will consume through Wiregate HTTPS while the ESP32-S3 serves the immutable artifacts to Wiregate over plain HTTP. That proof belongs to MS5-007 and must not silently pull WireGuard forward from MS5-008.
