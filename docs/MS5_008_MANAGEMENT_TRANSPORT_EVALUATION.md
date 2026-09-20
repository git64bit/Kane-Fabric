# MS5-008 — Management Transport Candidate Evaluation

## Status

Repository evaluation contract for the active MS5-008 work item.

Normative architecture remains in `docs/MILESTONE_5_DESIGN.md`. This document
does not retain WireGuard as a Kane Fabric dependency and does not authorize a
firmware flash, management hub, persistent credential, participant-router
change, or live tunnel.

Machine-readable authority:

```text
ms5/management-transport-candidate.json
```

Executable repository validator:

```text
ms5/tools/kane_fabric_management_transport.py
```

## Candidate identity

MS5-008 evaluates exactly this WireGuard implementation:

```text
repository     esphome-libs/wireguard
component      esphome/wireguard
version        0.4.6
tag            v0.4.6
commit         cddaa4eab4e633847bf846723ac0449a34c3d2f7
published      2026-08-17
license        BSD-3-Clause
```

The release is an evaluation candidate only. Its presence in the MS5-008 record
does not add it to `third_party/manifest.json`, make it a v1 firmware
requirement, or make WireGuard a prerequisite for the already accepted browser
path.

The candidate's ESP-IDF component metadata declares:

```text
esphome/libsodium ^1.10021.1
```

A floating compatible range is unsuitable for comparative runtime evidence.
MS5-008 therefore freezes the evaluation dependency resolution to:

```text
repository     esphome-libs/libsodium
component      esphome/libsodium
version        1.10021.11
tag            1.10021.11
commit         40c22448d6e8f42be56c45f739b52a5c8d21c8ca
release asset  libsodium-1.10021.11.tar.gz
SHA-256        72696259f15278f146b700854798f639aa5ab193e0068f2f1f56d6d3cbe9692f
license        MIT
```

The libsodium release itself is not recorded by GitHub as immutable, so the
evaluation identity relies on the exact commit plus the published release-asset
SHA-256, not the mutable tag name alone.

## Evaluation boundary

The candidate must remain separate from Fabric identity and from browser
serving.

MS5-008 does not permit the evaluation to require:

- participant-router administration;
- inbound residential port forwarding;
- a participant DHCP reservation;
- a static participant-LAN firmware address;
- a WireGuard key, tunnel address, endpoint, hostname, MAC address, or LAN
  locator as Fabric logical identity.

WireGuard remains optional management transport. Loss of the candidate
management path must not invalidate an already activated participant
publication that can still be served locally.

## Required evidence before a retain decision

The physical evaluation must produce evidence for all of the following before
WireGuard can be retained:

1. exact pinned ESP32-S3 build against the accepted ESP-IDF v6.0.3 baseline;
2. outbound establishment from an ordinary independently administered
   participant NAT;
3. no inbound port forwarding and no participant-router reservation;
4. authenticated handshake to a controlled WireGuard hub;
5. routed management traffic through the tunnel;
6. NAT behavior with persistent keepalive;
7. Wi-Fi interruption and reconnect;
8. repeated disconnect/reconnect;
9. flash, RAM, task, socket, and CPU cost;
10. coexistence with plain-HTTP artifact serving, storage operations, and update
    operations;
11. continued validity of the last activated participant publication when the
    management path is unavailable.

These are feasibility measurements, not thresholds invented in advance. The
evidence should support a later architectural decision about whether the
candidate is proportionate to the reference ESP32-S3 role.

## Decision rule

Valid MS5-008 outcomes are:

```text
retain
reject
defer
```

Before physical runtime evidence exists, the state is `defer`.

A `retain` outcome requires all required evidence plus a separate dependency
policy follow-up: exact source retention/vendoring strategy, license/notice
review, offline reproduction, and an explicit addition to
`third_party/manifest.json`.

A `reject` or `defer` outcome leaves the accepted browser/Wiregate/ESP32
artifact path unchanged and does not make the v1 firmware incomplete.

## Repository acceptance

This primitive is accepted only when CT102 proves:

- the candidate JSON validates;
- its ESP-IDF reference pin matches `ms5/toolchain-selection.json`;
- WireGuard is still absent from `third_party/manifest.json`;
- the MS5 work-sequence authority remains valid;
- the development dependency-policy check passes;
- Python compileall succeeds for `ms5`;
- the complete MS5 repository test suite passes;
- the CT102 checkout is clean after synchronization.

That repository acceptance authorizes construction of the later physical
outbound-handshake gate on `fw`. It does not itself authorize a flash or live
tunnel.
