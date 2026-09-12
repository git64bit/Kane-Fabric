# ESP32-S3 Edge Reference

## Purpose

The initial Kane Fabric physical edge reference is an ESP32-S3-class device running Kane Fabric firmware built with ESP-IDF and serving released Fabric artifacts to browsers.

The device is deliberately **replaceable infrastructure**. It is not geographic authority, an application owner, a partition identity, a subscription identity, or a permanent hardware root of trust.

The active normative MS5 work sequence is defined only in:

```text
docs/MILESTONE_5_DESIGN.md
```

This document records the hardware/reference boundary, not a second work sequence.

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
ESP32-S3-class edge
(replaceable compute/radio/storage)
        ↓
browser
(validation, selective fetch, decompression, composition, rendering)
```

Loss, compromise, replacement, or reflashing of one physical edge must not change the logical identity of the jurisdiction, substrate, partition, subscription, or accepted geographic state.

## Security position

Kane Fabric's reference edge does not contain financial assets or authoritative private county state. Most served data is public geography and independently integrity-checked by the browser.

The project therefore does not attempt to make the ESP32-S3 physically unextractable.

Kane Fabric MS5 does **not** require irreversible eFuse burning for secure boot, flash encryption, JTAG disablement, or UART/download disablement.

The priority is:

- local compromise stays local;
- fleet-wide software/provisioning failures are preventable and recoverable;
- authoritative signing/CA/promotion keys never exist on the edge;
- the physical device can be replaced without changing Fabric logical identity.

A deployment with a stronger consumer-specific threat model may add hardware protection without changing the Fabric contracts.

## ESP32 platform versus secure element

The ESP32-S3 is the reference compute/radio/storage platform.

A secure element, if used, is a **separate optional cryptographic provider**. Kane Fabric must be able to express device-local cryptographic operations through a replaceable key-provider boundary so that:

```text
software-held replaceable keys
```

and

```text
external secure-element-backed keys
```

can satisfy the same device role where appropriate.

Neither provider becomes Fabric geography or content identity.

A secure element may be replaced or reprovisioned independently of the logical Fabric artifacts the node serves.

## Identity separation

The following are distinct:

```text
substrate identity
partition identity
subscription generation identity
logical placement intent

physical ESP32 identity
TLS/browser-origin identity
management/WireGuard identity
optional secure-element identity
storage location
network address
```

Changes in the second group do not change the first group.

## Browser serving

The browser remains the durable client and must validate immutable Fabric artifacts.

The edge must support the required HTTP/range behavior and a browser execution context that exposes the required WebCrypto SHA-256 interface. Plain arbitrary LAN HTTP must not be assumed to satisfy browser secure-context requirements.

The initial local-access direction is an ESP32-hosted AP with deterministic discovery/origin behavior. STA operation may coexist for upstream management. AP+STA shares one radio, so concurrency, channel behavior, memory, and throughput must be measured on the real device.

The browser-origin/TLS credential proves a serving endpoint role only. It must not expose persistent civic delivery-point identity.

## Management connectivity

Management connectivity is independent of local browser serving.

An edge with valid activated Fabric data should continue to serve it when management/upstream connectivity is unavailable.

WireGuard is the preferred management candidate to test, not an accepted requirement. Compile-level ESP32-S3 feasibility has been observed using an external maintained component; runtime handshake, NAT recovery, reconnect behavior, resource consumption, and coexistence with Fabric serving remain MS5 evidence tasks.

A WireGuard public key or VPN address is replaceable physical-node configuration.

## Firmware and updates

Normal Kane Fabric update flow should authenticate/verify firmware artifacts and recover from failed updates.

This protects the operational fleet from corrupted or unauthorized normal updates. It is not a claim that an owner with physical possession of the ESP32 can never replace firmware manually.

Transport authentication and firmware authenticity are separate controls.

## Storage

The edge may use internal flash, external storage, or both.

Storage is a physical implementation detail. The edge must verify immutable Fabric identities before activation and must not expose a mixed generation after interrupted update.

Replacing storage must not change the logical identity of the artifacts.

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

MS5 proves one replaceable physical reference edge.

Later milestones add:

- accepted parcel/delivery-point geography exposed by real consumers;
- managed synchronization and credential replacement;
- multi-node placement/replication/sharding.

Those later functions consume the MS5 physical-node boundary rather than redefining MS3/MS4 logical identity.
