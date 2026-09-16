# Kane Fabric — Current Handoff

Start with `docs/DEVELOPMENT_PROCESS.md`, `docs/CURRENT_STATE.json`, `docs/SESSION_START.md`, `docs/CIVICVS_PROJECT_ENVIRONMENT.md`, and `docs/CPE_HOST_CONTROL_PLANE_MODEL.md` before physical CPE or Firmware Authority work. `docs/MILESTONE_5_DESIGN.md` remains the sole detailed authority for Milestone 5.

## Released foundation

Milestones 0–4 are complete. The accepted MS3 substrate identity is `fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc`; the accepted MS4 implementation is `9f6013d1b8b44998047f71e2b3f3e9c55c9ed298`; the accepted MS4 composition identity is `a58c8398248cee05b7baad9ae289fe0581bdb3624ce1aff3aa8a49721f92ee53`.

The authoritative Kane Fabric runtime/test environment remains CT102 `kane-fabric` on Proxmox host `srv-b`, with operational state rooted at `/var/lib/kane-fabric` and the recorded checkout at `/tmp/kane-fabric-ms2`.

## Accepted CT102 repository checkpoint

CT102 accepted the complete implementation/evidence checkpoint at:

```text
2b7c74ea631f30615ca10e8c79934748a96c7941
```

Acceptance evidence on 2026-09-16:

```text
Python compileall                  PASS
MS5 tests                          70 passed, 1 expected environment skip
configured Fabric DB authority     readable / accepted-geographic-state
development-state checks           all true
worktree                            clean
branch/upstream/origin/refspec      conformant
```

The single skip is expected because CT102 deliberately has no host C compiler. Later documentation/state-record commits advance GitHub `main` beyond `2b7c74e...`; they do not convert into a new CT102 acceptance claim unless CT102 is explicitly rerun.

## CPE execution domains

```text
srv-b / 10.110.0.12
  Proxmox / pct
  CT102 private service address 10.20.0.12/24

fw / 10.110.0.4
  bare-metal Ubuntu
  CPE wrappers
  ESP-IDF build / direct USB programming / runtime evidence

annales / 10.110.0.9
  Ubuntu LXD / lxc
  firmware-authority on lxdbr0 private NAT
```

Do not transfer filesystem paths, control-plane commands, or guest-network assumptions between these environments.

## Firmware Authority Node — complete inert deployment

The inert Firmware Authority deployment is accepted on `annales`.

```text
container                   firmware-authority
state                       RUNNING
image fingerprint           6330af160fc7a345119549990a92e7cba23c25bc846e4906729f525d6ddd1b19
CPU / RAM                    2 / 2 GiB
unprivileged                yes
autostart                   yes
network                     lxdbr0 / NAT
container CPE identity      none
WireGuard                   absent
GPU                         none
host-directory passthrough none
proxy device                none
USB signer                  none
private signing key         NOT CREATED
signing                     DISABLED
activation                  gated by MS5-009
```

Final physical acceptance ended with:

```text
ANNALES_FIRMWARE_AUTHORITY_ACCEPTANCE=PASS
```

Detailed evidence: `docs/CPE_FIRMWARE_AUTHORITY_ACCEPTANCE.md`.

Do not return to `annales` for ordinary ESP32 work. Leave the container inert until MS5-009 explicitly freezes and accepts the external hardware-backed signer and authorization envelope.

## ESP32-S3 physical checkpoint — accepted first flash and cold boot

`fw` is the dedicated build/programming workstation. `/home/cpe-build` is the CPE project home; `/home/civicus-build` is legacy and must not be used.

Fixed USB roles:

```text
CPE-USB-1  branch 1.1.2  PROGRAM   Espressif USB Serial/JTAG 303a:1001
CPE-USB-2  branch 1.1.3  TERMINAL  Silicon Labs CP2102 UART  10c4:ea60
```

Reference board:

```text
chip                       ESP32-S3 QFN56 revision v0.2
PSRAM                      8 MB
MAC                        b8:f8:62:e2:d5:2c
Secure Boot                disabled
Flash Encryption           disabled
Security Flags             0x00000000
reference flash            16 MB
```

A separate pre-secured experimental board ending `B8:F8:62:E2:D2:84` is excluded and must remain untouched.

### First controlled flash

