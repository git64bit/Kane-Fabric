# Kane Fabric Development Process

## Purpose

This document defines how Kane Fabric development is executed, which system owns each kind of state, and how a successor resumes work without repeating already accepted discovery and verification.

The process has two goals that must coexist:

1. never confuse repository/sandbox work with real CT102 acceptance;
2. do not spend each new session reconstructing stable facts that the repository already records.

Historical milestone handoffs preserve historical procedure and evidence. They do not override this document.

## Current-state documents

Use these documents for different purposes:

- `docs/HANDOFF.md` — durable system mental model, historical evidence, non-obvious invariants, current milestone narrative;
- `docs/CURRENT_STATE.json` — compact machine-readable latest observed operational checkpoint;
- `docs/SESSION_START.md` — low-churn session-resume procedure;
- current milestone handoff — milestone-specific implementation/acceptance detail.

`CURRENT_STATE.json` is a recorded observation, not a substitute for live authority. It deliberately distinguishes the last observed CT state from the current GitHub `main` commit.

## Authority map

Kane Fabric separates four authorities:

| Authority | Owns |
| --- | --- |
| GitHub `git64bit/Kane-Fabric`, branch `main` | software, contracts, migrations, tests, documentation, small deterministic manifests |
| Proxmox host `srv-b` | LXC lifecycle, host conformance, host firewall/network policy, host-to-container execution |
| CT102 `kane-fabric` | real Kane Fabric runtime/test/compiler environment |
| `/var/lib/kane-fabric` inside CT102 | operational databases, immutable evidence, staging, rollback, audit, compiled artifacts |

These roles must not be collapsed. An Assistant sandbox is not CT102.

## Session-start fast path

A new Assistant must not begin by searching the host/container filesystem or replaying already accepted test gates.

Start with:

1. read live GitHub `main`;
2. read `docs/HANDOFF.md`;
3. read `docs/CURRENT_STATE.json`;
4. read `docs/SESSION_START.md` and the current milestone documents needed for the next action;
5. use the recorded CT102 checkout path directly;
6. run the one-command repository/state check;
7. investigate only a fact that the check contradicts.

Stable facts are not discovery tasks. Repository identity, `srv-b`, CT102, `/var/lib/kane-fabric`, normal test entry points, and the recorded operational checkout path remain usable until deliberately changed or contradicted by a failed verification.

The current read-only CT checker is:

```bash
bash development/kane-fabric-dev-state.sh
```

Use `--deep` only when full database validation and SHA-256 are required:

```bash
bash development/kane-fabric-dev-state.sh --deep
```

Do not incur deep database hashing/validation on every normal session start.

## Normal command path

Kane Fabric runtime commands execute inside CT102 through `srv-b`:

```bash
pct status 102
pct exec 102 -- COMMAND ARGUMENTS...
pct exec 102 -- bash -lc '...'
```

A stopped/unavailable CT is infrastructure state, not an application test failure.

Do not substitute CT100, CT101, or an Assistant sandbox for CT102 acceptance.

## Assistant responsibility and manual relay exception

Routine project execution is an Assistant/development responsibility.

When an authorized execution channel to `srv-b` exists, the Assistant uses it and then `pct exec 102` for CT commands. The user is not the default terminal relay merely because relaying commands is convenient.

If a session lacks an authorized `srv-b` execution channel:

- state that capability gap accurately;
- do not claim CT102 commands ran;
- do not present sandbox output as CT102 evidence;
- continue repository-only work where valid.

The user may explicitly choose or accept a bounded manual command relay. When that exception is in use, issue one bounded command group at a time for state-changing or diagnostic work and evaluate its returned output before the next such group.

Milestones 1 and 2 used this manual relay pattern for many accepted gates; that historical evidence remains valid.

## Repository workflow

GitHub `main` is the software Single Source of Truth.

Work directly on `main` unless the user explicitly requests a branch/PR workflow.

Before changing checkout state, inspect at minimum:

```bash
git status --short --branch
git branch -vv
git config --get-all remote.origin.fetch
git remote -v
```

Never discard unexplained local changes. Never silently restrict the fetch refspec to one branch.

CT102 does not need GitHub write credentials for Assistant publication. Use the authorized GitHub integration for repository writes; do not ask the user to add CT102 credentials merely to publish or clean up Assistant-created branches.

## CT102 checkout rule

The path in `docs/CURRENT_STATE.json` is the **current operational checkout path** until deliberately changed or contradicted.

A successor must try that path first. Do not search `/tmp`, `/root`, `/opt`, `/srv`, or `/var/lib` for another checkout unless:

- the recorded path does not exist;
- it is not `git64bit/Kane-Fabric`;
- branch/upstream/refspec/worktree checks contradict the recorded contract.

If a different canonical checkout is deliberately established, update `CURRENT_STATE.json`, `docs/HANDOFF.md`, and the current milestone handoff at the same material checkpoint.

## Host commands versus CT commands

Run on `srv-b`:

- `pct status`, `pct config`, LXC lifecycle inspection;
- host firewall/network checks;
- host storage/systemd checks;
- the host-owned `/usr/local/sbin/ct-baseline.sh` gate;
- `pct exec 102 -- ...`.

