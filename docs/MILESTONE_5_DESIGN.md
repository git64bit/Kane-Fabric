# Milestone 5 Design — Reference Physical Edge Architecture

## Status

Design authority for the active Milestone 5.

Milestones 3 and 4 are released. MS5 maps their frozen logical identities onto a real constrained edge implementation. This document replaces the earlier assumption that MS5 was primarily "put an HTTP server on an ESP32." Consumer review and WireGuard/ESP-IDF feasibility work exposed a broader requirement: the edge must be replaceable, recoverable, securely manageable in proportion to actual risk, and unable to acquire geographic authority merely because it stores or serves Fabric bytes.

## Purpose

Milestone 5 proves a reference physical edge appliance using ESP32-S3-class hardware and ESP-IDF while preserving the already-released logical model:

```text
accepted Fabric geography
        ↓
MS3 substrate
+ MS4 partitions/subscriptions
        ↓
replaceable physical edge
(plain HTTP artifact source)
        ↓
Wiregate hub
(HTTPS termination / browser origin)
        ↓
browser
```

The physical edge is a distribution appliance. It is not the identity of a jurisdiction, substrate, partition, subscription, building, parcel, delivery point, application object, or accepted geographic release.

## First-release firmware role

The ESP32-S3 is included in the first Kane Fabric release primarily so firmware is a first-class project component from the beginning. The first release does not require the microcontroller to absorb every serving, security, discovery, or management responsibility merely because ESP-IDF can implement it.

Establishing the firmware source tree, pinned build toolchain, firmware release artifacts, physical storage contract, provisioning/replacement discipline, update/recovery path, and hardware acceptance process now avoids having to bolt an entirely new firmware lifecycle onto a mature Kane Fabric later.

The first-release ESP32-S3 role is intentionally modest:

- immutable artifact storage;
- bounded plain-HTTP artifact and byte-range serving to the Wiregate hub;
- a real firmware build/release/provisioning lifecycle;
- replaceable physical-edge identity and storage;
- a foundation on which later synchronization, management, update, and richer edge behavior may evolve.

HTTPS termination, browser certificate lifecycle, and browser secure-origin trust belong to the Wiregate hub, not to the ESP32-S3 reference firmware.

## Fixed boundaries

MS5 must preserve these constraints:

- accepted geographic state changes only through explicit Fabric promotion;
- MS3 substrate identity and MS4 partition/subscription identity are not redesigned by edge implementation;
- edge compilation, provisioning, synchronization, storage, activation, serving, or replacement never promotes geography;
- an ESP32 serial number, MAC address, hostname, IP address, Wi-Fi SSID, storage path, Wiregate TLS key, WireGuard key, secure-element key, or hardware identifier never becomes a Fabric logical identity;
- the browser continues to validate immutable publication bytes rather than trusting the edge as geographic authority;
- authoritative release-signing, CA, promotion, and county-control-plane keys never reside on the edge;
- application-specific participation/account/credential semantics remain outside Kane Fabric.

## Security posture

Kane Fabric does not assume a banking, payment, DRM, or high-value-secret threat model.

The edge primarily carries public civic geography and replaceable operational credentials. A person with physical possession of one edge may be able to read or alter that device. The architecture must make that a local, recoverable event rather than pretending the microcontroller is physically unextractable.

Threat classes:

### A. Individual physical edge compromise

Expected to be tolerable.

A compromised device may lose local confidentiality, availability, or its replaceable device credentials. It must not gain:

- accepted geographic authority;
- candidate-promotion authority;
- Fabric release-signing authority;
- CA/issuing authority;
- the ability to redefine substrate/partition/subscription identity;
- authority over other edge nodes merely because it was once a valid node.

Recovery is replacement or reprovisioning.

### B. Fleet-class implementation or provisioning failure

Systemic.

Examples include one exploitable firmware defect across the fleet, a broken update, incorrect credential provisioning, unsafe activation logic, or a storage-format implementation that corrupts generations. MS5 must prioritize deterministic provisioning, signed/identified firmware artifacts, rollback/recovery, and reproducible acceptance against this class.

