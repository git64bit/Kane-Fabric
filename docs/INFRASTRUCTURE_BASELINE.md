# Kane Fabric Infrastructure Baseline

## 1. Initial deployment

The first Kane Fabric node is CT102 `kane-fabric` on Proxmox host `srv-b`.

Initial allocation:

- Debian 12;
- 4 vCPU;
- 6144 MB RAM;
- 2048 MB swap;
- 20 GiB root filesystem;
- 20 GiB data filesystem mounted at `/var/lib/kane-fabric`;
- unprivileged LXC;
- autostart enabled;
- network `10.20.0.12/24` via `vmbr1`;
- gateway `10.20.0.1`.

The initial allocation is deliberately conservative and may be resized when measured workload justifies it.

## 2. Required LXC features

For the current Proxmox/Debian environment, the CT requires:

```text
nesting=1,keyctl=1
```

Without these flags the Debian 12 CT exhibited systemd unit failures with `226/NAMESPACE`, including `systemd-logind`, `systemd-networkd`, and `systemd-timedated`.

This is part of the bootstrap contract for this environment.

## 3. Locale baseline

Minimal Debian CTs in this environment do not initially contain the expected `en_US.UTF-8` locale and produce Perl/locale warnings.

The standard CT bootstrap must:

- install `locales`;
- enable and generate `en_US.UTF-8`;
- set `LANG=en_US.UTF-8`;
- avoid forcing persistent `LC_ALL`.

A clean verification should show all normal locale categories resolving to `en_US.UTF-8` and no Perl locale warning.

## 4. Timezone

The initial Kane deployment uses:

```text
America/Chicago
```

Timezone is deployment policy, not a county-data identity.

## 5. Base software

Current minimum known packages/capabilities:

- Python 3;
- SQLite library and `sqlite3` CLI;
- Git;
- CA certificate bundle;
- standard Unix archive/hash tools;
- systemd.

Kane Condo 0.4's database pipeline is intentionally lightweight and was proven on the reconstructed CT using Python standard-library facilities and SQLite.

Do not add PostgreSQL/PostGIS, Docker, Node.js, GDAL, nginx, Apache, or other platforms merely because they are common GIS/web tools. Add dependencies only when an explicit Kane Fabric requirement needs them.

## 6. Health gate

A county Fabric CT baseline is not accepted until:

- network route is present;
- gateway reachability is confirmed;
- data mount is present and writable for active state;
- timezone is correct;
- locale is clean;
- required packages are installed;
- `systemctl is-system-running` reports `running`;
- `systemctl --failed` reports zero failed units.

## 7. Data layout

Current Kane node external state is rooted at:

```text
/var/lib/kane-fabric/
```

Expected categories:

```text
seed/                    immutable initial seed evidence
reconstruction-inputs/   imported historical reconstruction evidence
reconstruction-code/     historical software/reference checkouts
database/                active Kane Fabric database
staging/                 candidate/reconciliation/promotion workspace
rollback/                rollback artifacts
audit/                   operational/reconstruction audit output
render/                   compiled substrate/subscription artifacts
```

The exact active layout may evolve, but seed/reference evidence and active mutable state must remain distinguishable.

## 8. File transfer policy for current environment

Large cross-machine artifacts are transferred manually as tarballs using Webmin download/upload, followed by SHA-256 verification before extraction.

The reconstruction procedure must not assume `scp` or SSH service availability.

## 9. Shared host boundary

`srv-b` also hosts Mechanical Compiler infrastructure.

Kane Fabric must not consume or repurpose Mechanical Compiler CT resources by default.

Mechanical Compiler may consume Kane Fabric geographic services through explicit network/data contracts, but it remains a separate application and infrastructure responsibility.