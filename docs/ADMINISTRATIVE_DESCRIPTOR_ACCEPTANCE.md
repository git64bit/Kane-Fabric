# Administrative Descriptor Browser Acceptance

Date: 2026-09-17

## Purpose

This document records the acceptance history of the descriptor-driven Kane Fabric Administrative Web. It preserves the first real-browser acceptance and the later incremental Illinois condominium Infrastructure slices without rewriting earlier checkpoints as though they occurred at the latest repository HEAD.

## First descriptor-driven acceptance

The first accepted implementation source is:

```text
7b8b116d5b43660d4260a21f0dc7ea85ec6bc753
```

That source established:

- the generic administrative descriptor engine in `web/admin-descriptor.js`;
- the descriptor bootstrap in `web/admin-app.json` and `web/admin-app.js`;
- descriptor schema `administration/descriptors/descriptor-v1.schema.json`;
- Illinois condominium insurance reference descriptor `administration/descriptors/illinois/condominium/insurance.v1.json`;
- descriptor-driven layout, help, authority references, controls, collections, and canonical JSON SHA-256 presentation;
- jurisdiction-neutral browser behavior, with Illinois and condominium semantics supplied by descriptor data rather than hard-coded renderer logic.

Observed on `srv-b` / CT102 (`kane-fabric`) at `/tmp/kane-fabric-ms2`:

```text
web/run-tests.sh                    35/35 PASS
real Chromium descriptor checks     10/10 PASS
worktree                            clean
```

The first accepted insurance descriptor canonical SHA-256 is:

```text
2128aac622601577c88a7ee08f348cbcffdda249b59851da20a8f299e847da4c
```

## Incremental accepted descriptor history

| Slice | Accepted HEAD | Repository tests | Chromium checks | Canonical SHA-256 |
|---|---|---:|---:|---|
| Insurance | `7b8b116d5b43660d4260a21f0dc7ea85ec6bc753` | 35/35 | 10/10 | `2128aac622601577c88a7ee08f348cbcffdda249b59851da20a8f299e847da4c` |
| Association records | `a1f0ed82eb16ec3aacf0e26a1c2656e78fdfe2f8` | 37/37 | 13/13 | `ca54d0820092635e4efe13e2d2912ae8ef34adea731f95d3276fc6fc24bf65ef` |
| Finance | `17ebb856057ad3137792b95ea15f69b9014cd63f` | 39/39 | 17/17 | `b1cab5d9d1978e9ceca388f716a6c6e92c97f97bd08fff8f13fa6cb965f07893` |
| Governance | `92969e1ba363443430e2065dfa6937b78ebde51f` | 41/41 | 22/22 | `2c124b5253c78efec708b305e946a7788a075970e7f4595e12bb58e7392a6923` |
| Management, licensing & service contracts | `9e762383cdc45eeb03aa80642f68b32b10237b0c` | 43/43 | 27/27 | `b9760a1278690b0625a9fa02b2848bb7626f4217580b304a4ac2c63b60c653c1` |
| Resale disclosures | `8ce34df74c177b0278705ed22ed0a012ede54a54` | 45/45 | 32/32 | `313cfab81d563cc31577f60b23429e138aa53fb2f5e2dd1466337c478b99936d` |
| Property identity, plat & tax | `9ae3cef6ff44bd310e8f0edeb4e5d1f71453e198` | 47/47 | 37/37 | `52ca1db95ea93fec294da92e476e776b8d72be2951479fa5c6a9819881cf7e0c` |
| Assessment collection, liens & remedies | `dbabf44ad294c8472517bd1c6cef53e84707bb95` | 49/49 | 42/42 | `3bc9ec8a2227fffdb551df606e2584f42e5c8dc238143a24996bd8868cb2e1f7` |
| Rules, violations & fines | `6f93403ca04c1e1ac22e96e19c02413d46bbc217` | 51/51 | 47/47 | `31db69d53302a7baa203a63c37224a8a56a66a915db946389e81f34d4efcbfce` |
| Maintenance, repairs & unit access | `0ea41fd43447bdcf44a552474013abf26707842a` | 53/53 | 52/52 | `a89c2e8e165a696f709dcba93ee67f091b07817550d04468b1802a81e31e939c` |
| Developer control & turnover | `5edcec8448b46b1f4ee0950e0cac42ff92c72b9f` | 55/55 | 57/57 | `945facfa9b66cbdf5b2e80e1966108f8cd62ddb32381d712a0cf72c6a3fcb846` |
| Sale of property & removal from Act | `5bf7d312bebe6b4c2e0a13f7893a0c045b1bf1c4` | 57/57 | 62/62 | `87d94c88ec36fb372731720ba2c2b58cb6180bdc990eeb9b3b67e2488858b733` |
| Complaint procedure & Ombudsperson | `dd60b817bd12cf76683e9e61686d66bccec58047` | 62/62 | 67/67 | `d4e0209770982841a98ecaf495a2547642e882680df6bc86d5e317c12ab00521` |

