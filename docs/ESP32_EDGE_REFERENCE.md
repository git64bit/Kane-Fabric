# ESP32-S3 Edge Reference

## Purpose

The initial Kane Fabric **default** physical edge reference is an ESP32-S3-class device running Kane Fabric firmware built with ESP-IDF and serving released Fabric artifacts to browsers.

The device is deliberately replaceable infrastructure. It is not geographic authority, an application owner, a partition identity, a subscription identity, or a permanent hardware root of trust.

The active normative MS5 work sequence is defined only in:

```text
docs/MILESTONE_5_DESIGN.md
```

This document records the default hardware/reference boundary, not a second work sequence.

## Default reference, not platform requirement

ESP32-S3 is the default reference implementation because it is constrained, inexpensive, widely available, and useful for proving that Kane Fabric does not require desktop-class hardware.

It is **not** the definition of a Kane Fabric edge.

A conforming edge may instead be implemented by another microcontroller, a single-board computer, a general-purpose appliance, or a software-only serving process if it satisfies the same durable Fabric edge and browser/publication contracts.

This portability is intentional. The ESP32 product line, ESP-IDF, compiler/tool releases, and related components are third-party implementations outside Kane Fabric control. They may evolve incompatibly, be superseded, or disappear from the market. Kane Fabric logical identity and browser semantics must survive that possibility.

Consequently:

- no Fabric logical identity depends on an ESP32 serial number, MAC, chipset family, SDK version, or continued product availability;
- the Web Application must not require an ESP32-specific JavaScript API or custom device RPC merely to consume Fabric geography;
- the accepted ESP-IDF/toolchain selection is default-reference groundwork, not architectural lock-in;
- platform-specific implementation should occur when consumer-facing requirements make it necessary, not merely because a default platform has been selected.

## Architectural position

```text
official geographic sources
        ↓
county Fabric node
(authority, validation, explicit promotion, compilation)
        ↓
released MS3 substrate
+ released MS4 partitions/subscriptions
        ↓
replaceable edge implementation
(ESP32-S3 default; other conforming platforms allowed)
        ↓
browser
(validation, selective fetch, decompression, composition, rendering)
```

Loss, compromise, replacement, or reflashing of one physical edge must not change the logical identity of the jurisdiction, substrate, partition, subscription, or accepted geographic state.

## Security position

Kane Fabric's reference edge does not contain financial assets or authoritative private county state. Most served data is public geography and independently integrity-checked by the browser.

The project therefore does not attempt to make the default ESP32-S3 physically unextractable.

Kane Fabric MS5 does **not** require irreversible eFuse burning for secure boot, flash encryption, JTAG disablement, or UART/download disablement.

The priority is:

- local compromise stays local;
- fleet-wide software/provisioning failures are preventable and recoverable;
- authoritative signing/CA/promotion keys never exist on the edge;
- the physical device/platform can be replaced without changing Fabric logical identity.

A deployment with a stronger consumer-specific threat model may add hardware protection without changing the Fabric contracts.

## ESP32 platform versus secure element

For the default reference implementation, the ESP32-S3 provides compute/radio/storage.

A secure element, if used, is a separate optional cryptographic provider. Kane Fabric expresses device-local cryptographic operations through a replaceable key-provider boundary so that software-held replaceable keys and external secure-element-backed keys can satisfy the same device role where appropriate.

Neither provider becomes Fabric geography or content identity.

## Identity separation

The following are distinct:

```text
substrate identity
partition identity
subscription generation identity
logical placement intent

physical platform identity
TLS/browser-origin identity
management/WireGuard identity
optional secure-element identity
storage location
network address
```

Changes in the second group do not change the first group.

## Browser serving

The browser remains the durable client and must validate immutable Fabric artifacts.

Any edge implementation must support the required HTTP/range behavior and a browser execution context that exposes the required WebCrypto SHA-256 interface. Plain arbitrary LAN HTTP must not be assumed to satisfy browser secure-context requirements.

For the ESP32-S3 default reference, the initial local-access direction is an ESP32-hosted AP with deterministic discovery/origin behavior. STA operation may coexist for upstream management. AP+STA shares one radio, so concurrency, channel behavior, memory, and throughput must be measured on the real device before those behaviors are accepted.

These ESP32-specific radio details are reference-implementation concerns, not browser/publication identity.

The browser-origin/TLS credential proves a serving endpoint role only. It must not expose persistent civic delivery-point identity.

## Management connectivity

Management connectivity is independent of local browser serving.

An edge with valid activated Fabric data should continue to serve it when management/upstream connectivity is unavailable.

WireGuard is the preferred management candidate to test for the ESP32-S3 reference, not an accepted requirement. Compile-level feasibility has been observed; runtime handshake, NAT recovery, reconnect behavior, resource consumption, and coexistence with Fabric serving remain later MS5 evidence tasks.

A WireGuard public key or VPN address is replaceable physical-node configuration.

## Firmware and updates

Normal Kane Fabric update flow should authenticate/verify firmware artifacts and recover from failed updates.

This protects the operational fleet from corrupted or unauthorized normal updates. It is not a claim that an owner with physical possession of the ESP32 can never replace firmware manually.

Other edge platforms may use different firmware/software update mechanisms while preserving the same authority and artifact-activation boundaries.

Transport authentication and firmware authenticity are separate controls.

## Storage

The edge may use internal flash, external storage, local filesystems, or other implementation-appropriate storage.

Storage is a physical implementation detail. The edge must verify immutable Fabric identities before activation and must not expose a mixed generation after interrupted update.

Replacing storage or the whole serving platform must not change the logical identity of the artifacts.

## Authority boundary

An edge may hold:

- released substrate generations;
- partition descriptors/selections;
- subscription generations;
- selected immutable objects/chunks;
- verification metadata;
- replaceable local device credentials;
- local placement and serving configuration.

It never owns:

- official source acquisition;
- candidate acceptance;
- geographic promotion;
- county-database mutation;
- release-signing authority;
- CA/issuing authority;
- application participation/account semantics.

## Relationship to later milestones

MS5 proves at least one constrained, replaceable physical reference implementation; ESP32-S3 is the current default.

Later milestones add accepted parcel/delivery-point geography, managed synchronization/credential replacement, and multi-node placement/replication/sharding.

Those functions consume the platform-neutral edge boundary rather than redefining MS3/MS4 logical identity or making one vendor's hardware permanent infrastructure.
