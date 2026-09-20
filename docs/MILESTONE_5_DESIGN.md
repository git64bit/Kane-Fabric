# Milestone 5 Design — Reference Physical Edge Architecture

## Status

Design authority for the active Milestone 5.

Milestones 3 and 4 are released. MS5 maps their frozen logical identities onto a real constrained edge implementation. This document replaces the earlier assumption that MS5 was primarily "put an HTTP server on an ESP32." Consumer review and WireGuard/ESP-IDF feasibility work exposed a broader requirement: the edge must be replaceable, recoverable, securely manageable in proportion to actual risk, and unable to acquire geographic authority merely because it stores or serves Fabric bytes.

The administrative/edge distinction is further frozen in `docs/ADMINISTRATIVE_EDGE_BOUNDARY.md`.

## Purpose

Milestone 5 proves a reference physical edge appliance using ESP32-S3-class hardware and ESP-IDF while preserving the already-released logical model.

The ESP32-S3 is **not** a miniature county Fabric node and is not required to store the complete county substrate. The administrative county infrastructure retains the accepted county geography, county-wide web/map, categories, and publication contracts. A physical edge carries a bounded participant publication that may reference those accepted identities.

```text
accepted county geography
+ administrative categories/contracts
+ county web/map
             ^
             | compose / integrate
             |
      bounded participant publication
             ^
             | local custody + HTTP
             |
      replaceable physical edge
             |
          ESP32-S3
```

A condominium is the reference bounded-participant example: one association edge may hold association and unit publication data without carrying all Kane County roads, water, or other county-wide substrate bytes.

The physical edge is a distribution/custody appliance. It is not the identity of a jurisdiction, substrate, partition, subscription, building, parcel, delivery point, application object, association, unit, participant publication, or accepted geographic release.

## Administrative infrastructure versus physical edge

The administrative infrastructure owns or defines:

- accepted county geography and provenance/release state;
- the county-wide web/map presentation;
- category and object-class definitions;
- publication/reference/visibility contracts;
- the rules by which bounded participant publications attach to accepted geographic identities;
- the operator-facing interoperability boundary needed for an independent operator to implement another county.

The physical edge owns only its bounded physical role:

- local custody of prepared participant publication artifacts;
- verification and activation of immutable generations;
- bounded local serving;
- continued local usefulness through management/upstream loss;
- replaceable physical identity and storage.

The edge may reference county substrate, building, partition, or subscription identities without duplicating the county-wide substrate. Capacity is therefore a deployment property, not a requirement to fit an entire county publication on every device.

Visibility/classification metadata may be part of the participant publication, including public, restricted, or private classes. Human authentication/person identity remains above the ESP32-S3 v1 firmware boundary.

## First-release firmware role

The ESP32-S3 is included in the first Kane Fabric release primarily so firmware is a first-class project component from the beginning. The first release does not require the microcontroller to absorb every serving, security, discovery, administrative, or management responsibility merely because ESP-IDF can implement it.

Establishing the firmware source tree, pinned build toolchain, firmware release artifacts, physical storage contract, provisioning/replacement discipline, update/recovery path, and hardware acceptance process now avoids having to bolt an entirely new firmware lifecycle onto a mature Kane Fabric later.

The first-release ESP32-S3 role is intentionally modest:

- bounded participant artifact storage;
- bounded plain-HTTP artifact and byte-range serving to the Wiregate hub;
- a real firmware build/release/provisioning lifecycle;
- replaceable physical-edge identity and storage;
- a foundation on which later synchronization, management, update, and richer edge behavior may evolve.

HTTPS termination, browser certificate lifecycle, county web/map composition, category administration, and browser secure-origin trust belong outside the ESP32-S3 reference firmware.

## Firmware v1 responsibility freeze

The initial ESP32-S3 firmware is a **small deterministic Fabric artifact appliance**. This section freezes its first-release responsibility boundary so later implementation work does not promote an experiment into a required feature merely because ESP-IDF can support it.

