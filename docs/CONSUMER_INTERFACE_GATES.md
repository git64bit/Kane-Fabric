# Consumer Interface Gates

Status: **ACTIVE NON-NORMATIVE GATE REGISTER**

This document records interface pressure from real or planned Kane Fabric consumers without allowing any consumer to redefine Kane Fabric's normative milestone sequence.

Current normative MS5 authority remains:

```text
docs/MILESTONE_5_DESIGN.md
```

A gate recorded here may block a future integration or milestone exit. It does not become Kane Fabric work merely because a consumer depends on it.

## 1. Current consumer: Mechanical Compiler

Source reviewed 2026-09-12:

```text
Mechanical Compiler / IDENTITY-CONTRACT.md
status: specified, not implemented
```

Follow-up received 2026-09-12: the Mechanical Compiler removed the earlier Kane-specific trusted-header names and made that relying-party interface deployment-neutral. The exact current header names remain owned by the Mechanical Compiler contract and are deliberately not copied into Kane Fabric because Fabric does not implement or consume that protocol.

The Mechanical Compiler identity contract is intentionally a relying-party contract. Its application does not authenticate users, hold a membership roll, know membership groups, or know building geography. A reverse proxy decides whether a request may proceed and supplies minimal request identity only after authorization.

That is compatible with the Kane Fabric boundary **provided Kane Fabric is not turned into the identity provider or authorization service**.

The current Mechanical Compiler contract creates no direct runtime API requirement for Kane Fabric.

## 2. Stable conclusions

### 2.1 Fabric is geography and publication infrastructure, not person authentication

Kane Fabric may eventually provide accepted parcel and persistent delivery-point geography. A membership system may consume those geographic facts.

Kane Fabric does not thereby own:

- human identity;
- email identity;
- login/session state;
- OIDC;
- membership rolls or group names;
- application authorization;
- reverse-proxy ACL policy;
- postal/anchor participation state.

A future path may look like:

```text
accepted Fabric geography
        ↓
membership / participation system
        ↓
authorization verdict
        ↓
Mechanical Compiler reverse proxy
        ↓
Mechanical Compiler application
```

The application need not learn the geographic facts used upstream to reach that verdict.

### 2.2 Transport is not authorization

The Mechanical Compiler currently reaches its service through `wg-pk` and a WireGuard tunnel, but intentionally places authorization at its own CT101 reverse proxy rather than at the shared WireGuard hub.

Kane Fabric carries the same rule forward:

```text
WireGuard / management transport
        ≠
application authorization
        ≠
accepted Fabric geography
```

MS5-008 may use existing WireGuard infrastructure for runtime feasibility testing. That does not make the existing hub, VPN address, peer key, or topology part of the Kane Fabric logical contract.

### 2.3 Mechanical Compiler public TLS is evidence for the Wiregate pattern, not edge TLS

The Mechanical Compiler's browser path terminates public TLS on centrally reachable infrastructure and then traverses private transport/proxy layers.

The accepted Kane Fabric MS5-004 topology applies the same role-separation principle locally: browser HTTPS terminates at the Wiregate hub and the hub reaches the ESP32-S3 reference edge over plain HTTP.

Mechanical Compiler's existing TLS deployment is therefore useful operational evidence for that separation, but it is not the Kane Fabric Wiregate implementation, browser-origin identity, or edge-management contract.

### 2.4 Future delivery-point identity must remain upstream of application authorization

The Mechanical Compiler explicitly does not want building or group information in the application.

That is a useful generic consumer constraint for planned MS6 work. Persistent parcel/building/delivery-point geography may be consumed by a membership service, but Kane Fabric must not automatically expose geographic identity in relying-party request metadata.

Data minimization at this boundary is desirable:

```text
Fabric geography
        ↓
consumer-owned eligibility logic
        ↓
minimum authorization result / application identity
```

## 3. Open gates

### KF-MC-001 — Kane Fabric must not be named as the identity provider

