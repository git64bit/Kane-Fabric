# Milestone 5 implementation

This directory implements the active Milestone 5 contract from
`docs/MILESTONE_5_DESIGN.md`.

The current contract slice covers MS5-001 through MS5-004. It deliberately
contains no ESP-IDF firmware and performs no irreversible hardware operation.

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
: device-local cryptographic key-provider boundary. The v1 private-key roles are
limited to browser TLS serving and optional management transport. Software and
external providers are interchangeable at this contract boundary. Fabric
release-signing, geographic-promotion, CA-issuing, and civic-anchor keys are not
valid edge roles.

`tools/kane_fabric_browser_access.py`
: browser secure-origin and local AP/STA access contract. The physical edge must
serve through HTTPS with a browser-trusted certificate, prove a secure browser
context with callable WebCrypto SHA-256, provide deterministic ESP32-hosted AP
reachability, preserve the shared-radio/channel measurement obligations of
AP+STA operation, and keep browser/TLS identity outside Fabric geography and
delivery-point identity.

## Fixed MS5 security posture

The reference edge is replaceable infrastructure carrying primarily public
Fabric artifacts and replaceable operational credentials.

- individual physical-device compromise is local and recoverable;
- fleet-class firmware/provisioning defects are systemic;
- authority/signing compromise is systemic and outside the edge boundary;
- no irreversible ESP32 security eFuse operation is an MS5 requirement;
- no secure element is mandatory;
- an external secure element may implement the same replaceable key-provider
  interface;
- changing ESP32 hardware, storage, TLS identity, management identity, or key
  provider must not change MS3/MS4 logical identities;
- a browser origin/TLS identity is a device-serving role, not persistent
  geographic or delivery-point identity.

## Tests

Run:

```bash
bash ms5/run-tests.sh
```

The tests are contract tests. Real ESP32-S3 firmware, browser execution,
storage, WireGuard, and concurrent-resource proofs occur in later MS5 work
items. MS5-004 contract tests define the secure-origin/AP+STA obligations; they
do not substitute for the later real-browser and constrained-resource proofs.
