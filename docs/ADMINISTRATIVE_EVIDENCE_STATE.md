# Administrative Evidence State

## Status

Architecture candidate for Kane Fabric Civic Infrastructure evidence handling.

This document is downstream of the accepted descriptor-driven Administrative Web and association/unit identity contracts. It defines how Kane Fabric should represent what is observed, what can be established, what conflicts, and what remains unresolved before participant-publication and derived-identity contracts are expanded.

The governing rule is simple:

> Record what can be established. Preserve where it came from. Expose contradictions. Represent absence explicitly. Infer only when labeled. Never convert uncertainty into fact merely to complete a model.

## Why this is Infrastructure

Civic records are not a clean database.

A public record may be:

- unavailable;
- incomplete;
- indexed differently across systems;
- represented with punctuation or formatting differences;
- copied into later instruments;
- internally inconsistent;
- contradicted by another public record;
- superseded without the earlier statement disappearing;
- observable but not independently confirmed.

Kane Fabric therefore must not make completeness or consistency a prerequisite for participation.

The purpose of provenance is not to claim that a statement is unquestionably true. It is to answer:

```text
Why does Kane Fabric display this?
What source supplied it?
What exactly did that source say?
What other evidence supports or conflicts with it?
What conclusion, if any, has been drawn from those observations?
```

## Evidence is separate from subject identity

The accepted association/unit identity contract identifies the civic subject being discussed. Evidence state describes claims about that subject.

These are separate concepts:

```text
association / unit identity
        ≠
claim about association / unit
        ≠
source containing the claim
        ≠
current evidence assessment
```

A contradiction does not create a second association. A missing record does not erase a unit. A corrected public record does not retroactively delete the prior observation.

## V1 evidence states

The first evidence contract should support at least the following states.

### observed

A specific source contains or presents the value.

This says nothing more than what was observed in that source.

### corroborated

Two or more independently identifiable observations support materially the same claim.

Corroboration does not convert the claim into absolute truth. The supporting observations remain separately inspectable.

### conflicting

Two or more relevant observations cannot all be accepted as the same factual statement without reconciliation.

Kane Fabric must preserve the conflicting observations rather than silently selecting one.

### unresolved

Evidence exists, but the available evidence is not sufficient to establish the claim.

### missing

A record or value is expected or required for a particular operation but has not been obtained.

Missing is not equivalent to false, nonexistent, withheld, or destroyed unless evidence establishes one of those narrower statements.

### inferred

The displayed conclusion is derived from one or more observations rather than directly stated by a source.

The inference and its inputs must remain distinguishable.

### disputed

An identified participant, institution, authority, or source expressly contests a claim.

Dispute is evidence about the claim's status; it does not itself decide which side is correct.

### established

The current evidence set is sufficient for the bounded Civic Infrastructure operation that depends on the claim.

`established` is deliberately operational rather than metaphysical. A later better source may still correct or supersede the conclusion. The underlying observations must remain retained.

## Unknown is a valid result

Schemas and user interfaces must not force uncertain values into false precision.

Where the evidence does not establish a value, the correct result may be:

```text
unknown
unresolved
missing
conflicting
```

A blank field must not silently mean all four.

## Raw observations versus normalized values

Raw source text and any normalized representation must remain distinct.

Normalization may eventually support comparison or derived logical identifiers, but it must not destroy the observed source form.

For example:

```text
observed source form A: 92K.79038
observed source form B: 92K79038
possible normalized comparison value: [not yet frozen]
```

The normalized value, if one is later defined, is an interpretation layer. It does not replace the two observations.

## Real-record exercise: Carriage Homes of Sandhurst

Kane County Board Resolution materials provide a usable identity exercise for Carriage Homes of Sandhurst Condominium in South Elgin.

One legal description identifies:

```text
UNIT NUMBER 3 IN BUILDING 1
CARRIAGE HOMES OF SANDHURST CONDOMINIUM
Declaration recorded November 4, 1992
Document Number 92K.79038
First Amendment recorded November 6, 1992
Document 92K82635
Plat of survey attached as Exhibit B to the Declaration
```

Source:

```text
Kane County Board agenda packet, August 11, 2009
Resolution 09-309, Exhibit A
https://www.kanecountyil.gov/Lists/Events/Attachments/865/AG%20PKT%20-%20AUGUST%20-%20FINAL.pdf
```

