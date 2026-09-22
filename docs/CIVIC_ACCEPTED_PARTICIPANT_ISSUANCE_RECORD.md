# Civic Accepted Participant Issuance Record

## Status

Architecture contract for the type-specific Civic accepted-history record referenced by:

~~~text
manifest.participants[].issuance_record_sha256
~~~

This document defines the minimum authority-epoch issuance invariants Civic must verify for one current participant.

It does not define the full serialization of every broader relationship, affordance, disclosure, revalidation, appliance, or claim-provenance field described by `docs/CIVIC_ISSUANCE_RECORD.md`.

It does not prescribe the physical or administrative issuance ceremony.

It is subordinate to:

- `docs/CIVIC_CRYPTOGRAPHIC_BASELINE.md`;
- `docs/CIVIC_EPOCH_MANIFEST_FORMAT.md`;
- `docs/CIVIC_HISTORY_HEAD_SEMANTICS.md`;
- `docs/CIVIC_SIGNED_HISTORY_RECORD_ENVELOPE.md`;
- `docs/CIVIC_PARTICIPANT_AUTHORITY_STATE_RECONSTRUCTION.md`;
- `docs/CIVIC_ISSUANCE_RECORD.md`;
- `docs/CIVIC_PARTICIPATION_RENEWAL.md`;
- `docs/CIVIC_SAME_AND_EQUAL_POLICY.md`;
- `docs/HOA_GOVERNING_SOURCE_INHERITANCE.md`.

This contract does not enable production signing.

## Scope

Epoch Manifest v1 already defines every current participant as:

~~~text
{
  "participant_record_sha256": bytes(32),
  "participant_key_id": bytes(32),
  "participant_public_key": bytes(65),
  "standing_record_sha256": bytes(32),
  "issuance_record_sha256": bytes(32)
}
~~~

This contract gives precise type-specific meaning to:

~~~text
issuance_record_sha256
~~~

The accepted participant-issuance record answers:

~~~text
which exact participant identity was admitted?
which exact participant public key was bound to that participant?
which exact standing record was relied upon?
which current operator performed or recorded the bounded issuance action?
which exact signed accepted-history record expresses that issuance?
~~~

It does not answer by itself:

~~~text
is the underlying standing legally or factually sufficient?
are all participant-maintained civic claims true?
what physical workflow was used?
what disclosure policy applies to every relationship tuple?
what appliance currently carries the participant's broader record?
~~~

Those questions remain separate.

## Separation of issuance and standing

The central v1 distinction is:

~~~text
issuance
    != standing
~~~

The issuance record proves or fails to prove that a particular participant/key/standing-record tuple was admitted into one accepted authority epoch.

The standing record proves or fails to prove why that participant qualifies under the applicable source-derived profile.

Therefore:

~~~text
valid issuance signature
    != valid standing

valid standing record
    != accepted epoch membership

accepted current participant
    requires both relationships to verify
~~~

This prevents the issuance mechanism from silently becoming the authority that defines the underlying civic standing.

## Relation to the broader Civic Issuance Record

`docs/CIVIC_ISSUANCE_RECORD.md` defines a broader logical snapshot that may include:

- subject lineage;
- appliance issuance;
- relationship tuples;
- participation window;
- claim provenance;
- revalidation;
- disclosure policy;
- supersession/correction lineage;
- broader authority proof.

That semantic model remains useful and is not discarded.

This document is narrower.

It defines only the accepted authority-history record needed to bind one current Epoch Manifest participant descriptor to:

~~~text
participant identity
participant epoch key
standing-record identity
operator provenance
exact accepted issuance-record identity
~~~

A later implementation may connect the broader issuance snapshot to this authority record without changing these invariants.

The broader snapshot must not weaken or redefine the accepted authority binding defined here.

## Record type

The exact v1 `record_type` is:

~~~text
kane-civic-accepted-participant-issuance-v1
~~~

A verifier must not treat another record type as equivalent.

## Required generic-envelope values

The record uses the generic Civic signed-history envelope.

For this type:

~~~text
history_link.stream = "accepted"
~~~

The permitted signer kinds are:

~~~text
participant
signing_node
~~~

No other signer kind is valid.

The generic envelope first verifies the cryptographic signer against the accepted Epoch Manifest authority context.

The type-specific verifier then applies the issuance rules below.

## Body schema

The v1 body contains exactly:

