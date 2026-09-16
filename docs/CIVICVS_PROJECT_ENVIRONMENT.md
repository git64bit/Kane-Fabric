# CIVICVS Project Environment (CPE)

## Purpose

The CIVICVS Project Environment is the physical and operational development substrate for Kane Fabric. It joins physical hosts, network identities, build environments, hardware interfaces, and operator workflows without making any one chassis part of Fabric logical identity.

This document is the Kane-Fabric SSOT for stable CPE infrastructure. A successor must read it before issuing commands against `fw`, the Dell Precision host, or any Firmware Authority container.

The CPE is infrastructure, not a credential store. Do not record passwords, WireGuard private/preshared keys, private SSH/TLS keys, API tokens, stored Webmin passwords, or firmware-signing private keys here.

## CPE network

The current CPE/Wiregate network is:

```text
10.110.0.0/22
hub/reference gateway: 10.110.0.1
```

CPE addresses are intentionally limited. A container or VM does not receive an independent CPE address merely because it exists. Assign one only when an architectural requirement justifies an independently addressable CPE role.

Current physical CPE hosts relevant to Kane Fabric:

```text
10.110.0.4  fw              CPE Build and Hardware Workstation
10.110.0.9  Dell Precision  Ubuntu/LXD host; future Firmware Authority host
```

These are physical/infrastructure identities. They are not Fabric geographic identity and do not become firmware release identity.

---

## `fw` — CPE Build and Hardware Workstation

### Role

`fw` is the dedicated physical Kane-Fabric build/programming workstation. Its role is durable; the current Lenovo chassis is replaceable.

It owns:

- exact pinned ESP32-S3 firmware build execution;
- direct USB programming and terminal access;
- physical ESP32-S3 acceptance;
- TrivialHTTP Linux x86-64 native builds;
- TrivialHTTP Windows x86-64 MinGW cross-builds;
- operator-facing CPE wrapper commands and evidence capture.

CT102 does not replace this role and must not acquire ESP-IDF or USB passthrough merely to imitate it.

### Current physical observation

```text
hostname                  fw
platform                  Lenovo ThinkCentre Edge 62z
DMI/product               2117EKU
system type               bare metal
OS                        Ubuntu 24.04.4 LTS
architecture              x86_64
current kernel            6.8.0-139-generic
CPU                       Intel Pentium G2020, 2 cores, 2.9 GHz
RAM                       ~1.8 GiB
swap                      8 GiB
primary disk              HGST ~465.8 GiB
LAN                       10.0.0.139/24
CPE/WireGuard             10.110.0.4/22
SSH                       TCP/22
Webmin                    TCP/10000 TLS
```

The physical chassis facts are reconstruction information, not identity requirements for a replacement workstation.

### CPE account boundary

The isolated project account is:

```text
account                   cpe-build
sudo                      no
interactive entry         /usr/local/bin/cpe-shell
device groups             dialout, plugdev
```

The previous `/home/civicus-build` tree is legacy and is outside the CPE environment.

**Do not source, modify, reuse, or depend on `/home/civicus-build` for Kane-Fabric CPE work.**

### CPE filesystem

```text
/home/cpe-build/
├── src/
│   ├── Kane-Fabric/
│   └── kane-map/
├── sdk/
│   └── esp-idf-v6.0.3/
├── tools/
│   └── esp-idf-v6.0.3/
├── downloads/
├── build/
│   ├── Kane-Fabric-ms5-esp32_reference/
│   └── TrivialHTTP/
│       ├── linux-x86_64/
│       └── windows-x86_64/
├── evidence/
│   ├── Kane-Fabric/
│   └── TrivialHTTP/
├── bin/
└── .config/cpe/
```

Generated binaries and physical-device evidence remain outside the Git source checkout.

### ESP32-S3 pinned toolchain

Repository authority remains `ms5/toolchain-selection.json`. The installed CPE environment currently implements:

