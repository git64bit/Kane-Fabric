# Kane Fabric — Current Handoff

Start with `docs/DEVELOPMENT_PROCESS.md`, `docs/CURRENT_STATE.json`, `docs/SESSION_START.md`, `docs/CIVICVS_PROJECT_ENVIRONMENT.md`, and `docs/CPE_HOST_CONTROL_PLANE_MODEL.md` before physical CPE or Firmware Authority work. `docs/MILESTONE_5_DESIGN.md` remains the sole detailed authority for Milestone 5.

## Released foundation

Milestones 0–4 are complete. The accepted MS3 substrate identity is `fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc`; the accepted MS4 implementation is `9f6013d1b8b44998047f71e2b3f3e9c55c9ed298`; the accepted MS4 composition identity is `a58c8398248cee05b7baad9ae289fe0581bdb3624ce1aff3aa8a49721f92ee53`.

The authoritative Kane Fabric runtime/test environment remains CT102 `kane-fabric` on Proxmox host `srv-b`, with operational state rooted at `/var/lib/kane-fabric` and the recorded checkout at `/tmp/kane-fabric-ms2`.

## Current accepted CT102 repository checkpoint

The earlier firmware-v1 responsibility freeze remains historically accepted at `5d45fd600468060104341166adf23bb6465393d2`. The repository has since advanced through the CPE SSOT repair and Firmware Authority scaffold.

CT102 accepted the current implementation at:

```text
84ca59a06c6fd4d4b81461d99d3f6d3889a43328
```

Acceptance evidence on 2026-09-16:

```text
Python compileall                  PASS
MS5 tests                          69 passed, 1 expected environment skip
CPE SSOT structural guard          PASS
Firmware Authority contract tests  PASS
configured Fabric DB authority     readable / accepted-geographic-state
worktree                            clean
branch/upstream/origin/refspec      conformant
```

The single skip is expected because CT102 deliberately has no host C compiler. The authoritative pinned ESP-IDF compile has already passed on `fw`.

Later documentation-only checkpoints record additional physical CPE observations without invalidating the implementation/tests exercised at `84ca59a...`.

## CPE host-mediated control-plane model

The stable virtualization rule is now explicit:

```text
physical virtualization host owns normal CPE/WireGuard membership
        !=
container/VM automatically receives CPE/WireGuard membership
```

Current physical CPE hosts relevant to Kane Fabric:

```text
10.110.0.4   fw       bare-metal CPE Build and Hardware Workstation
10.110.0.9   annales  Dell Precision 5820 / Ubuntu LXD host
10.110.0.12  srv-b    HP ProLiant DL360 G7 / Proxmox host
```

Virtualized workloads remain on host-private service networks and are administered through the host-native control plane unless a specific later design requires an independent CPE identity.

### `srv-b`

Observed physical host baseline:

```text
hostname                  srv-b
hardware                  HP ProLiant DL360 G7
OS                        Debian GNU/Linux 12
kernel                    6.8.12-9-pve
Proxmox                   pve-manager 8.4.0
LAN                       10.0.0.12/24 via vmbr0
CPE/WireGuard             10.110.0.12/32 via wg0
private CT bridge         vmbr1 / 10.20.0.1/24
management                SSH :22 / Proxmox :8006 / Webmin :10000
```

CT102 is `10.20.0.12/24` on `vmbr1`, gateway `10.20.0.1`, and is managed through `srv-b` with `pct`. CT102 has no independent CPE/WireGuard identity.

Current observed CT inventory is CT100 `mechcomp`, CT101 `mcproxy`, and CT102 `kane-fabric`; only CT102 is Kane Fabric.

### `fw`

`fw` is the dedicated physical Kane-Fabric build/programming workstation. The current implementation is a bare-metal Lenovo ThinkCentre Edge 62z running Ubuntu 24.04.4 LTS, x86-64, current kernel `6.8.0-139-generic`.

The project environment is isolated under `/home/cpe-build`; `/home/civicus-build` is legacy and must not be sourced, modified, reused, or treated as part of the CPE.

The exact pinned ESP-IDF v6.0.3 / ESP32-S3 build has already succeeded on `fw`. The first firmware image was generated at size `0x28180` against a `0x100000` smallest application partition, leaving 84% free. This is physical build evidence, not flash/runtime evidence.

The fixed switched hub is accepted as:

```text
CPE-USB-1  branch 1.1.2  PROGRAM   Espressif USB Serial/JTAG 303a:1001
CPE-USB-2  branch 1.1.3  TERMINAL  Silicon Labs CP2102 UART  10c4:ea60
CPE-USB-3  branch 1.1.1  spare/test
CPE-USB-4  branch 1.1.4  spare/test
```

The clean reference ESP32-S3 is MAC `b8:f8:62:e2:d5:2c`, revision v0.2, 8 MB PSRAM, Security Flags `0x00000000`, Secure Boot disabled, and Flash Encryption disabled. It is currently left connected to CPE-USB-1 / PROGRAM. First controlled flash remains pending.

A separate pre-secured experimental board ending `B8:F8:62:E2:D2:84` is excluded from the reference workflow and is left intact.

### TrivialHTTP

`fw` builds native Linux x86-64 and MinGW Windows x86-64 TrivialHTTP outputs from `git64bit/kane-map`; macOS is accepted through native macOS CI rather than cross-built on `fw`. At Kane-map commit `5d323196f877ceb86c8042afeadc7b44b6eaedbd`, the synchronized outputs were:

```text
Linux x86-64 SHA-256   ae822f27001ee9496a80a79d9e4a7ce8bbdec8ac5d050e60b5d4c27623ad1807
Windows x86-64 SHA-256 4ec4c7504191b82dec81d92cd57653ef420d93da403930f88c3ed264bcf49f6a
```

## Firmware Authority Node

The non-secret repository scaffold was introduced at `e42ec17f0ccd6de39c2b5b6987063a424a22a649` and is accepted in CT102 as part of the `84ca59a...` checkpoint. This accepts the repository contract only; it does **not** activate signing authority.

The physical host is `annales`, a Dell Precision 5820 already on the CPE/WireGuard network at `10.110.0.9/22`. It runs Ubuntu 24.04.5 LTS with LXD 5.21.7 LTS and carries unrelated RAG/LLM workloads.

Read-only placement discovery is complete:

```text
LXD project               default
storage                   default / dir
storage available         ~803 GiB observed
private network           lxdbr0 / 10.56.172.0/24 NAT
GPU                       RTX 3050 used only by existing infer/train containers
host management           SSH :22 / Webmin :10000 / LXD :8443 + unix control
```

Initial Firmware Authority placement remains:

```text
annales physical host / 10.110.0.9
└── LXD
    └── unprivileged container: firmware-authority
        network: lxdbr0 / NAT
        GPU: none
        host-directory passthrough: none initially
        private signing key file: prohibited
        signing: disabled
        container CPE identity: not assigned
        operational acceptance: MS5-009
```

`10.110.0.9` is the physical host identity. The Firmware Authority container does not receive a CPE address merely because it exists.

## Stable operational authorities

```text
repository                    git64bit/Kane-Fabric
branch                        main
CPE SSOT                      docs/CIVICVS_PROJECT_ENVIRONMENT.md
host-control-plane model      docs/CPE_HOST_CONTROL_PLANE_MODEL.md
Proxmox host                  srv-b / 10.110.0.12
Kane runtime/test container   CT102 / kane-fabric / 10.20.0.12
CT102 checkout                /tmp/kane-fabric-ms2
last accepted CT102 HEAD      84ca59a06c6fd4d4b81461d99d3f6d3889a43328
operational root              /var/lib/kane-fabric
authoritative DB              /var/lib/kane-fabric/database/kane-county-fabric.gpkg
DB SHA256                     31e362b696a37f1b9c45ae355c5669511a3128c17a651108a62e20d1cedebd67
CPE build/program host        fw / 10.110.0.4
Firmware Authority host       annales / 10.110.0.9
```

## Execution-domain rule

```text
srv-b / 10.110.0.12
  Proxmox / pct
  private CT network vmbr1 / 10.20.0.0/24

fw / 10.110.0.4
  bare-metal Ubuntu / cpe-shell and CPE wrappers

annales / 10.110.0.9
  Ubuntu LXD / lxc
  private container network lxdbr0 / 10.56.172.0/24 NAT
```

Do not transfer filesystem paths, control-plane commands, or guest-network assumptions between these environments.

## Next safe action

The host-control-plane model and both virtualization-host baselines are now recorded. The next Firmware Authority gate is to freeze the **initial inert LXD container specification** from the completed `annales` baseline: Ubuntu release image identity, explicit CPU/RAM/root-disk limits, unprivileged state, autostart policy, default project/storage, `lxdbr0` NAT, and explicit absence of GPU, proxy, host-directory, WireGuard/CPE, and signing-key state.

The first controlled ESP32-S3 flash on `fw` remains separately pending.
