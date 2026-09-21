# Kane Fabric Session Start

This document defines the fast path for resuming Kane Fabric development without rediscovering or inventing stable infrastructure facts.

## Read order

At the beginning of a development session:

1. read live GitHub `main`;
2. read `docs/HANDOFF.md`;
3. read `docs/CURRENT_STATE.json`;
4. read `docs/BROWSER_FIRST_ONLINE_FIRST_DIRECTIVE.md`;
5. read `docs/ADMINISTRATIVE_DESCRIPTOR_ARCHITECTURE.md` and `docs/ADMINISTRATIVE_DESCRIPTOR_ACCEPTANCE.md`;
6. read `administration/README.md` and `docs/WEB_APPLICATION_DESIGN.md` for the active workstream;
7. read `docs/DEVELOPMENT_PROCESS.md`;
8. **before physical CPE, ESP, TrivialHTTP, or Firmware Authority work, read `docs/CIVICVS_PROJECT_ENVIRONMENT.md`;**
9. read only the current milestone documents needed for the next action.

Do not use private chat history as a substitute for these records.

## Current priority

The first HOA Diagnostics workflow must now be derived from Illinois statutory procedure before Civic-specific workflow design.

Read first:

- `docs/ILLINOIS_STATUTORY_PROCEDURE_BASELINE.md`
- `docs/CIVIC_OPERATOR_PEER_SCRUTINY.md`
- `docs/CIVIC_PARTICIPATION_RENEWAL.md`
- `docs/CIVIC_ISSUANCE_RECORD.md`

Initial statutory anchors are `765 ILCS 605/18`, `/18.4`, `/18.8`, and `/19`. Reuse statutory roles, notice/delivery mechanisms, record duties, inspection rights, meeting openness/recording rights, deadlines, and fiduciary duties where applicable. Do not present Civic additions as statutory mandates.

Next: derive the minimal participant-operated SASE workflow by marking each step either `STATUTORY_SOURCE` or `CIVIC_ADDITION`. No implementation code yet.

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
Wiregate container             CT103 / kane-wiregate / 10.20.0.13
Wiregate browser origin        https://kane-wiregate.dev.infra
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

MS5-008 deliberately resumes lifecycle feasibility work, but the accepted runtime remains unchanged until the repository candidate/evaluation contract is accepted. The first MS5-008 step is therefore repository-only, not a flash or tunnel mutation.

## CT102 administrative environment

CT102 is the authoritative county runtime/compiler/test environment and the target for the current administrative/browser work.

It has no independent CPE/WireGuard address. Normal management is host-mediated through `srv-b`.

From `srv-b`, the control-plane pattern is:

```bash
pct status 102
pct exec 102 -- ...
```

The first descriptor-driven Administrative Web implementation was explicitly accepted in CT102 at:

```text
7b8b116d5b43660d4260a21f0dc7ea85ec6bc753
```

Acceptance evidence:

```text
web/run-tests.sh                  35 passed / 0 failed / 0 skipped
real Chromium descriptor render  10/10 checks passed
worktree                          clean
```

The acceptance record is:

```text
docs/ADMINISTRATIVE_DESCRIPTOR_ACCEPTANCE.md
```

Later commits may add acceptance tooling/documentation without changing the accepted implementation. Use `docs/CURRENT_STATE.json` to distinguish the accepted implementation HEAD from current GitHub `main`.

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

## Administrative browser gates

The synthetic/browser unit gate is:

```bash
bash web/run-tests.sh
```

The repository-owned real-browser descriptor gate is:

```bash
bash web/run-admin-browser-acceptance.sh
```

The real-browser gate serves the repository locally inside CT102, executes the application in installed Chromium, validates the generated DOM, and verifies the exact canonical SHA-256 identity of the reference descriptor.

Do not confuse this structural/render acceptance with final visual-design acceptance, persistent storage, authentication, offline operation, or a finished Illinois ontology.

## CPE physical work on `fw`

For `fw`, use the operator contract recorded in `docs/CIVICVS_PROJECT_ENVIRONMENT.md`. The normal entry is `cpe-shell`, followed by CPE wrappers such as `cpe-status`, `cpe-ports`, `cpe-chip-info`, `cpe-build`, `cpe-flash`, and `cpe-monitor`.

Do not source or reuse `/home/civicus-build`. The isolated project home is `/home/cpe-build`.

The fixed hardware roles are:

```text
CPE-USB-1 / branch 1.1.2 / PROGRAM
CPE-USB-2 / branch 1.1.3 / TERMINAL
```

Do not switch USB roles. The first MS5-008 application-only evaluation flash has already occurred and was restored byte-identical after the runtime panic. The current MS5-008 action is diagnostic only: symbolize the captured panic on `fw`; do not flash again until the exact crashing function/line is known.

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

Do not mutate this boundary during ordinary web/descriptor work. In particular, do not attach a signer, create a persistent signing key, add an independent WireGuard peer, or activate signing before MS5-009.

## Browser/admin development boundary

The next implementation surface remains the full online Administrative Web, using existing accepted browser work under `web/`, `substrate/browser/`, and `ms4/browser/` as the foundation.

The active work now proceeds from the Infrastructure side outward:

- model statewide Illinois condominium obligations and record categories;
- represent legal/statutory authority explicitly in descriptors;
- keep Infrastructure definitions separate from association-instance values;
- keep semantic identity separate from presentation placement;
- keep the descriptor engine jurisdiction-neutral;
- use versioned/canonical/hashable descriptors;
- expand generic renderer capabilities only when a real Infrastructure slice requires them;
- defer participant-publication and edge-device shape until the Infrastructure boundary is concrete.

The first accepted descriptor slice is Illinois condominium insurance. It is a proof of the descriptor architecture, not a claim that the Illinois insurance model is complete.

The reduced offline/local browser is deferred until the online Infrastructure model and shared browser modules stabilize.

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

A successor should not need private chat history to reconstruct stable project topology, current development order, the accepted descriptor/browser checkpoint, or the accepted physical-edge checkpoint.