```text
target                    esp32s3
ESP-IDF                   v6.0.3
ESP-IDF source commit     76f5dedd9950a3012fee8fb7d5586df21fc67802
ESP-IDF archive SHA-256   748b12484402d8a1cb58ba68b7545d2a1f96d36820ab0145e0332c8348ba5ab7
Xtensa compiler           15.2.0_20251204
compiler archive SHA-256  3d50f5cd5f173acfd524e07c1cd69bc99585731a415ca2e5bce879997fe602b8
SDK path                  /home/cpe-build/sdk/esp-idf-v6.0.3
tools path                /home/cpe-build/tools/esp-idf-v6.0.3
Kane-Fabric checkout      /home/cpe-build/src/Kane-Fabric
ESP project               /home/cpe-build/src/Kane-Fabric/ms5/esp32_reference
build output              /home/cpe-build/build/Kane-Fabric-ms5-esp32_reference
evidence                  /home/cpe-build/evidence/Kane-Fabric
```

The direct ESP-IDF `export.sh` path is not the CPE operator contract. CPE wrappers source `~/.config/cpe/env.sh` so `IDF_TOOLS_PATH` resolves to the isolated tool installation.

### Accepted pinned build

The first exact pinned ESP32-S3 build on `fw` completed successfully before first flash:

```text
Creating ESP32-S3 image...
Generated kane_fabric_ms5_edge_reference.bin
binary size              0x28180
smallest app partition   0x100000
free                     84%
```

This proves the tracked project builds on the physical CPE workstation with the selected target/toolchain. It does not prove flash/boot/runtime behavior.

### Operator commands

The CPE operator interface includes:

```text
cpe-status
cpe-ports
cpe-chip-info
cpe-build
cpe-flash
cpe-monitor
cpe-flash-monitor
cpe-help
cpe-sync

cpe-trivialhttp-status
cpe-trivialhttp-build
cpe-trivialhttp-build-linux
cpe-trivialhttp-build-windows
cpe-trivialhttp-sync
cpe-trivialhttp-macos
```

The wrappers, not ad-hoc environment sourcing, are the normal operator path.

---

## Fixed switched-USB topology on `fw`

A four-port switched VIA Labs USB hub is physically fixed to the only workstation USB port on that side of the chassis. The hub ports are physically labeled.

Front-panel numbering does not match Linux's internal branch order:

```text
CPE-USB-1  front port 1  USB branch 1.1.2  PROGRAM
CPE-USB-2  front port 2  USB branch 1.1.3  TERMINAL
CPE-USB-3  front port 3  USB branch 1.1.1  spare/test
CPE-USB-4  front port 4  USB branch 1.1.4  spare/test
```

Accepted durable role paths:

```text
PROGRAM
/dev/serial/by-path/pci-0000:00:1a.0-usb-0:1.1.2:1.0
expected interface: Espressif USB Serial/JTAG
VID:PID: 303a:1001

TERMINAL
/dev/serial/by-path/pci-0000:00:1a.0-usb-0:1.1.3:1.0-port0
expected interface: Silicon Labs CP2102 UART
VID:PID: 10c4:ea60
```

Three identities must remain distinct:

```text
physical workstation/hub socket  -> /dev/serial/by-path/...
board/interface identity          -> /dev/serial/by-id/...
transient Linux allocation        -> /dev/ttyACM* or /dev/ttyUSB*
```

Persist physical roles by path and validate the attached interface. Never persist transient tty numbers as CPE role identity.

### Reference ESP32-S3

The clean Kane-Fabric reference board currently accepted for first flash has native USB identity:

```text
Espressif USB Serial/JTAG
VID:PID    303a:1001
MAC        b8:f8:62:e2:d5:2c
chip       ESP32-S3 QFN56 revision v0.2
PSRAM      8 MB
USB mode   USB-Serial/JTAG
flags      0x00000000
Key0-5     USER/EMPTY
Secure Boot       Disabled
Flash Encryption  Disabled
SPI_BOOT_CRYPT_CNT 0
```

The same board's UART side is a Silicon Labs CP2102 (`10c4:ea60`, serial `0001`).

At the current checkpoint the clean board is left connected to **CPE-USB-1 / PROGRAM**. First controlled Kane-Fabric flash remains pending.

### Pre-secured experimental board — excluded

A separate board with native USB identity ending `B8:F8:62:E2:D2:84` was found in Secure Download Mode with Secure Boot enabled, JTAG permanently disabled, programmed secure-boot digest key blocks, and a revoked key.

That board is deliberately set aside intact and is **not** the Kane-Fabric reference board. Do not erase/reprovision it without the original signing material.

---

## TrivialHTTP CPE role