Run inside CT102 through `pct exec`:

- Kane Fabric Git inspection/synchronization;
- project tests and tools;
- source-profile/status work;
- candidate harvest/validation/registration;
- database validation/comparison;
- reconciliation/promotion preparation;
- substrate compilation/package generation;
- `/var/lib/kane-fabric` inspection.

Do not duplicate the host `ct-baseline.sh` inside the repository as a competing authority.

## Development loop

The normal loop is:

```text
read current main + current checkpoint
        ↓
run one-command CT state check
        ↓
make smallest coherent implementation/contract change
        ↓
update GitHub main
        ↓
verify/synchronize CT102 when required
        ↓
run only the tests invalidated by the change
        ↓
run the required real-data gate
        ↓
verify authoritative state changed only when intended
        ↓
record one material checkpoint
```

Do not insert documentation commits after every intermediate observation. Repeated handoff commits create recursive Git/CT synchronization churn and reduce useful development time.

## Documentation/checkpoint cadence

Update `docs/CURRENT_STATE.json`, `docs/HANDOFF.md`, and the milestone handoff at a **material checkpoint**, not after every command.

Material checkpoints include:

- an acceptance gate passes/fails and changes the next safe action;
- current operational DB path/hash is established or changes;
- implementation boundary changes;
- deployment/authority/checkout path changes;
- a new non-obvious invariant or exception is discovered.

Carry ordinary intermediate observations through the bounded gate and record them together.

A documentation-only commit after an accepted test does not by itself invalidate that test. Record the implementation/test HEAD that was actually exercised and rerun only if relevant code/environment changed.

## Test invalidation discipline

Use the least expensive useful test and make claims only at the level actually run:

1. static/repository review;
2. synthetic/local unit tests;
3. repository regression tests inside CT102;
4. real Kane County read-only/derived-data gate inside CT102;
5. deliberately scoped candidate/reconciliation/promotion gate;
6. release evidence with exact hashes/counts.

Accepted tests are **not rerun just because a new Assistant/session started**.

Rerun when an invalidating change exists, such as:

- implementation covered by that test changed;
- migration/source contract changed;
- relevant runtime/dependency/environment changed;
- a contradictory live observation appears.

Do not rerun an unchanged accepted gate merely to rediscover confidence.

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

`/var/lib/kane-fabric` is operational state, not source-control authority:

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

Large GeoPackages, harvested source data, staging/rollback directories, and generated packages remain outside Git.

Immutable evidence must never be modified as a testing shortcut.

## Read-only, staged, and authority-changing work

### Read-only / derived

Examples: source status, validation, accepted-vs-candidate comparison, substrate compilation from a read-only DB, tests using temporary DBs.

Where practical, verify the source database before and after derived compilation.

### Staged/provenance writes

Candidate registration records lineage; it does not promote geography. Reconciliation/promotion preparation creates candidate artifacts and must pass validators.

### Accepted-state changes

Promotion is explicit authority-changing work. It must never be hidden in a test, source-status operation, or substrate build.

Promotion requires explicit `promote`, rollback backup, validation, atomic replacement, and post-verification/restore behavior. Rollback is likewise explicit.

Operational accepted state must not be promoted merely to satisfy test coverage.

## Source refresh discipline

Freshness is not authority:

```text
source-status
  → changed source detected
  → complete candidate harvest
  → candidate validation
  → candidate registration
  → deterministic comparison
  → identity reconciliation where required
  → promotion prepare/validate
  → explicit atomic promotion
```

A newer upstream response never bypasses these gates.

## File transfer

For large cross-machine artifacts in the current environment, the established workflow remains:

```text
create tarball
→ Webmin download/upload
→ verify SHA-256
→ extract/use
```

Do not prescribe SCP/SSH transfer as the default unless deployment policy is deliberately changed. This rule is separate from host-to-LXC `pct exec` command execution.

## Project boundaries on srv-b

CT102 is Kane Fabric.

CT100 and CT101 are Mechanical Compiler infrastructure and must not be repurposed for Kane Fabric merely because they share the Proxmox host.

## Handoff rule

At material checkpoints, the durable handoff/current state must capture:

- current milestone and implementation boundary;
- last observed CT checkout path/branch/head/upstream/worktree state;
- current operational DB path/hash when established;
- accepted CT102 gates and the implementation HEAD actually tested;
- deliberate compatibility names/exclusions/source-policy exceptions;
- unavailable execution capability where relevant;
- exact next safe action.

`CURRENT_STATE.json` should contain compact values that a checker can consume. `HANDOFF.md` should explain the meaning and history that cannot be understood safely from raw fields alone.

A successor should not need private chat history and should not need to rediscover stable project topology.

## Correction history

Milestone 2 contains the historical sentence:

> The user performs infrastructure commands on `srv-b` and returns output.

That describes the workflow actually used then. It is not the current default rule.

The MS-2 branch/refspec incident and the later handoff/access failures established two permanent lessons:

1. keep the normal repository workflow on clean `main` unless explicitly changed;
2. preserve a compact current-state checkpoint and verify it directly instead of reconstructing the whole environment every session.