**Owner:** Mechanical Compiler / future membership system  
**Blocks:** first authenticated Mechanical Compiler integration  
**Does not block:** Kane Fabric MS5

The reviewed Mechanical Compiler contract used `kane-fabric/oidc` as an example authentication method.

Kane Fabric currently defines no OIDC service, no person authentication service, and no membership authority. The example must not become an implementation assumption.

If a future identity or membership service uses OIDC, the reported method must identify that actual service or mechanism rather than imply that Kane Fabric authenticated the person.

### KF-MC-002 — persistent email authorship versus epoch-unlinkable civic identity

**Owner:** Mechanical Compiler + whichever membership system is selected  
**Blocks:** using an epoch-unlinkable civic anchor system as Mechanical Compiler membership without an explicit bridge contract  
**Does not block:** Kane Fabric MS5 or MS6 geography work

The reviewed Mechanical Compiler contract defines an email address as the application identity and anticipates persisted designs attributed to a verified person.

The civic-participation architecture discussed alongside Kane Fabric instead trends toward address-bound, opaque, per-epoch participation credentials with no persistent person identity.

Those are not automatically compatible.

Before integration, one of the following must be explicitly chosen:

- Mechanical Compiler uses a separate persistent account/membership system;
- Mechanical Compiler accepts an epoch-scoped alias/identity and its persistence semantics;
- another explicit bridge is designed, with the privacy consequences documented.

Kane Fabric must not solve this by inventing a person identity.

### KF-MC-003 — building wording versus delivery-point geography

**Owner:** future membership system; Mechanical Compiler documentation  
**Blocks:** membership semantics only  
**Does not block:** Mechanical Compiler's verdict-only relying-party interface

The reviewed Mechanical Compiler contract says membership attaches to buildings while simultaneously insisting the compiler itself never learns what a building is.

Planned Kane Fabric MS6 work distinguishes persistent delivery points from building footprints because multi-unit structures contain multiple independently addressable dwellings.

The relying-party interface can survive this change unchanged if geography remains upstream. The membership system must eventually reconcile whether its eligibility unit is a building, parcel, delivery point, or another consumer-owned concept.

### KF-MC-004 — deployment-neutral relying-party naming

**Status:** RESOLVED by Mechanical Compiler, 2026-09-12  
**Owner:** Mechanical Compiler

The first reviewed contract used Kane-specific trusted-header names. Mechanical Compiler subsequently removed those names and reported that the interface no longer carries the county name.

This is the preferred direction for multi-county reuse. Kane Fabric records the resolution but intentionally does not import the replacement header names into its own contracts. Header syntax remains Mechanical Compiler-owned deployment/interface detail unless a future integration requires a jointly frozen protocol.

Parent-domain deployment names may still be Kane-specific operational configuration; that does not create a Fabric interface requirement.

### KF-MC-005 — trust-header forgery prevention must land before authentication

**Owner:** Mechanical Compiler CT101 proxy  
**Blocks:** enabling trusted request identity  
**Does not block:** Kane Fabric

The Mechanical Compiler contract requires any client-supplied copies of its trusted identity headers to be stripped before proxy-authenticated values are added.

This is a Mechanical Compiler security gate. Kane Fabric has no action except to avoid treating those headers as a Fabric protocol.

### KF-MC-006 — existing `wg-pk` is test infrastructure, not fleet topology

**Owner:** Kane Fabric MS5/MS7 + estate operator  
**Blocks:** production managed-edge rollout at fleet scale  
**Does not block:** MS5-008 feasibility proof against controlled infrastructure

The existing WireGuard hub already carries unrelated estate peers. Manual peer identity drift has previously caused outages.

Kane Fabric must not silently assume that the current hub, manual peer inventory, address space, or operational ownership model scales to a civic edge fleet.

MS5 may prove the ESP32 transport against a controlled hub. Before managed synchronization becomes production architecture, peer lifecycle, capacity, ownership, replacement, and failure isolation require an explicit design.