The executable mirror of this boundary is `ms5/tools/kane_fabric_firmware_v1.py`. This document remains the normative authority.

### Core runtime responsibilities

The v1 reference firmware must:

- expose firmware build identity and operational state through serial diagnostics;
- attach as a client to a deployment-provided local IP network sufficient for Wiregate-to-edge HTTP;
- mount prepared bounded participant artifact storage read-only;
- verify the active artifact inventory before serving it;
- serve immutable Fabric artifacts by plain HTTP;
- implement the exact closed byte-range behavior required by the accepted Kane Fabric HTTP contract;
- fail closed rather than serve an invalid active generation;
- continue serving the last valid activated generation when management/upstream connectivity is unavailable.

The exact network-provisioning mechanism is an implementation concern. A browser-facing ESP32 access point is not required. A management tunnel is not required for local serving.

### Required lifecycle responsibilities

V1 also establishes a durable firmware lifecycle. These are project responsibilities even when they are not part of the steady-state HTTP serving loop:

- firmware source, build inputs, host-testable logic, build/flash/acceptance scripts, and documentation are tracked in the Kane Fabric repository;
- the tracked source builds with the exact pinned ESP-IDF/toolchain selection;
- the resulting firmware artifact has an identifiable build/version identity;
- a device can be flashed, reprovisioned, and replaced reproducibly;
- normal firmware authenticity, update, rollback, and recovery behavior is proved before MS5 closeout;
- physical replacement preserves Fabric logical identities;
- device acceptance evidence is collected from the dedicated ESP programming node.

Generated build directories, flashed binaries, serial captures, and large physical-device evidence are not repository source merely because the firmware source is. They stay outside Git unless a later release process explicitly publishes selected binaries as release artifacts.

### Explicitly not v1 firmware responsibilities

The ESP32-S3 v1 reference firmware does not own:

- browser HTTPS termination;
- browser certificate lifecycle or browser authentication;
- an ESP32-hosted browser access point;
- Fabric geographic authority or Fabric release-signing authority;
- county-database mutation, official source acquisition, or candidate promotion;
- county-wide substrate replication as a prerequisite for participation;
- county web/map hosting or GIS composition;
- category and publication-contract administration;
- application membership/person identity;
- fleet orchestration.

These exclusions are deliberate architecture boundaries, not unfinished firmware features.

### Candidate-only later capabilities

The following capabilities may be measured or prototyped during later MS5 work but are **not v1 firmware prerequisites**:

- WireGuard management transport;
- managed artifact synchronization;
- automatic update transport;
- external secure-element use;
- remote fleet telemetry;
- richer network discovery.

A later gate may retain one of these capabilities, reject it, or defer it. In particular, **MS5-008 may conclude that WireGuard is not retained on the ESP32-S3** without making the v1 firmware incomplete. The browser path and the core artifact appliance must remain valid either way.

### Acceptance layers

Firmware acceptance is split deliberately by environment and scope.

**Repository acceptance in CT102** proves that the role contract, source, host-testable logic, work-sequence authority, and dependency/build-selection records are internally consistent. CT102 does not build or flash ESP32 firmware and does not need ESP-IDF or USB passthrough.

**Device acceptance on the dedicated ESP programming node** proves the exact pinned build, flash/boot behavior, serial firmware identity, read-only storage mount, active-inventory verification, real HTTP GET/range behavior, and fail-closed response to invalid active state.

**MS5 integration acceptance** later proves browser integration of a focused participant publication with the administrative county/web view, continued serving during management loss, firmware update/rollback/recovery, physical replacement/reprovisioning, and constrained-resource coexistence. Candidate-only capabilities do not become core firmware requirements merely because an integration gate measures them.

## Fixed boundaries

MS5 must preserve these constraints:

