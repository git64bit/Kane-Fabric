# Civic Affordance Source Baseline

## Status

Documentation baseline imported from the public source repository for Civic Affordances Diagnostics. No Kane-Fabric executable contract or code is created by this document.

## Exact source

Repository:

`Civic-Affordances-Diagnostics/civic-affordance-model`

Observed main commit:

`3745d7a07b5f69c580020d5b5a4f70c5b9f44457`

Primary source files interrogated:

- `README.md`
- `docs/model-vocabulary-addendum.md`
- `docs/diagnostic-families.md`
- `docs/diagnostic-surface-qualification.md`
- `docs/cooperation-interfaces.md`
- `docs/county-surface-cooperation-intake.md`
- `docs/interface-declaration-template.md`
- `docs/local-economic-attribution-and-anti-capture.md`
- `hubzilla/civic-workspace/docs/participant-baseline.md`
- `hubzilla/civic-workspace/docs/README.md`

Public Hubzilla material was also reviewed as contextual publication, but repository documents above are the stronger machine-readable/design source for import.

## Source model

The source repository defines Civic Affordances Diagnostics as a diagnostic model for defining, classifying, recording, and publishing affected-status relationships with evidence discipline. It explicitly does not claim governmental, judicial, regulatory, representational, or enforcement authority.

A civic affordance is defined there as an evidenced capacity of a person, household, address, role, local actor, professional, or qualified contributor to claim affected status in relation to a civic condition.

The model distinguishes observation from contribution:

- Hear / Read: observe, learn, audit, review, inspect.
- Speak / Write: contribute to the diagnostic record.

The core qualification rule is that write access follows qualified affordance; publication authority follows evidence discipline.

## Diagnostic families

The source currently defines six families:

1. Residency
2. Parcel / Dwelling
3. Private Governance
4. Public Governance
5. Procedural / Evidentiary
6. Expert

## Initial affordance identifiers

### Residency

- `CURRENT_RESIDENT`
- `COUNTY_RESIDENT`
- `MUNICIPAL_RESIDENT`
- `UNINCORPORATED_RESIDENT`

### Parcel / Dwelling

- `PARCEL_LINKED_OCCUPANT`
- `PROPERTY_TAXPAYER`
- `TENANT_OCCUPANT`
- `CONDO_UNIT_OWNER`
- `FLOODPLAIN_AFFECTED_RESIDENT`

### Private Governance

- `HOA_MEMBER`
- `HOA_BOARD_MEMBER`
- `HOA_VENDOR`
- `HOA_MANAGER`
- `HOA_COUNSEL_PROFESSIONAL_ACTOR`

### Public Governance

- `REGISTERED_VOTER`
- `SCHOOL_DISTRICT_RESIDENT`
- `PARENT_OF_STUDENT`
- `SPECIAL_DISTRICT_RATEPAYER`
- `PUBLIC_RECORDS_REQUESTER`

### Procedural / Evidentiary

- `COURT_LINKED_PARTY`
- `PERMIT_APPLICANT`
- `CODE_ENFORCEMENT_SUBJECT`
- `DIRECT_WITNESS`
- `RECORD_CUSTODIAN`

### Expert

- `SUBJECT_MATTER_EXPERT`
- `LICENSED_PROFESSIONAL`
- `TECHNICAL_OPERATOR`
- `CASE_LAW_MATCHED_PARTICIPANT`

## First expansion priority

The source repository currently ranks these as its initial priority affordances:

1. `CURRENT_RESIDENT`
2. `HOA_MEMBER`
3. `PROPERTY_TAXPAYER`
4. `PARCEL_LINKED_OCCUPANT`
5. `PUBLIC_RECORDS_REQUESTER`
6. `PARENT_OF_STUDENT`
7. `SCHOOL_DISTRICT_RESIDENT`
8. `SPECIAL_DISTRICT_RATEPAYER`
9. `COURT_LINKED_PARTY`
10. `SUBJECT_MATTER_EXPERT`

## Qualification dimensions relevant to issuance

The source taxonomy does not treat an affordance as a single Boolean label. A diagnostic surface may specify at least:

- affordance family;
- affordance identifier;
- affectedness type;
- evidence requirement;
- access mode;
- sensitivity;
- exposure posture;
- protocol fit;
- persistence requirement;
- cooperation mode;
- obstruction expectation;
- qualification authority;
- publication authority;
- replication rule.

This is important for Kane Fabric: the Civic Issuance Record must not reduce the source model to only `affordance=true`. It must preserve enough policy identity to explain why the affordance was issued and what it permits on a given surface.

## Current Resident source profile

The source `Current Resident` surface currently uses:

Affordance:

`CURRENT_RESIDENT`

Affectedness:

- directly affected person;
- county resident;
- address-linked person.

Evidence:

- address-evidenced;
- mail-evidenced;
- county-boundary-evidenced.

Access:

- Read;
- Submit evidence;
- Write after qualification.

Qualification authority:

- published rule;
- operator review.

The source also states that CEAS and SASE may support mail-evidenced participation where adopted by a county root. SASE is a process component, not a universal requirement for every affordance.

## HOA Member source profile

The formal example uses:

`HOA_MEMBER`

with affectedness including directly affected, parcel-linked, and association-linked person.

Evidence may include:

- parcel evidence;
- association-record evidence;
- public-record evidence where available;
- case linkage where applicable.

Access may include Read, Submit evidence, Write after qualification, and Speak after qualification.

The source explicitly says this does not govern, represent, adjudicate, or replace an HOA.

## Affordance stacking

The source defines stacking as cumulative layering, not hierarchy. One participant may simultaneously have several standings, for example county resident, current resident, HOA member, parcel-linked occupant, property taxpayer, procedural party, witness, or expert.

This strongly supports a Civic Issuance Record carrying a set/stack of independently evidenced affordances rather than one exclusive role.

## County-root plurality

The source does not require one canonical county operator. Multiple roots may declare surfaces for the same county, and cooperation is elective/interface-specific.

Recognition is explicitly not permission, endorsement, legal certification, ethical certification, commercial certification, or political approval.

This means a Kane Civic Issuance Authority must identify which county root/policy issued a claim; it cannot imply monopoly authority over all civic standing in Kane County.

## Diagnostic divergence

The source repeatedly treats obstruction, disagreement, capture, false local standing, technical incompatibility, isolation, forking, and failure as diagnostic signals rather than conditions that must be erased.

This matches the Kane Fabric authority model: authenticity supports provenance and comparison; it does not promise the impossibility of counterfeit or divergent implementations.

## Naming discrepancies that must remain unresolved until explicitly decided

### CURRENT_RESIDENT vs CURRENT_RESIDENCE

`docs/diagnostic-families.md` and the qualification taxonomy use `CURRENT_RESIDENT`.

`hubzilla/civic-workspace/docs/participant-baseline.md` states that the `CURRENT_RESIDENCE` affordance is gained through SASE.

Kane Fabric must not silently choose one or treat them as aliases until the source project clarifies whether this is a naming drift, intentional distinction, or draft inconsistency.

### HOA Homeowner vs formal identifiers

Public Hubzilla material uses the phrase `HOA Homeowner` as a civic specification. The formal source taxonomy currently defines `HOA_MEMBER` under Private Governance and `CONDO_UNIT_OWNER` under Parcel / Dwelling.

Kane Fabric must not silently map `HOA Homeowner` to either identifier. The relationship must be explicitly defined by the source model or by a documented Kane-profile decision.

### Same and Equal

Public Hubzilla material names `Same and Equal` as a foundational specification. No formal identifier/definition for it was found in the source documents interrogated for this baseline.

It therefore remains a published concept without an imported formal Kane-Fabric affordance definition.

## Implications for Civic Issuance Authority

The next Civic Issuance Record design should bind:

- exact affordance identifier(s);
- exact source/policy version or content identity;
- qualification authority used;
- evidence class(es) satisfied;
- jurisdiction/surface scope;
- access/action implications only by reference to the policy, not ad hoc firmware logic;
- issuance/revalidation/supersession metadata;
- county-root issuer identity;
- current appliance issuance reference while keeping the device replaceable.

## Implementation hold

No Kane-Fabric affordance schema or issuance code should be written until the three naming/semantic discrepancies above are resolved or explicitly represented as unresolved in the v1 contract.
