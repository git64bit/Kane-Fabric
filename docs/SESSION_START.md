# Kane Fabric Session Start

This document defines the fast path for resuming Kane Fabric development. It exists to prevent each new Assistant from spending most of a session rediscovering stable deployment facts that have already been observed and recorded.

## Read order

At the beginning of a development session:

1. read live GitHub `main`;
2. read `docs/HANDOFF.md` for the durable system mental model and historical evidence;
3. read `docs/CURRENT_STATE.json` for the compact latest observed operational checkpoint;
4. read `docs/DEVELOPMENT_PROCESS.md` for execution rules;
5. read only the current milestone documents needed for the next action.

Do not reread every historical release/handoff unless a current document points to it for exact evidence.

## Stable facts are not discovery tasks

The following are stable facts until a deliberate change or a failed verification proves otherwise:

- repository: `git64bit/Kane-Fabric`;
- development branch: `main`;
- Proxmox host: `srv-b`;
- Kane Fabric container: CT102, hostname `kane-fabric`;
- operational state root: `/var/lib/kane-fabric`;
- current checkout path: the path recorded in `docs/CURRENT_STATE.json`;
- normal host-to-container execution: `pct exec 102 -- ...`;
- database test entry point: `bash database/run-tests.sh`;
- substrate test entry point: `bash substrate/run-tests.sh`.

A successor must **use the recorded checkout path first**. Do not search `/tmp`, `/opt`, `/srv`, `/root`, or `/var/lib` for another checkout unless the recorded path is missing, is not the expected repository, or the one-command check reports a contradiction.

Likewise, accepted test results in `docs/CURRENT_STATE.json` are not rerun merely because a new Assistant arrived. Rerun a gate when implementation affecting that gate changed, the environment changed materially, a dependency changed, or a contradictory observation appears.

## One-command CT check

From `srv-b`, after confirming CT102 is running, run the repository state checker at the recorded checkout path:

```bash
pct status 102
pct exec 102 -- bash -lc '
  cd /tmp/kane-fabric-ms2
  bash development/kane-fabric-dev-state.sh
'
```

The literal path above reflects the current recorded operational checkout. If `docs/CURRENT_STATE.json` later changes the path, use that recorded path instead; this document should be updated at the same material checkpoint.

The checker is read-only. It reports:

- recorded milestone/checkpoint;
- live repository identity, branch, HEAD, upstream, refspec and worktree state;
- relation between live HEAD and the last observed CT HEAD;
- configured current database if one has been established;
- otherwise the small set of GeoPackage candidates under the operational database directory;
- the exact next safe action recorded in `CURRENT_STATE.json`.

Use `--deep` only when database SHA-256 and full Fabric database validation are actually needed:

```bash
bash development/kane-fabric-dev-state.sh --deep
```

Do not pay the deep-validation/hash cost on every ordinary session start.

## Repository freshness

GitHub `main` remains software authority. `CURRENT_STATE.json` deliberately records the **last observed CT state**, not a promise that CT102 equals the latest GitHub commit forever.

A documentation-only advance of `main` does not invalidate already accepted implementation tests. Before a state-changing operation, compare/fetch/synchronize deliberately. Before ordinary read-only analysis, it is enough to know and report the relation between the live CT checkout and current GitHub `main`.

Do not fast-forward blindly when the worktree is dirty, the branch/upstream is unexpected, or local commits are ahead.

## Documentation cadence

Do not update handoff/state files after every command group. That creates a commit, makes CT102 appear stale again, and causes recursive synchronization churn.

Batch documentation at **material checkpoints**, for example:

- an acceptance gate passes or fails in a way that changes the next safe action;
- the current operational database/path/hash is established or changes;
- a milestone implementation boundary changes;
- an authority, deployment path, branch policy, or invariant changes;
- a new non-obvious exception is discovered.

Ordinary intermediate observations should be carried through the current bounded gate and recorded together at its end.

## Contradictions

If the one-command check contradicts a stable recorded fact:

1. stop before destructive/state-changing work;
2. inspect only the contradicted area;
3. determine whether the live state or documentation is wrong;
4. update `docs/CURRENT_STATE.json` and the durable handoff at the same material checkpoint;
5. continue from the corrected state.

Do not respond to one contradiction by rediscovering the entire project.