- accepted geographic state changes only through explicit Fabric promotion;
- MS3 substrate identity and MS4 partition/subscription identity are not redesigned by edge implementation;
- county-wide geography/web/category/contract administration remains outside the physical edge;
- an edge may hold a focused participant publication and reference county identities without carrying the whole county substrate;
- edge compilation, provisioning, synchronization, storage, activation, serving, or replacement never promotes geography;
- an ESP32 serial number, MAC address, hostname, IP address, Wi-Fi SSID, storage path, Wiregate TLS key, WireGuard key, secure-element key, or hardware identifier never becomes a Fabric logical identity;
- the browser continues to validate immutable publication bytes rather than trusting the edge as geographic authority;
- authoritative release-signing, CA, promotion, and county-control-plane keys never reside on the edge;
- application-specific participation/account/credential semantics remain outside Kane Fabric firmware.

## Security posture

Kane Fabric does not assume a banking, payment, DRM, or high-value-secret threat model.

The edge carries bounded participant civic artifacts and replaceable operational credentials. Some publication classes may be public and others may be restricted or encrypted by higher-layer contracts. A person with physical possession of one edge may be able to read or alter that device. The architecture must make that a local, recoverable event rather than pretending the microcontroller is physically unextractable.

Threat classes:

### A. Individual physical edge compromise

Expected to be tolerable.

A compromised device may lose local confidentiality, availability, or its replaceable device credentials. It must not gain:

- accepted geographic authority;
- candidate-promotion authority;
- Fabric release-signing authority;
- CA/issuing authority;
- the ability to redefine substrate/partition/subscription or administrative category/contract identity;
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

This keeps the reference platform recoverable, inspectable, replaceable, and suitable for civic infrastructure.

## Cryptographic role separation

Separate roles must remain separate:

```text
Fabric logical content identity
    ≠ bounded participant publication identity
    ≠ physical ESP32 identity
    ≠ Wiregate hub / browser TLS identity
    ≠ management/WireGuard identity
    ≠ optional secure-element identity
    ≠ firmware/release-signing authority
```

No private key is reused across unrelated roles.

MS5 must define a key-provider boundary for device-local cryptographic operations. The default reference edge does not require a browser TLS private key. Device-local private keys are limited to roles that actually remain on the edge, such as an optional management transport if later retained. A deployment may use software-held replaceable keys or substitute an external secure element without changing MS3/MS4 identities, browser data semantics, participant publication identity, or logical placement intent.

The secure element, when present, is a peripheral/service to the physical node. It does not define the node and does not define Fabric content.

## Firmware authenticity versus physical resistance

Firmware authenticity and transport security are useful even though physical modification of one device is tolerated.

The normal update/activation path must be able to reject damaged or unauthorized firmware artifacts and recover from failed updates. This protects fleet operation.

MS5 does not claim that a determined person with physical possession of an ESP32-S3 can never replace firmware. If they do, the resulting local device must not acquire additional Fabric authority.

Transport security likewise does not create artifact authority:

```text
authenticated transport ≠ accepted Fabric geography
authenticated transport ≠ valid participant publication
authenticated transport ≠ valid firmware artifact
```

## Storage and activation

The edge holds a focused immutable participant publication derived from or referencing released Fabric contracts. It is not required to hold the complete county substrate.

MS5 freezes a physical storage/activation model that provides:

- explicit inventory of the logical generations present;
- deterministic verification before activation;
- no mixed-generation exposure during activation;
- bounded access compatible with constrained memory;
- recovery to the last known-good activated generation after interrupted or failed update;
- replacement/migration of storage without changing logical content identity.

The implementation may use internal flash, external storage, or a combination, but storage location and storage capacity are never part of Fabric identity. Capacity is selected for the bounded deployment publication, not by assuming every edge must mirror the county.

## Browser access and secure origin

The browser remains the durable user client and still requires a trustworthy secure context with callable WebCrypto SHA-256.

For the Kane Fabric reference topology, HTTPS terminates at the **Wiregate hub**. The browser-facing administrative view can compose the county publication with bounded participant publications obtained from physical edges:

