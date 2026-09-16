# Kane Fabric Session Start

This document defines the fast path for resuming Kane Fabric development without rediscovering or inventing stable infrastructure facts.

## Read order

At the beginning of a development session:

1. read live GitHub `main`;
2. read `docs/HANDOFF.md`;
3. read `docs/CURRENT_STATE.json`;
4. read `docs/DEVELOPMENT_PROCESS.md`;
5. **before physical CPE, ESP, TrivialHTTP, or Firmware Authority work, read `docs/CIVICVS_PROJECT_ENVIRONMENT.md`;**
6. read only the current milestone documents needed for the next action.

Do not use private chat history as a substitute for these records.

## Stable facts are not discovery tasks

The following remain stable until deliberately changed or contradicted by a failed verification:

```text
repository                   git64bit/Kane-Fabric
branch                       main
Proxmox host                 srv-b
Kane Fabric container        CT102 / kane-fabric
CT102 checkout               /tmp/kane-fabric-ms2
operational root             /var/lib/kane-fabric
CPE network                  10.110.0.0/22
CPE build/program host       fw / 10.110.0.4
Firmware Authority host      Dell Precision / 10.110.0.9
```

The physical host control planes are different:

```text
srv-b  -> Proxmox -> pct
fw     -> bare-metal Ubuntu -> cpe-shell / CPE wrappers
Dell   -> Ubuntu LXD -> LXD control plane
```

Do not use `pct` on the Dell. Do not assume `/home/cpe-build` exists on `srv-b` or the Dell. Do not assume a file path merely because an Assistant generated a file with that filename.

## CT102 one-command check

From `srv-b`, after confirming CT102 is running:

```bash
pct status 102
pct exec 102 -- bash -lc '
  cd /tmp/kane-fabric-ms2
  bash development/kane-fabric-dev-state.sh
'
```

The literal checkout path above is the current recorded operational path. If `docs/CURRENT_STATE.json` later changes it, use the recorded path and update this document at the same material checkpoint.

The checker is read-only. It verifies repository identity, branch/upstream/refspec/worktree state, the relation between live and recorded HEAD, the configured database authority, and the recorded next safe action.

Use `--deep` only when full database SHA-256 and validation are required.

## CPE physical work

For `fw`, use the operator contract recorded in `docs/CIVICVS_PROJECT_ENVIRONMENT.md`. The normal entry is `cpe-shell`, followed by CPE wrappers such as `cpe-status`, `cpe-ports`, `cpe-chip-info`, `cpe-build`, `cpe-flash`, and `cpe-monitor`.

Do not source or reuse `/home/civicus-build`. The isolated project home is `/home/cpe-build`.

The fixed hardware roles are:

```text
CPE-USB-1 / branch 1.1.2 / PROGRAM
CPE-USB-2 / branch 1.1.3 / TERMINAL
```

At the current checkpoint the clean ESP32-S3 is connected to PROGRAM and the first controlled flash remains pending.

## Dell / Firmware Authority work

The Dell Precision is already a physical CPE host at `10.110.0.9`; the future `firmware-authority` container does not yet have an independently assigned CPE address.

Before any Dell mutation, run a bounded read-only LXD/host inventory. The exact hostname, LXD version, projects, storage pools, profiles, bridges, instance naming, resource availability, passthrough state, and management/file-transfer path must be observed before they are used.

Do not invent a storage pool, bridge, container IP, host staging path, or transfer path.

## Repository freshness

GitHub `main` is software authority. `CURRENT_STATE.json` records the last observed accepted operational checkpoint, not a guarantee that CT102 already equals current `main`.

Never fast-forward a dirty or unexpected checkout blindly. Compare branch, upstream, refspec, origin, worktree, and current HEAD before synchronization.

Accepted tests are not rerun merely because a new session began. Rerun only the gates invalidated by changed implementation, dependency/environment changes, or contradictory live observations.

## Contradictions

If a stable fact is contradicted:

1. stop before state-changing work;
2. inspect only the contradicted area;
3. determine whether live state or documentation is wrong;
4. correct `CURRENT_STATE.json`, `HANDOFF.md`, and the relevant SSOT document at the same material checkpoint;
5. continue from the corrected state.

A successor should not need private chat history to reconstruct stable project topology.
