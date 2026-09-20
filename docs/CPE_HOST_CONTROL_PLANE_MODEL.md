# CPE Host-Mediated Control-Plane Model

## Purpose

The CIVICVS Project Environment uses **host-mediated CPE membership** for virtualization hosts.

The physical virtualization host participates in the CPE/WireGuard network. Containers and VMs behind that host remain on the host's local virtualization networks unless a later architecture gate explicitly requires an independently addressable CPE identity.

This is a deliberate design rule, not an incidental implementation detail.

## Core model

```text
CPE / WireGuard 10.110.0.0/22
        |
        +-- srv-b / 10.110.0.12
        |       Proxmox / pct
        |       |
        |       +-- CT102 kane-fabric / 10.20.0.12
        |       `-- CT103 kane-wiregate / 10.20.0.13
        |
        +-- annales / 10.110.0.9
        |       LXD / lxc
        |       |
        |       `-- firmware-authority / lxdbr0
        |
        `-- fw / 10.110.0.4
                bare-metal CPE workstation
```

The host is the management and network boundary. The normal container/VM does not receive a WireGuard peer or CPE address merely because it is hosted on a CPE machine.

## `srv-b` / Proxmox

`srv-b` is the physical Proxmox host and the WireGuard/CPE participant for its virtualization environment.

Observed host identity on 2026-09-16:

```text
hostname                  srv-b
hardware                  HP ProLiant DL360 G7
OS                        Debian GNU/Linux 12 (bookworm)
kernel                    6.8.12-9-pve
Proxmox                   pve-manager 8.4.0
LAN                       10.0.0.12/24 via vmbr0
CPE/WireGuard             10.110.0.12/32 via wg0
private CT bridge         vmbr1 / 10.20.0.1/24
management                SSH :22, Proxmox :8006, Webmin :10000
```

Kane Fabric CTs are managed from the host with the Proxmox control plane:

```text
srv-b physical host / 10.110.0.12
  control plane: Proxmox / pct
  private bridge: vmbr1 / 10.20.0.0/24
  |
  +-- CT102 kane-fabric
  |   service address: 10.20.0.12/24
  |   gateway: 10.20.0.1
  |   control: pct exec 102 -- ...
  |
  `-- CT103 kane-wiregate
      service address: 10.20.0.13/24
      gateway: 10.20.0.1
      control: pct exec 103 -- ...
```

CT102 and CT103 do not need independent CPE/WireGuard identities for ordinary Kane Fabric administration. Their service-network addresses and management relationship to `srv-b` are separate from the host's CPE identity. CT103 follows the same single-homed `vmbr1` proxy-class container pattern as CT101; reaching a participant edge is not justification to attach CT103 directly to the residential/LAN bridge.

Other currently observed CTs are CT100 `mechcomp` and CT101 `mcproxy`; co-location does not make them Kane Fabric resources.

## Operator infrastructure versus participant networking

Host-mediated CPE membership describes operator-controlled infrastructure. It does not imply that an operator controls the participant's home router or participant-LAN addressing.

A participant edge is expected to work behind an ordinary independently administered network:

```text
participant router / arbitrary DHCP + NAT
        |
        `-- participant edge
             local address: transient operational locator
             Fabric publication identity: independent
```

The participant must not be required to configure DHCP reservations, static LAN addresses, port forwarding, or other router policy for normal Fabric operation. A future management transport must establish whatever operator reachability it needs without converting the participant's local address or NAT endpoint into Fabric identity.

During MS5-007 only, the controlled Kane laboratory may use a temporary local transport adapter to prove browser HTTPS -> Wiregate -> plain-HTTP physical-edge composition. The adapter may discover and verify the current reference-board locator and install a temporary narrowly scoped host policy for the acceptance run. That is laboratory evidence, not a deployable participant-network contract.

Scalable authenticated edge reachability is evaluated separately from the browser path. MS5-008 owns candidate management-transport feasibility; later managed-edge synchronization owns fleet enrollment, credential lifecycle, locator tracking, and replacement behavior.

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
- service CTs remain single-homed on their established private virtualization network unless a separately accepted architecture requires otherwise;
- participant residential networks are not an extension of the operator control plane;
- an independent WireGuard peer inside a container is an explicit exception, not a default provisioning step.

## Permanent rule

```text
physical virtualization host owns normal CPE/WireGuard membership
        !=
container/VM automatically receives CPE/WireGuard membership
```

Before assigning any container or VM a CPE address, document the architectural requirement that cannot be satisfied through the host-mediated control plane and private service network.
