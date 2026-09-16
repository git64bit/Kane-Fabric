# Firmware Authority implementation boundary

This directory is the non-secret repository side of the Kane Fabric Firmware Authority Node.
It is subordinate to `docs/MILESTONE_5_DESIGN.md`; it does not create a new Milestone 5 work sequence.

Current state is deliberately inert:

```text
Firmware Authority Node
status: architectural placeholder / implementation scaffold
container: firmware-authority
private signing key: NOT CREATED
signing: DISABLED
network identity: NOT ASSIGNED
operational acceptance: MS5-009
```

The reference deployment is an **unprivileged LXC/LXD container on a separate physical host** from the CPE build/programming workstation. The container may hold policy, canonical release manifests, public verification keys, signatures/authorizations after activation, and audit/evidence records. It must not hold an ordinary persistent firmware-signing private-key file.

A later MS5-009 gate must select and accept the hardware-backed signer and its provider-specific interface. Until that gate, this repository contains no private-key generation or signing command.

## Role separation

```text
CPE build/programming workstation
  builds firmware and produces artifact/provenance evidence

Firmware Authority Node
  verifies proposed release material
  prepares/normalizes the release manifest
  requests operator-authorized signing from an external hardware-backed signer

Firmware Distribution
  stores/delivers firmware + manifest + authorization
  cannot create authorization

Physical edge
  receives firmware
  holds only public verification material needed by the retained update design
```

Build authority is not signing authority. Distribution is not signing authority. Authenticated transport is not firmware authorization.

## Release manifest

The repository contract is implemented by `ms5/tools/kane_fabric_firmware_authority.py`.
A release manifest identifies at minimum:

- device family and target;
- release version and monotonic release sequence;
- firmware filename, byte length, and SHA-256;
- Git source repository and exact commit;
- toolchain record identity and build identity;
- rollback floor and recovery compatibility;
- deterministic manifest SHA-256.

The manifest contract is intentionally device-family generic. ESP32-S3 is the first enabled family; Zigbee-capable and future device families are added as explicit families rather than creating a separate signing authority per platform.

The cryptographic authorization envelope is not frozen yet because the hardware-backed signing provider has not been selected. MS5-009 must freeze that representation together with algorithm/key-provider selection and real verification evidence.
