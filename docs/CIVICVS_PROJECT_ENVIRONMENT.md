# CIVICVS Project Environment (CPE)

## Purpose

The CIVICVS Project Environment is the physical and operational development substrate for Kane Fabric. It joins physical hosts, network identities, build environments, hardware interfaces, and operator workflows without making any one chassis part of Fabric logical identity.

This document is the Kane-Fabric SSOT for stable CPE infrastructure. A successor must read it before issuing commands against `srv-b`, `fw`, `annales`, CT102, or the Firmware Authority container.

The CPE is infrastructure, not a credential store. Do not record passwords, WireGuard private/preshared keys, private SSH/TLS keys, API tokens, stored Webmin passwords, or firmware-signing private keys here.

## CPE network

The current CPE/Wiregate network is:

```text
10.110.0.0/22
hub/reference gateway: 10.110.0.1
```

CPE addresses are intentionally limited. A container or VM does not receive an independent CPE address merely because it exists. Assign one only when an architectural requirement justifies an independently addressable CPE role.

Current physical CPE hosts relevant to Kane Fabric include:

```text
10.110.0.4  fw       CPE Build and Hardware Workstation
10.110.0.9  annales  Dell Precision 5820 / Ubuntu LXD host
```

`srv-b` is also a physical CPE/WireGuard virtualization host, but its exact CPE address has not yet been recorded in this repository and must not be invented.

These are physical/infrastructure identities. They are not Fabric geographic identity and do not become firmware release identity.

## Host-mediated virtualization model

The normal CPE virtualization rule is:

```text
physical virtualization host owns normal CPE/WireGuard membership
        !=
container/VM automatically receives CPE/WireGuard membership
```

The physical host is the CPE/WireGuard endpoint and the management boundary. Containers remain on the host's private virtualization network and are managed through the host-native control plane unless a later architecture gate explicitly requires an independent CPE identity.

Reference pattern:

```text
CPE / WireGuard 10.110.0.0/22
        |
        +-- srv-b physical host
        |     control plane: Proxmox / pct
        |     |
        |     `-- CT102 kane-fabric
        |         service network: 10.20.0.12/24
        |
        +-- annales physical host / 10.110.0.9
        |     control plane: Ubuntu LXD / lxc
        |     |
        |     `-- firmware-authority
        |         private network: lxdbr0 / NAT
        |         CPE address: not assigned
        |
        `-- fw physical host / 10.110.0.4
              direct bare-metal CPE workstation
```

CT102 does not need an independent WireGuard peer for normal Kane administration because it is managed through `srv-b` with `pct`. Likewise, `firmware-authority` does not need a WireGuard peer because it is managed through `annales` with LXD and can use `lxdbr0` for ordinary network access.

Existing containers such as `witness-hubzilla` and `witness-ipfs` that carry their own WireGuard interfaces are explicit workload-specific exceptions, not the default CPE provisioning model.

Detailed rationale: `docs/CPE_HOST_CONTROL_PLANE_MODEL.md`.

---

## `srv-b` — Proxmox CPE virtualization host

`srv-b` is the physical Proxmox host for Kane Fabric CT102. Its host CPE/WireGuard membership is distinct from the private service network used by its CTs.

```text
control plane              Proxmox / pct
Kane container             CT102 / kane-fabric
CT102 service address      10.20.0.12/24
CT102 checkout             /tmp/kane-fabric-ms2
CT102 operational root     /var/lib/kane-fabric
```

Normal management is host-mediated:

```bash
pct status 102
pct exec 102 -- ...
```

Do not put the `fw` filesystem model or the `annales` LXD control plane onto `srv-b`.

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

```text
Creating ESP32-S3 image...
Generated kane_fabric_ms5_edge_reference.bin
binary size              0x28180
smallest app partition   0x100000
free                     84%
```

This proves the tracked project builds on the physical CPE workstation with the selected target/toolchain. It does not prove flash/boot/runtime behavior.

### Operator commands

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

A four-port switched VIA Labs USB hub is physically fixed to the workstation. The hub ports are physically labeled.

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

Three identities remain distinct:

```text
physical workstation/hub socket  -> /dev/serial/by-path/...
board/interface identity          -> /dev/serial/by-id/...
transient Linux allocation        -> /dev/ttyACM* or /dev/ttyUSB*
```

Persist physical roles by path and validate the attached interface. Never persist transient tty numbers as CPE role identity.

### Reference ESP32-S3

```text
Espressif USB Serial/JTAG
VID:PID    303a:1001
MAC        b8:f8:62:e2:d5:2c
chip       ESP32-S3 QFN56 revision v0.2
PSRAM      8 MB
USB mode   USB-Serial/JTAG
flags      0x00000000
Key0-5     USER/EMPTY
Secure Boot        Disabled
Flash Encryption   Disabled
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

