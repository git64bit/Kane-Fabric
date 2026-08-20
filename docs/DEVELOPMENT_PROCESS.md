# Kane Fabric Development Process

## Purpose

This document defines how Kane Fabric software work is performed, where commands run, which system is authoritative for each kind of state, and how real-environment validation is distinguished from repository-only work.

It exists because repository history proved that correct code is not enough if an Assistant or developer uses the wrong execution environment, treats a historical checkout path as current, creates an unnecessary branch, or asks the user to act as a routine terminal relay.

This is the current development-process authority. Historical milestone handoffs describe the process used at that time and do not override this document.

## Authority map

Kane Fabric deliberately separates four authorities:

| Authority | Role |
| --- | --- |
| GitHub repository `git64bit/Kane-Fabric`, branch `main` | software, contracts, migrations, tests, documentation, small deterministic manifests |
| Proxmox host `srv-b` | LXC lifecycle, host conformance, host firewall/network policy, host-to-container execution |
| CT102 `kane-fabric` | authoritative Kane Fabric execution environment for runtime tests, county database operations, compilation, and real-environment acceptance |
| `/var/lib/kane-fabric` inside CT102 | operational county state, immutable evidence, active databases, staging, rollback, audit, and compiled artifacts |

These roles must not be collapsed.

The Assistant's own local/sandbox filesystem is not CT102 and must never be described as though commands run there prove CT102 behavior.

## Normal command path

Kane Fabric runtime commands are executed inside CT102 through the Proxmox host.

The normal host-to-container form is:

```bash
pct exec 102 -- COMMAND ARGUMENTS...
```

For a compound shell command:

```bash
pct exec 102 -- bash -lc '...'
```

Before attempting an exec, verify the container state on `srv-b`:

```bash
pct status 102
```

A stopped or unavailable CT is an infrastructure condition. It must not be misreported as an application or test failure.

Do not substitute an Assistant sandbox, a different container, CT100, or CT101 for CT102 merely because those environments are reachable.

## Assistant responsibility

Routine project execution is an Assistant/development responsibility, not a user command-relay workflow.

When an authorized execution channel to `srv-b` is available, the Assistant should use it and then use `pct exec 102 -- ...` for CT102 commands. The user should not be asked to copy ordinary test, Git, inspection, build, or validation commands into CT102 merely because doing so is convenient for the Assistant.

If an Assistant session does not expose an authorized execution channel to `srv-b`, that is a capability gap for that session. The Assistant must state the limitation accurately and must not:

- claim that CT102 commands were executed;
- claim that a real-environment acceptance gate passed;
- run the same command in a local sandbox and present it as equivalent;
- silently redefine the development process so that the user becomes the normal terminal operator.

The Assistant may continue repository analysis, documentation, design work, and other tasks that do not require CT102. Execution-dependent work remains unverified until the actual CT environment is available.

The user may explicitly choose to perform a command manually, but that is an exception initiated or accepted by the user, not the default development process.

## Repository workflow

The GitHub repository is the software Single Source of Truth.

Before substantive work:

1. read current `main` rather than relying only on a prior handoff;
2. inspect the current milestone and governing documents;
3. verify that the repository has not advanced since the proposed change was prepared.

For this repository, work directly on `main` unless the user explicitly requests a feature branch, pull request, or other branch workflow.

Do not silently change a checkout to a single-branch fetch configuration.

Before changing local branch or refspec state, inspect:

```bash
git status --short --branch
git branch -vv
git config --get-all remote.origin.fetch
```

Never discard apparent local changes until they have been compared with the intended authoritative ref.

CT102 intentionally does not need GitHub write credentials for Assistant-driven repository publication. Repository writes should use the authorized GitHub integration when available. Do not ask the user to add GitHub credentials to CT102 merely to accommodate an Assistant-created Git workflow.

## CT102 checkout discovery

A historical checkout path is evidence, not a permanent path contract.

The Milestone 2 cleanup used `/tmp/kane-fabric-ms2`. Future work must not assume that path still exists or is the current checkout simply because a historical handoff names it.

At the start of a real CT102 execution session, determine the current Kane Fabric checkout and verify:

- it is the `git64bit/Kane-Fabric` repository;
- it is on `main` unless the user explicitly requested otherwise;
- it tracks the intended `origin/main`;
- its worktree state is understood before update/reset operations;
- its fetch refspec is not unexpectedly restricted.

Once a stable canonical checkout path is deliberately established for current operations, record it in the current milestone/release documentation. Do not infer one from an old milestone.

## Host commands versus CT commands

Commands belong to the authority that owns the state being inspected or changed.

Run on `srv-b`:

- `pct status`, `pct config`, and other Proxmox/LXC lifecycle inspection;
- host firewall/network inspection;
- the host-owned executable `ct-baseline.sh` conformance gate;
- host storage and host systemd checks;
- `pct exec 102 -- ...` itself.

Run inside CT102 through `pct exec`:

- Kane Fabric Python tools and shell entry points;
- `database/run-tests.sh` and `substrate/run-tests.sh`;
- Git inspection/update of the CT102 runtime checkout;
- source-profile/status checks;
- candidate harvest/validation/registration;
- database validation and comparison;
- reconciliation preparation/validation;
- substrate compilation and browser-package generation;
- inspection of `/var/lib/kane-fabric` operational state.

Do not duplicate the host's `ct-baseline.sh` inside the repository or CT as an alternative authority. The repository records the dependency on that host gate; `srv-b` owns its executable definition.

## Development loop

