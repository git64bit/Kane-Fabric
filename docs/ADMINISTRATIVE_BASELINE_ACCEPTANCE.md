# Administrative Civic Infrastructure — Initial Baseline Acceptance

Date: 2026-09-17

## Status

**INITIAL BASELINE COMPLETE**

This document closes the first Administrative/Civic Infrastructure leg of Kane Fabric.

The purpose of this leg was to establish the base: a generic browser-driven administrative model, an initial statewide Illinois condominium Infrastructure profile, and a source-neutral identity boundary that later participant publications can attach to.

This is an initialization checkpoint, not a claim that all future Civic Infrastructure work is complete.

## Accepted baseline

### Generic Administrative Web

The browser engine is descriptor-driven and jurisdiction-neutral. Illinois condominium semantics live in descriptor data rather than hard-coded renderer logic.

Accepted descriptor architecture source:

```text
3eee5523ce5689eff6e06542ff68b08fd8c2198f
```

Accepted generic descriptor contract hardening:

```text
f2c995f7610a273031926cf681facd20dce1ad22
```

That checkpoint passed:

```text
web/run-tests.sh                    60/60 PASS
web/run-admin-browser-acceptance.sh 62/62 PASS
```

### Illinois condominium Infrastructure profile

Thirteen current-effective statewide domains are represented as descriptor-driven Infrastructure:

```text
insurance
records
finance
governance
management
resale
property
collections
enforcement
maintenance
turnover
termination
complaints / Ombudsperson
```

Accepted thirteen-descriptor browser checkpoint:

```text
dd60b817bd12cf76683e9e61686d66bccec58047
```

Observed CT102 evidence:

```text
web/run-tests.sh                    62/62 PASS
web/run-admin-browser-acceptance.sh 67/67 PASS
worktree                            clean
```

All thirteen canonical descriptor SHA-256 identities were independently verified by the real Chromium gate.

### Association and unit identity boundary

The baseline distinguishes civic subject identity from Board authority, ownership, residency, management accounts, portals, source URLs, publication generations, and physical edge/device identity.

Accepted architecture checkpoint:

```text
199e090583c265285bf8a2a69fb8da6f0a1845a2
```

Accepted source-neutral association/unit identity contract:

```text
a1629361063f4dd2806bcddade05f7cb9b1548ed
```

Accepted recording-reference hardening checkpoint:

```text
4b24dc0e7eb50511bfbd9b9f530f67c1ef46357d
```

Observed CT102 evidence at the latest executable identity checkpoint:

```text
web/run-tests.sh 71/71 PASS
worktree         clean
```

The identity contract intentionally permits opaque public recording references, including pre-computerized book/page-style references. It does not derive permanent association or unit identifiers yet.

## What this baseline establishes

The initial baseline establishes that Kane Fabric can:

- describe statewide Civic Infrastructure without hard-coding Illinois concepts into the browser engine;
- distinguish statewide rules from association-instance values;
- render multiple administrative domains together in a normal browser;
- retain deterministic descriptor identities and independent browser verification;
- recognize that a condominium association and its units are civic subjects independently of Board, manager, portal, account, or edge-device control;
- represent identity anchors using source-neutral public-record references;
- preserve gaps rather than invent values merely to satisfy a schema.

## What is deliberately not part of the initial baseline

This checkpoint does **not** freeze or claim:

- a complete Illinois condominium ontology;
- every possible statutory or regulatory domain;
- derived association/unit logical IDs;
- participant-publication generation contracts;
- public/restricted/private visibility contracts;
- authentication or Board authority;
- server-side mutation or persistence;
- evidence-ranking or automated truth adjudication;
- offline reduction;
- ESP32 application specialization beyond the previously accepted bounded artifact runtime.

Those belong to later work when a concrete participant-publication requirement demands them.

## Evidence discipline carried forward

The baseline does not require public records to be complete or internally consistent.

The governing operational rule is:

```text
Use what can be established.
Preserve where it came from.
Leave gaps unresolved when evidence is insufficient.
Do not manufacture certainty to complete the model.
```

This principle is carried forward as development discipline. It is not promoted here into a separate evidence subsystem or schema.

## Baseline boundary

The first Administrative/Civic Infrastructure leg ends here.

Further statutory descriptor expansion is no longer part of initialization. New domains may be added later when a concrete participant or interoperability requirement demonstrates that they are missing.

The next leg begins with a bounded participant publication using the accepted base:

```text
accepted county geography
        +
accepted administrative descriptors
        +
accepted association/unit identity anchors
        +
bounded participant publication
        =
composed Civic Infrastructure view
```

The next leg must consume this baseline rather than reopen it.

## Baseline source checkpoints

```text
13-descriptor browser acceptance   dd60b817bd12cf76683e9e61686d66bccec58047
identity contract acceptance       a1629361063f4dd2806bcddade05f7cb9b1548ed
identity evidence hardening        4b24dc0e7eb50511bfbd9b9f530f67c1ef46357d
last synchronized documented state 37fe4d1f770bde2e5e17d3a6bae08fa6f63eedbe
```

The temporary `ADMINISTRATIVE_EVIDENCE_STATE.md` candidate introduced after `37fe4d1` was removed before this baseline closure because it expanded the architecture beyond what initialization requires.
