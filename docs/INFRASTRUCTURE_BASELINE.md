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

## 2. Host-level conformance authority

CT102 does not define an independent container standard for properties shared with other containers on `srv-b`.

The host-level executable baseline check, `ct-baseline.sh`, is the authority for those shared properties. It is read-only, may be run at any time, and exits non-zero when a checked container diverges.

The governing rule is:

> A property not checked by the host baseline is not part of the shared container standard.

If a property must be uniform across `srv-b` containers, it belongs in the host baseline rather than in Kane Fabric documentation alone. Kane Fabric may add project-specific requirements, but it must not silently redefine host-level ones.

The canonical host-level check belongs to `srv-b`, outside the Kane Fabric repository. Kane Fabric documentation records its dependency on that check rather than maintaining a competing copy.

The accepted host baseline reported on 2026-08-18:

```text
scope      srv-b, CT 100, CT 101, CT 102
result     62 passed, 0 failed, 3 informational
```

## 3. LXC features

For Debian 12 unprivileged containers on this host:

- `nesting=1` is required. Its absence was proven to cause systemd `226/NAMESPACE` failures.
- `keyctl=1` is not a universal host requirement. It is needed where Docker or another workload explicitly requires it.

CT102 currently has both `nesting=1,keyctl=1`. That is conformant. Kane Fabric must not treat `keyctl=1` as a permanent platform dependency unless an actual Fabric workload requires it.

## 4. Locale baseline

Minimal Debian CTs in this environment do not initially contain the expected `en_US.UTF-8` locale and produce Perl/locale warnings.

The standard CT bootstrap must:

- install `locales`;
- enable and generate `en_US.UTF-8`;
- set `LANG=en_US.UTF-8`;
- avoid forcing persistent `LC_ALL`.

A clean verification should show all normal locale categories resolving to `en_US.UTF-8` and no Perl locale warning.

## 5. Timezone

The initial Kane deployment uses:

```text
America/Chicago
```

Timezone is deployment policy, not a county-data identity.

## 6. Shared container requirements on srv-b

The host baseline currently asserts, per container:

- `onboot: 1`;
- unprivileged LXC;
- `nesting=1`;
- exactly one network interface;
- that interface is on `vmbr1`;
- one matching guest interface stanza;
- Debian 12;
- timezone `America/Chicago`;
- generated `en_US.UTF-8` locale;
- `curl` installed;
- `ca-certificates` installed;
- `openssh-server` installed;
- `sshd` active;
- administrative account present with correctly owned `authorized_keys` at mode `0600`;
- no container mail agent;
- SMTP egress blocked while ordinary internet egress remains usable;
- home-LAN gateway unreachable;
- systemd `running` with zero failed units.

Host-level checks also cover host systemd health, firewall isolation rules, disk monitoring, and bastion-key presence.

Kane Fabric-specific checks may be stricter where the application requires it, but they are additive to this baseline.

## 7. Base software for Kane Fabric

Current minimum known Kane Fabric capabilities include:

- Python 3;
- SQLite library and `sqlite3` CLI;
- Git;
- CA certificate bundle;
- `curl`;
- standard Unix archive/hash tools;
- systemd.

Kane Condo 0.4's database pipeline is intentionally lightweight and was proven on the reconstructed CT using Python standard-library facilities and SQLite.

Do not add PostgreSQL/PostGIS, Docker, Node.js, GDAL, nginx, Apache, or other platforms merely because they are common GIS/web tools. Add dependencies only when an explicit Kane Fabric requirement needs them.

## 8. Network and mail boundary

CT102 shares the `10.20.0.0/24` service network with CT100 and CT101 but remains a separate project resource.

Containers on this host do not originate mail. Only `srv-b` sends its own operational alerts through the existing relay path. CT102 therefore inherits the host SMTP egress block.

If Kane Fabric later needs application mail, that is a separate application/infrastructure design problem. Installing a mail agent inside CT102 while SMTP egress remains blocked is not an acceptable partial solution.

Co-location does not imply application trust or shared ownership. Mechanical Compiler and Kane Fabric integration must use explicit contracts.

## 9. Acceptance and conformance gate

A Kane Fabric infrastructure baseline on `srv-b` is accepted only when both layers pass:

1. the host-level `ct-baseline.sh` check exits zero for CT102 and the host requirements it depends on;
2. Kane Fabric-specific requirements also pass, including data storage and application tooling not covered by the host standard.

Run the host conformance check:

- before beginning work on CT102 when host/container state may have changed;
- after changes to CT102 or relevant host firewall rules;
- after a host reboot;
- before backup work;
- as part of restore verification.

Conformance is a precondition for backup. A backup of an unverified configuration merely preserves an unknown or divergent state.

## 10. Kane Fabric-specific health gate

In addition to host conformance, verify:

- `/var/lib/kane-fabric` is mounted and writable for active state;
- immutable/reference evidence remains distinguishable from active mutable state;
- Python, SQLite, and Git versions/capabilities required by the current reconstruction are present;
- the Kane Fabric database/reconstruction test gates appropriate to the current milestone pass.

## 11. Data layout

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

## 12. File transfer policy for current environment

Large cross-machine artifacts are transferred manually as tarballs using Webmin download/upload, followed by SHA-256 verification before extraction.

The reconstruction procedure must not assume `scp` or SSH service availability between machines.

## 13. Shared host boundary

`srv-b` also hosts Mechanical Compiler infrastructure.

Kane Fabric must not consume or repurpose Mechanical Compiler CT resources by default.

Mechanical Compiler may consume Kane Fabric geographic services through explicit network/data contracts, but it remains a separate application and infrastructure responsibility.

Host-level infrastructure rules may apply to both projects; application ownership does not.