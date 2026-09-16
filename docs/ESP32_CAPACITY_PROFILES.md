# ESP32 Capacity Profiles

## Purpose

Kane Fabric keeps **physical storage capacity separate from device utility and civic semantics**.

A flash partition size answers only a physical deployment question: how much local storage is available to the firmware role currently installed on the device. It does not define the jurisdiction, legal regime, association type, document taxonomy, geographic identity, or application purpose of the bytes stored there.

This distinction is required because the reference ESP32-S3 is replaceable and reflashable. The same physical board may be provisioned for different firmware roles over its lifetime. Those roles do not need to coexist in one firmware image or one storage layout.

## Capacity is not utility

The following must remain separate:

```text
physical capacity profile
    != firmware utility
    != jurisdiction or civic classification
    != Fabric logical identity
```

Examples of utility include the current Kane Fabric immutable-artifact edge role and possible later specialized civic roles. A future role may need different firmware and a different storage allocation. Reflashing the physical device for another role does not change the meaning of a Kane Fabric logical identity.

Likewise, deployment-specific properties such as country, state, jurisdiction, association or institution type, document classes, registrations, licenses, contracts, statutory requirements, record formats, and similar classifications belong in the data/inventory model above the physical partition layer. They must not be encoded into ESP32 partition names or offsets.

## Capacity tiers

Capacity profiles are implementation envelopes, not semantic types.

A deployment may define tiers such as:

```text
DATA-2   approximately 2 MiB role-data capacity
DATA-4   approximately 4 MiB role-data capacity
DATA-6   approximately 6 MiB role-data capacity
DATA-8   approximately 8 MiB role-data capacity
```

The exact usable bytes depend on the physical flash layout, alignment, filesystem overhead, firmware/update requirements, and platform constraints. The tier name therefore describes an intended capacity class rather than a wire-format identity.

Logical records may use their own deterministic sizing rules independent of flash erase/alignment requirements. For example, a future 160-byte record format with a target of 10,000 records represents 1,600,000 raw bytes before filesystem, index, inventory, and safety overhead. That calculation may justify a DATA-2 or larger deployment profile without making the 160-byte record format itself a flash-layout property.

When a deployment outgrows one capacity tier, moving to a larger tier must not require redefining its logical schema merely because more physical storage is available.

## Kane Fabric ESP32-S3 first reference profile

The current reference device has 16 MiB of internal flash. For MS5-006, the first bounded artifact-storage profile reserves **4 MiB** for immutable Fabric data while leaving the remainder uncommitted for firmware lifecycle, later update/recovery work, alternate layouts, and future evidence.

The partition label remains deliberately generic:

```text
fabric
```

For the ESP-IDF FAT raw-flash implementation it is a `data,fat` partition mounted read-only by the Kane Fabric storage component.

The first reference table is tracked as:

```text
ms5/esp32_reference/partitions.fabric-4m.csv
```

This is a **reference capacity profile for the current 16 MiB ESP32-S3**, not a universal Kane Fabric partition map and not a requirement for other edge implementations.

## NVS boundary

ESP-IDF NVS remains for relatively small device-local state such as configuration, counters, selected operational metadata, and similarly bounded values.

Bulk immutable Fabric artifacts, large record collections, and application archives do not belong in NVS merely because NVS is available. They use the role-data storage mechanism selected for that deployment.

## Portability

Kane Fabric is intended to remain portable across jurisdictions and implementations. A deployment in another county, state, hardware platform, or civic context may select a different capacity profile without changing the project’s authority, identity, inventory, or browser/publication contracts.

Physical capacity is therefore a deployment choice. Utility and civic meaning are expressed above it.
