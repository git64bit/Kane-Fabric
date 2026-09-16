# Firmware Authority implementation boundary

This directory is the non-secret repository side of the Kane Fabric Firmware Authority Node. It is subordinate to `docs/MILESTONE_5_DESIGN.md`; it does not create a parallel Milestone 5 work sequence.

The physical CPE placement is recorded in `docs/CIVICVS_PROJECT_ENVIRONMENT.md`.

Current state is deliberately inert:

```text
Firmware Authority Node
status: repository scaffold only
physical host: Dell Precision / 10.110.0.9
container: firmware-authority
container network identity: NOT ASSIGNED
private signing key: NOT CREATED
signing: DISABLED
operational acceptance: MS5-009
```

The **physical Dell host already has CPE/Wiregate address `10.110.0.9/22`**. `network identity: NOT ASSIGNED` refers only to the future `firmware-authority` container. Do not conflate the host address with a container address.

## Physical placement

The reference deployment is an **unprivileged LXD container on the separate Dell Precision Ubuntu/LXD host**. The Dell already carries unrelated RAG/LLM workloads. The Firmware Authority does not require GPU access and Kane Fabric must not disturb existing GPU/device passthrough merely because it shares that physical host.

The Dell host is inside the authority trust boundary because LXD containers share the host kernel. Persistent firmware-signing private key custody therefore remains outside the container in a hardware-backed signer selected and accepted by MS5-009.

Before any container creation or mutation, perform a bounded **read-only LXD inventory** and record the actual host hostname/Ubuntu release, LXD version, projects, storage pools, profiles, networks/bridges, existing instances, available resources, passthrough state, and management/file-transfer path. Do not invent any of those values. The Dell is not Proxmox; `pct` commands do not apply.

## Role separation

```text
CPE build/programming workstation: fw / 10.110.0.4
  builds firmware and produces artifact/provenance evidence

Firmware Authority host: Dell Precision / 10.110.0.9
  Ubuntu/LXD host for the authority role

Firmware Authority container: firmware-authority
  verifies proposed release material
  prepares/normalizes the release manifest
  requests operator-authorized signing from an external hardware-backed signer
  does not contain an ordinary persistent signing private-key file

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

The manifest contract is device-family generic. ESP32-S3 is the first enabled family; Zigbee-capable and future families are added as explicit families rather than creating a separate signing authority per platform.

The cryptographic authorization envelope is not frozen yet because the hardware-backed signing provider has not been selected. Until MS5-009 freezes the signer/provider/algorithm and real verification evidence, this repository contains no private-key generation or operational signing command.