Finance implementation was first introduced at `3774742e5433518e054422c4f80b11f3f8f529d1`. Its initial real-browser gate reached 16/17 because HTML serialization rendered an ampersand as `&amp;`; `17ebb856057ad3137792b95ea15f69b9014cd63f` changed only the independent browser validator to decode textual checks while preserving raw serialized-DOM SHA checks. No finance descriptor or browser implementation changed in that hotfix.

## Descriptor-contract hardening acceptance

After the first twelve descriptor slices above were accepted, the generic descriptor contract was tightened at:

```text
f2c995f7610a273031926cf681facd20dce1ad22
```

Observed CT102 evidence:

```text
web/run-tests.sh                    60/60 PASS
web/run-admin-browser-acceptance.sh 62/62 PASS
worktree                            clean
```

This checkpoint formalized already-used presentation metadata without changing accepted descriptor bytes:

- `unit` and `format` are explicit optional non-empty strings in `descriptor-v1.schema.json`;
- `validateAdministrativeDescriptor()` rejects malformed `unit` or `format` metadata, including nested collection controls;
- `format_version` remains 1 because the change is backward-compatible;
- all twelve canonical descriptor SHA-256 values remained unchanged.

The complaint slice subsequently reused that hardened v1 contract without requiring any renderer or schema change. The latest accepted repository/browser acceptance HEAD is therefore:

```text
dd60b817bd12cf76683e9e61686d66bccec58047
```

Latest observed CT102 evidence:

```text
web/run-tests.sh                    62/62 PASS
web/run-admin-browser-acceptance.sh 67/67 PASS
worktree                            clean
```

## Real-browser acceptance path

The repository-owned real-browser gate is:

```text
web/run-admin-browser-acceptance.sh
web/validate-admin-browser-dump.py
```

The browser path proves:

```text
HTTP fetch
  -> administrative bootstrap JSON
  -> enabled administrative descriptors
  -> runtime descriptor validation
  -> canonical descriptor SHA-256
  -> generic descriptor renderer
  -> generated DOM controls and layout
  -> independent DOM acceptance checks
```

The validator independently computes each enabled descriptor's canonical SHA-256 and requires the real Chromium DOM to contain that exact identity.

## Acceptance scope

Accepted:

- JSON supplies the Administrative Web semantics and presentation represented by the current descriptor vocabulary;
- the browser engine remains generic while descriptors supply Illinois-specific meaning;
- control type, labels, help, authority references, layout, options, conditional presentation, repeating collections, units, and presentation formats are descriptor-driven;
- semantic bindings remain distinct from presentation placement;
- descriptors are versioned and represented by canonical SHA-256 identity;
- thirteen current-effective Illinois condominium Infrastructure domains render together in real Chromium;
- statewide Infrastructure notices and association-instance data are represented separately within the descriptor model;
- future-effective statutory changes are not silently promoted into current Infrastructure.

Not accepted or claimed by this checkpoint:

- final visual design or usability;
- complete Illinois condominium ontology;
- persistent storage or server-side mutation;
- authentication, authorization, encrypted private delivery, or abuse resistance;
- offline/local reduction;
- participant-publication or edge-device contract;
- ESP32-S3 application shape;
- any requirement not established as Illinois-wide Civic Infrastructure or explicitly represented as association-instance data.

## Development consequence

The Administrative Web remains the active design instrument for determining the Civic Infrastructure boundary. Further statewide domains should be added only when they represent a materially distinct Illinois-wide function. Existing accepted descriptor identities should remain stable unless an intentional descriptor-version change is made.
