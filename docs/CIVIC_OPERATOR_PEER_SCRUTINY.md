# Participant-Operated SASE Validation and Peer Scrutiny

## Status

Architecture contract. Documentation only.

This document defines the operator role for Civic Infrastructure participation issuance.

## Core principle

Kane Fabric is civic infrastructure because operation is not reserved to a permanent administrator, institution, board, school administration, vendor, or platform owner.

Any active participant may become a SASE validator and therefore operate a Kane Fabric issuance role under the published rules.

Operator is a participant role, not a superior civic identity.

~~~text
active participant
      ↓ may assume
SASE validator / Kane Fabric operator
      ↓ performs
bounded published issuance procedure
      ↓ remains subject to
peer participant scrutiny
~~~

## Operator authority is procedural

The operator's authority comes from carrying out a published procedure within an active participation context.

The operator does not become:

- owner of participant identity;
- owner of participant claims;
- final authority on all civic facts;
- representative of an HOA, school, county, or other institution merely by operating Kane Fabric;
- permanent administrator whose continued availability is required.

The operator can attest facts the operator directly controls or observes through the published process, such as receipt and handling of a SASE participation-renewal act.

## Any active participant may operate

An active participant may become a SASE validator/operator if the applicable Civic Infrastructure profile permits that role and the participant follows the published operator procedure.

Operator eligibility is therefore rooted in active participation, not institutional office.

A participant may cease operating without losing ordinary participant standing. Another eligible active participant may take over the operator function.

## Operator role does not erase participant role

A participant who becomes an operator remains a participant with their own civic relationships and credibility history.

Operator actions must therefore remain attributable as operator actions without turning that participant into a privileged global authority.

Conceptually:

~~~text
participant P
  ├─ ordinary civic relationships
  └─ operator role for bounded issuance actions
~~~

## Peer scrutiny: scrubbing

Operator-issued facts and procedures must be inspectable by other participants.

This peer scrutiny is called **scrubbing** in the Civic Infrastructure model.

Scrubbing means participants can examine an operator's published actions and supporting facts and may:

- confirm consistency;
- corroborate facts from independent knowledge or records;
- identify omissions;
- expose contradictions;
- identify stale or inaccurate claims;
- identify procedural departures;
- identify institutional capture or preferential treatment.

Scrubbing is diagnostic. It does not require pretending that disagreement can be eliminated.

## Scrubbing does not imply centralized adjudication

Peer scrutiny does not automatically create a majority vote, central moderation authority, or institutional appeal board.

A participant confirmation is itself a provenance-bearing observation.

A participant challenge is likewise a provenance-bearing observation.

The infrastructure should preserve enough history to compare:

~~~text
operator issuance
participant confirmation(s)
participant challenge(s)
subsequent correction or supersession
~~~

The existence of conflict is diagnostic data.

Exact confirmation/challenge record formats remain future design work.

## Institutional anti-capture

The institution being observed must not automatically control the Civic Infrastructure used to observe it.

Examples:

### HOA Diagnostics

HOA Diagnostics is the first intended consumer of Kane Fabric.

For an HOA diagnostic profile, the infrastructure must not be captured by the HOA Board, property manager, management company, counsel, or other service provider merely because those actors administer the association.

Homeowners possess first-hand information and affected standing necessary to compare the Board's or service providers' claims against lived association operation.

The HOA profile should therefore preserve an operator path rooted in active homeowner participants rather than giving the Board an exclusive infrastructure-control role.

This does not make homeowners infallible. Their claims and operator actions remain subject to peer scrutiny by other participants.

### Schools

A school administration must not automatically control the Civic Infrastructure used to diagnose school-related civic conditions.

The applicable school profile must preserve operation by affected active participants rather than making institutional administration the sole validator or publisher.

The exact eligible affected roles for a school profile remain to be defined by its published affordance contract; this document does not invent them.

## Operator capture is itself diagnostic

If one operator:

- inconsistently validates equivalent SASE events;
- suppresses records;
- favors one participant class;
- makes undocumented exceptions;
- changes published procedure silently;
- misstates participant claims;
- attempts to exclude other eligible operators;

those actions are not merely implementation defects.

They are diagnostic signals about operator credibility and possible infrastructure capture.

## Multiple operators

The architecture must allow more than one eligible operator over time and, where a profile chooses, more than one contemporaneous operator.

No single operator identity becomes permanent Kane Fabric identity.

The exact coordination model between multiple operators is not yet frozen.

Possible future mechanisms may include independent issuance roots, shared published history, cross-observation, or explicit handoff, but none is selected here.

## SASE validation boundary

A SASE validator attests the procedural fact the validator actually handles:

> A participant voluntarily initiated or renewed participation by the required SASE procedure for this bounded interval.

The validator does not thereby certify every other participant-maintained affordance in the issuance record.

This remains consistent with `docs/CIVIC_PARTICIPATION_RENEWAL.md`.

## Credibility of the operator

Operator credibility is earned in the same general way as participant credibility:

- consistent application of published rules;
- transparent provenance;
- preserved history;
- correction rather than silent rewriting;
- equal treatment of equivalent cases;
- tolerance of peer scrutiny;
- absence of unexplained preferential treatment.

An operator does not acquire credibility merely by holding the role.

## Same and Equal and operators

Operator status should not silently alter Same-and-Equal standing in unrelated civic comparisons.

For example, two current homeowners in the same HOA may remain Same and Equal as homeowners even if one temporarily performs the SASE-validator role.

If a diagnostic surface specifically compares operator conduct, then operator role may become a material comparison dimension under that surface's published Same-and-Equal policy.

## Future operator records

A future implementation will need bounded records for:

- operator eligibility at time of issuance;
- operator identity/provenance;
- SASE receipt/validation event;
- issuance action;
- peer confirmation/challenge observations;
- correction or supersession;
- operator handoff or replacement.

These are design requirements only. No record schema is frozen here.

## Anti-monopoly invariant

No institution may claim exclusive control of the Civic Infrastructure solely because it controls the institution being observed.

That means, for example:

~~~text
HOA Board control of HOA != exclusive control of HOA civic diagnostics
school administration control of school operations != exclusive control of school civic diagnostics
~~~

The diagnostic infrastructure must remain operable by qualified affected participants under published rules.

## Next design implication

The minimal SASE issuance workflow must now include:

- participant eligibility to act as validator/operator;
- operator provenance on each issuance;
- a bounded validation act;
- public/participant-visible evidence sufficient for later scrutiny;
- operator replacement/handoff;
- peer confirmation/challenge hooks;
- no requirement for institutional administrators to control the validation role.

No implementation code should precede that workflow design.


## Statutory procedure inheritance

The participant-operated validator workflow must not recreate procedures Illinois law already defines for the underlying institution.

For HOA Diagnostics, `docs/ILLINOIS_STATUTORY_PROCEDURE_BASELINE.md` records the first statutory anchors in the Illinois Condominium Property Act. Statutory member/board roles, notices, records, inspection rights, meeting openness, recording rights, delivery methods, and fiduciary duties remain sourced to Illinois law where applicable.

SASE validation, rotating Civic operators, and peer scrubbing are Civic Infrastructure additions layered above those source-defined relationships; they are not represented as statutory condominium procedures.
