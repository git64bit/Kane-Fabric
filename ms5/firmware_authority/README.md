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

The Dell host is inside the authority trust boundary because LXD containers share the host kernel. The 2026-09-22 Civic functionality/platform-neutrality decision removes the prior hardware-backed-custody requirement: MS5-009 must retain a portable software-capable signing path, with any optional hardening remaining non-authoritative and removable.

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
  performs or requests operator-authorized signing through the selected replaceable provider
  must remain operable without a proprietary hardware/security service

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

The cryptographic authorization envelope is now frozen independently of the
physical signing provider:

```text
algorithm            ECDSA P-256 / SHA-256
signature encoding   64-byte P1363 r || s
public key encoding  65-byte uncompressed SEC1 P-256
key identifier       SHA-256 of exact public-key bytes
signed object        SHA-256 of the fixed 152-byte firmware authorization payload
```

The signing provider is still not selected or activated.
This repository still contains no release-signing private key and no
operational release-signing authority. Provider selection must now begin from a
portable software-capable baseline; hardware/tooling discovery may inform
optional hardening but cannot define the authority or become a prerequisite.


## Signer-provider status

The 2026-09-21 `annales` preflight found zero hardware-signer candidates and
no PIV/PKCS#11 tooling. This does not select or imply any provider class.

The provider remains deliberately **selection-pending**. The baseline provider
must be portable and software-capable, preserve deliberate operator
authorization, remain compatible with the project authorization format, and
support documented loss/backup/transition behavior without making a proprietary
hardware or service provider part of Firmware Authority identity.

ATECC608A/ATECC608A-class custody and irreversible ESP security-eFuse custody
are prohibited project mechanisms. YubiKey, PIV, PKCS#11, HSM, USB-token,
remote-signer, slot, PIN, and touch mechanisms may be evaluated only as
optional hardening or interfaces; none is a baseline prerequisite.


## Current design-interrogation hold

The original scaffold required signer/provider selection and cryptographic authorization-format freeze to occur as one staged MS5-009 decision. A later implementation introduced a P-256 candidate before that selection was complete. It is now explicitly provisional.

See `docs/MS5_009_AUTHORITY_INTERROGATION.md`.

Do not install signer tooling, attach signer hardware, create/import a release key, or extend provider-specific code until that interrogation is accepted.
