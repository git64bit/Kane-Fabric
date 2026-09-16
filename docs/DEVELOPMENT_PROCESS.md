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

- `docs/HANDOFF.md` — durable system mental model, historical evidence, non-obvious invariants, current milestone narrative;
- `docs/CURRENT_STATE.json` — compact machine-readable latest observed operational checkpoint;
- `docs/SESSION_START.md` — low-churn session-resume procedure;
- `docs/CIVICVS_PROJECT_ENVIRONMENT.md` — physical CPE hosts, CPE network identities, `fw` build/programming environment, fixed USB topology, Dell/LXD Firmware Authority placement, and cross-host execution boundaries;
- current milestone design/handoff — milestone-specific implementation and acceptance detail.

`CURRENT_STATE.json` is a recorded observation, not a substitute for live authority. It deliberately distinguishes the last observed operational state from the current GitHub `main` commit.

## Authority map

Kane Fabric separates these authorities:

| Authority | Owns |
| --- | --- |
| GitHub `git64bit/Kane-Fabric`, branch `main` | software, contracts, migrations, tests, documentation, small deterministic manifests |
| Proxmox host `srv-b` | CT lifecycle, host conformance, host firewall/network policy, host-to-CT execution |
| CT102 `kane-fabric` | real Kane Fabric runtime/test/compiler environment for repository/data gates |
| `/var/lib/kane-fabric` inside CT102 | operational databases, immutable evidence, staging, rollback, audit, compiled artifacts |
| `fw` / `10.110.0.4` | CPE build and hardware workstation: pinned ESP-IDF build, direct USB programming/terminal, physical ESP acceptance, TrivialHTTP Linux/Windows builds |
| Dell Precision / `10.110.0.9` | Ubuntu/LXD physical host for the future Firmware Authority container; existing unrelated workloads remain separate |

These roles must not be collapsed. An Assistant sandbox is none of them.

The physical CPE hosts are replaceable infrastructure. Their addresses and hardware do not become Fabric logical/geographic identity.

## Session-start fast path

A new Assistant must not begin by searching host filesystems or replaying already accepted gates.

Start with:

1. read live GitHub `main`;
2. read `docs/HANDOFF.md`;
3. read `docs/CURRENT_STATE.json`;
4. read `docs/SESSION_START.md`;
5. before physical ESP/CPE/TrivialHTTP/Firmware Authority work, read `docs/CIVICVS_PROJECT_ENVIRONMENT.md`;
6. read only the current milestone documents needed for the next action;
7. use recorded paths/control planes directly unless a live check contradicts them;
8. investigate only the contradicted fact.

Stable facts are not discovery tasks.

## Execution domains

### `srv-b` / CT102

Kane Fabric runtime/data commands execute inside CT102 through Proxmox host `srv-b`:

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

Do not substitute CT100, CT101, `fw`, the Dell, or an Assistant sandbox for CT102 repository/data acceptance.

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

### Dell Precision / Firmware Authority host

The Dell at `10.110.0.9` runs Ubuntu/LXD, not Proxmox. `pct` does not apply.

Before any Firmware Authority mutation, obtain the bounded read-only LXD/host inventory required by `docs/CIVICVS_PROJECT_ENVIRONMENT.md`. Do not invent the host hostname, LXD storage pool, project, profile, bridge, instance naming, host staging path, management path, transfer path, or container network identity.

The physical Dell host already has CPE address `10.110.0.9`; this does not assign an address to the future `firmware-authority` container.

## Cross-host anti-drift rule

A valid path or command on one host is not evidence that it exists on another.

In particular:

- `/tmp/kane-fabric-ms2` is the recorded CT102 checkout, not an `fw` or Dell path;
- `/home/cpe-build` is the `fw` CPE home, not a `srv-b` or Dell path;
- `pct` belongs to `srv-b`/Proxmox, not `fw` or the Dell;
- LXD control-plane operations belong to the Dell, not `srv-b`;
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

## Documentation/checkpoint cadence

Update `CURRENT_STATE.json`, `HANDOFF.md`, `SESSION_START.md`, and the applicable environment/milestone SSOT at a material checkpoint, including when:

- an acceptance gate changes the next safe action;
- a deployment/authority/checkout path changes;
- a physical CPE host or hardware mapping is accepted or replaced;
- a new non-obvious invariant or exception is discovered;
- operational DB path/hash changes;
- an implementation boundary changes.

A documentation-only commit after an accepted test does not by itself invalidate that test. Record the implementation/test HEAD actually exercised and rerun only when relevant code/environment changed.

## Test invalidation discipline

Use the least expensive useful gate and make claims only at the level actually run:

1. static/repository review;
2. synthetic/local unit tests;
3. repository regression tests inside CT102;
4. exact pinned firmware build on `fw` when firmware build inputs change;
5. physical device flash/runtime evidence on `fw` when device behavior is under test;
6. real Kane County read-only/derived-data gate inside CT102;
7. deliberately scoped authority-changing/release evidence.

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

The Dell's management/file-transfer path has not yet been frozen. Do not copy the `srv-b` workflow to the Dell by assumption; establish it during the Dell read-only inventory.

## Project boundaries

CT102 is Kane Fabric. CT100 and CT101 are Mechanical Compiler infrastructure and must not be repurposed for Kane Fabric merely because they share `srv-b`.

The Dell's existing RAG/LLM workloads are likewise separate from Kane Fabric. Co-location does not imply application trust, resource ownership, or permission to alter GPU/device passthrough.

## Handoff rule

At material checkpoints, durable state must capture:

- current milestone and implementation boundary;
- live/last-observed checkout path, branch, HEAD, upstream, refspec, and worktree state where applicable;
- current operational DB path/hash when established;
- accepted CT102 gates and implementation HEAD actually tested;
- accepted `fw` build/device/USB facts when they change;
- Dell/LXD host/container facts once observed;
- deliberate exclusions and trust boundaries;
- exact next safe action.

A successor should not need private chat history and should not need to rediscover stable project topology.

## Correction history

The MS-2 branch/refspec incident and later handoff/access failures established two permanent lessons:

1. keep the normal repository workflow on clean `main` unless explicitly changed;
2. preserve compact current-state checkpoints and verify them directly instead of reconstructing the whole environment every session.

The 2026-09-16 CPE reconciliation added a third permanent lesson: **physical development infrastructure must be recorded in GitHub SSOT as soon as it becomes a stable project dependency.** The `fw` build/programming environment and fixed USB topology had been accepted operationally without being preserved in Kane-Fabric, which allowed a later command to incorrectly assume an `fw` filesystem path existed on `srv-b`. The CPE SSOT and cross-host anti-drift rule exist to prevent recurrence.