The CPE also builds TrivialHTTP from `git64bit/kane-map`.

On `fw`, Linux and Windows outputs live outside the source checkout:

```text
/home/cpe-build/build/TrivialHTTP/linux-x86_64/trivialhttp
/home/cpe-build/build/TrivialHTTP/windows-x86_64/trivialhttp.exe
```

At Kane-map commit `5d323196f877ceb86c8042afeadc7b44b6eaedbd`:

```text
Linux x86-64
compiler   GCC 13.3.0
SHA-256    ae822f27001ee9496a80a79d9e4a7ce8bbdec8ac5d050e60b5d4c27623ad1807

Windows x86-64
compiler   x86_64-w64-mingw32-gcc 13-win32
SHA-256    4ec4c7504191b82dec81d92cd57653ef420d93da403930f88c3ed264bcf49f6a
```

macOS is deliberately not cross-built on `fw`. Native GitHub-hosted macOS acceptance at the same Kane-map source state proved both arm64 and x86-64 builds plus a real loopback HTTP request.

---

## Dell Precision — CPE LXD host

### Known current role

The second physical CPE host relevant to Kane Fabric is a Dell Precision:

```text
physical platform         Dell Precision
CPE/Wiregate address      10.110.0.9/22
host OS family            Ubuntu
container stack           LXD
Proxmox                    no
existing primary role     RAG/LLM infrastructure
future Kane role          host for Firmware Authority Node
```

The host already exists on the CPE/Wiregate network. **10.110.0.9 is the physical Dell host's network identity.**

The future `firmware-authority` LXD container does not yet have an independently assigned CPE address. `network identity: NOT ASSIGNED` in Firmware Authority state refers to the container, not to the Dell host.

The Dell's existing GPU-backed LXD workloads are outside Kane Fabric. The Firmware Authority requires no GPU access and must not disturb or inherit those workloads merely because it shares the physical host.

### Firmware Authority placement

Planned placement:

```text
Dell Precision physical host (10.110.0.9)
└── Ubuntu LXD
    └── unprivileged container: firmware-authority
        private signing key file: prohibited
        signing: disabled until MS5-009
        independent CPE address: not yet assigned
```

The LXD host is inside the authority trust boundary because containers share the host kernel. The intended mitigation is that persistent firmware-signing private key custody remains outside the container in a hardware-backed signer selected and accepted at MS5-009.

### Required Dell discovery before mutation

The Dell is not Proxmox and `pct` commands do not apply.

Before any Firmware Authority container is created or modified, perform a bounded **read-only** LXD/host inventory and record at minimum:

- actual host hostname and Ubuntu release;
- LXD version;
- LXD projects;
- storage pools;
- profiles;
- networks/bridges;
- existing instances and naming conventions relevant to collision avoidance;
- available CPU/RAM/storage appropriate to the authority container;
- current device/GPU passthrough configuration so Kane work does not disturb it;
- management/file-transfer path actually used for this host.

Do not invent a host staging directory, bridge, storage pool, profile, container address, or transfer path before that inventory is returned.

---

## Execution-domain discipline

These environments use different control planes:

```text
srv-b / CT102
  Proxmox
  host commands: pct ...
  CT102 checkout: /tmp/kane-fabric-ms2

fw
  bare-metal Ubuntu
  operator entry: cpe-shell
  CPE project root: /home/cpe-build
  no pct

Dell Precision / 10.110.0.9
  Ubuntu LXD
  LXD control plane
  no pct
  exact management and storage paths must be observed before use
```

A path valid on one host must never be assumed to exist on another.

A file created by an Assistant or downloaded through the chat UI is not present on `srv-b`, `fw`, or the Dell merely because its filename is known. A host-side path is valid only after it has been established by SSOT or observed live.

This is a permanent anti-drift rule.

---

## Replacement and identity

All CPE physical hosts are replaceable infrastructure.

Replacing `fw` requires re-accepting its physical USB paths and pinned build environment before flashing. Replacing the Dell requires re-establishing LXD host/container acceptance before Firmware Authority use.

Neither replacement changes:

- Fabric geographic identity;
- substrate/partition/subscription identities;
- firmware release-manifest semantics;
- the separation between build authority and firmware signing authority.

The SSOT records enough stable topology and procedure that a successor should not require private chat history to reconstruct these roles.
