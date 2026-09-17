# Kane Fabric Session Start

This document defines the fast path for resuming Kane Fabric development without rediscovering or inventing stable infrastructure facts.

## Read order

At the beginning of a development session:

1. read live GitHub `main`;
2. read `docs/HANDOFF.md`;
3. read `docs/CURRENT_STATE.json`;
4. read `docs/BROWSER_FIRST_ONLINE_FIRST_DIRECTIVE.md`;
5. read `administration/README.md` and `docs/WEB_APPLICATION_DESIGN.md` for the active workstream;
6. read `docs/DEVELOPMENT_PROCESS.md`;
7. **before physical CPE, ESP, TrivialHTTP, or Firmware Authority work, read `docs/CIVICVS_PROJECT_ENVIRONMENT.md`;**
8. read only the current milestone documents needed for the next action.

Do not use private chat history as a substitute for these records.

## Current priority

The active priority workstream is **Online County Browser + Administrative Category/Contract Development**.

Kane Fabric remains Browser-First, but implementation is Online-First. Build the full online county interface and stabilize its category/participant/publication contracts before producing the reduced local/offline browser.

Do not resume ESP32 programming merely because an administrative contract is unresolved.

## Stable facts are not discovery tasks

The following remain stable until deliberately changed or contradicted by a failed verification:

```text
repository                   git64bit/Kane-Fabric
branch                       main
Proxmox host                 srv-b / 10.110.0.12
Kane Fabric container        CT102 / kane-fabric
CT102 checkout               /tmp/kane-fabric-ms2
operational root             /var/lib/kane-fabric
CPE network                  10.110.0.0/22
CPE build/program host       fw / 10.110.0.4
Firmware Authority host      annales / 10.110.0.9
Firmware Authority container firmware-authority / LXD private NAT
```

The physical host control planes are different:

```text
srv-b    -> Proxmox -> pct
fw       -> bare-metal Ubuntu -> cpe-shell / CPE wrappers
annales  -> Ubuntu LXD -> lxc
```

Do not use `pct` on `annales`. Do not use LXD commands on `srv-b`. Do not assume `/home/cpe-build` exists on `srv-b` or `annales`.

## Current accepted ESP32 checkpoint

MS5-006 physical runtime is accepted on the reference ESP32-S3.

Accepted firmware source:

```text
7aa3c836bae470704d051a36a6261a1140e9d3d0
```

Accepted physical behavior includes read-only Fabric storage, active-inventory verification, Wi-Fi provisioning/station attachment, plain HTTP GET/range serving, fail-closed invalid storage, and known-good restore.

Acceptance record:

```text
docs/CPE_ESP32_MS5_006_DEVICE_RUNTIME_ACCEPTANCE.md
```

The MS5 repository suite was rerun on `fw` after the administrative/edge correction:

```text
Ran 72 tests
OK
```

Firmware work is currently paused. Leave the accepted runtime unchanged unless a concrete administrative/browser contract exposes a necessary edge change or a later MS5 lifecycle gate is deliberately resumed.

## CT102 administrative environment

CT102 is the authoritative county runtime/compiler/test environment and the target for the current administrative/browser work.

It has no independent CPE/WireGuard address. Normal management is host-mediated through `srv-b`.

From `srv-b`, the control-plane pattern is:

```bash
pct status 102
pct exec 102 -- ...
```

The last explicitly accepted CT102 repository checkpoint remains historical at:

```text
2b7c74ea631f30615ca10e8c79934748a96c7941
```

Later GitHub commits include accepted physical-edge evidence and the new administrative/browser development-order documents. Do not claim CT102 has accepted those later commits until its checkout is synchronized and the relevant checks are rerun.

## CT102 read-only state check

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

## CPE physical work on `fw`

For `fw`, use the operator contract recorded in `docs/CIVICVS_PROJECT_ENVIRONMENT.md`. The normal entry is `cpe-shell`, followed by CPE wrappers such as `cpe-status`, `cpe-ports`, `cpe-chip-info`, `cpe-build`, `cpe-flash`, and `cpe-monitor`.

Do not source or reuse `/home/civicus-build`. The isolated project home is `/home/cpe-build`.

The fixed hardware roles are:

```text
CPE-USB-1 / branch 1.1.2 / PROGRAM
CPE-USB-2 / branch 1.1.3 / TERMINAL
```

Do not switch USB roles or reflash the accepted board during ordinary administrative/browser work.

## Firmware Authority on `annales`

The `firmware-authority` container already exists and its inert deployment is accepted.

Current boundary:

```text
container                   firmware-authority
network                     lxdbr0 / private NAT
independent CPE identity    none
WireGuard                   absent
GPU                         none
host-directory passthrough none
proxy device                none
USB signer                  none
persistent private key      none
signing                     DISABLED
activation                  gated by MS5-009
```

Do not mutate this boundary during ordinary web/category/contract work. In particular, do not attach a signer, create a persistent signing key, add an independent WireGuard peer, or activate signing before MS5-009.

## Browser/admin development boundary

The next implementation surface is the full online Kane County browser/interface.

Use existing accepted browser work under `web/`, `substrate/browser/`, and `ms4/browser/` as the foundation. Do not start a second offline-only application.

The active browser/admin work must make concrete:

- county-facing categories/object classes;
- condominium association identity;
- unit identity/reference semantics;
- participant publication generations;
- public/restricted/private visibility classifications;
- source-neutral publication acquisition;
- composition of bounded participant publications into accepted county geography;
- independent operator conformance for another Illinois county.

The reduced offline/local browser is deferred until these contracts and shared browser modules stabilize.

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

A successor should not need private chat history to reconstruct stable project topology, current development order, or the accepted physical-edge checkpoint.
