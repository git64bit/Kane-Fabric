# Kane Fabric — Current Handoff

Start with `docs/DEVELOPMENT_PROCESS.md`, `docs/CURRENT_STATE.json`, `docs/SESSION_START.md`, and `docs/CIVICVS_PROJECT_ENVIRONMENT.md` before physical CPE or Firmware Authority work. `docs/MILESTONE_5_DESIGN.md` remains the sole detailed authority for Milestone 5.

## Released foundation

Milestones 0–4 are complete. The accepted MS3 substrate identity is `fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc`; the accepted MS4 implementation is `9f6013d1b8b44998047f71e2b3f3e9c55c9ed298`; the accepted MS4 composition identity is `a58c8398248cee05b7baad9ae289fe0581bdb3624ce1aff3aa8a49721f92ee53`.

The authoritative Kane Fabric runtime/test environment remains CT102 `kane-fabric` on Proxmox host `srv-b`, with operational state rooted at `/var/lib/kane-fabric` and the recorded checkout at `/tmp/kane-fabric-ms2`.

## Accepted MS5 repository baseline

The MS5-006 repository implementation remains accepted at `ef6a08f03a94aabd6c15e9c02f6ed9470c65d3ce`. The accepted transport architecture is `9cdb0206f4f7280799bec9d228a4f56a326a4ad1`; residual reconciliation is `c43814961cb14d6623ef92e40d6cf4d72f8ef37e`; and the ESP32-S3 v1 firmware responsibility freeze is accepted in CT102 at `5d45fd600468060104341166adf23bb6465393d2`.

That CT102 checkpoint produced:

```text
firmware-v1 structural guard    PASS
MS5 work-sequence authority     valid
Python compileall               PASS
MS5 tests                       54 passed, 1 environment skip
host C compiler                 absent on CT102
host C compile                  SKIPPED
worktree                        clean
```

CT102 deliberately does not build or flash ESP firmware and does not receive USB passthrough for the reference workflow.

## CIVICVS Project Environment

The physical CPE is now explicitly recorded in `docs/CIVICVS_PROJECT_ENVIRONMENT.md`. That document is the SSOT for the physical build/programming workstation, fixed USB topology, CPE network identities, TrivialHTTP build role, and Dell/LXD Firmware Authority host placement.

Current CPE physical hosts:

```text
10.110.0.4  fw              CPE Build and Hardware Workstation
10.110.0.9  Dell Precision  Ubuntu/LXD host; future Firmware Authority host
```

These are infrastructure identities, not Fabric logical/geographic identities.

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

The non-secret repository scaffold was introduced at `e42ec17f0ccd6de39c2b5b6987063a424a22a649`. It is not yet an accepted operational signing authority and has not yet been accepted in CT102.

The physical host is the Dell Precision already on the CPE/Wiregate network at `10.110.0.9/22`. The host runs Ubuntu with LXD, not Proxmox, and already carries unrelated RAG/LLM workloads. Kane Fabric must not disturb those workloads or inherit GPU passthrough merely because the authority container shares that physical host.

Planned placement:

```text
Dell Precision physical host / 10.110.0.9
└── Ubuntu LXD
    └── unprivileged container: firmware-authority
        private signing key file: prohibited
        signing: disabled
        container CPE identity: not assigned
        operational acceptance: MS5-009
```

`10.110.0.9` is the physical Dell host identity. The Firmware Authority container's `network identity: NOT ASSIGNED` does not mean the Dell host lacks a CPE address.

Before any Dell/LXD mutation, perform a bounded read-only inventory of host identity, Ubuntu/LXD version, projects, storage pools, profiles, networks, existing instances, resources, passthrough configuration, and actual management/file-transfer path. Do not use `pct` on the Dell and do not invent a storage pool, bridge, host path, or container address.

## Stable operational authorities

```text
repository                    git64bit/Kane-Fabric
branch                        main
CPE SSOT                      docs/CIVICVS_PROJECT_ENVIRONMENT.md
Proxmox host                  srv-b
Kane runtime/test container   CT102 / kane-fabric
CT102 checkout                /tmp/kane-fabric-ms2
operational root              /var/lib/kane-fabric
authoritative DB              /var/lib/kane-fabric/database/kane-county-fabric.gpkg
DB SHA256                     31e362b696a37f1b9c45ae355c5669511a3128c17a651108a62e20d1cedebd67
CPE build/program host        fw / 10.110.0.4
Firmware Authority host       Dell Precision / 10.110.0.9
```

## Execution-domain rule

Do not transfer command assumptions between hosts:

```text
srv-b       Proxmox / pct
fw          bare-metal Ubuntu / cpe-shell and CPE wrappers
Dell        Ubuntu LXD / LXD control plane; exact live paths/config first
```

A path valid on one host is not valid on another merely because an Assistant produced a file with that name. Host paths must come from the SSOT or live observation.

## Next safe action

The repository now contains the missing CPE topology but CT102 still reflects the last accepted firmware-v1 checkpoint. The next repository gate is to synchronize CT102 using its recorded checkout `/tmp/kane-fabric-ms2` and run only the tests invalidated by the CPE/Firmware Authority additions.

After repository acceptance, the Firmware Authority workstream proceeds with a read-only Dell/LXD inventory before any container creation or mutation. The first controlled ESP32-S3 flash on `fw` remains separately pending.
