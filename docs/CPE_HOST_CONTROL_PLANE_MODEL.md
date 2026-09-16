# CPE Host-Mediated Control-Plane Model

## Purpose

The CIVICVS Project Environment uses **host-mediated CPE membership** for virtualization hosts.

The physical virtualization host participates in the CPE/WireGuard network. Containers and VMs behind that host remain on the host's local virtualization networks unless a later architecture gate explicitly requires an independently addressable CPE identity.

This is a deliberate design rule, not an incidental implementation detail.

## Core model

```text
CPE / WireGuard 10.110.0.0/22
        |
        +-- virtualization host
        |       CPE/WireGuard identity on the physical host
        |       host-local virtualization control plane
        |       |
        |       +-- container / VM
        |       +-- container / VM
        |       `-- container / VM
        |
        `-- other physical CPE hosts
```

The host is the management and network boundary. The normal container/VM does not receive a WireGuard peer or CPE address merely because it is hosted on a CPE machine.

## `srv-b` / Proxmox

`srv-b` is the physical Proxmox host and is the WireGuard/CPE participant for its virtualization environment. Kane Fabric CTs are managed from the host with the Proxmox control plane:

```text
srv-b physical host
  CPE/WireGuard endpoint: host
  control plane: Proxmox / pct
  |
  `-- CT102 kane-fabric
      service address: 10.20.0.12/24
      control: pct exec 102 -- ...
```

CT102 does not need an independent CPE/WireGuard identity for ordinary Kane Fabric administration. Its service-network address and its management relationship to `srv-b` are separate from the host's CPE identity.

The exact CPE/WireGuard address of `srv-b` is not recorded in the current Kane-Fabric SSOT and must not be invented. It may be added after direct observation.

## `annales` / LXD

`annales` is the physical Ubuntu/LXD host and is the WireGuard/CPE participant for its virtualization environment:

```text
annales physical host
  CPE/WireGuard: 10.110.0.9/22
  control plane: LXD / lxc
  |
  `-- LXD containers
      default network: lxdbr0 / 10.56.172.0/24 NAT
```

The future `firmware-authority` container follows this same pattern:

```text
annales / 10.110.0.9
  |
  `-- firmware-authority
      network: lxdbr0 / NAT
      independent CPE/WireGuard address: not assigned
```

The container is managed with LXD from the host. It does not receive a CPE address merely because the host has one.

Existing witness containers that have their own `wg0` interfaces are explicit workload-specific exceptions. They do not establish a default rule for LXD containers.

## `fw`

`fw` is not a virtualization host. It is itself the physical CPE Build and Hardware Workstation at `10.110.0.4/22` and is managed directly through its CPE operator environment.

## Why this matters

This model keeps the scarce CPE/WireGuard address space tied to infrastructure roles that actually require independent CPE presence. It also prevents management drift:

- Proxmox CTs are managed through the Proxmox host and `pct`;
- LXD containers are managed through the LXD host and `lxc`;
- container-private service networks remain separate from the CPE network;
- an independent WireGuard peer inside a container is an explicit exception, not a default provisioning step.

## Permanent rule

```text
physical virtualization host owns normal CPE/WireGuard membership
        !=
container/VM automatically receives CPE/WireGuard membership
```

Before assigning any container or VM a CPE address, document the architectural requirement that cannot be satisfied through the host-mediated control plane and private service network.
