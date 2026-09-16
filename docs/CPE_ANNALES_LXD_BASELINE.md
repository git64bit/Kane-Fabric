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

The managed LXD bridge is therefore `lxdbr0`; this observation does not yet make it the accepted Firmware Authority network attachment. The container remains without an independently assigned CPE address.

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

The LXD API advertises the physical CPE address `10.110.0.9:8443` in addition to LAN, bridge, loopback/IPv6-derived addresses. No decision has yet been made to use the remote LXD API as the Kane operator path.

## LXD project

Only one project was observed:

```text
default (current)
```

No Kane-specific LXD project exists yet.

## Storage

Observed storage pool:

```text
name        default
driver      dir
source      /var/snap/lxd/common/lxd/storage-pools/default
state       CREATED
used by     16
```

The server reports `dir` as its active storage driver. Other drivers are supported by the host but are not active merely because LXD reports support for them.

Do not introduce ZFS, LVM, Ceph, Btrfs, or another pool solely for Firmware Authority without a measured requirement.

## Networks

Observed LXD networks:

```text
eno1    physical  unmanaged
lxdbr0  bridge    managed  10.56.172.1/24  fd42:bdf1:d776:c506::1/64
```

`lxdbr0` is currently used by existing instances. Its exact DHCP/NAT/DNS configuration must be inspected before the Firmware Authority network contract is frozen.

## Profiles

Observed profiles:

```text
default  Default LXD profile  used by 6
```

The expanded profile content has not yet been recorded. Do not assume its root-disk or NIC device shape until `lxc profile show default` is inspected.

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

This establishes the existing naming and address environment for collision avoidance. These containers are not Kane-Fabric resources merely because they share `annales`.

The RAG/LLM containers and any GPU/device passthrough they use remain outside Kane Fabric. Firmware Authority must not inherit GPU or other device mappings from an existing workload.

## Firmware Authority boundary after first inventory

Still unchanged:

```text
container name                 firmware-authority
deployment class               unprivileged LXD container
container CPE identity         NOT ASSIGNED
private signing key created    NO
persistent private key file    PROHIBITED
signing enabled                NO
GPU requirement                NONE
operational acceptance         MS5-009
```

The first inventory is sufficient to stop guessing about the host, LXD version, project, storage pool, bridge, profile name, and existing instances. It is not yet sufficient to create the container.

## Remaining read-only discovery before container design

Inspect only the facts that affect safe placement:

- host CPU, RAM, disks, and currently available capacity;
- exact `default` profile contents;
- exact `default` storage-pool configuration;
- exact `lxdbr0` network configuration;
- expanded device/resource configuration of existing RAG/LLM containers, especially GPU/device passthrough;
- whether any project/profile restrictions or resource limits are already in use;
- the actual operator management and file-transfer method intended for Kane work.

No state-changing LXD command is authorized by this baseline.
