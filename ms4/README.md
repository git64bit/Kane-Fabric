# Milestone 4 implementation

This directory contains the implementation of Kane Fabric Milestone 4 logical geographic partitions and application subscriptions.

The normative work sequence is maintained only in `docs/MILESTONE_4_DESIGN.md`.

## MS4-001 partition identity

`tools/kane_fabric_partition.py` freezes the v1 logical partition descriptor and key algorithm.

A partition identity is the SHA-256 of canonical JSON containing only:

- the partition identity format/version;
- explicit jurisdiction identity; and
- a normalized logical scope envelope.

The stable key is `kfp1-` plus the first 32 hexadecimal characters of that SHA-256. Human labels are carried by the descriptor but are excluded from identity. Floating-point scope values are rejected at this layer so class-specific normalization can freeze their representation before hashing. Physical device/network/storage metadata is forbidden from the identity document.

Run:

```bash
bash ms4/run-tests.sh
```

## MS4-002 scope normalization and inclusion

The partition module normalizes WGS84 coordinates to fixed seven-decimal text and defines whole-jurisdiction, explicit bounded, accepted-boundary administrative, and deterministic composite scopes. Bounding-box intersection is inclusive: boundary-touching and boundary-crossing objects/chunks are selected rather than clipped, preventing partition-edge holes while preserving logical object identity.

## MS4-003 substrate partition selection

`tools/kane_fabric_selection.py` compiles a deterministic selection manifest that binds one partition identity to one canonical Milestone 3 substrate content identity and exact selected road/water chunk references. It verifies component bytes against the substrate manifest before producing references.

## MS4-004 / MS4-005 subscription generations and geographic references

`tools/kane_fabric_subscription.py` defines independently versioned subscription generations. A generation binds application ownership, rights/license metadata, compatible substrate identity, explicit partition coverage, canonical object bytes, and immutable Fabric geographic references. Fabric references bind dataset, accepted release key/hash, and persistent object key without transferring application ownership into Kane Fabric geography.