```text
browser -- HTTPS --> Wiregate / administrative web view
                         |\
                         | +--> accepted county publication
                         |
                         +-- HTTP --> ESP32-S3 bounded participant publication
```

The ESP32-S3 reference firmware therefore does not own browser certificates, browser TLS private keys, certificate renewal, county-map rendering, or browser trust configuration. Direct arbitrary `http://ESP32/...` access may be used for diagnostics or controlled backend probes, but it is not the normal browser secure-origin path.

An ESP32-hosted AP is not an MS5 browser requirement. Network attachment of the edge is an implementation concern and may evolve independently. MS5-007 must prove browser integration of a focused participant edge publication through the Wiregate/administrative web path without making WireGuard a prerequisite. Management/WireGuard feasibility remains the later MS5-008 gate.

The Wiregate hub origin/TLS identity is a serving role only. It must not contain or expose persistent geographic, association, unit, or delivery-point identity merely for convenience.

## MS5-007 laboratory transport adapter

MS5-007 proves the browser/Wiregate/physical-edge composition contract. It does **not** define how hundreds of deployed participant edges are located or managed across residential networks.

The reference board used for MS5-007 may be attached to a controlled laboratory LAN and may receive an ordinary DHCP address. That address is transient operational state. It must not be stabilized or promoted into architecture merely to make the acceptance convenient.

A valid MS5-007 laboratory run may therefore:

1. discover the reference board's current local locator;
2. verify that locator against expected physical-device evidence and the exact accepted participant artifact;
3. install a temporary, narrowly scoped operator-host policy allowing the Wiregate service to reach that verified locator on the required plain-HTTP port;
4. run the normal-browser HTTPS -> Wiregate -> physical-edge composition acceptance;
5. remove the temporary locator-specific policy before the acceptance procedure exits.

The MS5-007 laboratory adapter must **not** require or persist:

- participant-router administration;
- a DHCP reservation for the participant edge;
- a static participant-LAN address in firmware;
- inbound residential port forwarding;
- a permanent per-device firewall rule keyed to the participant-LAN address;
- a participant LAN address, MAC address, hostname, TLS name, or transport endpoint as Fabric logical identity.

This bounded adapter is acceptable because MS5-007 is proving that Wiregate can consume the physical edge's plain-HTTP publication while presenting the browser with its secure HTTPS origin. It is not the fleet transport.

The deployable scaling question is intentionally separate: a participant edge behind an independently administered network must be able to establish an authenticated operator-approved management transport without requiring the operator to control the participant's router. MS5-008 evaluates candidate transport feasibility. Fleet enrollment, registry/current-locator handling, immutable-generation synchronization, and operational replacement belong to the later managed-edge synchronization milestone.

## Management transport and WireGuard

Management/synchronization transport is distinct from browser serving and from administrative county/web/category/contract development.

WireGuard is the preferred candidate for evaluation because the maintained external ESP32 implementation has been shown to compile for ESP32-S3 with a current ESP-IDF development environment. That is feasibility evidence, not an accepted Kane Fabric dependency and not a v1 firmware requirement.

MS5 must establish runtime facts before adoption:

- an edge can establish the candidate authenticated transport outbound from an ordinary independently administered participant network without inbound port forwarding or a participant-router reservation;
- real handshake to a controlled WireGuard hub;
- routed management traffic;
- NAT/persistent-keepalive behavior;
- Wi-Fi interruption and reconnect behavior;
- repeated disconnect/reconnect;
- flash/RAM/task/socket/CPU cost;
- coexistence with edge networking, storage, plain-HTTP artifact serving, and update operations.

The result of MS5-008 may be **retain**, **reject**, or **defer**. Rejecting or deferring WireGuard does not invalidate the frozen v1 firmware role.

The reference topology may be hub-and-spoke with one WireGuard peer per edge if WireGuard is retained. A peer public key or VPN address is physical-node management configuration, never a Fabric logical identity.

Failure of WireGuard, if present, must not invalidate already activated participant artifacts. A disconnected edge should continue serving the last valid local publication by HTTP when the local path remains available.

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