~~~text
{
  "participant_record_sha256": bytes(32),
  "participant_key_id": bytes(32),
  "participant_public_key": bytes(65),
  "standing_record_sha256": bytes(32),
  "issuing_operator_participant_record_sha256": bytes(32)
}
~~~

Unknown body fields are invalid in v1.

Private key material is forbidden.

## Participant identity binding

The body names exactly one participant identity:

~~~text
record.body.participant_record_sha256
~~~

The verifier must locate exactly one descriptor in:

~~~text
manifest.participants
~~~

whose:

~~~text
participant_record_sha256
    == record.body.participant_record_sha256
~~~

That exact manifest descriptor is the participant descriptor bound by the issuance record.

The participant identity remains opaque.

This contract does not derive it from:

- legal name;
- email address;
- postal address;
- device MAC address;
- ESP32 serial number;
- IP address;
- hostname;
- operator account;
- Signing Node key.

## Participant key binding

The record body contains:

~~~text
participant_key_id
participant_public_key
~~~

The verifier requires:

~~~text
SHA-256(record.body.participant_public_key)
    == record.body.participant_key_id

record.body.participant_key_id
    == manifest participant.participant_key_id

record.body.participant_public_key
    == manifest participant.participant_public_key
~~~

The public key representation is the accepted Civic v1 form:

~~~text
65-byte uncompressed SEC1 P-256 point
0x04 || X(32) || Y(32)
~~~

The issuance record therefore binds one exact epoch-specific participant key to one exact participant identity.

It does not create a permanent human master key.

## Epoch-specific key meaning

The participant key is valid as authority material only for the accepted epoch in which the participant descriptor appears.

A historical participant key remains usable to verify historical records created under its historical epoch.

It does not establish current authority after the participant leaves the current set or a successor epoch replaces that key.

Therefore:

~~~text
historical key verification
    != current participant authority
~~~

## Standing-record binding

The issuance record body contains:

~~~text
standing_record_sha256
~~~

The verifier requires:

~~~text
record.body.standing_record_sha256
    == manifest participant.standing_record_sha256
~~~

This is an exact content-identity binding.

The issuance record does not reinterpret the standing record.

The standing record remains responsible for the source-derived facts and policy context by which the participant qualifies.

Examples may include current voluntary participation, relevant HOA/unit-owner standing, or another profile-specific qualification.

The exact meaning depends on the applicable governing profile.

## Standing remains separately verifiable

The standing record must remain independently retainable and verifiable.

A valid participant-issuance record with a missing, corrupted, unrecognized, expired, or semantically insufficient standing record does not make the participant valid merely because the issuance signature verifies.

The required relationship is:

~~~text
verified standing
    +
verified participant issuance
    +
accepted history
    +
accepted Epoch Manifest
    =
current participant authority relationship
~~~

The precise standing schema is a separate contract.

This document does not freeze it.

## Voluntary participation boundary

The Kane participation model currently uses a fresh SASE as the voluntary participation/renewal act.

That is a Civic participation rule for the Kane profile, not a universal legal rule for every future Civic profile.

This participant-issuance record does not encode:

~~~text
"SASE is universally required by all Civic deployments"
~~~

Instead, the standing layer and applicable profile establish whatever voluntary-participation evidence is required.

For the Kane HOA profile, that standing evidence can preserve the six-month SASE participation fact already defined by `docs/CIVIC_PARTICIPATION_RENEWAL.md`.

## Issuing operator provenance

The body contains:

~~~text
issuing_operator_participant_record_sha256
~~~

For v1 it must equal:

~~~text
manifest.operator.participant_record_sha256
~~~

This preserves which current participant was acting in the bounded operator role when the issuance was recorded.

The operator identity is separate from:

- the HOA Civic root identity;
- the participant being issued;
- the Signing Node identity;
- the Signing Node key.

The issued participant may also happen to be the current operator.

That relationship is permitted if the accepted Epoch Manifest says so.

It is not inferred automatically.

## Signer cases

### Participant signer

If:

~~~text
signer.kind = "participant"
~~~

then the signer must be the current manifest operator:

~~~text
record.signer.participant_record_sha256
    == record.body.issuing_operator_participant_record_sha256

record.body.issuing_operator_participant_record_sha256
    == manifest.operator.participant_record_sha256
~~~

The generic history verifier already verifies the participant signature using that participant's current epoch key.

This establishes direct participant-key attribution for the bounded issuance action.

A different current participant may not sign this record type as though they were the issuing operator.

