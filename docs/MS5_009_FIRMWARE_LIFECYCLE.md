# MS5-009 Firmware Authenticity, Update, Rollback, and Recovery

## Status

MS5-009 is the active normative work item after MS5-008 closed with `defer`.

The machine-readable repository contract is:

```text
ms5/firmware-lifecycle-contract.json
```

Executable validation is:

```text
ms5/tools/kane_fabric_firmware_lifecycle.py
ms5/tests/test_firmware_lifecycle.py
```

## Starting point

The project already has the accepted ESP32-S3 artifact appliance, exact
ESP-IDF/toolchain selection, a canonical firmware release-manifest contract,
and a physically accepted inert `firmware-authority` LXD container on
`annales`.

Signing remains disabled. No private release-signing key is created by this
contract.

## Update architecture

The accepted reference layout remains fixed:

```text
nvs      0x009000   24 KiB
phy_init 0x00f000    4 KiB
factory  0x010000    1 MiB
fabric   0x110000    4 MiB
```

The 16 MiB device has sufficient unused flash after the Fabric partition to add:

```text
otadata  0x510000    8 KiB
ota_0    0x520000    1 MiB
ota_1    0x620000    1 MiB
unused   0x720000 .. 0xFFFFFF
```

This is additive: accepted factory, Fabric, and provisioning NVS locations do
not move.

## Fixed lifecycle boundary

Normal firmware update must be transport-independent, require authorization of
the canonical release manifest, verify the exact firmware SHA-256, enforce
release sequence/normal-path rollback floor, trial-boot before confirmation,
retain the previous valid image until health confirmation, roll back a failed
trial, preserve Fabric and provisioning NVS, remain useful without management
transport, and require no irreversible eFuse operation.

## Signing boundary

The Firmware Authority remains inert while lifecycle machinery is implemented.

The authorization envelope is now frozen independently of the physical signer:

```text
signed object        canonical release manifest SHA-256
algorithm            ECDSA P-256 / SHA-256
signature encoding   fixed 64-byte P1363 r || s
public key encoding  65-byte uncompressed SEC1 P-256
key identifier       SHA-256 of exact public-key bytes
```

The ESP32 verifier accepts public verification material only. The physical
hardware-backed signer provider, concrete key identity, and key-transition /
recovery procedure remain a separate activation gate. The authority container
may never gain an ordinary persistent private release-signing key file.
