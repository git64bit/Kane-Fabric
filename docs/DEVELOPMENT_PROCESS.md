# Kane Fabric Development Process

## Purpose

This document defines how Kane Fabric development is executed, which system owns each kind of state, and how a successor resumes work without repeating already accepted discovery and verification.

The process has three goals that must coexist:

1. never confuse repository/sandbox work with real environment acceptance;
2. do not spend each new session reconstructing stable facts already recorded in the SSOT;
3. never transfer filesystem paths, control-plane commands, or host assumptions from one physical environment to another.

Historical milestone handoffs preserve historical procedure and evidence. They do not override this document.

## Current-state documents

Use these documents for different purposes:

- `docs/HANDOFF.md` — durable system mental model, accepted checkpoints, non-obvious invariants, current workstream narrative, and exact next safe action;
- `docs/CURRENT_STATE.json` — compact machine-readable latest observed operational checkpoint;
- `docs/SESSION_START.md` — low-churn session-resume procedure;
- `docs/BROWSER_FIRST_ONLINE_FIRST_DIRECTIVE.md` — current browser implementation-order authority;
- `administration/README.md` — active administrative county/web/category/contract workstream;
- `docs/WEB_APPLICATION_DESIGN.md` — browser application design authority;
- `docs/CIVICVS_PROJECT_ENVIRONMENT.md` — physical CPE hosts, CPE network identities, `fw` build/programming environment, fixed USB topology, `annales`/LXD Firmware Authority placement, and cross-host execution boundaries;
- current milestone design/handoff — milestone-specific implementation and acceptance detail.

`CURRENT_STATE.json` is a recorded observation, not a substitute for live authority. It deliberately distinguishes the last observed operational state from the current GitHub `main` commit.

## Current implementation order

Kane Fabric remains Browser-First, but implementation is now Online-First.

The current development sequence is:

```text
full online Kane County browser/interface
        ↓
administrative categories + participant contracts
        ↓
bounded participant-publication composition
        ↓
shared browser modules/contracts stabilize
        ↓
local/offline browser reduction
```

The reduced offline browser is a derivative of the same application architecture. It is not a separate product or schema.

This ordering is an implementation rule, not a relaxation of the anti-capture architecture. The online operator must not become the exclusive custodian of participant data or the source of civic identity merely because online development happens first.

## Authority map

Kane Fabric separates these authorities:

| Authority | Owns |
| --- | --- |
| GitHub `git64bit/Kane-Fabric`, branch `main` | software, contracts, migrations, tests, documentation, small deterministic manifests |
| Proxmox host `srv-b` | CT lifecycle, host conformance, host firewall/network policy, host-to-CT execution |
| CT102 `kane-fabric` | real Kane Fabric runtime/test/compiler environment for repository/data/browser/admin gates |
| `/var/lib/kane-fabric` inside CT102 | operational databases, immutable evidence, staging, rollback, audit, compiled artifacts |
| `fw` / `10.110.0.4` | CPE build and hardware workstation: pinned ESP-IDF build, direct USB programming/terminal, physical ESP acceptance, TrivialHTTP Linux/Windows builds |
| `annales` / `10.110.0.9` | Ubuntu/LXD physical host for the accepted inert `firmware-authority` container; unrelated RAG/LLM and witness workloads remain separate |

These roles must not be collapsed. An Assistant sandbox is none of them.

The physical CPE hosts are replaceable infrastructure. Their addresses and hardware do not become Fabric logical/geographic identity.

## Session-start fast path

A new Assistant must not begin by searching host filesystems or replaying already accepted gates.

Start with:

1. read live GitHub `main`;
2. read `docs/HANDOFF.md`;
3. read `docs/CURRENT_STATE.json`;
4. read `docs/SESSION_START.md`;
5. read `docs/BROWSER_FIRST_ONLINE_FIRST_DIRECTIVE.md`;
6. read `administration/README.md` and `docs/WEB_APPLICATION_DESIGN.md` for the active workstream;
7. before physical ESP/CPE/TrivialHTTP/Firmware Authority work, read `docs/CIVICVS_PROJECT_ENVIRONMENT.md`;
8. read only the current milestone documents needed for the next action;
9. use recorded paths/control planes directly unless a live check contradicts them;
10. investigate only the contradicted fact.

Stable facts are not discovery tasks.

## Execution domains

### `srv-b` / CT102

Kane Fabric runtime/data/browser/admin commands execute inside CT102 through Proxmox host `srv-b`:

```bash
pct status 102
pct exec 102 -- COMMAND ARGUMENTS...
pct exec 102 -- bash -lc '...'
```

The current recorded CT102 checkout is:

```text
/tmp/kane-fabric-ms2
```

A stopped/unavailable CT is infrastructure state, not an application test failure.

Do not substitute CT100, CT101, `fw`, `annales`, or an Assistant sandbox for CT102 repository/data/browser acceptance.

The current administrative/browser workstream belongs here after the checkout is synchronized to current GitHub `main` and the relevant gates are rerun.

### `fw`

