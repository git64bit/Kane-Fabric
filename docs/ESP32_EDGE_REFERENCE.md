# ESP32-S3 Edge Reference

## Purpose

The initial Kane Fabric edge reference is an ESP32-S3-class device running Kane Fabric firmware built with ESP-IDF and serving Fabric artifacts to browsers over HTTP.

The edge node is part of the Kane Fabric civic-infrastructure layer. It is a replaceable distribution resource, not a source of geographic authority, not an application owner, and not the identity of a geographic partition or subscription.

## Architectural position

The intended path is:

```text
official geographic sources
        ↓
county Fabric node
(authority, validation, compilation)
        ↓
immutable county substrate
+ logical geographic partitions
+ subscription generations
        ↓
ESP32-S3 edge node(s)
(physical placement + ESP-IDF HTTP serving)
        ↓
browser
(validation, selective fetch, decompression, composition, rendering)
```

The browser must not require the county Fabric control plane to remain online when valid generations have already been activated on edge nodes.

Loss or replacement of an edge device must not change the logical identity of the jurisdiction, substrate, partition, subscription, or accepted geographic state.

## Logical partition versus physical node

Milestone 4 introduces deterministic geographic partition identity so a constrained node does not have to carry every county-wide subscription or every possible working set.

Examples of logical scopes include:

- whole county;
- municipality/incorporated place;
- township/equivalent administrative subdivision;
- explicit bounded region;
- deterministic composite scope where justified.

These are logical distribution/composition scopes. They are not physical-device identities.

One ESP32-S3 may carry several partitions and subscriptions. One partition or subscription may be replicated or sharded across several devices. Moving bytes between devices must not change the logical partition/subscription identity presented to the browser.

Administrative boundaries are convenience scopes rather than semantic ownership boundaries. Roads, water, buildings, and application objects crossing a partition boundary retain one logical identity.

## ESP-IDF HTTP server

The initial firmware implementation uses ESP-IDF and its HTTP-server facilities rather than introducing a separate general-purpose server stack.

The edge-serving contract is expected to provide the browser with immutable files, objects, ranges, partition descriptors, and subscription manifests required by an activated Fabric generation.

The HTTP implementation must remain subordinate to public artifact and logical identity contracts. A future edge device or HTTP implementation may replace ESP32-S3/ESP-IDF without requiring a new browser data model, new substrate identity, new partition identity, or new subscription identity.

## Milestone relationship

### Milestone 3 — complete

Milestone 3 defined and proved the browser-consumable shared county substrate:

```text
county-overview.json
roads-lod.kfs
water-lod.kfs
substrate-manifest.json
```

It proved deterministic bytes, selective indexed byte-range access, browser validation/decompression/rendering, and bounded reference-server reads without completing ESP32-S3 firmware.

### Milestone 4 — logical partition/subscription contract

Milestone 4 defines:

- subscription manifests and independent generations;
- deterministic geographic partition/scoping identity;
- municipality/township/bounded-region scope normalization;
- selection/reference of relevant substrate chunks/ranges;
- cross-boundary inclusion and composition behavior;
- browser composition of focused substrate + subscriptions;
- device-independent placement semantics.

Milestone 4 is hardware-aware but deliberately does **not** implement ESP-IDF firmware. Its output must make focused subsets practical for constrained nodes without baking an ESP32 identity, storage path, or network endpoint into the logical data model.

### Milestone 5 — actual ESP32-S3/ESP-IDF implementation

Milestone 5 implements and proves the edge-serving contract on the ESP32-S3 reference hardware.

It owns:

- exact ESP-IDF/toolchain selection, license review, pinning, and vendoring if retained;
- firmware implementation;
- physical storage layout/capacity planning;
- mapping partitions/subscriptions to devices;
- HTTP handler/range behavior;
- local browser serving;
- AP/STA deployment behavior;
- activation/recovery;
- node replacement.

This sequencing keeps logical partition/subscription identity independent from one hardware implementation while preserving the ESP32-S3 as a first-class resource constraint.

## Authority boundary

An edge node may hold:

- activated substrate generations;
- geographic partition descriptors/manifests;
- activated subscription generations;
- selected substrate chunks/ranges or immutable component/object bytes;
- verification metadata;
- local serving/placement configuration;
- replaceable caches.

It does not become authoritative for:

- official source acquisition;
- candidate acceptance;
- geographic promotion or rollback policy;
- county database mutation;
- partition semantics merely because it stores a partition copy;
- application-owned classifications, qualifications, workflows, or business state merely because it serves copies of those artifacts.

## Civic-infrastructure rights boundary

Kane Fabric edge firmware and Kane Fabric HTTP-serving implementation are part of the civic-infrastructure code governed by the repository's public-domain/Unlicense intent.

ESP-IDF is a third-party framework and retains its own legal terms. If it is retained for Kane Fabric firmware release, the exact selected distribution/toolchain must satisfy the project's dependency/vendoring policy.

An edge device may also serve application/subscription artifacts whose ownership or licensing differs from Kane Fabric. Co-location on one physical ESP32-S3 does not merge those rights boundaries.

For example:

```text
Kane Fabric substrate + partition descriptors + Kane Fabric edge firmware
    public civic-infrastructure layer

building categories + qualifications + workflows + other domain state
    application/subscription layer with separately determined terms
```

A proprietary, restricted, private, or commercially licensed subscription must not acquire ownership of the underlying public Kane Fabric substrate. Conversely, the public-domain Kane Fabric layer does not force separately owned application state into the public domain.

## Design constraints carried backward into logical contracts

The substrate, partition, and subscription contracts must be evaluated against the initial edge reference for:

- bounded memory use;
- streamable or seekable access without loading an entire county component into RAM;
- focused geographic placement so an edge device can carry a useful subset;
- simple immutable-file/object/range serving over HTTP;
- deterministic byte/logical identities and straightforward integrity verification;
- activation without exposing a mixed old/new generation;
- browser access without server-side rendering or application logic;
- storage layouts that can be replaced or migrated without changing logical package/partition/subscription identity;
- cross-boundary objects that remain usable without destructive partition-specific identity changes.

These are architectural constraints, not permission to optimize prematurely around one microcontroller implementation.

## Non-goal

ESP32-S3 is the first reference implementation, not the permanent definition of an edge node.

Kane Fabric should prove that this constrained, inexpensive device can participate in the system while keeping the public browser/package/partition/subscription contracts portable to later hardware.
