# MS5-008 Runtime Investigation

## Status

This is a factual investigation record, not an acceptance record.

MS5-008 remains in `defer`. WireGuard is not a retained Kane Fabric dependency.

## Repository and candidate baseline

The physical attempt was made from Kane Fabric repository head:

```text
3aeebe0b33570859277aae11aa1b3e147267db79
```

Exact evaluation inputs:

```text
ESP-IDF                 6.0.3
ESP-IDF commit          76f5dedd9950a3012fee8fb7d5586df21fc67802
WireGuard commit        cddaa4eab4e633847bf846723ac0449a34c3d2f7
libsodium wrapper       40c22448d6e8f42be56c45f739b52a5c8d21c8ca
libsodium upstream      d24faf56214469b354b01c8ba36257e04737101e
live component resolve  disabled
```

The evaluation key remains a temporary management identity and is not Fabric
logical identity.

## Source-preparation correction

The first physical-build attempt failed before any flash because the raw pinned
`esphome-libs/libsodium` wrapper had been staged without applying its pinned
patch series. The compile failure was:

```text
port/x25519_m15.c:1197:10:
fatal error: crypto_core/ed25519/ref10/base_packed.h: No such file or directory
```

The wrapper repository's own CI applies `patches/apply.sh` to its pinned
upstream submodule before compiling. Patch 10 creates `base_packed.h`.

The corrected physical attempt applied the complete pinned patch series before
build.

## Corrected physical attempt

The corrected build passed:

```text
libsodium patch series        PASS
base_packed.h                 PASS
evaluation application bytes  918240
evaluation application SHA256 691d72e834b0bd3e7f75b9d75b0ad758a2927e136a8bb2159ec10467c44fb892
```

Before flashing the temporary evaluation application, the existing 1 MiB
factory application partition was read and hashed:

```text
6e3c2bbcfb77107898bd96210f85bd49d93621ea057739e86c2914a56f554c96
```

Only the application partition was temporarily replaced.

## Runtime result

The temporary application booted far enough to prove that the accepted
participant runtime remained intact before management transport startup:

```text
Fabric partition mounted read-only       PASS
participant image inventory verification PASS
Wi-Fi association/DHCP                   PASS
observed LAN address                     10.0.0.185
plain-HTTP artifact server ready         PASS
MS5-008 evaluation task started          PASS
```

Immediately after the evaluation task printed its WireGuard transport
configuration, the ESP32-S3 panicked:

```text
Guru Meditation Error: Core 0 panic'ed (LoadProhibited)
EXCVADDR: 0x00000000
```

No `MS5_008_WG_PEER_UP=PASS` line was produced. The same panic recurred after
the automatic reboot.

The wrapper reported the outer assertion as missing peer-up evidence, but the
more precise runtime classification is:

> the exact-pinned candidate build succeeds, but the first physical runtime
> attempt crashes during WireGuard startup before an authenticated peer-up can
> be established.

This is not evidence of a rejected handshake. It is a local device runtime
failure that must be symbolized before changing the network or hub.

## Restoration

The gate restored the exact pre-test application bytes after the failed
runtime attempt and verified the read-back SHA-256:

```text
pre-test application SHA256  6e3c2bbcfb77107898bd96210f85bd49d93621ea057739e86c2914a56f554c96
restored application SHA256  6e3c2bbcfb77107898bd96210f85bd49d93621ea057739e86c2914a56f554c96
restore                       PASS
```

The Fabric partition was not rewritten.

## What is now established

Established:

- the frozen WireGuard and libsodium inputs can be prepared without live
  package resolution;
- the complete pinned libsodium patch series is required by the selected
  evaluation source identity;
- the exact-pinned ESP32-S3 evaluation firmware builds under ESP-IDF 6.0.3;
- the application fits the accepted 1 MiB factory partition;
- application-only temporary flash and exact predecessor restoration work;
- the accepted participant image, Wi-Fi path, and HTTP server initialize before
  the WireGuard startup crash.

Not established:

- successful WireGuard initialization;
- authenticated handshake;
- routed management traffic;
- persistent-keepalive NAT behavior;
- reconnect behavior;
- resource-cost acceptance;
- coexistence beyond the point at which WireGuard startup crashes.

WireGuard therefore remains **candidate-only / not retained / defer**.

## Runtime-only hub peer

The temporary `wg-pk` peer was accepted earlier as a runtime-only,
non-persistent peer for `10.110.3.254/32`.

Because it was intentionally never written to persistent `wg0.conf`, this
document does not claim that the peer is still present now. Its live presence
must be reverified only when another actual handshake attempt is justified.

## Next safe action

Stay on `fw`.

Do not flash again yet. Do not modify `wg-pk`.

First symbolize the captured backtrace against the preserved evaluation ELF/map
from the corrected physical attempt. If the temporary build workspace still
exists, use that exact ELF. If it does not, reproduce the exact pinned build
without flashing and obtain equivalent symbols.

The next accepted fact must be the exact crashing function and source line.
Only then should the integration or candidate implementation be corrected,
retested, or rejected.
