# Civic Issuance Record

## Status

Architecture contract. Documentation only.

This document defines the logical record produced by a future Civic Issuance Authority for one participant appliance issuance.

It is not yet a canonical byte encoding, JSON schema, database schema, cryptographic signature format, firmware structure, API, or persistence implementation.

## Purpose

The Civic Issuance Record is the durable authoritative statement:

> This issuer, operating under this exact published affordance-authority contract, asserted this complete set of civic relationships for this participant issuance at this time and bound that issuance to this current appliance bearer.

The record is designed for authority, credibility, inspectability, offline usefulness, supersession, device replacement, and later diagnostics.

## Complete snapshot, not delta

Each Civic Issuance Record is a complete snapshot of the relationships the issuer currently asserts for the participant issuance under the named authority contract.

It is not a patch such as:

~~~text
+ HOA_MEMBER
- CURRENT_RESIDENT
~~~

A later change creates a complete new record.

This gives an offline verifier one bounded object that explains the current issued state without requiring reconstruction from an indefinite sequence of deltas.

History still matters: new records link to prior records through explicit lineage.

## Logical record

The first logical form is:

~~~text
I = (
  record_identity,
  record_kind,
  issuer,
  authority_contract,
  subject_reference,
  appliance_issuance_reference,
  sequence,
  issued_at,
  effective_time,
  relationship_tuples[],
  lineage,
  revalidation,
  disclosure_policy,
  authority_proof
)
~~~

Exact serialization is deliberately deferred.

## 1. record_identity

`record_identity` uniquely identifies this exact issuance record.

The future canonical representation should permit content-addressed identity, but canonicalization/hash details are not frozen here.

Record identity is not person identity, device identity, or relationship identity.

## 2. record_kind

`record_kind` explains why this record exists.

Initial logical kinds include:

- `INITIAL_ISSUANCE`;
- `REVALIDATION`;
- `APPLIANCE_REPLACEMENT`;
- `RELATIONSHIP_CHANGE`;
- `CORRECTION`;
- `POLICY_MIGRATION`.

The kind is explanatory metadata. The complete relationship snapshot remains authoritative regardless of kind.

## 3. issuer

`issuer` identifies the Civic Issuance Authority/root/profile that created the record.

The issuer identity must be scoped and inspectable.

It does not mean the issuer is a government body, monopoly county authority, legal adjudicator, or owner of the participant.

Multiple roots may issue their own records under their own published contracts.

## 4. authority_contract

`authority_contract` identifies the exact Affordance Authority Contract used to interpret every relationship tuple in this record.

For the first record design, one issuance record uses one authority-contract identity.

This deliberate constraint avoids silently mixing tuple semantics from multiple contract versions inside one signed snapshot.

When policy meaning changes, a new issuance under the new contract is created.

## 5. subject_reference

`subject_reference` is an opaque issuer-scoped participant lineage reference.

It must not require:

- legal name;
- email address;
- ESP32 MAC address;
- IP address;
- Hubzilla account identifier;
- globally reusable person identifier.

The reference exists so successive issuance records can belong to the same issuer-scoped participant lineage without making a physical appliance the person.

Cross-root correlation must not be assumed merely because two roots happen to describe the same human being.

## 6. appliance_issuance_reference

`appliance_issuance_reference` identifies the current physical appliance issuance carrying this record.

It binds the issuance event to one current bearer without making that device the permanent civic identity.

Important:

~~~text
subject_reference != appliance_issuance_reference
~~~

If the ESP32-S3 fails, is lost, or is replaced, the issuer can create an `APPLIANCE_REPLACEMENT` record with the same participant lineage and appropriate relationship snapshot but a new appliance issuance reference.

The old record remains historically valid as what was issued then; it is no longer the latest current issuance.

## 7. sequence

`sequence` orders issuance records within one issuer + subject lineage.

It must increase monotonically for that lineage.

Sequence provides simple local ordering when a verifier has more than one record.

It does not imply a global sequence across all participants or all roots.

## 8. issued_at

`issued_at` records when the issuer created the record.

This time belongs to the issuance event.

It is distinct from the validity/effective times of individual relationship tuples.

## 9. effective_time

`effective_time` describes when this complete issuance snapshot becomes the issuer's current assertion.

It may normally equal `issued_at`, but the distinction is preserved for controlled policy migration, scheduled changes, or other future cases.

## 10. relationship_tuples[]

The record contains one or more complete Civic Relationship Tuples as defined by `docs/CIVIC_RELATIONSHIP_TUPLE.md`.

Affordance stacking is represented by multiple tuples, not by collapsing distinct civic relationships into one broad role.

Example:

~~~text
subject P
  CURRENT_RESIDENCE / Kane participant initiation
  CURRENT_RESIDENT / Kane County
  CONDO_UNIT_OWNER / Unit 211 / Association X
  HOA_MEMBER / Association X / current unit-owner role
  PROPERTY_TAXPAYER / Parcel Z
~~~

Each relationship tuple retains its own target, domain, role, state, qualification, initiation, validity, and policy context.

## 11. lineage

`lineage` links this record to earlier issuance records without mutating them.

It should be capable of expressing:

- immediately previous record;
- record being superseded;
- record being corrected;
- policy-migration predecessor;
- appliance-replacement predecessor.

Lineage is historical provenance, not deletion.

## 12. revalidation

`revalidation` records the issuance-level revalidation posture.

It may identify:

- whether this was an initial or repeated qualification;
- when the next review is expected if policy defines one;
- which relationship tuples were revalidated;
- whether unchanged tuples were carried forward under an allowed policy;
- whether new evidence was required.