`fw` is bare-metal Ubuntu, not Proxmox. Its normal project entry is:

```text
/usr/local/bin/cpe-shell
```

The isolated CPE project home is:

```text
/home/cpe-build
```

Normal work is performed through the CPE wrappers recorded in `docs/CIVICVS_PROJECT_ENVIRONMENT.md`, including `cpe-status`, `cpe-ports`, `cpe-chip-info`, `cpe-build`, `cpe-flash`, and `cpe-monitor`.

`/home/civicus-build` is legacy and must not be sourced, modified, reused, or treated as the CPE environment.

MS5-006 physical device runtime is accepted at firmware source `7aa3c836bae470704d051a36a6261a1140e9d3d0`. Firmware work is currently paused while the online administrative/browser contracts are developed.

Do not reflash or specialize the ESP32 during ordinary county/web/category/contract work unless a concrete contract requirement or a later MS5 lifecycle gate intentionally returns work to `fw`.

### `annales` / Firmware Authority host

`annales` at `10.110.0.9` runs Ubuntu/LXD, not Proxmox. `pct` does not apply.

The `firmware-authority` LXD container already exists and its inert deployment is accepted.

Current accepted boundary:

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

Do not invent a new bridge, CPE address, passthrough device, signer path, or authority activation merely because the container exists.

## Cross-host anti-drift rule

A valid path or command on one host is not evidence that it exists on another.

In particular:

- `/tmp/kane-fabric-ms2` is the recorded CT102 checkout, not an `fw` or `annales` path;
- `/home/cpe-build` is the `fw` CPE home, not a `srv-b` or `annales` path;
- `pct` belongs to `srv-b`/Proxmox, not `fw` or `annales`;
- LXD control-plane operations belong to `annales`, not `srv-b`;
- an Assistant-generated/downloadable file is not present on any remote host until its placement has been established by SSOT or observed live.

Never issue a state-changing command containing an unrecorded host path merely because that path would be convenient.

## Assistant responsibility and manual relay exception

Routine project execution is an Assistant/development responsibility when an authorized execution channel exists.

If a session lacks an authorized channel to a required host:

- state the capability gap accurately;
- do not claim remote commands ran;
- do not present sandbox output as remote acceptance evidence;
- continue repository-only work where valid.

The user may explicitly choose or accept a bounded manual command relay. When that exception is in use, issue one bounded command group at a time for state-changing or diagnostic work and evaluate returned output before the next group.

## Repository workflow

GitHub `main` is the software Single Source of Truth.

Work directly on `main` unless the user explicitly requests a branch/PR workflow.

Before changing a live checkout, inspect at minimum:

```bash
git status --short --branch
git branch -vv
git config --get-all remote.origin.fetch
git remote -v
```

Never discard unexplained local changes. Never silently restrict the fetch refspec to one branch.

CT102 and `fw` do not need GitHub write credentials merely for Assistant publication. Use the authorized GitHub integration for repository writes.

## CT102 checkout rule

The path in `docs/CURRENT_STATE.json` is the current operational CT102 checkout path until deliberately changed or contradicted.

Use that path first. Do not search `/tmp`, `/root`, `/opt`, `/srv`, or `/var/lib` for another checkout unless:

- the recorded path does not exist;
- it is not `git64bit/Kane-Fabric`;
- branch/upstream/refspec/worktree checks contradict the recorded contract.

If a new canonical checkout is deliberately established, update `CURRENT_STATE.json`, `HANDOFF.md`, and `SESSION_START.md` at the same material checkpoint.

## One-command CT state check

The normal read-only CT checker is:

```bash
bash development/kane-fabric-dev-state.sh
```

From `srv-b`:

```bash
pct status 102
pct exec 102 -- bash -lc '
  cd /tmp/kane-fabric-ms2
  bash development/kane-fabric-dev-state.sh
'
```

Use `--deep` only when full database validation and SHA-256 are required. Do not incur deep database hashing on every session start.

## Development loop

The normal loop is:

```text
read current main + current checkpoint + relevant environment SSOT
        ↓
run the least expensive live state check for the target environment
        ↓
make the smallest coherent implementation/contract change
        ↓
update GitHub main
        ↓
verify/synchronize the affected real environment when required
        ↓
run only invalidated acceptance gates
        ↓
verify authoritative state changed only when intended
        ↓
record one material checkpoint
```

Do not insert documentation commits after every intermediate observation. Batch ordinary observations into a material checkpoint.

## Browser/admin development loop

For the current workstream, prefer this sequence:

```text
accepted county geography + existing browser foundation
        ↓
define one administrative contract slice
        ↓
exercise it in the full online browser/interface
        ↓
add repository tests for the stabilized contract
        ↓
accept in CT102 / real browser as appropriate
        ↓
repeat
```

Do not begin by designing the offline-only form. Once the online contracts and shared browser modules are stable, produce the offline/local form by source substitution and removal of network-only conveniences.

## Documentation/checkpoint cadence

