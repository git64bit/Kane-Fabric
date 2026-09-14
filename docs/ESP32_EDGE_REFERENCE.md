# ESP32-S3 Edge Reference

## Purpose

The initial Kane Fabric **default** physical edge reference is an ESP32-S3-class device running Kane Fabric firmware built with ESP-IDF and serving released Fabric artifacts by plain HTTP to the Wiregate hub.

The device is deliberately replaceable infrastructure. It is not geographic authority, an application owner, a partition identity, a subscription identity, or a permanent hardware root of trust.

The active normative MS5 work sequence is defined only in:

```text
docs/MILESTONE_5_DESIGN.md
```

This document records the default hardware/reference boundary, not a second work sequence.

## Default reference, not platform requirement

ESP32-S3 is the default reference implementation because it is constrained, inexpensive, widely available, and useful for establishing a real firmware component from the first Kane Fabric release.

Its first-release role is intentionally modest. The point is to establish the firmware source/build/release/provisioning/replacement lifecycle early, before Kane Fabric becomes mature enough that introducing firmware later would require a major architectural retrofit. The ESP32-S3 does not need to absorb browser TLS, certificate management, or every future management function to justify its presence.

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
(ESP32-S3 default; plain HTTP)
        ↓
Wiregate hub
(HTTPS termination / browser origin)
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
management/WireGuard identity
optional secure-element identity
storage location
network address

Wiregate hub / browser TLS identity
```

Changes in the second group do not change the first group.

## Artifact serving and browser path

The browser remains the durable client and must validate immutable Fabric artifacts, but the browser does not terminate TLS on the ESP32-S3.

The first-release reference path is:

```text
browser -- HTTPS --> Wiregate hub -- HTTP --> ESP32-S3
```

The Wiregate hub owns the browser-trusted certificate and HTTPS termination. The ESP32-S3 owns bounded plain-HTTP artifact serving, including the required byte-range behavior. It holds no browser TLS private key and has no browser certificate-renewal responsibility.

Direct HTTP access to the ESP32-S3 may be used for diagnostics and device acceptance. It is not the reference browser secure-origin path. An ESP32-hosted AP is not required by the Kane Fabric browser contract.

This separation deliberately keeps the initial firmware role small while retaining a real firmware/storage/serving component that can evolve later.

## Management connectivity

Management connectivity is independent of the Wiregate-to-edge HTTP serving path.

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
