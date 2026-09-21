# Civic Relationship Tuple

## Status

Architecture primitive. Documentation only.

This document defines the logical civic relationship carried by a future Civic Issuance Record. It is not yet a wire format, JSON schema, firmware structure, database table, signature envelope, or authorization implementation.

## Purpose

Civic Infrastructure must describe affected-status relationships precisely enough to support:

- voluntary participation;
- multiple simultaneous affordances;
- current and former relationships;
- institutional and geographic scope;
- Same and Equal comparison;
- evidence-qualified issuance;
- device replacement without identity collapse;
- later Witness Attestation assembled by the participant appliance.

A flat permission list cannot represent these requirements.

## Fundamental distinction

The **relationship tuple** describes the civic relationship being asserted.

The **Civic Issuance Record** later wraps one or more relationship tuples with issuance provenance such as issuer, record identity, sequence, appliance issuance reference, issuance time, supersession lineage, and signature.

Therefore:

~~~text
relationship fact != issuance event != physical appliance
~~~

A relationship may remain meaningful across appliance replacement. An issuance event may supersede an earlier issuance without rewriting historical relationship evidence.

## Logical tuple

The first logical form is:

~~~text
R = (
  subject,
  relation,
  target,
  domain,
  role,
  state,
  qualification,
  initiation,
  validity,
  policy
)
~~~

Each field is independently meaningful. Fields may be absent only when the governing policy explicitly says they are not applicable.

## 1. subject

`subject` identifies the participant to whom the relationship applies.

The subject identifier should be opaque and issuance-oriented. It must not require the ESP32 MAC address, IP address, email address, person's legal name, or a platform account to become the permanent civic identity.

Examples:

- one participant who voluntarily entered the Current Residence process;
- one current condominium unit owner;
- one former unit owner;
- one service provider with an HOA-related affected status;
- one property taxpayer;
- one direct witness.

## 2. relation

`relation` identifies the affected-status or civic relationship being asserted.

Examples from the current source model include:

- `CURRENT_RESIDENCE`;
- `CURRENT_RESIDENT`;
- `PROPERTY_TAXPAYER`;
- `CONDO_UNIT_OWNER`;
- `HOA_MEMBER`;
- `PUBLIC_RECORDS_REQUESTER`;
- `COURT_LINKED_PARTY`;
- `DIRECT_WITNESS`;
- `SUBJECT_MATTER_EXPERT`.

The relation is not automatically a permission. Published policy determines what a qualified relation permits on a particular diagnostic surface.

## 3. target

`target` identifies the specific civic object to which the relationship attaches when one exists.

Examples:

- a particular condominium unit;
- a particular parcel;
- a particular address;
- a particular court case;
- a particular public-records request;
- a particular event witnessed;
- a particular service relationship.

`target` is intentionally separate from `domain`.

Two participants may have different targets while still being Same and Equal inside the same comparison domain. For example, two current unit owners may own different units in the same condominium association.

## 4. domain

`domain` identifies the institutional, geographic, procedural, or other bounded context in which the relationship has meaning.

Examples:

- Kane County, Illinois;
- a specific municipality;
- one specific condominium association;
- one school district;
- one court/case jurisdiction;
- one diagnostic surface.

Domain is essential to prevent false equivalence. Two people holding the same relation identifier in different domains are not automatically Same and Equal.

## 5. role

`role` refines the relationship where the broad relation alone is insufficient.

Examples within an HOA-related relationship may include:

- unit owner;
- former unit owner;
- board member;
- manager;
- service provider;
- vendor;
- counsel/professional actor;
- another policy-defined subtype.

`role` must not be inferred merely from relation name when published policy distinguishes subtypes.

## 6. state

`state` records the temporal or lifecycle status of the relationship.

Examples:

- current;
- former;
- pending qualification;
- superseded;
- expired;
- historical;
- another policy-defined state.

A former HOA relationship is not equivalent to a current one merely because both share `HOA_MEMBER`.

State is not punishment. It records what the authority currently asserts about the relationship.

## 7. qualification

`qualification` binds the relationship to the evidence discipline or claim basis under which it is presented. For participant-maintained affordances, this does not by itself imply that the Kane operator independently verified the claim.

It should be capable of referring to:

- evidence class;
- qualification path;
- reviewing authority or published rule;
- bounded evidence references or hashes where appropriate.

Examples of evidence classes from the source model include:

- address-evidenced;
- mail-evidenced;
- county-boundary-evidenced;
- parcel-evidenced;
- tax-evidenced;
- association-record-evidenced;
- public-record-evidenced;
- case-linked;
- credential-evidenced;
- multi-source verified.

Raw private evidence does not automatically belong in the tuple or on the ESP32.

## 8. initiation

`initiation` records how participation or the relationship assertion entered the Civic Infrastructure when initiation itself matters.

This field is essential for `CURRENT_RESIDENCE`.

For the current Kane process:

~~~text
method: SASE
meaning: participant voluntarily initiated participation
secondary evidence value: postal/reachability evidence
~~~

A discovered public record, scraped address, or operator-created account is not equivalent to voluntary SASE initiation.

Not every civic relationship requires an initiation field. Policy decides when it is material.

## 9. validity

`validity` records the time interval or temporal conditions under which the relationship assertion is current.

It may include:

- valid-from;
- valid-until when applicable;
- revalidation requirement;
- event-bounded validity;
- open-ended current state subject to supersession.

Historical records remain historical evidence after a relationship ceases to be current.

## 10. policy

`policy` identifies the exact published rule set under which the tuple was interpreted and qualified.