Update `CURRENT_STATE.json`, `HANDOFF.md`, `SESSION_START.md`, and the applicable environment/milestone SSOT at a material checkpoint, including when:

- an acceptance gate changes the next safe action;
- a deployment/authority/checkout path changes;
- a physical CPE host or hardware mapping is accepted or replaced;
- a new non-obvious invariant or exception is discovered;
- operational DB path/hash changes;
- an implementation boundary or development-order rule changes.

A documentation-only commit after an accepted test does not by itself invalidate that test. Record the implementation/test HEAD actually exercised and rerun only when relevant code/environment changed.

## Test invalidation discipline

Use the least expensive useful gate and make claims only at the level actually run:

1. static/repository review;
2. synthetic/local unit tests;
3. repository regression tests inside CT102;
4. real browser/admin integration in the accepted CT102 environment when browser-visible behavior changes;
5. exact pinned firmware build on `fw` when firmware build inputs change;
6. physical device flash/runtime evidence on `fw` when device behavior is under test;
7. real Kane County read-only/derived-data gate inside CT102;
8. deliberately scoped authority-changing/release evidence.

Accepted tests are not rerun merely because a new Assistant/session started.

Rerun when implementation, dependency, relevant environment, or contradictory live observation invalidates the prior result.

## Shell safety

Use strict mode inside a bounded subprocess, not by injecting it into an interactive root shell:

```bash
pct exec 102 -- bash -lc '
  set -euo pipefail
  ...
'
```

Quote paths/data deliberately. Do not interpolate untrusted source values into shell command text.

## Operational data boundary

`/var/lib/kane-fabric` is CT102 operational state, not source-control authority:

```text
seed/                    immutable seed evidence
reconstruction-inputs/   frozen historical evidence
reconstruction-code/     frozen historical software reference
database/                active/working Fabric databases
staging/                 candidate/reconciliation/promotion work
rollback/                rollback evidence
audit/                    audit reports
render/                   compiled substrate/subscription artifacts
```

Generated firmware builds and physical-device evidence on `fw` live under the CPE paths documented in `docs/CIVICVS_PROJECT_ENVIRONMENT.md`; they are not silently redirected into CT102.

## Read-only, staged, and authority-changing work

Freshness is not authority. Source refresh, candidate registration, reconciliation, promotion, firmware authorization, and deployment are distinct operations.

Promotion of geographic state remains explicit authority-changing work and requires its accepted prepare/validate/rollback process.

Firmware build evidence likewise does not equal firmware authorization:

```text
build authority ≠ firmware signing authority ≠ distribution authority
```

The Firmware Authority remains inactive until MS5-009 accepts its signer/provider and operational verification path.

## File transfer

For the established `srv-b`/CT102 environment, large cross-machine artifacts use the recorded workflow:

```text
create tarball
→ Webmin download/upload
→ verify SHA-256
→ extract/use
```

Do not prescribe SCP/SSH as the default there unless deployment policy deliberately changes.

`annales`/LXD management is host-mediated. Do not copy `srv-b` filesystem paths or Proxmox transfer assumptions onto `annales`. If a later MS5-009 signer/authority workflow requires a durable transfer path, freeze and document that path at that gate.

## Project boundaries

CT102 is Kane Fabric. CT100 and CT101 are Mechanical Compiler infrastructure and must not be repurposed for Kane Fabric merely because they share `srv-b`.

`annales`' existing RAG/LLM and witness workloads are likewise separate from Kane Fabric. Co-location does not imply application trust, resource ownership, or permission to alter GPU/device passthrough.

## Handoff rule

At material checkpoints, durable state must capture:

- current milestone and implementation boundary;
- current Browser-First/Online-First development order when relevant;
- live/last-observed checkout path, branch, HEAD, upstream, refspec, and worktree state where applicable;
- current operational DB path/hash when established;
- accepted CT102 gates and implementation HEAD actually tested;
- accepted `fw` build/device/USB facts when they change;
- `annales`/LXD host/container facts when they change;
- deliberate exclusions and trust boundaries;
- exact next safe action.

A successor should not need private chat history and should not need to rediscover stable project topology.

## Correction history

The MS-2 branch/refspec incident and later handoff/access failures established two permanent lessons:

1. keep the normal repository workflow on clean `main` unless explicitly changed;
2. preserve compact current-state checkpoints and verify them directly instead of reconstructing the whole environment every session.

The 2026-09-16 CPE reconciliation added a third permanent lesson: **physical development infrastructure must be recorded in GitHub SSOT as soon as it becomes a stable project dependency.** The `fw` build/programming environment and fixed USB topology had been accepted operationally without being preserved in Kane-Fabric, which allowed a later command to incorrectly assume an `fw` filesystem path existed on `srv-b`. The CPE SSOT and cross-host anti-drift rule exist to prevent recurrence.

The 2026-09-17 administrative/browser correction added a fourth permanent lesson: **Browser-First is a product/interface boundary, not a mandate to implement the offline form before the online form.** The full online interface may be developed first, provided the shared contracts remain portable and the later offline form is a reduction rather than a fork.
