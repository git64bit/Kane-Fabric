# Civic Affordance Authority Contract

## Status

Architecture contract. Documentation only.

This document defines the versioned source-of-meaning consumed by a future Civic Issuance Authority. It is not yet a JSON schema, database schema, firmware structure, signature format, or runtime implementation.

## Purpose

A Civic Issuance Authority must not decide affordance meaning ad hoc for each participant.

It must operate from a published, versioned authority contract that answers:

- which civic relations exist;
- what each relation means;
- which domains and targets it can attach to;
- which roles and temporal states are valid;
- which evidence/qualification paths can establish it;
- whether voluntary initiation is required;
- how long the relation remains current;
- which derivations are allowed;
- which diagnostic surfaces may use it;
- which Same-and-Equal policies apply.

The contract is therefore the semantic authority used to interpret Civic Relationship Tuples.

## Source lineage

The current model source is:

`Civic-Affordances-Diagnostics/civic-affordance-model`

Observed baseline commit:

`3745d7a07b5f69c580020d5b5a4f70c5b9f44457`

Kane Fabric does not silently copy the external repository's current branch forever. Each accepted authority contract must identify the exact source lineage from which it was derived.

A later source update does not retroactively change an already-issued relationship tuple. New meaning requires a new contract identity/version.

## Plural roots and local profiles

The external source model explicitly permits multiple county roots and does not create one monopoly county operator.

Therefore an affordance-authority contract is published by a particular root/profile.

Conceptually:

~~~text
shared civic-affordance model
        +
explicit local/root profile
        ↓
versioned Affordance Authority Contract
~~~

A local profile may:

- specialize evidence rules;
- bind a generic relation to local geography or institutions;
- define local participation-initiation procedures;
- define local diagnostic surfaces;
- define local Same-and-Equal policies;
- add clearly namespaced local relations when needed.

A local profile must not silently:

- rename a source relation;
- merge two distinct relations;
- imply a derivation that is not published;
- turn recognition into monopoly authority;
- rewrite historical contract meaning.

## Logical contract

The first logical form is:

~~~text
A = (
  contract_identity,
  source_lineage,
  publisher,
  scope,
  relation_definitions,
  role_definitions,
  state_definitions,
  qualification_profiles,
  initiation_profiles,
  validity_profiles,
  derivation_rules,
  surface_bindings,
  equivalence_policies
)
~~~

Exact serialization is intentionally deferred.

## 1. contract_identity

The contract needs a stable version/content identity.

The exact canonicalization and hash representation are not frozen here, but an issuance must eventually be able to refer unambiguously to the exact contract under which its relationship tuples were interpreted.

## 2. source_lineage

`source_lineage` records the external/base model and exact revision(s) used to construct the contract.

This is provenance, not automatic authority. A county/root profile may intentionally diverge, but divergence must be explicit.

## 3. publisher

`publisher` identifies the root/profile that published this authority contract.

Publisher identity does not imply monopoly authority over a county or institution. It tells a verifier whose rules produced the issuance.

## 4. scope

`scope` declares the geographic, institutional, procedural, or surface boundaries in which this contract is intended to operate.

Examples may include a county implementation, a particular diagnostic surface family, or a bounded institutional profile.

## 5. relation_definitions

Each relation definition must include enough meaning to populate and validate the `relation` field of a Civic Relationship Tuple.

A relation definition should identify:

- stable relation identifier;
- affordance family;
- human-readable meaning;
- permitted target kinds;
- permitted domain kinds;
- permitted role vocabulary;
- permitted state vocabulary;
- applicable qualification profiles;
- applicable initiation profile if any;
- applicable validity profile;
- applicable diagnostic surfaces;
- Same-and-Equal policy references where defined.

Initial source-model relation identifiers include, among others:

- `CURRENT_RESIDENT`;
- `PROPERTY_TAXPAYER`;
- `PARCEL_LINKED_OCCUPANT`;
- `CONDO_UNIT_OWNER`;
- `HOA_MEMBER`;
- `PUBLIC_RECORDS_REQUESTER`;
- `COURT_LINKED_PARTY`;
- `DIRECT_WITNESS`;
- `SUBJECT_MATTER_EXPERT`.

`CURRENT_RESIDENCE` is also required by the Kane participant-initiation design and is intentionally not collapsed into `CURRENT_RESIDENT`.

## 6. role_definitions

Roles refine a relation; they do not replace it.

For example, an HOA-related relation may distinguish current unit owner, former unit owner, board member, manager, service provider, vendor, counsel/professional actor, or another published subtype.

A role identifier is meaningful only in the relation/domain contexts declared by the contract.

## 7. state_definitions

States describe temporal/lifecycle posture of a relation.

Examples:

- current;
- former;
- pending qualification;
- superseded;
- expired;
- historical.

The contract must define which states can be issued as current assertions and which are retained only as historical state.

## 8. qualification_profiles

