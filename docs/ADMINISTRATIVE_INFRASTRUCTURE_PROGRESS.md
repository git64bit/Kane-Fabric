# Administrative Infrastructure — Accepted Descriptor Progress

Date: 2026-09-17

This file records progressively accepted descriptor-driven Illinois condominium Civic Infrastructure slices. It complements the first-render acceptance in `docs/ADMINISTRATIVE_DESCRIPTOR_ACCEPTANCE.md`.

## Accepted CT102 baseline

Accepted repository HEAD:

```text
92969e1ba363443430e2065dfa6937b78ebde51f
```

Observed on `srv-b` / CT102 (`kane-fabric`) at `/tmp/kane-fabric-ms2`:

```text
web/run-tests.sh                    41/41 PASS
web/run-admin-browser-acceptance.sh 22/22 PASS
worktree                            clean
```

The real Chromium gate verified the exact canonical SHA-256 identity of every enabled descriptor.

## Accepted descriptors

| Descriptor | Scope | Canonical SHA-256 |
|---|---|---|
| `us.il.condominium.insurance` | Association insurance and policy-instance data | `2128aac622601577c88a7ee08f348cbcffdda249b59851da20a8f299e847da4c` |
| `us.il.condominium.records` | Section 19 record inventory and member examination framework | `ca54d0820092635e4efe13e2d2912ae8ef34adea731f95d3276fc6fc24bf65ef` |
| `us.il.condominium.finance` | Budget, assessments, reserves, and fiscal administration | `b1cab5d9d1978e9ceca388f716a6c6e92c97f97bd08fff8f13fa6cb965f07893` |
| `us.il.condominium.governance` | Board, meetings, notices, elections, and voting | `2c124b5253c78efec708b305e946a7788a075970e7f4595e12bb58e7392a6923` |

## Boundary

Acceptance means that the descriptor validates, its expected statewide and association-instance distinctions are represented, and the real browser renders the enabled descriptor with its exact canonical identity.

It does not claim that Illinois condominium Civic Infrastructure is complete. New statewide domains should be added incrementally and should not alter already accepted descriptor identities unless an intentional descriptor-version change is made.

Future-effective statutory changes are not silently promoted into current Infrastructure. They must be modeled separately or incorporated when effective.
