# CPE annales / Dell Precision LXD baseline

## Status

Observed read-only on 2026-09-16 from the existing administrative shell on the physical host. This document records the live LXD-host facts needed before any Firmware Authority container mutation.

It is subordinate to `docs/CIVICVS_PROJECT_ENVIRONMENT.md` and does not authorize container creation, network assignment, signer attachment, or any other state change.

## Physical host

```text
hostname                 annales
hardware vendor          Dell Inc.
hardware model           Precision 5820 Tower
architecture             x86-64
OS                       Ubuntu 24.04.5 LTS (Noble)
kernel                   6.8.0-139-generic
firmware version         2.41.0
firmware date            2025-02-14
CPE/WireGuard            10.110.0.9/22
LAN                      10.0.0.36/24
```

`10.110.0.9` is the physical host's CPE identity. It is not the future `firmware-authority` container identity.

## Host resources

Observed with `lxc info --resources`:

```text
CPU                      Intel Xeon W-2223 @ 3.60 GHz
physical cores           4
hardware threads         8
maximum reported clock   3.9 GHz
NUMA nodes               1
RAM total                66.00 GiB
RAM used                 5.19 GiB
RAM free                 60.81 GiB

GPU                      NVIDIA GeForce RTX 3050 6GB
GPU PCI                   0000:65:00.0
GPU driver                nvidia 595.91.07
GPU UUID                  GPU-99e86230-ea5f-754c-955c-357f6cc5043d

NIC                      Intel I219-LM
NIC                      eno1 / 1 Gbit/s full duplex
```

The host therefore has ample CPU/RAM headroom for a small Firmware Authority container. That observation does not authorize an unbounded container; resource limits should be explicit when the container contract is frozen.

The NVIDIA GPU belongs to existing compute workloads. Firmware Authority has no GPU requirement and must not receive a GPU device.

Observed physical disks include four approximately 477 GiB S5-512 devices, one approximately 238 GiB Samsung PM881 device containing mounted host partitions, and one approximately 5.46 TiB USB WDC device. This inventory does **not** establish free capacity for the active LXD `default` pool; filesystem free-space inspection remains required before sizing the container root disk.

## Host networking

Observed host interfaces:

```text
lo       127.0.0.1/8
         ::1/128

eno1     10.0.0.36/24
         public/global IPv6 present

wg0      10.110.0.9/22

lxdbr0   10.56.172.1/24
         fd42:bdf1:d776:c506::1/64
```

## LXD daemon

```text
client version           5.21.7 LTS
server version           5.21.7 LTS
server                   lxd
server name              annales
clustered                no
instance drivers         lxc | qemu
LXC driver               6.0.6
QEMU                     8.2.2
firewall                 nftables
server LTS               true
current project          default
HTTPS listen             :8443
TLS certificate SHA-256  004fc19b4870633d10c8b647f0ab47f96757676b030fa8c1a44470672a6769d1
```

The LXD API advertises the physical CPE address `10.110.0.9:8443` in addition to LAN, bridge, loopback/IPv6-derived addresses. No decision has been made to use the remote LXD API as the Kane operator path.

## LXD project

Only one project was observed:

```text
default (current)
```

No Kane-specific LXD project exists yet. The first Firmware Authority container can therefore either use the existing default project or justify creation of a dedicated project; no project split is assumed before that design decision.

## Storage

Observed active storage pool:

```text
name        default
driver      dir
source      /var/snap/lxd/common/lxd/storage-pools/default
state       CREATED
used by     existing instances, snapshots, and the default profile
```

The server reports `dir` as its active storage driver. Other drivers are supported by the host but are not active merely because LXD reports support for them.

Do not introduce ZFS, LVM, Ceph, Btrfs, or another pool solely for Firmware Authority without a measured requirement.

The exact free space of the filesystem backing this `dir` pool has not yet been recorded.

## Network

The managed LXD bridge is fully observed as:

```text
name          lxdbr0
type          bridge
managed       true
IPv4          10.56.172.1/24
IPv4 NAT      true
IPv6          fd42:bdf1:d776:c506::1/64
IPv6 NAT      true
```

All six current containers use this bridge, directly or through the default profile.

This makes `lxdbr0` a viable non-CPE network attachment for a future Firmware Authority container, but that attachment is not frozen until the container design gate. A container on `lxdbr0` can use ordinary NATed connectivity without consuming a scarce `10.110.0.0/22` CPE address.

## Default profile

Exact observed profile:

```yaml
name: default
config: {}
devices:
  eth0:
    name: eth0
    network: lxdbr0
    type: nic
  root:
    path: /
    pool: default
    type: disk
```

The default profile contributes only the root disk and bridged NIC. It contains no GPU, host-directory passthrough, proxy device, CPU limit, memory limit, or privileged-container setting.

Firmware Authority must not rely on accidental absence of limits; explicit CPU, memory, disk, privilege, autostart, and device policy should be frozen in its own instance configuration or dedicated profile.

## Existing instances

All observed instances were running containers:

```text
annales-corpus    10.56.172.2
annales-infer     10.56.172.222
annales-train     10.56.172.87
infra             10.56.172.117
witness-hubzilla  10.56.172.200   wg0 10.110.0.19
witness-ipfs      10.56.172.201   wg0 10.110.0.20
```

No observed instance has an explicit `limits.cpu` or `limits.memory` value.

Observed instance-local device mappings:

```text
annales-corpus
  /data/corpus host disk passthrough

annales-infer
  GPU device
  /data/models host disk passthrough

annales-train
  GPU device
  /data/models host disk passthrough
  /data/training host disk passthrough
  TCP proxy 0.0.0.0:8888 -> 10.56.172.87:8888

infra
  no instance-local devices

witness-hubzilla
  static eth0 10.56.172.200
  /mnt/mailboxes -> /home host disk passthrough

witness-ipfs
  static eth0 10.56.172.201
```

GPU passthrough is therefore instance-specific to `annales-infer` and `annales-train`; it is **not** inherited from the default profile. Firmware Authority must receive no GPU device.

Host-directory passthrough is also instance-specific. Firmware Authority should begin with no host-directory disk passthrough; any later signer/device exposure must be an explicit, separately reviewed authority-boundary decision.

The witness containers' WireGuard addresses are configured inside those workloads and do not establish a rule that every LXD container receives a CPE address.

## Firmware Authority boundary after second inventory

Still unchanged:

```text
container name                 firmware-authority
deployment class               unprivileged LXD container
container CPE identity         NOT ASSIGNED
private signing key created    NO
persistent private key file    PROHIBITED
signing enabled                NO
GPU requirement                NONE
host-directory passthrough     NONE initially
network candidate              lxdbr0 / NAT, not yet frozen
operational acceptance         MS5-009
```

The second inventory is sufficient to freeze several negative requirements:

- no GPU device;
- no inherited host-directory passthrough;
- no inherited proxy device;
- no independent CPE address merely because the container exists;
- no use of Proxmox/`pct` conventions;
- no new storage driver without a measured requirement.

## Remaining read-only discovery before container creation

Only the following host facts remain unresolved for the initial container placement gate:

- filesystem free space backing `/var/snap/lxd/common/lxd/storage-pools/default`;
- cached/available LXD image path to use for the base Ubuntu container;
- actual operator management path intended for routine Kane work on `annales`;
- actual file-transfer method intended for Kane artifacts on this host.

No state-changing LXD command is authorized by this baseline.
