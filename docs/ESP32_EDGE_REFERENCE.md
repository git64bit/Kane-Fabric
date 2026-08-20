# ESP32-S3 Edge Reference

## Purpose

The initial Kane Fabric edge reference is an ESP32-S3-class device running Kane Fabric firmware built with ESP-IDF and serving Fabric artifacts to browsers over HTTP.

The edge node is part of the Kane Fabric civic-infrastructure layer. It is a replaceable distribution resource, not a source of geographic authority and not an application owner.

## Architectural position

The intended path is:

```text
official geographic sources
        ↓
county Fabric node
(authority, validation, compilation)
        ↓
immutable substrate/subscription artifacts
        ↓
ESP32-S3 edge node
(ESP-IDF firmware + HTTP serving)
        ↓
browser
(validation, decompression, composition, rendering)
```

The browser must not require the county Fabric control plane to remain online when a valid generation has already been activated on the edge node.

Loss or replacement of an edge device must not change the logical identity of the jurisdiction, substrate, subscription, or accepted geographic state.

## ESP-IDF HTTP server

The initial firmware implementation uses ESP-IDF and its HTTP-server facilities rather than introducing a separate general-purpose server stack.

The edge-serving contract is expected to provide the browser with the immutable files or objects required by an activated Fabric generation, including manifests and compiled geographic components.

The HTTP implementation must remain subordinate to the public artifact contract. A future edge device or HTTP implementation may replace ESP32-S3/ESP-IDF without requiring a new browser data model or new package identities.

## Milestone relationship

Milestone 3 defines and proves the browser-consumable shared substrate.

Milestone 3 does not need to complete the ESP32-S3 firmware, but its durable package and manifest decisions must be made with the ESP32-S3/ESP-IDF edge as a first-class consumer constraint. A format that is practical only when served from a desktop-class machine is not an acceptable long-term Fabric substrate format without explicit evidence and justification.

Milestone 5 implements and proves the edge-serving contract on the ESP32-S3 reference hardware.

This sequencing separates package compilation from edge firmware implementation without treating edge delivery as optional to the architecture.

## Authority boundary

An edge node may hold:

- activated substrate generations;
- activated subscription generations;
- manifests;
- immutable component/object bytes;
- verification metadata;
- local serving configuration;
- replaceable caches.

It does not become authoritative for:

- official source acquisition;
- candidate acceptance;
- geographic promotion or rollback policy;
- county database mutation;
- application-owned classifications, qualifications, workflows, or business state merely because it serves copies of those artifacts.

## Civic-infrastructure rights boundary

Kane Fabric edge firmware and Kane Fabric HTTP-serving implementation are part of the civic-infrastructure code governed by the repository's public-domain/Unlicense intent.

ESP-IDF is a third-party framework and retains its own legal terms.

An edge device may also serve application/subscription artifacts whose ownership or licensing differs from Kane Fabric. Co-location on one physical ESP32-S3 does not merge those rights boundaries.

For example:

```text
Kane Fabric substrate + Kane Fabric edge firmware
    public civic-infrastructure layer

building categories + qualifications + workflows + other domain state
    application/subscription layer with separately determined terms
```

A proprietary, restricted, private, or commercially licensed subscription must not acquire ownership of the underlying public Kane Fabric substrate. Conversely, the public-domain Kane Fabric layer does not force separately owned application state into the public domain.

## Design constraints carried backward into Milestone 3

Before the substrate format is frozen, evaluate it against the initial edge reference for:

- bounded memory use;
- streamable or seekable access without loading an entire county component into RAM;
- simple immutable-file/object serving over HTTP;
- deterministic byte identities and straightforward integrity verification;
- activation without exposing a mixed old/new generation;
- browser access without server-side rendering or application logic;
- storage layouts that can be replaced or migrated without changing logical package identity.

These are architectural constraints, not permission to optimize prematurely around one microcontroller implementation.

## Non-goal

ESP32-S3 is the first reference implementation, not the permanent definition of an edge node.

Kane Fabric should prove that this constrained, inexpensive device can participate in the system while keeping the public browser/package contract portable to later hardware.
