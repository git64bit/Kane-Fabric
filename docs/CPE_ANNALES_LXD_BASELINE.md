# CPE annales / Dell Precision LXD baseline

## Status

Observed read-only on 2026-09-16 from the existing administrative shell on the physical host. This document records the live LXD-host facts needed before any Firmware Authority container mutation.

It is subordinate to `docs/CIVICVS_PROJECT_ENVIRONMENT.md` and does not authorize signer attachment or Firmware Authority activation.

The initial host-placement discovery is now complete. The next step may freeze and create the inert `firmware-authority` container using the observed host/LXD baseline.

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

The CPE virtualization model is documented in `docs/CPE_HOST_CONTROL_PLANE_MODEL.md`: the physical virtualization host normally owns CPE/WireGuard membership, while its containers remain on private host-managed networks unless an explicit exception is justified.

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
GPU PCI                  0000:65:00.0
GPU driver               nvidia 595.91.07
GPU UUID                 GPU-99e86230-ea5f-754c-955c-357f6cc5043d

NIC                      Intel I219-LM
NIC                      eno1 / 1 Gbit/s full duplex
```

The host has ample CPU/RAM headroom for a small Firmware Authority container. That does not authorize an unbounded container; resource limits should be explicit in the container contract.

The NVIDIA GPU belongs to existing compute workloads. Firmware Authority has no GPU requirement and must not receive a GPU device.

Observed physical disks include four approximately 477 GiB S5-512 devices, one approximately 238 GiB Samsung PM881 device containing mounted host partitions, and one approximately 5.46 TiB USB WDC device.

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

The LXD API advertises the physical CPE address `10.110.0.9:8443` in addition to LAN, bridge, loopback/IPv6-derived addresses. Local administrative use currently occurs through the existing host shell and the local `lxc` client. No requirement has been established to use the remote LXD API for Kane operations.

## LXD project

Only one project was observed:

```text
default (current)
```

No Kane-specific LXD project exists. The initial Firmware Authority container can use the existing default project; creating a dedicated project would require a separate measured isolation requirement.

## Storage

Observed active storage pool:

```text
name        default
driver      dir
source      /var/snap/lxd/common/lxd/storage-pools/default
state       CREATED
used by     existing instances, snapshots, and the default profile
```

The pool source resolves to the host root filesystem:

```text
filesystem                /dev/md0p1
filesystem type           ext4
mount point               /
filesystem size           935 GiB
used                      84 GiB
available                 803 GiB
utilization               10%
```

The server reports `dir` as its active storage driver. Other drivers are supported by the host but are not active merely because LXD reports support for them.

Do not introduce ZFS, LVM, Ceph, Btrfs, or another pool solely for Firmware Authority without a measured requirement. The existing `default` pool has ample observed capacity for a small authority container.

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

`lxdbr0` is the accepted initial network attachment for the inert Firmware Authority container. It provides ordinary NATed connectivity without consuming a scarce `10.110.0.0/22` CPE address.

The physical host remains the CPE/WireGuard participant. The container does not receive its own CPE/WireGuard address by default.

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

Firmware Authority must not rely on accidental absence of limits; explicit CPU, memory, disk, privilege, autostart, and device policy must be frozen for the authority instance.

## Images and remotes

No cached local LXD images were present when observed.

Configured image remotes include:

```text
images                https://images.lxd.canonical.com
ubuntu                https://cloud-images.ubuntu.com/releases/
ubuntu-daily          https://cloud-images.ubuntu.com/daily/
ubuntu-minimal        https://cloud-images.ubuntu.com/minimal/releases/
ubuntu-minimal-daily  https://cloud-images.ubuntu.com/minimal/daily/
local                 unix://
```

Use a release image, not a daily image, for the authority container. The exact base image alias/fingerprint must be captured when the container is created so later reconstruction does not depend on a moving remote alias.

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

GPU passthrough is instance-specific to `annales-infer` and `annales-train`; it is **not** inherited from the default profile. Firmware Authority must receive no GPU device.

Host-directory passthrough is also instance-specific. Firmware Authority begins with no host-directory disk passthrough; any later signer/device exposure is an explicit authority-boundary change.

The witness containers' WireGuard addresses are workload-specific exceptions. They do not establish a rule that every LXD container receives a CPE address.

## Host management surfaces

The following host services were active when observed:

```text
SSH                    active, TCP/22
Webmin                 active, TCP/10000
LXD daemon             active, TCP/8443 plus local unix control
```

The existing administrative shell plus local `lxc` command is the reference control path for the initial Firmware Authority deployment.

Webmin remains available for human-oriented host/file administration. The repository does not assume that a file exists on `annales` merely because it was generated elsewhere; any transfer must still be explicit and verified.

Remote LXD API use is not required for the initial deployment.

## Firmware Authority boundary after completed placement discovery

```text
container name                 firmware-authority
deployment class               unprivileged LXD container
LXD project                    default
storage pool                   default / dir
network                        lxdbr0 / NAT
container CPE identity         NOT ASSIGNED
private signing key created    NO
persistent private key file    PROHIBITED
signing enabled                NO
GPU requirement                NONE
GPU device                     NONE
host-directory passthrough     NONE initially
remote LXD API requirement     NONE
operational acceptance         MS5-009
```

The placement discovery freezes these negative requirements:

- no GPU device;
- no inherited host-directory passthrough;
- no inherited proxy device;
- no independent CPE address merely because the container exists;
- no use of Proxmox/`pct` conventions;
- no new storage driver or project without a measured requirement;
- no daily/moving image accepted as reproducible release input without recording the resolved image identity.

## Next gate

The host-side discovery required before container design is complete.

The next gate is to freeze the initial inert container specification, including:

- exact Ubuntu release image and resolved image fingerprint;
- CPU limit;
- memory limit;
- root-disk size;
- unprivileged security state;
- autostart policy;
- `default` project and `default` storage pool;
- `lxdbr0` NAT attachment;
- explicit absence of GPU, proxy, host-directory, WireGuard/CPE, and signing-key state.

Only after that specification is recorded should the `firmware-authority` container be created.