The first controlled flash and cold boot succeeded. The initial boot exposed a reproducibility defect: physical flash was 16 MB while the binary header inherited ESP-IDF's 2 MB default.

The repository default was corrected at:

```text
d26ec418751b7b2f82a8814297204e1b62bceda4
```

Tracked defaults now include:

```text
CONFIG_IDF_TARGET="esp32s3"
CONFIG_ESPTOOLPY_FLASHSIZE_16MB=y
```

After regenerating the build configuration, `cpe-flash` used:

```text
--chip esp32s3
--flash-size 16MB
```

The corrected firmware was reflashed successfully; bootloader, partition table, and application each completed written-data hash verification.

A PROGRAM→TERMINAL power transition produced a true cold boot:

```text
rst:0x1 (POWERON)
SPI Flash Size : 16MB
App version: d26ec41
```

The earlier `16384k` versus `2048k` warning was absent. The application reached `app_main()` normally without reset loop, panic, or fatal error.

Detailed evidence: `docs/CPE_ESP32_FIRST_FLASH_ACCEPTANCE.md`.

Current physical state:

```text
PROGRAM / CPE-USB-1    OFF
TERMINAL / CPE-USB-2   ON
```

Do not switch ports merely to verify them. Switch back to PROGRAM only when another firmware flash is actually required.

## Current MS5-006 boundary

The current firmware is still the MS5-006 build probe. It proves that the storage/range components link under the pinned toolchain, but it intentionally does not yet start networking or mount a physical artifact partition.

Already accepted on physical hardware:

```text
pinned ESP-IDF/toolchain build       PASS
PROGRAM role                         PASS
TERMINAL role                        PASS
reference-board security baseline    PASS
first controlled flash               PASS
cold boot after power loss           PASS
firmware identity diagnostics        PASS
esp32s3 target pin                   PASS
16 MB flash geometry                 PASS
```

Still pending:

```text
prepared read-only artifact storage
active-inventory verification
real plain-HTTP GET
exact closed byte-range runtime behavior
fail-closed invalid-active-state behavior
Wiregate browser path
firmware authenticity/update/rollback/recovery
replacement/reprovisioning proof
constrained-resource acceptance
```

## TrivialHTTP

`fw` also builds TrivialHTTP from `git64bit/kane-map`.

At Kane-map commit `5d323196f877ceb86c8042afeadc7b44b6eaedbd`:

```text
Linux x86-64 SHA-256   ae822f27001ee9496a80a79d9e4a7ce8bbdec8ac5d050e60b5d4c27623ad1807
Windows x86-64 SHA-256 4ec4c7504191b82dec81d92cd57653ef420d93da403930f88c3ed264bcf49f6a
```

macOS arm64 and x86-64 are accepted through native GitHub-hosted macOS CI rather than cross-built on `fw`.

## Stable authorities/checkpoints

```text
repository                         git64bit/Kane-Fabric
branch                             main
accepted CT102 HEAD                2b7c74ea631f30615ca10e8c79934748a96c7941
ESP32 accepted firmware source     d26ec418751b7b2f82a8814297204e1b62bceda4
ESP32 physical acceptance doc      docs/CPE_ESP32_FIRST_FLASH_ACCEPTANCE.md
CPE SSOT                           docs/CIVICVS_PROJECT_ENVIRONMENT.md
host-control-plane model           docs/CPE_HOST_CONTROL_PLANE_MODEL.md
Kane runtime/test container        CT102 / kane-fabric / 10.20.0.12
operational root                   /var/lib/kane-fabric
authoritative DB                   /var/lib/kane-fabric/database/kane-county-fabric.gpkg
DB SHA256                          31e362b696a37f1b9c45ae355c5669511a3128c17a651108a62e20d1cedebd67
CPE build/program host             fw / 10.110.0.4
Firmware Authority host            annales / 10.110.0.9
Firmware Authority container       firmware-authority / lxdbr0 private NAT
```

## Next safe action

Stay on `fw`.

Leave PROGRAM off and TERMINAL on until a new firmware flash is actually required.

Continue MS5-006 by implementing and physically proving prepared read-only artifact storage and active-inventory verification on the reference ESP32-S3. After that, prove real plain-HTTP GET and exact closed byte-range behavior.

Do not activate Firmware Authority signing during this work; MS5-009 remains the signing-activation boundary.