The same Kane County packet contains additional Carriage Homes of Sandhurst legal descriptions referring to the original declaration as:

```text
92K79038
```

without the punctuation appearing in `92K.79038`. It also identifies other units through combinations such as Unit 3 in Building 47 and Unit 2 in Building 1, again by reference to the plat attached to the same declaration.

This is not treated as a contradiction in the underlying declaration identity merely because punctuation differs. It is, however, evidence that byte-for-byte equality of raw recording-reference strings is not a sufficient logical identity rule.

### Sandhurst consequence

The accepted identity contract can represent the real subject:

```text
jurisdiction: US / IL
recording authority: Kane County Recorder, Illinois
original declaration recording reference: observed as 92K.79038 and 92K79038
unit designation: Unit Number 3 in Building 1
unit recorded locator: the Exhibit B plat attached to the declaration, as referenced by the legal description
```

The precise normalization/canonicalization rule for the declaration reference is still intentionally not frozen.

## Real-record exercise: Summit Square Condominiums

A Village of East Dundee public agreement presents a useful conflicting-evidence case.

The body of the agreement states that the Summit Square Condominium Declaration was made September 17, 2013 and recorded with the Kane County Recorder as:

```text
2013K069969
```

The attached legal-description exhibit identifies the same document number but states that the declaration was recorded:

```text
September 26, 2014
```

Sources are within the same public document:

```text
Village of East Dundee agreement / Ordinance 22-50 material
https://cms9files.revize.com/eastdundeeil/ord2250.pdf
```

The document therefore contains two different date statements associated with the same declaration number.

Kane Fabric must not silently rewrite one date to match the other.

The correct evidence representation is conceptually:

```text
claim: declaration recording document number
observations:
  2013K069969
assessment: corroborated within the public document

claim: declaration recording date
observations:
  September 17, 2013 / declaration made date
  September 26, 2014 / exhibit recording-date statement
assessment: unresolved or conflicting until better evidence establishes the recording date
```

The distinction between execution/made date and recording date may ultimately explain part of the apparent discrepancy, but the exhibit explicitly uses the word `RECORDED`; that observation must remain preserved until reconciled from stronger evidence.

## Evidence source hierarchy is not automatic truth

Source type matters, but Kane Fabric must not implement a rule such as:

```text
Recorder > County > Municipality > Association > Participant
```

as an automatic truth selector.

A source may be authoritative for one kind of fact and merely derivative for another. Later instruments often quote earlier recording information. A public agency document can contain a typo. A participant can possess the only surviving copy of a record.

The evidence contract should therefore record source identity/type and provenance, while the operation that consumes the evidence decides what level of support is sufficient.

## Historical observations are retained

If later evidence resolves a conflict, prior observations are not deleted.

Conceptually:

```text
observation A  retained
observation B  retained
resolution     added
current assessment updated
```

This permits another participant or operator to audit why the displayed conclusion changed.

## Relationship to identity canonicalization

The Sandhurst exercise demonstrates that canonicalization cannot simply hash the raw observed declaration-reference string.

A future derived association identifier must be stable across harmless representational differences while still preserving the source forms that produced the normalized anchor.

Therefore the order is:

```text
raw observations
        ↓
evidence/provenance model
        ↓
bounded authority-specific normalization rules, if justified
        ↓
canonical identity anchor
        ↓
derived logical identifier
```

The project must not skip directly from one observed text string to a permanent civic identifier.

## Next implementation step

After this architecture checkpoint is accepted, implement a small source-neutral evidence-claim contract that can represent:

- claim identity/path;
- one or more observations;
- source reference for each observation;
- observed raw value;
- observation date or source date when known;
- evidence state;
- optional explanatory note;
- optional relationship to another observation or resolution.

Do not combine that first evidence contract with:

- human authentication;
- Board authority;
- legal adjudication;
- confidence percentages;
- automated source ranking;
- destructive conflict resolution;
- derived association/unit IDs;
- participant publication visibility;
- edge transport.

## Acceptance criterion

This checkpoint is accepted when the repository records the evidence-state principles and the Sandhurst/Summit Square exercises, and CT102 confirms that the change is documentation-only relative to the last synchronized state.

No claim is made by this checkpoint that the evidence-claim JSON contract is already implemented.