A qualification profile identifies the evidence discipline required to assert a relation.

Source-model evidence classes include:

- self-attested;
- address-evidenced;
- mail-evidenced;
- county-boundary-evidenced;
- parcel-evidenced;
- occupancy-evidenced;
- tax-evidenced;
- association-record-evidenced;
- public-record-evidenced;
- case-linked;
- credential-evidenced;
- expert-reviewed;
- multi-source verified.

A qualification profile may require one or multiple evidence classes and may specify operator review, expert review, records review, published-rule evaluation, or another published qualification authority.

Evidence class is not evidence instance. The contract defines classes/rules; an issuance records that a specific qualification path was satisfied.

## 9. initiation_profiles

Initiation is separate from qualification.

`CURRENT_RESIDENCE` demonstrates why:

~~~text
method: SASE
primary meaning: participant voluntarily initiated participation
secondary value: mail/postal reachability evidence
~~~

A contract may require an initiation profile even when public records would otherwise provide enough evidence to infer the underlying factual relationship.

This prevents passive enrollment from being treated as equivalent to voluntary participation.

## 10. validity_profiles

A validity profile defines whether a relation is:

- event-bounded;
- time-bounded;
- current until revalidation;
- current until superseded;
- historical-only after a transition;
- subject to another published temporal rule.

Validity policy does not erase history. It determines what the publisher currently asserts.

## 11. derivation_rules

Derivation is **deny-by-default**.

No relation is derived from another merely because the two often correlate.

Examples of prohibited implicit derivation:

- `CONDO_UNIT_OWNER` -> `HOA_MEMBER`;
- `HOA_MEMBER` -> `CONDO_UNIT_OWNER`;
- `PROPERTY_TAXPAYER` -> `CURRENT_RESIDENT`;
- `CURRENT_RESIDENCE` -> `CURRENT_RESIDENT`;
- device possession -> any civic relation;
- expert role -> personal affected status.

If a publisher wants one relation to support another, the contract must publish an explicit directional derivation rule containing at least:

- source relation(s);
- resulting relation;
- additional conditions;
- domain constraints;
- role/state constraints;
- qualification/evidence requirements;
- validity behavior;
- whether human/operator review remains required.

Derivation rules are not automatically transitive.

~~~text
A -> B
B -> C
does not imply
A -> C
~~~

unless the contract explicitly defines that path.

## 12. surface_bindings

The source model distinguishes having a civic relation from being allowed to act on every diagnostic surface.

A surface binding therefore links relationship qualifications to actions such as:

- Hear;
- Read;
- Attend;
- Comment;
- Submit evidence;
- Speak;
- Write;
- Publish;
- Moderate;
- Administer.

The relationship tuple does not itself contain universal permission flags.

A surface binding evaluates one or more relationship tuples under a named published policy.

## 13. equivalence_policies

`equivalence_policies` identify the Same-and-Equal comparison rules published by this contract.

The detailed representation is defined in `docs/CIVIC_SAME_AND_EQUAL_POLICY.md`.

## CURRENT_RESIDENCE and CURRENT_RESIDENT

The contract must preserve both names until their relationship is explicitly formalized by the source/profile.

For the Kane participant process:

`CURRENT_RESIDENCE` records the participant's voluntary initiation through SASE.

`CURRENT_RESIDENT` remains the source-model residency affected-status identifier.

The contract must not silently treat them as aliases.

A future explicit derivation may relate them only if its qualification and initiation conditions are published.

## HOA_MEMBER and ownership

`HOA_MEMBER` is not defined by current ownership alone.

The contract must support HOA-related roles and temporal states broad enough to represent policy-qualified relationships such as:

- current unit owner;
- former unit owner;
- service provider;
- board member;
- manager;
- vendor;
- counsel/professional actor;
- other directly affected HOA roles recognized by published policy.

`CONDO_UNIT_OWNER` remains a distinct Parcel / Dwelling relation.

## Policy changes

A contract version must be immutable in meaning after publication.

Corrections or policy changes create a new version/identity.

An issuance refers to the exact contract used at issuance time.

A later contract may revalidate or supersede a relationship through a new issuance, but it does not rewrite the earlier record.

## Credibility rule

The authority contract exists to make institutional behavior inspectable.

Given equivalent evidence and equivalent relationship context under the same contract, the issuer should reach the same result.

If it does not, that inconsistency is itself a diagnostic signal.

## Future Witness Attestation

The contract may later define which relationship contexts qualify a device to assemble a particular Witness Attestation.

The witness record should reference the exact relationship-policy context that existed when the appliance assembled it.

This future use does not turn the affordance contract into an event recorder and does not authorize Witness Attestation implementation now.

## Next boundary

With this authority contract and the Same-and-Equal policy defined at the architecture level, the next object is the canonical Civic Issuance Record.

No issuance/runtime/signing code should precede that design checkpoint.
