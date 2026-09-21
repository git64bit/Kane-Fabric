# Six-Month Participation and Participant-Credibility Model

## Status

Architecture clarification. Documentation only.

This document defines the only recurring administrative duty imposed by the Kane Civic Infrastructure on both participant and operator.

## Core rule

Every participant MUST initiate or renew participation by sending a new Self-Addressed Stamped Envelope (SASE) every six months.

If no new SASE is received for the next participation interval, participation ends.

There is no automatic renewal and no passive continuation.

Historical records remain historical records; ending participation does not erase prior issuance or prior participant publications.

## Why SASE matters

SASE serves two distinct functions:

1. **voluntary participation** — the participant takes a deliberate physical action to initiate or renew participation;
2. **bounded continuity** — active participation cannot persist indefinitely merely because the operator still has an old address or prior record.

The operator must not infer continued participation from:

- public property records;
- prior participation;
- continued device possession;
- an unchanged address;
- email activity;
- Hubzilla activity;
- apparent continued residency;
- any other passive signal.

A fresh SASE is the renewal act.

## Six-month participation interval

Each accepted SASE creates one bounded participation interval of six months.

The exact machine representation of interval boundaries is not frozen here, but the policy semantics are:

~~~text
fresh accepted SASE
        ↓
active participation interval
        ↓
six months
        ↓
new SASE required
        ↓
if absent: participation ends
~~~

There is no administrative grace period implied by this architecture document.

## Operator burden

The recurring administrative burden on whichever active participant is presently acting as Kane Fabric operator/SASE validator is deliberately narrow:

- receive the participant's SASE;
- recognize the voluntary renewal act;
- create the next bounded participation issuance;
- return the participant's self-addressed stamped envelope as defined by the participation workflow;
- preserve issuance history.

The operator is **not** expected to continuously investigate, monitor, or maintain every participant's claimed civic affordances. The operator is not a permanent office: any eligible active participant may assume the published SASE-validator role.

## Participant burden

The participant is responsible for keeping all other claimed affordances accurate and current.

Examples include claimed relationships such as:

- current residency;
- property-taxpayer status;
- current or former HOA relationship;
- condominium unit ownership;
- public-records-requester status;
- court-linked status;
- witness status;
- expert/professional status;
- any other published affordance the participant chooses to claim.

The participant decides when a claim should be added, corrected, narrowed, changed from current to former, or otherwise updated according to the published affordance vocabulary.

## Credibility model

The Civic Infrastructure does not obtain credibility by having the operator certify every fact.

Participant credibility is built over time by the participant keeping claimed affordances consistent with reality and correcting them when reality changes.

Conceptually:

~~~text
participant claim
    +
published meaning
    +
evidence/provenance where supplied
    +
history of accurate maintenance
    +
observable corrections when needed
    ↓
participant credibility
~~~

A false, stale, exaggerated, or internally inconsistent claim is a diagnostic signal.

It may reduce the credibility of that participant's claims without invalidating the Civic Infrastructure itself.

## Two provenance classes in one issuance

A Civic Issuance Record must distinguish at least two provenance classes.

### Operator-attested participation

The operator can authoritatively state:

> This participant voluntarily initiated or renewed participation through the required SASE process and is within the resulting six-month participation interval.

This is an operator-controlled fact because the operator receives the SASE and performs the issuance.

### Participant-maintained civic claims

For other affordances, the record must make clear that the participant is the claimant/maintainer unless a specific published rule says some other authority attested that fact.

The operator's issuance signature must **not** silently transform a participant-maintained claim into an operator-certified fact.

Therefore the future record representation needs explicit claim provenance.

## Claim provenance

Each relationship tuple or claim wrapper must be able to identify who is responsible for the assertion.

Initial logical provenance classes include:

- `OPERATOR_ATTESTED_PARTICIPATION`;
- `PARTICIPANT_CLAIMED`;
- `EXTERNAL_EVIDENCE_REFERENCED`;
- `OTHER_PUBLISHED_ATTESTATION`.

These are conceptual classes, not frozen identifiers or serialization.

A participant-claimed affordance may also reference evidence, but evidence reference and claim responsibility are separate concepts.

## Renewal does not equal affordance re-verification

The six-month SASE renewal re-establishes active participation.

It does not imply that the operator re-investigated every claimed affordance.

At renewal, the participant should have the opportunity to:

- carry forward claims they still maintain;
- update claims that changed;
- mark relationships former/historical where appropriate;
- add new claims;
- remove claims they no longer wish to assert;
- supply or update evidence references where the participant chooses or policy requires.

The credibility responsibility remains with the participant.

## Participation ends without renewal

When the six-month participation interval ends without a new accepted SASE:

- the participant is no longer an active participant in that Kane root;
- the current participation assertion is no longer active;
- the appliance and historical records do not vanish;
- historical claims remain inspectable as historical claims;
- future publication surfaces may treat the participant as inactive according to published policy;
- re-entry requires a new SASE.

This is expiration of participation, not deletion of history.

## Device possession after participation ends

Possession of a previously issued ESP32-S3 does not itself continue participation.

The device may still physically contain prior records. That fact is diagnostic and historical.

Active participation is established only by a current six-month participation issuance.

## Relation to Same and Equal

Same-and-Equal comparisons must distinguish active participation from historical standing.

Two participants cannot be treated as Same and Equal for a policy that requires **currently active participation** if one person's SASE interval has ended.

Other historical comparisons may still compare their relationship tuples at an earlier evaluation time.

## Relation to Witness Attestation

A future Witness Attestation may need to state whether the device owner was within an active participation interval when the device assembled the witness record.

The device can reference its then-current participation issuance and participant-maintained civic context.

The operator still does not author the witnessed event or certify every underlying affordance.

## Anti-burden principle

The Civic Infrastructure intentionally avoids turning participation into an ongoing administrative dependency.

The operator's recurring task is SASE renewal issuance.

The participant's recurring task is the same SASE renewal plus responsible maintenance of their own claimed affordances.

No additional periodic operator review is implied unless a future affordance-specific policy explicitly creates one.

## Next design implication

The Civic Issuance Record must be revised so that:

- six-month active participation is explicit;
- SASE renewal is the sole recurring operator-administered requirement;
- participant-maintained claims are clearly distinguished from operator attestations;
- claim provenance is explicit;
- expiration of participation does not erase history;
- renewal does not falsely imply operator re-verification of every affordance.


## Participant-operated validation and peer scrubbing

The SASE validator/operator is itself an active participant, not a permanent administrator above the participant body.

Any eligible active participant may perform the validator/operator role under the applicable profile. Each issuance must eventually preserve operator provenance so other participants can inspect who performed the validation.

Other participants may scrub operator actions: confirm them, compare them with independent facts, or expose contradictions, procedural departures, unequal treatment, or capture. The operator therefore builds credibility through consistent visible behavior rather than institutional status.

See `docs/CIVIC_OPERATOR_PEER_SCRUTINY.md`.


## Statutory procedure boundary

The six-month SASE rule is a Civic Infrastructure participation rule, not a claim about condominium-law renewal requirements.

For an HOA participant, underlying facts such as unit-owner status, board role, association records, notices, meetings, and statutory inspection rights should be interpreted from the applicable Illinois authority. See `docs/ILLINOIS_STATUTORY_PROCEDURE_BASELINE.md`.
