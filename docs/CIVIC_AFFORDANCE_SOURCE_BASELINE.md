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

## Semantic clarifications and remaining source normalization

### CURRENT_RESIDENT and CURRENT_RESIDENCE are not aliases

`CURRENT_RESIDENCE` is intentionally gained through the SASE participant-initiation process. Sending the SASE is a voluntary act that initiates participation; it is not merely an address lookup or passive assignment.

The formal diagnostic taxonomy separately uses `CURRENT_RESIDENT` for residency affectedness. Kane Fabric must preserve both identifiers and must not silently normalize one to the other until the source model explicitly defines their relationship.

### HOA_MEMBER is not equivalent to CONDO_UNIT_OWNER

`CONDO_UNIT_OWNER` is an ownership relationship. `HOA_MEMBER` is broader and can include affected HOA relationships that are not current ownership, including former unit owners and service-provider relationships where the applicable published policy recognizes them for a diagnostic surface.

Kane Fabric must therefore carry relationship subtype and temporal state rather than treating ownership as the definition of HOA membership.

### Same and Equal

`Same and Equal` is a foundational relational rule, not global equivalence between people. It is evaluated inside a bounded comparison domain.

Two current unit owners in the same HOA may be Same and Equal for the relevant unit-owner standing. Unit owners in different HOAs are not Same and Equal merely because both own units. A current HOA member and former HOA member are not Same and Equal merely because both have an HOA relationship.

The eventual source normalization therefore needs an explicit equivalence rule keyed by institutional/geographic domain, exact standing, role/subtype, temporal state, and policy version. Kane Fabric must carry enough context to evaluate the relation; it must not reduce Same and Equal to an unconditional Boolean label.

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

No Kane-Fabric affordance or issuance code should be written until the remaining source normalization is expressed as explicit versioned authority data. The three previously ambiguous points now have architectural meaning: `CURRENT_RESIDENCE` is intentional voluntary initiation via SASE; `HOA_MEMBER` is broader than current ownership; and `Same and Equal` is a scoped relational equivalence rule.