### C. Authority/signing infrastructure compromise

Systemic and outside the edge trust boundary.

Private CA/issuing keys, release-signing keys, and geographic promotion authority require stronger protection on non-edge infrastructure. An edge device must never contain enough authority to manufacture a new accepted Fabric release.

## No irreversible ESP32 security requirement

The Kane Fabric reference edge SHALL NOT require burning irreversible security eFuses as an MS5 acceptance condition.

In particular, MS5 does not require:

- secure-boot eFuse commitment;
- flash-encryption eFuse commitment;
- irreversible JTAG disablement;
- irreversible UART/download-mode disablement.

A deployment may choose additional hardware protections for its own threat model, but those are deployment policy rather than Fabric identity or wire-format requirements.

This keeps the reference platform recoverable, inspectable, replaceable, and suitable for civic infrastructure whose primary payload is public data.

## Cryptographic role separation

Separate roles must remain separate:

```text
Fabric logical content identity
    ≠ physical ESP32 identity
    ≠ Wiregate hub / browser TLS identity
    ≠ management/WireGuard identity
    ≠ optional secure-element identity
    ≠ firmware/release-signing authority
```

No private key is reused across unrelated roles.

MS5 must define a key-provider boundary for device-local cryptographic operations. The default reference edge does not require a browser TLS private key. Device-local private keys are limited to roles that actually remain on the edge, such as an optional management transport if later retained. A deployment may use software-held replaceable keys or substitute an external secure element without changing MS3/MS4 identities, browser data semantics, or the placement identity of the served Fabric generations.

The secure element, when present, is a peripheral/service to the physical node. It does not define the node and does not define Fabric content.

## Firmware authenticity versus physical resistance

Firmware authenticity and transport security are useful even though physical modification of one device is tolerated.

The normal update/activation path must be able to reject damaged or unauthorized firmware artifacts and recover from failed updates. This protects fleet operation.

MS5 does not claim that a determined person with physical possession of an ESP32-S3 can never replace firmware. If they do, the resulting local device must not acquire additional Fabric authority.

Transport security likewise does not create artifact authority:

```text
authenticated transport ≠ accepted Fabric geography
authenticated transport ≠ valid firmware artifact
```

## Storage and activation

The edge must hold complete or focused immutable artifacts derived from released MS3/MS4 contracts.

MS5 will freeze a physical storage/activation model that provides:

- explicit inventory of the logical generations present;
- deterministic verification before activation;
- no mixed-generation exposure during activation;
- bounded access compatible with constrained memory;
- recovery to the last known-good activated generation after interrupted or failed update;
- replacement/migration of storage without changing logical content identity.

The implementation may use internal flash, external storage, or a combination, but storage location is never part of Fabric identity.

## Browser access and secure origin

The browser remains the durable user client and still requires a trustworthy secure context with callable WebCrypto SHA-256.

For the Kane Fabric reference topology, HTTPS terminates at the **Wiregate hub**. The browser talks HTTPS to the hub; the hub talks plain HTTP to the ESP32-S3 artifact server:

```text
browser -- HTTPS --> Wiregate hub -- HTTP --> ESP32-S3
```

The ESP32-S3 reference firmware therefore does not own browser certificates, browser TLS private keys, certificate renewal, or browser trust configuration. Direct arbitrary `http://ESP32/...` access may be used for diagnostics or controlled backend probes, but it is not the normal browser secure-origin path.

An ESP32-hosted AP is not an MS5 browser requirement. Network attachment of the edge is an implementation concern and may evolve independently. MS5-007 must prove browser consumption through the Wiregate hub without making WireGuard a prerequisite; management/WireGuard feasibility remains the later MS5-008 gate.

The Wiregate hub origin/TLS identity is a serving role only. It must not contain or expose persistent geographic/delivery-point identity merely for convenience.

## Management transport and WireGuard

Management/synchronization transport is distinct from browser serving.

