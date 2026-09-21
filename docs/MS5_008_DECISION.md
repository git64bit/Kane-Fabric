# MS5-008 Management Transport Decision

## Decision

MS5-008 is closed with the permitted outcome:

```text
defer
```

WireGuard is not retained as a Kane Fabric dependency or v1 firmware
requirement.

The exact-pinned ESP32-S3 candidate build succeeded and a physical evaluation
was attempted. The device reached its accepted participant runtime, then
panicked with `LoadProhibited` before authenticated WireGuard peer-up. The
pre-test application was restored byte-identical afterward.

That runtime defect remains useful diagnostic backlog, but it is not a blocker
for MS5-009 through MS5-012 because the frozen MS5-008 contract explicitly
allows `retain`, `reject`, or `defer`.

Machine-readable decision:

```text
ms5/management-transport-decision.json
```

## Consequences

- WireGuard remains candidate-only and absent from `third_party/manifest.json`.
- The accepted browser/Wiregate/plain-HTTP path remains unchanged.
- Firmware v1 does not acquire a management-transport prerequisite.
- No WireGuard key, VPN address, endpoint, or participant LAN locator becomes
  Fabric logical identity.
- The runtime panic may be diagnosed when management transport is resumed,
  especially before or during MS7 managed-edge synchronization.
- MS5-009 may proceed independently because firmware authenticity and recovery
  are transport-independent.
