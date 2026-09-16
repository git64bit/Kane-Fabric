# CPE Firmware Authority inert-container acceptance

## Status

Accepted on 2026-09-16 on physical CPE host `annales` after the initial `firmware-authority` LXD container was created, started, bootstrapped from pinned repository inputs, and validated.

This is an **inert implementation-scaffold acceptance**, not Firmware Authority activation. Signing remains disabled and operational signing acceptance remains gated by MS5-009.

The pre-deployment physical/LXD discovery remains recorded separately in `docs/CPE_ANNALES_LXD_BASELINE.md`. The normative container contract is `ms5/firmware_authority/container-spec.json`.

## Physical placement

```text
physical host              annales
platform                   Dell Precision 5820 Tower
host CPE/WireGuard         10.110.0.9/22
control plane              LXD 5.21.7 LTS / local lxc
container                  firmware-authority
LXD project                default
storage pool               default / dir
private network            lxdbr0 / NAT
```

The host-mediated CPE rule remains intact: `annales` owns CPE/WireGuard membership. The container has no independent CPE/WireGuard identity.

## Pinned base image

The container was initialized from the exact observed Ubuntu minimal release image fingerprint:

```text
remote                     ubuntu-minimal
observed alias             24.04
fingerprint                6330af160fc7a345119549990a92e7cba23c25bc846e4906729f525d6ddd1b19
image serial               20260905
image description          ubuntu 24.04 LTS amd64 (minimal release) (20260905)
architecture               amd64 / x86_64
release                    noble / 24.04
```

Runtime `/etc/os-release` identified Ubuntu 24.04.4 LTS (Noble Numbat). The image is pinned by fingerprint rather than by the moving release alias.

## LXD contract accepted before first start

The container was created stopped and inspected before its first start.

Accepted host-side configuration:

```text
state before first start   STOPPED
limits.cpu                 2
limits.memory              2GiB
security.privileged        false
boot.autostart             true
profile                    default
eth0                       inherited from default profile on lxdbr0
local root device          default pool, requested size 16GiB
GPU device                 none
proxy device               none
host-directory device      none
USB/signer device          none
base image                 exact pinned fingerprint above
```

The observed unprivileged idmap mapped container UID/GID 0 to host ID 1000000.

### `dir` storage qualification

The active `default` pool uses the LXD `dir` driver backed by the host root filesystem. The instance records a requested root size of `16GiB`, but the running guest reports the shared backing filesystem capacity rather than an enforced 16 GiB filesystem ceiling.

For this host, `16GiB` is therefore retained as requested instance configuration, **not accepted as an enforced quota**. No new storage backend was introduced merely to force a quota.

## First boot and network acceptance

After first start:

```text
systemd                    running
cloud-init                 done, no errors
virtualization             lxc
runtime IPv4               10.56.172.112/24 (dynamic DHCP observation)
default gateway            10.56.172.1
DNS                        lxdbr0 gateway
wg0                        absent
```

`10.56.172.112` is a dynamic observed DHCP lease, not a stable identity and not a CPE address.

The container remains on the host-private `lxdbr0` network. No WireGuard peer was created.

## Repository-pinned bootstrap

No additional package installation was required. The minimal image already provided Bash and Python 3.12.3; `git` was absent and was deliberately not installed because the inert bootstrap does not require it.

The two bootstrap inputs were downloaded from exact accepted repository commit:

```text
repository commit          ee3dcd1b4530283c44f04c33c08458f58c41fb3e
bootstrap-container.sh     Git blob fec68e6cc4cf6af1fac48b0221c8603692dde64a
authority-state.json       Git blob 26c869d2d913045fd884e53cbb7e7c2c11b39466
```

Both downloaded files were independently recomputed as Git blobs inside the container and matched the expected identities before execution.

## Installed inert authority state

Bootstrap created the locked service identity:

```text
user                       firmware-authority
uid                        999
primary group              firmware-authority / gid 991
password state             locked
shell                      /usr/sbin/nologin
```

Installed configuration:

```text
/etc/civicus-firmware-authority/STATUS
/etc/civicus-firmware-authority/authority-state.json
```

Installed non-secret authority state directories:

```text
/var/lib/civicus-firmware-authority/incoming
/var/lib/civicus-firmware-authority/manifests
/var/lib/civicus-firmware-authority/authorizations
/var/lib/civicus-firmware-authority/public-keys
/var/lib/civicus-firmware-authority/evidence
```

The installed `authority-state.json` retained exact Git blob identity:

```text
26c869d2d913045fd884e53cbb7e7c2c11b39466
```

No files existed under `/var/lib/civicus-firmware-authority` at acceptance time.

The installed status was:

```text
role=firmware-authority
state=implementation-scaffold
private_signing_key=NOT_CREATED
persistent_private_signing_key_in_container=PROHIBITED
signing=DISABLED
network_identity=NOT_ASSIGNED
acceptance=MS5-009
```

## Negative-boundary acceptance

The final acceptance explicitly verified:

```text
WireGuard interface             absent
independent CPE identity        absent
NVIDIA/GPU device               absent
USB serial/JTAG device          absent
hardware signer                 absent
host-directory passthrough      absent
proxy device                    absent
private signing key             not created
persistent private key file     prohibited / absent
signing                         disabled
private authority-state files   none
```

The only files in the authority configuration/state roots were the two expected non-secret files under `/etc/civicus-firmware-authority`.

## Acceptance result

The final on-host check ended with:

```text
ANNALES_FIRMWARE_AUTHORITY_ACCEPTANCE=PASS
```

This accepts the physical placement and inert container scaffold on `annales`.

It does **not** accept or authorize:

- firmware release signing;
- signer attachment or key provisioning;
- any persistent private signing key inside the container;
- an independent WireGuard/CPE identity for the container;
- GPU or unrelated host-device passthrough;
- firmware authenticity/update/rollback/recovery completion, which remains MS5-009 work.

## Next repository gate

After this physical acceptance is recorded in GitHub `main`, CT102 on `srv-b` should perform one final repository synchronization and acceptance pass. That repository gate records the accepted documentation/state checkpoint; it does not require returning to `annales` unless a later explicit authority-boundary change is made.
