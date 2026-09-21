# Civic Issuance Authority and Affordance Model

## Status

Architecture checkpoint. Documentation only; no wire format, signer implementation, or firmware behavior is frozen by this document.

This document separates civic issuance from firmware release signing and records the authority/credibility model that individual ESP32-S3 issuance must eventually implement.

## Published civic-standing source

The current public terminology is published through the Civic Infrastructure / HOA Diagnostics Hubzilla realm:

https://directory.diagnostics.kane-il.us/directory

Repository searches show that this affordance vocabulary is not yet represented in Kane-Fabric contracts. The public material currently establishes, at minimum, these terms:

- Same and Equal;
- Current Resident, scoped to an actual place/jurisdiction;
- Affected Status;
- HOA Homeowner;
- Property Taxpayer.

The public material describes these as real positions in local life and as a way to match civic participation to actual exposure, obligation, risk, residence, ownership, payment, or other affected standing.

The full affordance taxonomy and exact eligibility rules are **not imported here yet**. No additional affordance may be invented from memory or inferred from firmware. The published definitions must be brought into the repository as explicit, versioned authority data before implementation.

## Core principle

The Civic Infrastructure is open; civic affordances are selective.

Anyone may observe public infrastructure, copy bytes, modify software, or make a false claim. The system does not depend on making forgery impossible.

The authoritative question is:

> What standing and affordances did the Civic Infrastructure actually issue, under which published rules, to which participant issuance?

A forged or inconsistent claim is therefore a diagnostic divergence from authoritative issuance history. It does not redefine the infrastructure.

Conceptually:

~~~text
published standing / affordance rules
              +
accepted standing evidence
              ↓
Civic Issuance Authority
              ↓
signed Civic Issuance Record
              ↓
replaceable participant appliance
~~~

## Authority is not security theater

The principal value of the signature is provenance and credibility:

~~~text
this is what the recognized Civic Issuance Authority issued
under this published rule set
at this time
for this bounded participant issuance
~~~

It is not a claim that firmware cannot be replaced, credentials cannot be copied, or code cannot be forged.

Credibility depends at least as much on consistent institutional behavior as on cryptography:

- published definitions;
- repeatable evidence standards;
- equal treatment of equivalent standing;
- explicit issuance history;
- explicit supersession/revalidation;
- inspectable provenance;
- no silent alteration of prior records;
- independent verification of what was actually issued.

## Distinct logical authorities

At least two signing authorities must remain logically distinct.

### Firmware Release Authority

Statement:

> This firmware release is an authorized Civic Infrastructure software release.

It operates on firmware artifacts and release manifests. It does not decide whether an individual is a Current Resident, HOA Homeowner, Property Taxpayer, or holder of another civic affordance.

### Civic Issuance Authority

Statement:

> This participant voluntarily initiated or renewed a bounded participation interval through the required SASE process, and this issuance carries the participant's then-current civic claims under these published rules.

It administers the bounded SASE participation issuance and records the participant's claimed affordance set with explicit provenance. It must not imply continuous operator verification of participant-maintained claims.

These two authorities may eventually be co-located on one physical machine or separated. Physical placement is not decided here. Their logical authority, records, and signing roles must remain distinct even if a later implementation shares hardware.

## Published affordance contract

The Civic Issuance Authority must not create affordance meaning ad hoc.

It consumes a versioned, publicly inspectable affordance definition set that determines:

- affordance identifier;
- human-readable meaning;
- jurisdiction or geographic scope;
- qualifying standing;
- evidence class required for issuance or revalidation;
- whether the affordance is inherited from another standing;
- validity/revalidation semantics;
- supersession semantics;
- any application surface to which the affordance applies.

The issuance node applies those rules; it does not silently rewrite them per person.

## Civic Issuance Record

The exact v1 wire representation is deliberately not frozen yet. The logical record must be able to bind at least:

~~~text
issuer identity
issuance sequence / record identity
published affordance-policy identity
jurisdiction / geographic scope
opaque participant issuance reference
standing claims
affected-status claims
granted affordance identifiers
evidence references or evidence-class references
current appliance issuance reference
issued-at / valid-from
revalidation or expiry semantics where applicable
supersedes / previous-record reference where applicable
signature / authority provenance
~~~

Raw private evidence does not automatically belong on the ESP32. The record may carry bounded evidence references, witness identities, hashes, or evidence classes while private source material remains in its proper custody domain.

## Person, standing, appliance, and firmware remain separate

These identities must never collapse:

~~~text
human person / participant
    != civic standing
    != civic affordance set
    != association or unit identity
    != Civic Issuance Record
    != physical ESP32-S3
    != firmware release
    != participant publication generation
~~~

A physical ESP32-S3 is the current bearer/custodian of an issuance, not the permanent identity of the person or standing.

Replacing a failed device must permit reissuance to a new physical appliance without pretending that the person, association, unit, or civic standing changed merely because the hardware changed.

## Standing is temporal