### KF-MC-007 — Wiregate browser origin remains independent

**Status:** RESOLVED by accepted MS5 transport-architecture correction, 2026-09-14  
**Owner:** Kane Fabric MS5-004  
**Does not block:** Mechanical Compiler

Central public TLS and reverse-proxy TLS used by Mechanical Compiler do not themselves define the Kane Fabric browser origin. The accepted MS5-004 solution is a local Wiregate hub that terminates browser HTTPS and proxies plain HTTP to the ESP32-S3 reference edge.

The Wiregate/browser-origin identity remains independent of person, delivery point, membership group, WireGuard address, physical edge identifier, and Fabric logical content identity.

### KF-MC-008 — CA and credential hierarchies remain separate by role

**Owner:** both projects / deployment operator  
**Blocks:** any proposal to collapse trust roots merely for convenience

Mechanical Compiler currently uses public TLS plus a local staging CA inside its service path. Kane Fabric MS5 separately uses a browser-serving Wiregate TLS identity and may later use edge management credentials.

No current evidence justifies sharing:

- Mechanical Compiler proxy certificates;
- Kane Fabric Wiregate TLS certificates or private keys;
- WireGuard keys;
- membership/identity issuer keys;
- Fabric release-signing or geographic-promotion authority.

Role separation remains the default.

### KF-MC-009 — persisted authorship semantics are unresolved

**Owner:** Mechanical Compiler + membership system  
**Blocks:** claims that a historical saved design remains attributable to the same verified person across identity epochs

The Mechanical Compiler deliberately does not reconstruct `verified=true` from a saved file. That is a good trust boundary.

However, if the external identity is ephemeral or rotates, historical attribution and later re-identification require an explicit policy. Kane Fabric must not supply that continuity implicitly through geographic identity.

## 4. Non-gates: work Kane Fabric should not create

The Mechanical Compiler identity contract does **not** justify adding any of the following to Kane Fabric:

- OIDC provider;
- login form;
- user/session database;
- membership roll;
- group or role directory;
- application ACL engine;
- consumer-specific trusted request-header protocol;
- Mechanical Compiler-specific reverse proxy;
- stable person/email identity;
- building or delivery-point identity embedded in application authentication metadata.

If a future consumer needs those services, the owning application or a separate membership/identity system must define them.

## 5. Milestone impact

### MS5

No newly discovered Mechanical Compiler gate blocks the current MS5 sequence.

Relevant carried constraints:

- **MS5-004:** browser HTTPS terminates at the Wiregate hub; the hub reaches the ESP32-S3 reference edge over plain HTTP; browser TLS identity remains separate from person/membership and Fabric logical identity.
- **MS5-008:** prove WireGuard only as management transport; do not promote the current `wg-pk` deployment into a fleet architecture by accident.
- **MS5-010:** physical device replacement changes device-local identities only, never application/person/geographic identity.

### MS6

Mechanical Compiler reinforces the need for a clean geographic upstream boundary:

- parcel/building/delivery-point identity remains Fabric geography;
- consumer membership logic may use it;
- the relying application can receive only the consumer-owned authorization result.

MS6 must not introduce a user/account identity merely because a consumer eventually needs authorization.

### MS7 and later

Managed edge synchronization must define its own device/peer lifecycle at fleet scale.

Existing shared estate WireGuard configuration is evidence and test infrastructure, not the production lifecycle contract.

## 6. Handoff rule

A successor Assistant should treat this register as a list of unresolved interfaces, not a backlog to implement indiscriminately.

For every gate:

1. identify the owner;
2. identify the milestone or integration it actually blocks;
3. preserve Kane Fabric's geography/publication boundary;
4. do not resolve another project's ambiguity by adding application semantics to Fabric;
5. update this register when the opposite tunnel exposes a concrete interface, test, or contradiction.

The projects are intentionally allowed to advance independently until a real interface is required.
