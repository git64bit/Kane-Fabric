# HOA Governing-Source Inheritance

## Status

Architecture clarification. Documentation only.

This document defines how HOA Diagnostics derives substantive governance rules.

## Core rule

HOA Diagnostics does not invent substantive HOA governance.

For an Illinois condominium association, the governing source chain is:

~~~text
Illinois statute
    ↓ constrains / requires
condominium instruments
    ↓ specialize the association
bylaws / declaration / applicable rules
    ↓ observed and taught by
HOA Diagnostics
    ↓ instrumented by
Kane Fabric + ESP32-S3 + SASE + peer scrubbing
~~~

The Civic Infrastructure may create mechanisms for participation, provenance, attestation, witnessing, transport, comparison, and diagnostics. It does not create competing substantive rules for how the HOA itself must govern when an authoritative source already supplies them.

## Statute and condominium instruments are complementary

Illinois statute supplies mandatory requirements, boundaries, defaults, and limits.

The association's condominium instruments supply association-specific rules where the statute permits or requires local specification.

Therefore HOA Diagnostics must evaluate both:

- the controlling Illinois statute;
- the association's actual governing instruments, especially declaration and bylaws, plus valid rules/regulations where relevant.

A statutory rule cannot be replaced by a conflicting bylaw merely because the bylaw exists.

A bylaw-specific rule must not be generalized to every Illinois condominium merely because it exists in one association.

## Education is a first-class function

HOA Diagnostics is not only an observer.

It must explain to homeowners:

- which source controls a question;
- what the statute requires;
- what the association's instruments add or specialize;
- which facts must be observed to determine compliance;
- which evidence can confirm or contradict the claimed procedure;
- which participant standing makes the observation relevant.

The educational layer should preserve source citations so a homeowner can distinguish law from bylaw from Civic instrumentation.

## Example: meeting cadence

Current Illinois Condominium Property Act Section 18 requires the board to meet at least four times annually.

That statutory cadence can become an input to a Civic profile without claiming that Illinois law itself requires SASE.

For example, an HOA Diagnostics profile may choose four participation renewals per year so the Civic participation cadence tracks the minimum statutory board-meeting cadence.

In that case:

~~~text
4 board meetings/year = statutory source fact
4 SASE renewals/year  = Civic mechanism parameter derived from that source
~~~

The Civic mechanism is new; the cadence is intentionally inherited rather than arbitrary.

## Example: voting thresholds

Illinois Condominium Property Act Section 27 establishes statutory rules for amendments to condominium instruments, including a general 2/3-of-those-voting rule or the majority specified by the condominium instruments, subject to the statutory ceiling.

Other voting/election matters have their own statutory/bylaw rules.

A Civic profile that elects or rotates an operator should therefore not invent a free-standing voting threshold.

Instead, it should identify the governing analog and inherit:

- who is entitled to vote;
- how vote weight is determined;
- notice/quorum requirements where applicable;
- required approval threshold;
- any association-specific bylaw specialization that remains valid under statute.

The exact operator-election analog must be named in the profile; no generic 'majority vote' rule is assumed.

## Same and Equal defines the electorate

The Civic operator is elected or selected only by participants who are Same and Equal under the relevant published relationship policy.

That means the electorate is not simply 'all accounts' or 'all active participants'.

For an HOA homeowner diagnostic profile, the relevant Same-and-Equal class may be current qualifying homeowners/unit owners in the same association, subject to the exact policy/source mapping.

Operator role does not create a superior class. The operator remains one participant chosen by the applicable Same-and-Equal electorate.

## Instrumented governance

The Civic Infrastructure can instrument a source-defined rule without claiming authorship of the rule.

Examples:

- SASE can implement a periodic participation checkpoint whose cadence is derived from an authoritative governance cycle;
- ESP32-S3 can witness/attest that a meeting notice, meeting event, vote, record delivery, or participant action occurred;
- peer scrubbing can compare operator assertions against statute, bylaws, participant-held evidence, and other witness records;
- Same-and-Equal can determine which participants belong to the relevant comparison/electorate class.

## Source provenance on every rule

Every HOA Diagnostics rule should eventually carry one of these provenance forms:

~~~text
STATUTE
CONDOMINIUM_INSTRUMENT
DERIVED_PROFILE_PARAMETER
OBSERVED_FACT
PARTICIPANT_CLAIM
WITNESS_ATTESTATION
~~~

`DERIVED_PROFILE_PARAMETER` means the Civic mechanism is new but its substantive parameter is inherited from a named statute/bylaw source.

Example:

~~~text
renewal mechanism = SASE
renewal cadence   = 4/year
cadence source    = 765 ILCS 605/18 board-meeting minimum
~~~

This prevents the project from disguising a design choice as law while also avoiding arbitrary civic governance.

## Bylaws as education and diagnostics source

For a specific HOA, the operator/profile must ingest the actual current governing instruments before evaluating association-specific procedure.

Examples can include:

- election procedure;
- officer roles;
- meeting procedures;
- notice details;
- assessment procedures;
- maintenance allocation;
- use restrictions;
- amendment procedures;
- other valid association-specific obligations.

The Civic Infrastructure should show the homeowner both the source text/reference and the observable condition that would satisfy or contradict it.

## ESP32-S3 role

The ESP32-S3 does not legislate or interpret law independently.

It can later attest and witness events against a known source context.

Conceptually:

~~~text
source rule
  statute + governing instrument
        ↓
expected event/procedure
        ↓
participant/device observation
        ↓
ESP32-S3 witness/attestation record
        ↓
peer scrubbing / education / diagnostics
~~~

## No orphan Civic rule

For HOA Diagnostics, no substantive governance rule should exist without a source lineage.

If a Civic mechanism needs a parameter such as cadence, electorate, threshold, notice window, or role eligibility, the profile should first attempt to inherit it from the governing-source chain.

Only the mechanics of Civic participation/provenance may be project-defined, and those mechanics should identify the authoritative source from which their substantive parameters were derived.

## Next design step

The participant-operated SASE workflow should now be defined as a source-derived profile rather than a standalone Civic procedure.

For each step, record:

- mechanism;
- governing source;
- source-derived parameter;
- eligible Same-and-Equal class;
- operator/witness role;
- record/attestation produced.

No implementation code should precede that profile design.