The normal implementation loop is:

```text
read current GitHub main
        ↓
make the smallest coherent software/contract change
        ↓
update main through the authorized repository channel
        ↓
verify CT102 is running on srv-b
        ↓
exec into CT102
        ↓
synchronize/verify the CT102 checkout against main
        ↓
run unit/regression tests in CT102
        ↓
run the real-data gate required by the milestone
        ↓
verify authoritative/evidence state was changed only when the operation intended it
        ↓
record accepted evidence in the repository when a milestone gate requires it
```

A local or synthetic test can catch defects earlier, but it does not replace the CT102 gate when the claim concerns the real Kane Fabric environment or real Kane County state.

## Shell safety

When compound commands are passed to a root shell, use an isolated shell/subshell rather than changing the state of an interactive shell unexpectedly.

Typical host-to-CT form:

```bash
pct exec 102 -- bash -lc '
  set -euo pipefail
  ...
'
```

Project scripts may contain their own `set -euo pipefail` because they execute in their own noninteractive process.

Quote paths and data deliberately. Do not embed untrusted source values into shell command text.

## Operational data boundary

`/var/lib/kane-fabric` is operational state, not source-control authority.

The expected categories remain:

```text
seed/                    immutable initial seed evidence
reconstruction-inputs/   imported historical reconstruction evidence
reconstruction-code/     historical reference software
 database/               active/working Kane Fabric databases
staging/                  candidate/reconciliation/promotion work
rollback/                 rollback evidence
audit/                    audit/reconstruction reports
render/                   compiled substrate/subscription artifacts
```

The leading space before `database/` above is not semantically significant; paths are rooted directly under `/var/lib/kane-fabric`.

Large GeoPackages, harvested GeoJSON, candidate directories, reconciliation databases, rollback copies, and compiled packages remain outside Git.

Immutable evidence must not be modified as a shortcut for testing.

## Read-only work, staged writes, and authority-changing writes

Not all CT102 commands have the same operational effect.

### Read-only / derived work

Examples:

- source status;
- database validation and inspection;
- deterministic accepted-versus-candidate comparison;
- substrate compilation from an authoritative database opened read-only;
- tests against temporary databases.

These should not mutate accepted county state. Where practical, hash or otherwise verify the source database before and after a derived build.

### Staged/provenance writes

Candidate registration records candidate provenance in the working database. It does not make the candidate accepted geography. Reconciliation and promotion preparation create external candidate artifacts rather than silently replacing the active database.

These writes must use the designated database/staging paths for the current operation and must pass their post-write validators.

### Accepted-state changes

Promotion is a distinct authority-changing operation. It must never be hidden inside an unrelated test or build command.

Kane Fabric promotion code requires an explicit `promote` command, retains a rollback backup, verifies the prepared candidate, replaces the database atomically, and automatically restores the previous state if post-promotion verification fails.

Rollback is likewise an explicit named operation.

A development test may prove promotion/rollback behavior on a disposable or deliberately prepared test database. It must not promote the operational accepted database merely because a test suite needs coverage.

## Test and acceptance hierarchy

Use the least expensive useful test first, but make acceptance claims only at the level actually tested.

1. static/repository review;
2. synthetic unit tests;
3. full repository regression tests inside CT102;
4. real Kane County read-only/derived-data gate inside CT102;
5. deliberately scoped candidate/reconciliation/promotion gate when the milestone requires it;
6. release evidence and exact hashes/counts recorded in documentation.

A result at level 1 or 2 must not be described as level 3 or 4 acceptance.

## Source refresh discipline

The project objective is to keep county geography current without confusing freshness with authority.

The operational sequence remains:

```text
source-status check
    ↓
new/changed source detected
    ↓
complete candidate harvest
    ↓
candidate validation
    ↓
registration as candidate
    ↓
deterministic comparison
    ↓
identity reconciliation where required
    ↓
promotion preparation and validation
    ↓
explicit atomic promotion
```

A newer upstream response does not bypass these gates.

## File transfer

For large cross-machine artifacts in the current environment, the established workflow is:

```text
create tarball
→ Webmin download/upload
→ verify SHA-256 locally
→ extract/use only after verification
```

Do not prescribe SCP/SSH-based transfer as the default unless the user explicitly requests it or the deployment policy is deliberately changed.

This transfer rule does not prohibit the host-to-LXC `pct exec` development path; they solve different problems.

## Project boundaries on srv-b

CT102 is Kane Fabric.

CT100 and CT101 belong to Mechanical Compiler infrastructure and must not be repurposed for Kane Fabric development merely because they are on the same Proxmox host.

Co-location does not transfer application ownership or authority.

## Handoff rule

Every future milestone handoff must state or reference:

- `docs/DEVELOPMENT_PROCESS.md` as the execution-process authority;
- the current GitHub `main` identity;
- the current CT102 checkout path if a stable path has been deliberately established;
- the current active/working database path and whether its recorded hash is historical evidence or current observed state;
- which real-environment gates have actually been executed;
- any execution capability that was unavailable rather than silently replaced by user command relay.

Historical handoffs may preserve obsolete procedures for forensic value, but they must not be treated as current execution instructions when they conflict with this document.

## Current correction

The Milestone 2 handoff contains the historical sentence:

> The user performs infrastructure commands on `srv-b` and returns output.

That sentence describes the interaction pattern used during that historical work. It is superseded for current development by this document.

The current rule is: **the Assistant/development process executes routine commands through the authorized `srv-b` → `pct exec 102` path; the user is not the default terminal relay.**