It must be versionable/content-identifiable.

This prevents a later policy change from silently changing the meaning of an earlier issuance.

Policy identity is required for credible comparison, revalidation, Same and Equal evaluation, and later diagnostics.

## Tuple identity versus issuance identity

The tuple should be canonically identifiable once its exact representation is frozen, but tuple identity and issuance-record identity are different.

Conceptually:

~~~text
relationship tuple
    = what relationship is asserted

issuance record
    = who issued which relationship tuple(s),
      when, under what issuance sequence,
      to which current appliance issuance,
      with what supersession lineage
~~~

This distinction prevents device replacement or record renewal from pretending that the underlying civic relationship itself is a new kind of identity.

## Same and Equal

`Same and Equal` is a comparison over relationship tuples under a published equivalence rule.

It is not a stored universal truth about two people.

Define an equivalence policy `E` that selects the tuple dimensions relevant to a particular civic comparison.

Conceptually:

~~~text
SAME_AND_EQUAL_E(Ra, Rb)
    = equal(
        relation dimensions selected by E,
        domain dimensions selected by E,
        role dimensions selected by E,
        state dimensions selected by E,
        policy/version constraints selected by E
      )
~~~

The `subject` values normally differ. The `target` values may also differ.

### Example: two current owners in one HOA

Participant A:

~~~text
relation = CONDO_UNIT_OWNER
target   = Unit 211
domain   = Association X
role     = unit_owner
state    = current
~~~

Participant B:

~~~text
relation = CONDO_UNIT_OWNER
target   = Unit 311
domain   = Association X
role     = unit_owner
state    = current
~~~

An equivalence rule for current unit-owner standing within Association X may ignore the differing unit targets and evaluate them as Same and Equal.

### Example: different HOA

If Participant C has the same relationship to a unit in Association Y, the domain differs. Same and Equal is false for the Association-X comparison.

### Example: current versus former

If Participant D has an HOA-related relationship in Association X but `state=former`, a current-member equivalence policy does not treat D as Same and Equal to a current participant.

### Same people, different civic purpose

Two participants may be Same and Equal for one relationship and not for another.

For example, they may be Same and Equal as current unit owners in one HOA while differing in property-taxpayer status, residency, board role, procedural-party status, or expert qualification.

## Affordance stacking

A participant may have multiple relationship tuples at once.

Conceptually:

~~~text
participant P
  ├─ CURRENT_RESIDENCE in Kane County
  ├─ CURRENT_RESIDENT in Kane County
  ├─ CONDO_UNIT_OWNER of Unit 211 / Association X
  ├─ HOA_MEMBER in Association X / current unit-owner role
  ├─ PROPERTY_TAXPAYER for Parcel Z
  └─ PUBLIC_RECORDS_REQUESTER for Request Q
~~~

No single tuple automatically dominates the others. Published surface policy decides which tuple or combination qualifies a particular action.

## Relationship derivation must be explicit

One relationship must not be silently inferred from another merely because they often correlate.

Examples:

- `CONDO_UNIT_OWNER` does not automatically define the full meaning of `HOA_MEMBER`;
- `CURRENT_RESIDENCE` does not silently collapse into `CURRENT_RESIDENT`;
- `PROPERTY_TAXPAYER` does not automatically imply residence;
- `HOA_MEMBER` does not automatically imply current ownership;
- expert status does not imply personal affected status;
- device possession does not imply any civic relationship.

If a policy defines a derivation or inheritance rule, that rule must itself be published and versioned.

## Relationship to the ESP32-S3

The ESP32-S3 may later carry issued relationship tuples inside a signed Civic Issuance Record.

The device is not the semantic authority for those relationships. It preserves and exposes the authority's issued statement while remaining replaceable.

This is also important for future Witness Attestation.

A later Witness Attestation design may allow the participant appliance itself to assemble an observation record using:

- its accepted relationship context;
- device-local observations or inputs;
- time/provenance information available to the device;
- the then-current Civic Issuance Record;
- a device-side attestation mechanism.

The value is that the appliance assembles the record rather than an institution or another human rewriting the event after the fact.

That future use does not change the present boundary: Witness Attestation is not implemented or specified here. The tuple merely preserves enough civic context for such a record to identify the standing from which the appliance was acting.

## Non-goals

This tuple does not:

- prove that a person can never lie;
- make counterfeit firmware impossible;
- make an institution infallible;
- adjudicate legal rights;
- replace government or HOA records;
- define a voting credential;
- define a universal person identity;
- make the ESP32 the owner of the civic relationship.

It provides a precise, inspectable vocabulary for what the Civic Infrastructure actually asserted.

## Next design step

The versioned Affordance Authority Contract and Same-and-Equal policy are now defined at the architecture level in:

- `docs/CIVIC_AFFORDANCE_AUTHORITY_CONTRACT.md`;
- `docs/CIVIC_SAME_AND_EQUAL_POLICY.md`.

The next architecture object is the canonical Civic Issuance Record that wraps one or more tuples with issuer/appliance/provenance/signature metadata.

No implementation code should precede that design checkpoint.


## Claim responsibility

The tuple describes the civic relationship being claimed/asserted; the enclosing Civic Issuance Record must also preserve **claim provenance**.

For Kane:

- active SASE participation is operator-attested;
- most other civic affordances are participant-maintained claims;
- evidence may support those claims without transferring claim responsibility to the operator;
- operator issuance/signature must not be interpreted as blanket certification of every tuple.

The participant is responsible for keeping claimed affordances accurate and current throughout each participation interval and across renewals.