Some standings are inherently current-state claims. A person may cease to be a Current Resident, may sell a unit, may cease to be a Property Taxpayer for a given property, or may otherwise lose or change affected standing.

The authority therefore needs explicit revalidation/supersession semantics. The purpose is not punitive revocation; it is to keep the Civic Infrastructure's current assertion credible.

Conceptually:

~~~text
record N     standing asserted under policy P
record N+1   revalidated / changed / superseded
~~~

An old record remains part of history. A new record states what the authority now asserts.

## Issuer independence after issuance

The anti-capture rule remains: continued availability of the original issuer must not be required for ordinary local usefulness after an appliance has been issued and accepted.

Therefore an accepted appliance must retain enough signed authority data and public verification material to explain its issued affordances without requiring a live SaaS account or continuous issuer lookup.

A public issuance/history service may improve diagnostics, discovery, and comparison, but normal local operation must not become dependent on its constant availability.

## Diagnostic divergence

Counterfeit firmware, copied credentials, false standing claims, altered issuance records, or inconsistent implementations are expected possibilities.

They become diagnostic signals when compared with authoritative records and published rules:

~~~text
claimed standing != issued standing
claimed affordance != affordance derived by published policy
presented record != authority-signed record
device claim != accepted issuance history
implementation behavior != published affordance semantics
~~~

The infrastructure improves by making these divergences observable and comparable, not by claiming they can be eliminated.

## Relationship to the ESP32-S3

The v1 ESP32 firmware must not become a semantic engine for civic standing.

The device may eventually:

- carry an issued Civic Issuance Record;
- expose the record or bounded derived capability metadata to an accepted consumer;
- preserve it through ordinary local operation;
- be reprovisioned/replaced through an issuance process.

But the firmware does not decide what Current Resident, HOA Homeowner, Property Taxpayer, Same and Equal, or Affected Status means. Those meanings belong to published civic contracts above the firmware boundary.

## Open questions before implementation

1. Import the full published affordance taxonomy and exact definitions into versioned repository authority data.
2. Define evidence classes for each standing without turning the issuer into a permanent account custodian.
3. Define the exact Civic Issuance Record and its canonical identity.
4. Define revalidation/supersession cadence for temporal standings.
5. Define how an appliance locally exposes its granted affordances to consumers.
6. Define independent verification when the original issuer is offline.
7. Define the diagnostic/public history model without making a central service mandatory.
8. Decide whether Firmware Release Authority and Civic Issuance Authority share physical infrastructure or remain physically separate.
9. Only after these are accepted, select signing/provider mechanics appropriate to each logical authority.

## Implementation hold

No civic-affordance or individual-issuance code should be written until the published taxonomy and Civic Issuance Record are accepted as repository contracts.


## Imported source baseline

The external Civic Affordances Diagnostics model has now been interrogated at exact commit `3745d7a07b5f69c580020d5b5a4f70c5b9f44457` and recorded in `docs/CIVIC_AFFORDANCE_SOURCE_BASELINE.md`.

Important refinement: an affordance is not merely a Boolean capability. The source model attaches qualification/evidence, access modes, surface scope, qualification authority, publication authority, persistence, and replication semantics. The eventual Civic Issuance Record must preserve policy identity rather than flattening these dimensions into firmware flags.

Three source discrepancies are deliberately unresolved: `CURRENT_RESIDENT` vs `CURRENT_RESIDENCE`; public `HOA Homeowner` vs formal `HOA_MEMBER`/`CONDO_UNIT_OWNER`; and `Same and Equal`, which is published publicly but lacks a formal identifier in the source documents interrogated.


## Authority-model clarifications

These clarifications resolve three previously open semantic questions.

### CURRENT_RESIDENCE is intentional and begins with voluntary participation

`CURRENT_RESIDENCE` is not to be normalized away as a typo for `CURRENT_RESIDENT`.

For the participant workflow, `CURRENT_RESIDENCE` is gained through the SASE process: the prospective participant initiates the relationship by sending a self-addressed stamped envelope to the issuer's residential address.

The significance is not merely postal reachability. The initiating act demonstrates that participation was voluntarily requested by the participant rather than silently assigned by the infrastructure.

Architectural consequence:

- `CURRENT_RESIDENCE` is an intentional-entry / participation-initiation affordance or workflow outcome;
- the issuance record must preserve the fact and method of voluntary initiation;
- no person should acquire participant standing merely because an operator discovered their address or other public record;
- SASE is therefore both a reachability/evidence mechanism and a consent/initiative boundary.

The formal taxonomy's `CURRENT_RESIDENT` remains a separate identifier used for residency affectedness. Kane Fabric must preserve both names until the source model explicitly defines their relationship; it must not silently alias one to the other.

### HOA_MEMBER is broader than current ownership

`HOA_MEMBER` must not be reduced to `CONDO_UNIT_OWNER`.

A participant can have an HOA-related affected-status relationship without being a current unit owner. Examples include a former unit owner whose rights or responsibilities continue to matter, or a service provider whose direct HOA relationship qualifies them for a specific diagnostic surface.