### Signing Node signer

If:

~~~text
signer.kind = "signing_node"
~~~

the generic verifier already requires the Signing Node key to match the referenced Epoch Manifest and verifies the signature under that key.

The body must still name:

~~~text
issuing_operator_participant_record_sha256
    == manifest.operator.participant_record_sha256
~~~

The Signing Node signature proves that the accepted epoch Signing Node authenticated the exact issuance-record bytes.

It does not prove that the broader standing facts are true.

It also does not collapse Signing Node identity into operator identity.

## Why both signer modes are permitted

The stable Civic invariant is:

~~~text
the exact issuance event must be attributable
and the issuing operator provenance must be explicit
~~~

It is not:

~~~text
every deployment must use one identical physical signing workflow
~~~

A deployment may therefore use:

~~~text
operator participant key
    -> direct issuance signature
~~~

or:

~~~text
operator-controlled workflow
    -> authorized local Signing Node
    -> issuance signature
~~~

provided the accepted type-specific relationships verify.

This preserves owner-operator implementation freedom without losing attribution.

## Signer does not certify every participant claim

The broader Civic issuance model may carry participant-maintained claims and relationship tuples.

Neither signer mode silently converts those claims into issuer-certified facts.

In particular:

~~~text
operator signature
    != certification of every participant-maintained claim

Signing Node signature
    != certification of every participant-maintained claim
~~~

The source/provenance class of each broader claim remains governed by its own published policy.

## Exact issuance-record binding

After generic signed-history verification:

~~~text
record_sha256 =
    SHA-256(exact complete COSE_Sign1 record bytes)
~~~

The type-specific verifier requires:

~~~text
record_sha256
    == matched manifest participant.issuance_record_sha256
~~~

A semantically equivalent body is not interchangeable.

A re-encoding is not interchangeable.

A second signature over the same semantic content is not interchangeable.

The Epoch Manifest binds one exact signed issuance record to the participant descriptor.

## Accepted-history requirement

The participant-issuance record belongs to:

~~~text
history_link.stream = "accepted"
~~~

Its authenticated predecessor relationship must satisfy the accepted-history chain.

For genesis:

~~~text
predecessor_record_sha256 = null
~~~

For a successor:

~~~text
predecessor_record_sha256 =
    SHA-256(exact preceding accepted-history record bytes)
~~~

The exact issuance record must lie on the selected accepted-history branch ending at:

~~~text
manifest.history.accepted_history_head_sha256
~~~

A valid signed issuance record stored elsewhere is insufficient.

A valid signed fork is insufficient.

## Authority-context binding

For the same accepted Epoch Manifest, the record must satisfy:

~~~text
record.hoa_root_id
    == manifest.hoa_root_id

record.epoch_sequence
    == manifest.epoch_sequence

record.ceremony_record_sha256
    == manifest.ceremony.ceremony_record_sha256
~~~

The participant issuance therefore belongs to one exact HOA root and authority epoch without introducing an Epoch Manifest hash cycle.

## What the issuance record authorizes

Successful type-specific verification means:

~~~text
this exact accepted epoch
contains this exact participant identity
with this exact participant public key
and this exact standing-record reference
through this exact signed issuance record
with this explicit issuing-operator provenance
~~~

It does not mean:

- every claimed civic affordance is true;
- every relationship tuple is operator-certified;
- standing can no longer expire;
- the participant remains current in later epochs;
- the participant key is permanent;
- the operator owns the HOA Civic identity;
- possession of the participant device proves present standing.

## Current participation and expiration

Current participant authority is not permanent merely because the historical issuance record remains valid.

Where the applicable profile requires bounded participation, the standing layer determines whether the standing remains current.

For the Kane profile, expiration of the required participation interval without renewal ends active participation even though the historical issuance record remains verifiable.

Historical preservation therefore means:

~~~text
record remains evidence of what was issued
~~~

not:

~~~text
participant remains current forever
~~~

## Renewal and reissuance

A later renewal, correction, key replacement, standing change, or appliance replacement does not rewrite this signed record.

The prior record remains historical evidence.

The applicable process creates new authority material.

If current participant/key/standing membership changes require a successor epoch, the new Epoch Manifest contains the new participant descriptor and new exact issuance-record identity.

The old participant private key need not be transferred into the successor.

## Participant key loss

Loss of one participant private key does not destroy the HOA Civic Identity.

The surviving current participant replicas retain the complete authenticated authority state.

