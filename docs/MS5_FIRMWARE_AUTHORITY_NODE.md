# MS5 Firmware Authority Node — Implementation Plan

## Authority

This document refines the firmware-authority portions of `docs/MILESTONE_5_DESIGN.md`. It is subordinate to that design authority and does not replace or reorder the normative MS5-001 through MS5-012 sequence.

The logical role is introduced now so firmware lifecycle architecture is not retrofitted after physical devices exist. Operational signing acceptance remains **MS5-009: firmware authenticity, update, rollback, and recovery proof**.

## Purpose

The Firmware Authority Node decides whether a proposed firmware artifact is an authorized CIVICVS/Kane Fabric firmware release. It does not build firmware merely because it can verify build provenance, and it does not distribute firmware merely because it can authorize a release.

The required separation is:

```text
source in GitHub main
        ↓
CPE build/programming workstation
(build artifact + provenance)
        ↓
Firmware Authority Node
(verify + normalize manifest + authorize)
        ↓
Firmware Distribution
(store/deliver artifact + manifest + authorization)
        ↓
physical device
(public verification material only)
```

Compromise of the build workstation alone must not authorize firmware. Compromise of distribution alone must not authorize firmware. Compromise of the authority container alone must not disclose an ordinary file-based signing private key because the private signing operation is held outside the container in hardware-backed custody.

## Reference placement

The reference Firmware Authority Node is an **unprivileged LXC/LXD container on a separate Dell Precision-class physical host** from the CPE Build and Hardware Workstation.

The physical host may carry unrelated compute workloads, but the Firmware Authority container is not granted GPU access and must remain minimal. Containers share the host kernel, so the physical host remains inside the authority trust boundary. Hardware-backed key custody limits what compromise of the host/container filesystem can extract.

Reference logical name:

```text
firmware-authority
```

The name is deliberately platform-neutral. Do not name it `esp-signing`, `esp32-signing`, or otherwise bind the authority to the first device family.

## Initial inert state

Before MS5-009 activation:

```text
Firmware Authority Node
status: architectural placeholder / implementation scaffold
private signing key: NOT CREATED
persistent private signing key in container: PROHIBITED
signing enabled: NO
network identity: NOT ASSIGNED
CPE/WireGuard address: NOT ASSIGNED
release authority: NOT OPERATIONALLY ACTIVE
acceptance: MS5-009
```

Do not allocate a scarce CPE address merely because the container exists. Independent CPE addressing must be justified by a later operational requirement.

## Key custody

The release-signing private key must not be an ordinary PEM, OpenSSH, raw seed, or other reusable private-key file stored in the container, its snapshot, its backup, the CPE workstation, the firmware distribution system, or an edge device.

MS5-009 must select a hardware-backed signer/provider that keeps private key material non-exportable or otherwise materially outside ordinary container filesystem custody. The preferred operating model requires deliberate operator presence such as PIN and/or physical touch for a release-signing operation.

The container may retain:

- public verification keys and fingerprints;
- signer/provider metadata that is not secret;
- release policy;
- canonical firmware release manifests;
- signed authorization objects after activation;
- audit and acceptance evidence.

Container snapshots and backups must be sufficient to recover software state but must **not** be sufficient to clone the private release-signing key.

## Build, authorization, and distribution are distinct

The CPE Build and Hardware Workstation owns reproducible compilation and physical programming. It may produce a candidate artifact plus provenance, but it does not decide that the candidate is an authorized release.

The Firmware Authority verifies the proposed artifact/provenance against accepted project policy and constructs or normalizes the canonical release manifest. When signing is later activated, it submits only the accepted manifest identity/content to the hardware-backed signer.

Firmware Distribution stores or transports already-authorized artifacts. It need not share a physical node with the authority, even if an early deployment temporarily co-locates non-secret distribution files. Distribution compromise must not become signing compromise.

## Canonical release manifest

The release manifest binds authorization to more than a binary filename. Version 1 records:

```text
release.device_family
release.target
release.version
release.sequence
firmware.name
firmware.byte_length
firmware.sha256
source.repository
source.commit
build.toolchain_record
build.toolchain_record_sha256
build.build_identity
recovery.rollback_floor_sequence
recovery.recovery_compatible
manifest_sha256
```

The deterministic contract is implemented by `ms5/tools/kane_fabric_firmware_authority.py`.

The `manifest_sha256` identifies the normalized manifest body. A later MS5-009 signing envelope must authorize this manifest rather than blindly authorizing an uncontextualized binary digest.

## Device-family model

Firmware Authority is one logical role with explicit device-family namespaces:

```text
Firmware Authority
├── esp32-s3
├── zigbee-family-a
├── future-device-family
└── recovery / key-transition records
```

ESP32-S3 is the first enabled family. Zigbee-capable hardware may use an ESP32 variant, a separate radio MCU, or another platform; that does not create a second authority architecture.

Where a platform later requires its own bootloader/native image-signature format, that signature is a platform mechanism. CIVICVS release authorization remains the project-level manifest authorization. The two may coexist and must not be conflated.

## Relationship to ESP32 security posture

This authority design does not reverse the MS5 rule against requiring irreversible ESP32 eFuse security operations. Firmware authorization and recoverable reference hardware are compatible.

The project may prove that the normal update path rejects unauthorized firmware without claiming that physical possession of an ESP32-S3 makes firmware replacement impossible. A locally modified edge still acquires no geographic, CA, promotion, or release-signing authority.

## Staged implementation

The implementation is deliberately staged without changing the normative MS5 sequence:

1. **Repository contract:** freeze role separation, inert authority state, device-family model, and canonical manifest structure.
2. **Container scaffold:** create the unprivileged `firmware-authority` container with no private key, no signer passthrough, no GPU, and no CPE address unless later justified.
3. **Verification workflow:** accept artifact/provenance input and reproduce manifest identity without signing.
4. **Signer selection:** select hardware-backed signer/provider and freeze public-key, algorithm, key-id, and authorization-envelope representation.
5. **MS5-009 activation:** generate/import the release key under accepted hardware-backed custody, prove operator-authorized signing, device-side verification, unauthorized-artifact rejection, update, rollback, recovery, key-transition/recovery procedure, and loss/rebuild of the container without loss of private-key custody.

Steps 1–3 are non-secret and reversible. Step 5 is the first point at which real release-signing authority becomes operational.

## Initial repository state

`ms5/firmware_authority/authority-state.json` is the machine-readable placeholder state. It intentionally records:

- unprivileged LXC/LXD deployment class;
- container name `firmware-authority`;
- no network identity;
- ESP32-S3 as the first enabled device family;
- no private signing key created;
- signing disabled;
- hardware-backed signer required for activation;
- operator presence required for release signing;
- MS5-009 as the activation/acceptance gate.

A repository change must not silently flip those placeholder booleans. Real activation requires explicit MS5-009 evidence and an accepted design change.


## MS5-009 interrogation status — 2026-09-21

Repository reconciliation found that implementation advanced beyond staged step 4 without completing the signer-selection decision.

Corrective authority: `docs/MS5_009_AUTHORITY_INTERROGATION.md`.

Current staged-plan status:

- step 1 repository role/manifest contract — accepted;
- step 2 inert container scaffold — accepted;
- step 3 unsigned verification workflow — substantially established;
- step 4 signer/provider + algorithm/envelope — **NOT ACCEPTED**;
- step 5 operational signing activation — **NOT STARTED**.

Current P-256 authorization code is a candidate only. No further authenticity implementation should proceed until step 4 is resolved as a design checkpoint.