## `annales` — Dell Precision CPE LXD host

Detailed observed host state is recorded in `docs/CPE_ANNALES_LXD_BASELINE.md`.

### Current host

```text
hostname                  annales
physical platform         Dell Precision 5820 Tower
CPE/WireGuard             10.110.0.9/22
LAN                       10.0.0.36/24
OS                        Ubuntu 24.04.5 LTS
kernel                    6.8.0-139-generic
container stack           LXD 5.21.7 LTS
existing primary role     RAG/LLM infrastructure plus unrelated containers
future Kane role          host for Firmware Authority Node
```

The host already exists on the CPE/Wiregate network. **10.110.0.9 is the physical host's network identity.**

The future `firmware-authority` LXD container does not have an independently assigned CPE address. `network identity: NOT ASSIGNED` refers to the container, not the host.

### Accepted host placement baseline

```text
LXD project               default
storage pool              default / dir
storage backing FS        /dev/md0p1 ext4 mounted at /
storage available         ~803 GiB observed
managed network           lxdbr0
lxdbr0 IPv4               10.56.172.1/24, NAT
lxdbr0 IPv6               fd42:bdf1:d776:c506::1/64, NAT
default profile           root on default + eth0 on lxdbr0
host SSH                  TCP/22
host Webmin               TCP/10000
LXD API                   TCP/8443 + local unix control
```

The default profile contains no GPU, host-directory passthrough, proxy device, CPU limit, memory limit, or privileged-container setting.

GPU passthrough is instance-local only to `annales-infer` and `annales-train`; it is not inherited. Firmware Authority requires no GPU and must receive none.

Existing witness containers with their own WireGuard interfaces are exceptions and do not change the host-mediated default.

### Firmware Authority placement

```text
annales physical host / 10.110.0.9
└── Ubuntu LXD
    └── unprivileged container: firmware-authority
        LXD project: default
        storage: default / dir
        network: lxdbr0 / NAT
        GPU: none
        host-directory passthrough: none initially
        private signing key file: prohibited
        signing: disabled until MS5-009
        independent CPE address: not assigned
```

The LXD host is inside the authority trust boundary because containers share the host kernel. Persistent firmware-signing private key custody remains outside the container in a hardware-backed signer selected and accepted at MS5-009.

The initial host-side discovery required before container specification is complete. The next gate is to freeze exact container CPU/RAM/root-disk/autostart/image identity and then create the inert container without signing authority.

---

## Execution-domain discipline

```text
srv-b
  physical CPE/WireGuard virtualization host
  Proxmox control plane
  host commands: pct ...
  CT102 checkout: /tmp/kane-fabric-ms2

fw / 10.110.0.4
  bare-metal Ubuntu
  operator entry: cpe-shell
  CPE project root: /home/cpe-build
  no pct

annales / 10.110.0.9
  physical CPE/WireGuard virtualization host
  Ubuntu LXD control plane
  host commands: lxc ...
  container network: lxdbr0 unless explicitly changed
  no pct
```

A path valid on one host must never be assumed to exist on another.

A file created by an Assistant or downloaded through the chat UI is not present on `srv-b`, `fw`, or `annales` merely because its filename is known. A host-side path is valid only after it has been established by SSOT or observed live.

This is a permanent anti-drift rule.

---

## Replacement and identity

All CPE physical hosts are replaceable infrastructure.

Replacing `fw` requires re-accepting its physical USB paths and pinned build environment before flashing. Replacing a virtualization host requires re-establishing its host CPE identity, native control plane, private virtualization network, and hosted-service acceptance.

Neither replacement changes:

- Fabric geographic identity;
- substrate/partition/subscription identities;
- firmware release-manifest semantics;
- the separation between build authority and firmware signing authority.

The SSOT records enough stable topology and procedure that a successor should not require private chat history to reconstruct these roles.
