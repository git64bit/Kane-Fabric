# Administrative Infrastructure — Accepted Descriptor Progress

Date: 2026-09-17

This file records progressively accepted descriptor-driven Illinois condominium Civic Infrastructure slices. It complements the first-render acceptance in `docs/ADMINISTRATIVE_DESCRIPTOR_ACCEPTANCE.md`.

## Accepted CT102 baseline

Accepted repository HEAD:

```text
5bf7d312bebe6b4c2e0a13f7893a0c045b1bf1c4
```

Observed on `srv-b` / CT102 (`kane-fabric`) at `/tmp/kane-fabric-ms2`:

```text
web/run-tests.sh                    57/57 PASS
web/run-admin-browser-acceptance.sh 62/62 PASS
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
| `us.il.condominium.management` | Community-association management licensing, management arrangement, fund safeguards, and service-contract inventory | `b9760a1278690b0625a9fa02b2848bb7626f4217580b304a4ac2c63b60c653c1` |
| `us.il.condominium.resale` | Current-effective resale disclosure package, request timing, fees, and lender notices | `313cfab81d563cc31577f60b23429e138aa53fb2f5e2dd1466337c478b99936d` |
| `us.il.condominium.property` | Recorded declaration/plat identity, unit/common-element interests, legal form, and separate real-estate tax treatment | `52ca1db95ea93fec294da92e476e776b8d72be2951479fa5c6a9819881cf7e0c` |
| `us.il.condominium.collections` | Assessment collection, statutory liens, remedies, successor liability, and collection-fee boundaries | `3bc9ec8a2227fffdb551df606e2584f42e5c8dc238143a24996bd8868cb2e1f7` |
| `us.il.condominium.enforcement` | Rule adoption, violation administration, hearing process, and reasonable-fine boundaries | `31db69d53302a7baa203a63c37224a8a56a66a915db946389e81f34d4efcbfce` |
| `us.il.condominium.maintenance` | Common-element maintenance, repairs/replacement/restoration, improvements, emergencies, and unit-access events | `a89c2e8e165a696f709dcba93ee67f091b07817550d04468b1802a81e31e939c` |
| `us.il.condominium.turnover` | Developer control, first owner-board election, Section 18.2 turnover delivery, and developer-era contract review | `945facfa9b66cbdf5b2e80e1966108f8cd62ddb32381d712a0cf72c6a3fcb846` |
| `us.il.condominium.termination` | Property-wide sale, objecting-owner protections, and unanimous removal from the Act | `87d94c88ec36fb372731720ba2c2b58cb6180bdc990eeb9b3b67e2488858b733` |

## Boundary

Acceptance means that the descriptor validates, its expected statewide and association-instance distinctions are represented, and the real browser renders the enabled descriptor with its exact canonical identity.

It does not claim that Illinois condominium Civic Infrastructure is complete. New statewide domains should be added incrementally and should not alter already accepted descriptor identities unless an intentional descriptor-version change is made.

Future-effective statutory changes are not silently promoted into current Infrastructure. They must be modeled separately or incorporated when effective.