Revalidation does not silently renew a relation. The new complete issuance record is the durable assertion.

## 13. disclosure_policy

A Civic Issuance Record is not automatically a public profile.

The record may contain relationships whose exposure differs by diagnostic surface.

`disclosure_policy` identifies the published rules governing what the appliance or another consumer may reveal in a given context.

This preserves the source model's distinction between:

- public;
- authenticated;
- county-local;
- private;
- expert-gated;
- archive-only;
- other constrained surfaces.

Possession of the record does not mean every tuple must be exposed to every requester.

## 14. authority_proof

`authority_proof` is the logical provenance proof by which a verifier can determine that this exact issuance record was produced by the stated Civic Issuance Authority.

It must eventually identify:

- proof/signature role;
- verification-material identity;
- exact object covered by the proof;
- proof/signature bytes or bounded reference as appropriate.

The cryptographic algorithm, signer hardware/provider, key representation, and canonical byte envelope remain intentionally unfrozen pending the authority/signing interrogation.

## Current-record rule

For one issuer + subject lineage, the current issuance is the highest accepted sequence whose effective-time and validity conditions apply and that has not been superseded by a later accepted issuance in that lineage.

This rule is local to the issuer's history.

A counterfeit record with a larger invented sequence does not become authoritative merely because its integer is larger; authority proof and lineage must also verify.

## Supersession instead of erasure

The Civic Infrastructure should prefer explicit supersession to destructive revocation semantics.

If a relationship changes:

1. retain the historical issuance record;
2. create a new complete record;
3. link it to the prior record;
4. state the current relationship set;
5. allow diagnostics to observe the transition.

Examples:

- current unit owner -> former unit owner;
- current resident -> former/non-current residency state;
- appliance A -> replacement appliance B;
- policy version P1 -> P2;
- correction of an issuance mistake.

The old record remains evidence of what the authority previously asserted.

## Correction

A correction must not overwrite history.

`CORRECTION` creates a new complete record whose lineage identifies the record containing the error.

This allows an observer to distinguish:

- original issuance;
- discovered mistake;
- corrected assertion.

That distinction is important to institutional credibility.

## Appliance replacement

Replacement is an issuance event, not a new human identity.

Conceptually:

~~~text
subject lineage P
record 17 -> appliance A
record 18 -> appliance B / APPLIANCE_REPLACEMENT
~~~

Relationships may remain unchanged, may be revalidated, or may change according to policy.

The old appliance may physically retain record 17. That is not a design failure; it is a diagnostic fact. Record 18 is the issuer's newer authoritative statement for that lineage.

## Voluntary participation

If the record contains `CURRENT_RESIDENCE`, its relationship tuple must preserve the accepted voluntary-initiation path, currently SASE for the Kane process.

The existence of other public evidence about the participant does not permit an issuer to manufacture voluntary participation retroactively.

## Same and Equal

The issuance record does not need to enumerate every participant to whom the subject is Same and Equal.

Same-and-Equal is derived from relationship tuples using the exact policy in `docs/CIVIC_SAME_AND_EQUAL_POLICY.md`.

This avoids creating stale peer lists and keeps equivalence tied to published relationship context.

A record may reference the applicable equivalence-policy identities through its authority contract, but peer-to-peer equivalence is evaluated when needed.

## Offline usefulness

An accepted appliance should retain enough information to explain:

- which issuer produced the record;
- which exact authority contract was used;
- which relationships were asserted;
- their relevant domains/roles/states/qualification context;
- which issuance sequence this is;
- which prior record it supersedes where available;
- how authority proof can be verified with public verification material.

Ordinary local usefulness must not require continuous availability of the original issuer.

A live issuance-history service may improve diagnostics but is not the sole source of meaning.

## Public history and diagnostics

Where policy permits, an issuer may publish record identities, lineage, selected non-sensitive fields, or durable attestations sufficient to compare a presented record with authoritative issuance history.

That publication is useful for detecting:

- fabricated records;
- stale records;
- conflicting sequences;
- inconsistent qualification;
- silent policy drift;
- unequal treatment under equivalent evidence;
- copied or divergent appliance state.

The diagnostic service does not need to prevent the divergence in order to learn from it.

## Relationship to Witness Attestation

A future Witness Attestation assembled by the ESP32-S3 should reference the Civic Issuance Record identity and the relevant relationship tuple identity/context from which the appliance was acting.

This preserves an important distinction:

~~~text
Civic Issuance Authority
    states the participant/appliance civic context

participant appliance
    later assembles its own witness record
~~~

The issuance authority does not author the witnessed event merely because its earlier record establishes the appliance's civic context.

Witness Attestation remains future scope.

## Non-goals

The Civic Issuance Record is not:

- a government identity card;
- a universal person identifier;
- a voting credential;
- a complete evidence archive;
- an account owned by the issuer;
- a firmware-release signature;
- a guarantee against copying or forgery;
- a substitute for an HOA, court, county, tax authority, or other source institution.

It is a durable statement of what this Civic Issuance Authority actually issued.

## Next design boundary

With the relationship tuple, affordance-authority contract, Same-and-Equal policy, and Civic Issuance Record defined semantically, the next work is **review and reconciliation** before implementation.

Specifically, the project must next reconcile:

- which fields become canonical/hashable versus references;
- what belongs on the ESP32 versus external evidence/history stores;
- how disclosure works locally without exposing the entire relationship stack;
- how the Civic Issuance Authority's signing role relates to the still-provisional Firmware Release Authority cryptographic design;
- what minimal issuance workflow is required for the first `CURRENT_RESIDENCE` appliance.

No implementation code is authorized merely by this document.
