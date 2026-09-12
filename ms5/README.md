# Milestone 5 implementation

This directory implements the active Milestone 5 contract from
`docs/MILESTONE_5_DESIGN.md`.

The initial implementation slice covers MS5-001 through MS5-003. It deliberately
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
  provider must not change MS3/MS4 logical identities.

## Tests

Run:

```bash
bash ms5/run-tests.sh
```

The tests are contract tests. Real ESP32-S3, browser, storage, WireGuard, and
concurrent-resource proofs occur in later MS5 work items.