WireGuard is the preferred candidate for evaluation because the maintained external ESP32 implementation has been shown to compile for ESP32-S3 with a current ESP-IDF development environment. That is feasibility evidence, not an accepted Kane Fabric dependency.

MS5 must establish runtime facts before adoption:

- real handshake to a controlled WireGuard hub;
- routed management traffic;
- NAT/persistent-keepalive behavior;
- Wi-Fi interruption and reconnect behavior;
- repeated disconnect/reconnect;
- flash/RAM/task/socket/CPU cost;
- coexistence with edge networking, storage, plain-HTTP artifact serving, and update operations.

The reference topology may be hub-and-spoke with one WireGuard peer per edge. A peer public key or VPN address is physical-node management configuration, never a Fabric logical identity.

Failure of WireGuard must not invalidate already activated public Fabric artifacts. A disconnected edge should continue serving the last valid local publication by HTTP to the local Wiregate/browser path when that local path remains available.

## Dependency boundary

ESP-IDF and any retained WireGuard/crypto component are project-controlled third-party implementations, not merely abstract platform APIs.

MS5 must not select a moving upstream development branch as the final release dependency merely because it compiled during feasibility work. Before closeout, retained dependencies must have exact immutable versions, license review, and an offline/vendored reproduction plan consistent with `docs/DEPENDENCY_POLICY.md`.

The current successful WireGuard compile observation remains evidence for feasibility only; runtime acceptance and final dependency selection are separate gates.

## Replacement model

Physical replacement must be ordinary operation.

A replacement device may receive new:

- hardware identity;
- management/WireGuard identity;
- local storage;
- optional secure-element identity.

The browser/TLS identity belongs to the Wiregate hub and is not a required ESP32 device-local identity.

It must be able to activate the same released:

- substrate content identity;
- partition keys/selections;
- subscription generation identities;
- logical placement intent.

Replacement therefore proves the MS4 rule in real hardware: physical placement and physical device identity are not logical Fabric identity.

## Normative implementation order

This section is the single authoritative definition of the detailed Milestone 5 work sequence. Current status documents may name the active item but must not maintain a second complete copy.

```text
MS5-001  physical-edge threat model, trust boundary, and replaceability contract
MS5-002  storage inventory, verification, activation, rollback, and recovery contract
MS5-003  device cryptographic role separation and replaceable key-provider boundary
MS5-004  Wiregate-terminated browser secure-origin plus hub-to-edge HTTP contract
MS5-005  ESP-IDF/toolchain and retained dependency selection plan
MS5-006  ESP32-S3 immutable artifact storage and HTTP byte-range implementation
MS5-007  real browser consumption through Wiregate of accepted MS3/MS4 generations served by ESP32-S3 HTTP
MS5-008  management transport and WireGuard runtime/resource feasibility proof
MS5-009  firmware authenticity, update, rollback, and recovery proof
MS5-010  physical device replacement/reprovisioning identity-preservation proof
MS5-011  constrained-resource and concurrent-workload acceptance evidence
MS5-012  release evidence and milestone closeout
```

## Exit gate

Milestone 5 is complete when all of the following are demonstrated on reference ESP32-S3-class hardware:

1. a normal browser consumes the accepted MS3 substrate and accepted MS4 partition/subscription generations through Wiregate HTTPS while the ESP32-S3 serves them to the hub by plain HTTP and CT102 is unavailable;
2. the browser validates the same immutable logical identities established by MS3/MS4;
3. storage activation and firmware/update failure do not expose a mixed or silently corrupted generation and have a tested recovery path;
4. the edge remains useful for already activated public data when upstream management connectivity is unavailable;
5. physical replacement/reprovisioning can change every device-local identity while retaining the same Fabric logical content/placement identities;
6. management transport feasibility is measured rather than assumed, with WireGuard adopted only if the runtime/resource proof succeeds;
7. no irreversible ESP32 eFuse operation is required to satisfy the Kane Fabric reference-edge contract;
8. optional external secure-element use remains substitutable and does not alter Fabric logical identities.

The output of MS5 becomes the physical-node foundation for later managed synchronization and multi-node distribution.