`CONDO_UNIT_OWNER` remains a distinct Parcel / Dwelling relationship. `HOA_MEMBER` is a broader Private Governance relationship class.

Architectural consequence:

- ownership is one possible evidence/relationship dimension, not the definition of HOA membership;
- current/former status must be representable;
- role/subtype must be representable;
- the same person may hold multiple HOA-related affordances simultaneously;
- an issuance record must not infer one affordance merely from another unless a published policy explicitly says so.

### Same and Equal is relational, scoped, and temporal

`Same and Equal` is not global equivalence between people.

It expresses equivalence within a defined civic comparison context.

Examples:

- two current unit owners in the same HOA may be Same and Equal for the relevant unit-owner standing;
- unit owners in different HOAs are not Same and Equal merely because both are unit owners;
- a current HOA member and a former HOA member are not Same and Equal merely because both have an HOA relationship.

Therefore Same and Equal depends on at least:

- the institutional/geographic comparison domain;
- the exact standing/affordance being compared;
- role/subtype;
- temporal state such as current/former where relevant;
- the policy version under which equivalence is evaluated.

Architectural consequence:

`Same and Equal` should be evaluated from authoritative issued context rather than treated as an unqualified Boolean badge. The issuance system must carry enough structured context for two records to be compared under a published equivalence rule.

Conceptually:

~~~text
participant A issued standing
        +
participant B issued standing
        +
same comparison domain
        +
same relevant role/state/policy
        ↓
Same and Equal for that bounded context
~~~

This relation may be true for one civic purpose and false for another.

## Resulting issuance-record requirements

The eventual Civic Issuance Record must therefore distinguish:

- participation initiation / consent evidence;
- person or opaque participant reference;
- jurisdiction and institutional domain;
- affordance identifier;
- affected-status family;
- role/subtype;
- current/former/other temporal state where applicable;
- evidence class and qualification path;
- policy identity/version;
- appliance issuance reference;
- issuance/revalidation/supersession history.

This is intentionally more precise than a flat list of permission flags.


## Civic relationship primitive

The relationship carried by an issuance is now factored into a separate architecture primitive:

`docs/CIVIC_RELATIONSHIP_TUPLE.md`

The tuple separates subject, relation, target, domain, role, temporal state, qualification, voluntary initiation, validity, and policy identity. Issuer/signature/appliance/sequence metadata remains outside the tuple in the future Civic Issuance Record.

This separation is necessary for Same-and-Equal comparison, device replacement, temporal standing, affordance stacking, and later Witness Attestation.


## Affordance authority and equivalence contracts

The relationship tuple now has two architecture-level policy authorities:

- `docs/CIVIC_AFFORDANCE_AUTHORITY_CONTRACT.md` defines the versioned vocabulary, qualification, initiation, validity, derivation, surface-binding, and equivalence-policy source of meaning;
- `docs/CIVIC_SAME_AND_EQUAL_POLICY.md` defines Same-and-Equal as a named equivalence-class evaluation over relationship tuples, with four diagnostic outcomes: `SAME_AND_EQUAL`, `NOT_SAME_AND_EQUAL`, `NOT_COMPARABLE`, and `INDETERMINATE`.

These documents deliberately keep relation semantics and equality semantics outside firmware and outside the individual issuance event.


## Canonical issuance-record semantics

The logical Civic Issuance Record is now defined in `docs/CIVIC_ISSUANCE_RECORD.md`.

The record is a complete issuance snapshot, not a delta. It wraps one or more Civic Relationship Tuples with issuer/root identity, one exact Affordance Authority Contract identity, issuer-scoped subject lineage, current appliance issuance reference, monotonic sequence, issuance/effective time, explicit supersession/correction/replacement lineage, revalidation posture, disclosure policy, and logical authority proof.

Cryptographic representation remains unfrozen.


## Six-month participation boundary

Kane participation is renewed only by a fresh SASE every six months. Without a new SASE, participation ends.

This is the only recurring administrative burden on the Kane operator and participant.

Other civic affordances are maintained by the participant. The operator may issue/sign the record that carries those claims, but the record must distinguish operator-attested participation from participant-claimed relationships so the operator signature is not misread as institutional certification of every claim.

Participant credibility is earned by keeping claims accurate, current, and appropriately evidenced over time. False or stale claims are diagnostic signals about the participant's credibility, not proof that the infrastructure failed.

See `docs/CIVIC_PARTICIPATION_RENEWAL.md`.


## Participant-operated issuance authority

The Civic Issuance Authority is a logical role, not a permanently privileged human or institution.

Under the Kane model, any eligible active participant may act as SASE validator/operator according to the published profile. Each issuance must identify the actual operator/validator provenance separately from the broader root/profile identity.

Operator action is peer-scrubbable by other participants. Institutional control of an HOA, school, or other underlying body does not confer exclusive control of its Civic Infrastructure diagnostic surface.

See `docs/CIVIC_OPERATOR_PEER_SCRUTINY.md`.