It must be able to activate the same bounded participant publication and retain the same logical references to released:

- substrate content identities;
- partition keys/selections where applicable;
- subscription generation identities where applicable;
- association/unit or other participant object identities defined by the administrative contracts;
- logical placement intent.

Replacement therefore proves the MS4 rule in real hardware: physical placement and physical device identity are not logical Fabric identity.

## Normative implementation order

This section is the single authoritative definition of the detailed Milestone 5 work sequence. Current status documents may name the active item but must not maintain a second complete copy.

The sequence contains three different kinds of work and they must not be conflated:

- **core firmware implementation:** MS5-006 establishes the frozen v1 artifact appliance;
- **administrative/integration proof:** MS5-007 uses the county/web/category/contract layer to integrate a focused participant edge publication without turning the ESP32 into the county server;
- **required lifecycle/integration proof:** MS5-009, MS5-010, and MS5-011 prove update/recovery, replacement, and constrained operation without broadening the v1 feature set;
- **candidate capability evaluation:** MS5-008 evaluates management transport and may retain, reject, or defer WireGuard.

```text
MS5-001  physical-edge threat model, trust boundary, and replaceability contract
MS5-002  storage inventory, verification, activation, rollback, and recovery contract
MS5-003  device cryptographic role separation and replaceable key-provider boundary
MS5-004  Wiregate-terminated browser secure-origin plus hub-to-edge HTTP contract
MS5-005  ESP-IDF/toolchain and retained dependency selection plan
MS5-006  ESP32-S3 v1 artifact appliance: immutable storage, verification, diagnostics, and HTTP byte-range implementation
MS5-007  county/web/category/contract integration of a focused participant edge publication through Wiregate HTTPS and ESP32-S3 HTTP
MS5-008  candidate outbound management transport and WireGuard runtime/resource feasibility proof across ordinary participant NAT; retain, reject, or defer
MS5-009  firmware authenticity, update, rollback, and recovery proof
MS5-010  physical device replacement/reprovisioning identity-preservation proof
MS5-011  constrained-resource and concurrent-workload acceptance evidence
MS5-012  release evidence and milestone closeout
```

## Exit gate

Milestone 5 is complete when all of the following are demonstrated with the reference ESP32-S3-class edge and the administrative integration path:

1. the firmware source and build inputs are tracked in the Kane Fabric repository, the exact pinned ESP-IDF/toolchain builds successfully on the dedicated ESP programming node, and the flashed device exposes its firmware build identity through diagnostics;
2. the device mounts prepared artifact storage read-only, verifies active inventory before serving, serves ordinary GET plus the accepted exact closed byte-range behavior, and fails closed on invalid active state;
3. a normal browser consumes a focused participant publication through Wiregate HTTPS while the ESP32-S3 serves that bounded publication to the hub by plain HTTP; the accepted county substrate remains an administrative publication rather than an ESP32 storage prerequisite;
4. the browser/admin composition validates the participant publication and the immutable Fabric logical identities it references;
5. storage activation and firmware/update failure do not expose a mixed or silently corrupted generation and have a tested recovery path;
6. the edge remains useful for already activated local data when upstream management connectivity is unavailable;
7. physical replacement/reprovisioning can change every device-local identity while retaining the same participant publication and Fabric logical content/placement references;
8. management transport feasibility is measured rather than assumed, including operation from an ordinary independently administered participant network without DHCP reservation or inbound port forwarding; WireGuard is retained only if the runtime/resource proof justifies it, and rejection or deferral is a valid MS5-008 outcome;
9. no irreversible ESP32 eFuse operation is required to satisfy the Kane Fabric reference-edge contract;
10. optional external secure-element use remains substitutable and does not alter Fabric logical identities.

The output of MS5 becomes the physical-node foundation for bounded participant custody/contribution, while county-wide geography, web presentation, categories, contracts, and independent-operator interoperability remain administrative infrastructure.