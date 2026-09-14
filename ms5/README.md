# Milestone 5 implementation

This directory implements the active Milestone 5 contract from
`docs/MILESTONE_5_DESIGN.md`.

MS5-001 through MS5-005 define the physical-edge contracts. MS5-006 now also
contains the first ESP-IDF reference firmware components under
`ms5/esp32_reference/`.

## Current reference topology

The first-release browser path is:

```text
browser -- HTTPS --> Wiregate hub -- HTTP --> ESP32-S3
```

Browser HTTPS, certificate lifecycle, and browser trust terminate at the
Wiregate hub. The ESP32-S3 reference firmware serves immutable artifacts by
plain HTTP and does not require a `browser-tls-server` private key.

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

The microcontroller does not need to own browser TLS, certificate management,
or every future synchronization function to justify its inclusion.

## Contract modules

`tools/kane_fabric_edge.py`
: physical-edge trust and replaceability contract. It binds a replaceable
physical instance to an existing MS4 logical placement without allowing the
physical node to acquire geographic, promotion, release-signing, credential-
issuing, or peer authority.

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
: browser secure-origin and local Wiregate/edge transport contract. The browser
uses HTTPS to a browser-trusted Wiregate hub; the hub uses plain HTTP to the
physical edge. The contract explicitly does not require an ESP32-hosted AP or
WireGuard for the browser path.

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

## Tests

Run:

```bash
bash ms5/run-tests.sh
```

Repository tests validate the contracts and the current MS5-006 implementation
shape. Real pinned ESP-IDF compilation and physical-device evidence remain
separate gates and must not begin until the current architecture correction is
accepted.
