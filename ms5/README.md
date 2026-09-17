# Milestone 5 implementation

This directory implements the active Milestone 5 contract from
`docs/MILESTONE_5_DESIGN.md`.

MS5-001 through MS5-005 define the physical-edge contracts. MS5-006 contains
the ESP-IDF reference firmware components under `ms5/esp32_reference/`.

The physical ESP32-S3 MS5-006 device-runtime gate was accepted on 2026-09-17 at
implementation head `7aa3c836bae470704d051a36a6261a1140e9d3d0`. The acceptance record is:

```text
docs/CPE_ESP32_MS5_006_DEVICE_RUNTIME_ACCEPTANCE.md
```

MS5-006 is therefore no longer the active development bottleneck. The active
work returns to the administrative county/web/category/contract layer needed by
MS5-007. The governing separation is:

```text
docs/ADMINISTRATIVE_EDGE_BOUNDARY.md
administration/README.md
```

## Current reference topology

The ESP32-S3 is a bounded participant edge, not a miniature county node:

```text
accepted county geography
+ county web/map
+ categories/contracts
             ^
             | compose / integrate
             |
      bounded participant publication
             ^
             |
          ESP32-S3
```

The browser-facing path may obtain a bounded participant publication through
Wiregate while the county substrate remains an administrative publication:

```text
browser -- HTTPS --> Wiregate / administrative web view
                         |\
                         | +--> accepted county publication
                         |
                         +-- HTTP --> ESP32-S3 bounded participant publication
```

Browser HTTPS, certificate lifecycle, county-map composition, categories, and
browser trust remain outside the ESP32-S3. The reference firmware serves
immutable bounded artifacts by plain HTTP and does not require a
`browser-tls-server` private key.

WireGuard remains a later management-transport candidate. It is not required
for the browser path and is not pulled forward merely to make MS5-007 work.

## Why firmware exists in the first release

The ESP32-S3 role is deliberately modest. Its first-release purpose is to make
firmware a first-class Kane Fabric component now, while the system is still
being built, rather than forcing a new firmware lifecycle into a mature
software-only architecture later.

The initial firmware establishes:

- a pinned ESP-IDF/toolchain build;
- firmware source and release artifacts;
- immutable physical storage;
- bounded HTTP/range serving;
- provisioning and physical replacement;
- later update/recovery and management extension points.

The microcontroller does not own county geography, the county web map,
category/contract administration, browser TLS, certificate management, or human
account/person identity.

## Contract modules

`tools/kane_fabric_edge.py`
: physical-edge trust and replaceability contract. It binds a replaceable
physical instance to logical placement without allowing the physical node to
acquire geographic, promotion, release-signing, credential-issuing, or peer
authority.

`tools/kane_fabric_storage.py`
: immutable storage inventory and whole-inventory activation/rollback contract.
An activation selects one verified inventory identity; components are not
independently promoted. Storage paths outside the logical artifact inventory are
physical implementation details.

`tools/kane_fabric_keys.py`
: device-local cryptographic key-provider boundary. Browser TLS is not an edge
private-key role. The current allowed private-key role is optional management
transport. Software and external providers remain interchangeable. Fabric
release-signing, geographic-promotion, CA-issuing, and civic-anchor keys are not
valid edge roles.

`tools/kane_fabric_browser_access.py`
: browser secure-origin and Wiregate/edge transport contract. The browser uses
HTTPS to a browser-trusted Wiregate hub; the hub may use plain HTTP to a
physical edge. The edge publication is bounded participant data; the county
substrate is not an ESP32 storage prerequisite.

`tools/kane_fabric_firmware_v1.py`
: executable freeze of the v1 responsibility boundary. It explicitly excludes
county-wide substrate replication, county web-map hosting, and category/
publication-contract administration from the ESP32 role.

`tools/kane_fabric_toolchain.py`
: MS5-005 firmware SDK/toolchain selection contract. It freezes the reference
ESP32-S3 SDK source identity, Linux-amd64 Xtensa compiler identity, license
boundary, offline-reproduction requirements, and the rule that WireGuard remains
an unretained candidate until the MS5-008 runtime proof.

Machine-readable toolchain selection:

```text
ms5/toolchain-selection.json
```

Detailed selection/reproduction plan:

```text
docs/MS5_TOOLCHAIN_DEPENDENCY_PLAN.md
```

## Active work

The next normative work item is MS5-007, now defined as county/web/category/
contract integration of a focused participant edge publication through
Wiregate HTTPS and ESP32-S3 HTTP.

The immediate development work is administrative, not firmware:

- county-facing category/object model;
- participant-publication contract;
- association/unit reference semantics;
- public/restricted/private classification semantics;
- web/map composition;
- independent county-operator conformance boundary.

Later MS5 firmware lifecycle work remains required for closeout: management
transport evaluation, update/rollback/recovery, physical replacement, and
constrained-resource acceptance.

## Tests

Run:

```bash
bash ms5/run-tests.sh
```

Repository tests validate the contracts and implementation shape. The pinned
ESP-IDF build and physical MS5-006 storage/network/HTTP/fail-closed behavior are
accepted separately on the dedicated ESP programming node.