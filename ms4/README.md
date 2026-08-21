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