Replacement of the lost participant key follows the applicable standing/governance/issuance process and, where required, a successor epoch.

The architecture does not recover the lost private key.

## Participant record versus device

The manifest participant identity and issuance record are not device serializations.

A physical reference appliance may carry or use the participant key and replicated authority state, but:

~~~text
participant identity
    != ESP32 serial number

participant identity
    != MAC address

participant identity
    != appliance issuance reference
~~~

A later appliance replacement may preserve the participant lineage while changing hardware.

The broader Civic issuance model may record that appliance transition separately.

## Authority-state reconstruction requirement

A current participant replica must preserve enough authenticated material to reconstruct and verify current authority.

Accordingly, any standing record required to establish current participant validity is authority-required content.

It must not exist only in:

- operator memory;
- a private SaaS account;
- an inaccessible portal;
- an ephemeral database row;
- an unverified filesystem path.

If the standing record is external to the history stream, its exact bytes must be retained by the authority-state replication/object-retention mechanism under its SHA-256 identity.

Loss of required standing bytes makes reconstruction visibly incomplete.

## Failure conditions

This record fails type-specific verification if any of the following is true:

- `record_type` is not the exact v1 value;
- authenticated history stream is not `accepted`;
- signer kind is neither `participant` nor `signing_node`;
- body fields differ from the exact v1 schema;
- participant identity is not exactly 32 bytes;
- participant key ID is not exactly 32 bytes;
- participant public key is not the accepted 65-byte P-256 representation;
- participant public-key SHA-256 does not equal the participant key ID;
- no manifest participant matches the body participant identity;
- more than one manifest participant matches that identity;
- body key differs from the matched manifest participant key;
- body standing-record identity differs from the matched manifest participant standing-record identity;
- body issuing-operator identity differs from `manifest.operator.participant_record_sha256`;
- participant signer is not the issuing operator;
- verified signer key disagrees with the generic signed-history result;
- record HOA root differs from the manifest HOA root;
- record epoch differs from the manifest epoch;
- ceremony context differs from the manifest ceremony context;
- exact record identity differs from the matched participant's `issuance_record_sha256`;
- required standing bytes are missing or corrupt;
- standing semantic verification fails;
- generic COSE/signature verification fails;
- accepted-history predecessor linkage fails;
- accepted-history final-head verification fails.

Failures are preserved as Diagnostics evidence rather than repaired heuristically.

## Verification order

After generic signed-history verification succeeds, the type-specific verifier performs:

1. require exact `record_type`;
2. require authenticated stream `accepted`;
3. require signer kind `participant` or `signing_node`;
4. validate exact body schema;
5. validate participant identity;
6. locate exactly one matching current manifest participant;
7. validate participant public-key representation;
8. derive and verify participant key identifier;
9. require body key ID/public key to equal the manifest participant key;
10. require body standing-record identity to equal the manifest participant standing-record identity;
11. require issuing-operator identity to equal the manifest operator participant identity;
12. if participant-signed, require the signer participant to be that issuing operator;
13. require verified signer key to agree with the generic signed-history result;
14. require HOA root, epoch, and ceremony context to match the manifest;
15. require exact record SHA-256 to equal the matched participant's `issuance_record_sha256`;
16. require the record to lie on authenticated accepted history;
17. require the selected accepted-history chain to terminate at the manifest head;
18. independently resolve and verify the standing record under the applicable source-derived standing contract.

Only after both issuance and standing verification succeed may the descriptor be treated as a valid current participant relationship for that accepted epoch.

## Implementation boundary

The first implementation should enforce only the invariants frozen by this document.

It should not yet attempt to serialize every field from the broader `CIVIC_ISSUANCE_RECORD.md`.

That broader record will be informed by real HOA deployment.

The minimum authority contract here is intentionally small enough to test in practice while still preserving:

~~~text
participant identity
key attribution
standing separation
operator provenance
accepted-history placement
exact manifest binding
reconstructability
~~~

## Production boundary

This document defines semantics only.

It does not:

- define a universal SASE workflow;
- define a universal standing schema;
- define a universal issuance ceremony;
- serialize every broader participant claim;
- generate production Civic keys;
- enable production signing;
- mutate `annales`;
- create a Civic Signing Node service;
- change Firmware Release Authority;
- change participant devices;
- change the accepted cryptographic profile.

Fixture-only cryptographic work remains the implementation boundary until a later explicit production-signing decision.
