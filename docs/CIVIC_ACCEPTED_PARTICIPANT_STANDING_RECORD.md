# Civic Accepted Participant Standing Record

## Status

Architecture contract. Documentation only.

This document defines the minimum type-specific meaning of:

~~~text
manifest.participants[].standing_record_sha256
~~~

for one current participant in an accepted Civic Epoch Manifest.

It does not define the complete broader Civic relationship snapshot, every possible civic affordance, a universal identity credential, or a production signing workflow.

It is subordinate to:

- `docs/CIVIC_EPOCH_MANIFEST_FORMAT.md`;
- `docs/CIVIC_CRYPTOGRAPHIC_BASELINE.md`;
- `docs/CIVIC_HISTORY_HEAD_SEMANTICS.md`;
- `docs/CIVIC_SIGNED_HISTORY_RECORD_ENVELOPE.md`;
- `docs/CIVIC_ACCEPTED_PARTICIPANT_ISSUANCE_RECORD.md`;
- `docs/CIVIC_PARTICIPATION_RENEWAL.md`;
- `docs/CIVIC_RELATIONSHIP_TUPLE.md`;
- `docs/CIVIC_AFFORDANCE_AUTHORITY_CONTRACT.md`;
- `docs/CIVIC_SAME_AND_EQUAL_POLICY.md`;
- `docs/CIVIC_PARTICIPANT_AUTHORITY_STATE_RECONSTRUCTION.md`;
- `docs/HOA_GOVERNING_SOURCE_INHERITANCE.md`.

This contract does not enable production signing.

## Purpose

The Epoch Manifest already names one exact standing record for every current participant:

~~~text
{
  "participant_record_sha256": bytes(32),
  "participant_key_id": bytes(32),
  "participant_public_key": bytes(65),
  "standing_record_sha256": bytes(32),
  "issuance_record_sha256": bytes(32)
}
~~~

The accepted participant-issuance record proves which standing-record identity was relied upon when the participant/key tuple was admitted.

It deliberately does not define whether that standing itself is sufficient.

This document supplies that missing semantic layer.

The standing record answers:

~~~text
which exact participant is the subject?

under which exact governing profile does the standing have meaning?

which profile-defined standing class is asserted?

what bounded currentness interval applies?

what voluntary-participation state is required by this profile?

who is responsible for the qualification assertion?

which exact evidence objects are authority-required?

which supplementary evidence identities are merely retained for diagnostics?

which current operator recorded the bounded standing determination?

which exact signed accepted-history record expresses that determination?
~~~

## Fundamental distinctions

The v1 design preserves these distinctions:

~~~text
standing
    != issuance
    != participant-maintained claims
    != operator certification of every fact
    != Epoch Manifest membership by itself
~~~

More precisely:

~~~text
standing record
    -> why the participant qualifies under the applicable profile

issuance record
    -> which participant/key/standing tuple was admitted

Epoch Manifest participant descriptor
    -> which tuple the accepted epoch currently names

participant-maintained claim
    -> an assertion whose factual responsibility remains with the participant
       unless a published policy assigns responsibility elsewhere
~~~

A valid standing record does not by itself admit a participant into an epoch.

A valid issuance record does not repair invalid standing.

A cryptographically valid Epoch Manifest can still expose a participant descriptor whose referenced standing is expired, missing, corrupted, or semantically insufficient at a later evaluation time.

That disagreement is Diagnostics evidence.

It must not be silently normalized.

## Standing is not a universal identity document

The standing record is intentionally narrow.

It identifies the minimum profile-defined basis by which one participant qualifies for the current Civic authority relationship.

It must not become a canonical container for:

- legal name;
- complete postal address history;
- email identity;
- government identifier;
- every Civic Relationship Tuple;
- every property or parcel relationship;
- every court or records-request relationship;
- every witness claim;
- every expert credential;
- every private evidence object;
- every broader appliance issuance field.

Those may exist in other Civic records or evidence objects.

The standing record carries only what is necessary to establish and reconstruct the participant's accepted standing under the governing profile.

## Record type

The exact v1 `record_type` is:

~~~text
kane-civic-accepted-participant-standing-v1
~~~

A verifier must not treat another record type as equivalent.

## Signed-history representation

The standing record uses the generic Civic signed-history envelope defined by:

~~~text
docs/CIVIC_SIGNED_HISTORY_RECORD_ENVELOPE.md
~~~

For this type:

~~~text
history_link.stream = "accepted"
~~~

The exact standing-record identity is:

~~~text
standing_record_sha256 =
    SHA-256(exact complete COSE_Sign1 history-record bytes)
~~~

It is not the hash of:

- only the standing body;
- a JSON projection;
- an evidence file;
- a database row;
- an unsigned sidecar;
- a filesystem path.

The signed record must lie on the selected accepted-history branch ending at:

~~~text
manifest.history.accepted_history_head_sha256
~~~

A valid signed standing record stored outside that selected branch is insufficient.

A valid signed fork is insufficient.

## Authority-context binding

The generic history envelope already binds the record to:

~~~text
hoa_root_id
epoch_sequence
ceremony_record_sha256
~~~

For the matching accepted Epoch Manifest:

~~~text
record.hoa_root_id
    == manifest.hoa_root_id

record.epoch_sequence
    == manifest.epoch_sequence

record.ceremony_record_sha256
    == manifest.ceremony.ceremony_record_sha256
~~~

This gives the standing record one exact HOA Civic root and one exact accepted authority epoch without creating an Epoch Manifest hash cycle.

## Body schema

The v1 body contains exactly:

~~~text
{
  "participant_record_sha256": bytes(32),

  "governing_profile": {
    "profile_id": text,
    "profile_sha256": bytes(32),
    "source_set_sha256": bytes(32)
  },

  "standing_class": text,

  "valid_from_ms": uint,
  "valid_until_ms": uint / null,

  "participation": {
    "required": bool,
    "policy_id": text / null,
    "valid_from_ms": uint / null,
    "valid_until_ms": uint / null,
    "authority_evidence": [
      * {
          "sha256": bytes(32),
          "byte_length": uint,
          "media_type": text,
          "semantic_role": text
        }
    ],
    "supplementary_evidence": [
      * {
          "sha256": bytes(32),
          "byte_length": uint,
          "media_type": text,
          "semantic_role": text
        }
    ]
  },

  "qualification": {
    "path_id": text,
    "claim_responsibility":
        "participant_claimed"
      | "operator_attested"
      | "other_published_attestation",

    "authority_evidence": [
      * {
          "sha256": bytes(32),
          "byte_length": uint,
          "media_type": text,
          "semantic_role": text
        }
    ],

    "supplementary_evidence": [
      * {
          "sha256": bytes(32),
          "byte_length": uint,
          "media_type": text,
          "semantic_role": text
        }
    ]
  },

  "recording_operator_participant_record_sha256": bytes(32)
}
~~~

Unknown body fields are invalid in v1.

Private key material is forbidden.

The two evidence arrays in each section are sorted bytewise ascending by `sha256`.

Duplicate evidence identities within one array are invalid.

The same evidence object may appear in more than one semantic section only when the governing profile gives it more than one explicitly defined role.

## Participant binding

The body names exactly one participant:

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

That descriptor is the participant whose standing is being evaluated.

The participant identity remains opaque.

This contract does not derive it from:

- legal name;
- postal address;
- email address;
- device serial number;
- MAC address;
- IP address;
- hostname;
- operator account;
- Signing Node key.

## Exact standing-record binding

After generic signed-history verification:

~~~text
record_sha256 =
    SHA-256(exact complete COSE_Sign1 record bytes)
~~~

The type-specific verifier requires:

~~~text
record_sha256
    == matched manifest participant.standing_record_sha256
~~~

A semantically equivalent re-encoding is not interchangeable.

A second signature over equivalent content is not interchangeable.

The Epoch Manifest binds one exact signed standing record.

## Governing-profile binding

The body repeats the exact governing-profile descriptor needed to interpret the standing:

~~~text
record.body.governing_profile.profile_id
    == manifest.governing_profile.profile_id

record.body.governing_profile.profile_sha256
    == manifest.governing_profile.profile_sha256

record.body.governing_profile.source_set_sha256
    == manifest.governing_profile.source_set_sha256
~~~

This redundancy is intentional.

It prevents a standing record created under one profile or source set from being silently reinterpreted under another.

Where exact profile or source bytes are required to interpret or verify standing, those bytes are authority-required content and must be retained through the manifest/object-store/reconstruction model.

A URI or later web lookup is not a substitute for required exact bytes.

## standing_class

`standing_class` is a nonempty profile-defined text identifier.

It names the bounded qualification class that makes the participant relevant to this Civic authority domain.

Examples of profile-defined meanings may include:

~~~text
current qualifying condominium unit owner in this HOA root

current qualifying HOA member in the applicable role class

another explicitly published Same-and-Equal participant class
~~~

Those examples are semantic illustrations, not universal identifiers frozen by this document.

The meaning of `standing_class` comes from the exact governing profile.

Therefore:

~~~text
same standing_class text
    under different profile_sha256
    != automatically same standing
~~~

The standing class must not silently absorb every other civic relationship the participant may claim.

## Source-derived meaning

For an HOA profile, substantive standing meaning is derived in the established order:

~~~text
applicable statute
    -> applicable condominium instruments
    -> published Civic profile
    -> Civic standing verification
~~~

Civic does not invent ownership, membership, voting, or other legal status.

It records a profile-defined standing assertion and verifies the evidence/provenance conditions that the profile says are necessary.

A Civic profile may instrument a source-derived rule.

It must not represent its own instrumentation as though the instrumentation itself were the underlying legal source.

## Qualification

The `qualification` map identifies the profile-defined qualification path used for this standing record.

### path_id

`path_id` is a nonempty text identifier whose meaning is defined by the exact governing profile.

Examples may distinguish:

- participant claim with required evidence;
- association-record evidence;
- public-record evidence;
- multi-source evidence;
- another explicitly published qualification path.

The standing record does not define those paths ad hoc.

### claim_responsibility

`claim_responsibility` identifies who bears responsibility for the substantive qualification assertion represented by this standing record.

The v1 values are:

~~~text
participant_claimed
operator_attested
other_published_attestation
~~~

Their meanings are:

~~~text
participant_claimed
    -> the participant remains responsible for the substantive claim;
       recording or signing the standing record does not transfer factual
       responsibility to the operator

operator_attested
    -> the governing profile explicitly makes the current operator the
       attesting authority for this qualification fact

other_published_attestation
    -> the governing profile identifies another attestation source or
       evidence discipline whose exact supporting object(s) are referenced
~~~

The default Kane principle remains:

~~~text
operator records the standing determination
    !=
operator certifies every participant-maintained claim
~~~

A profile must explicitly authorize `operator_attested` for a substantive qualification fact.

The implementation must not infer it merely because the operator or Signing Node signed the record.

## Evidence identity

Each evidence reference contains:

~~~text
sha256
byte_length
media_type
semantic_role
~~~

The SHA-256 is the content identity.

The other fields describe the exact referenced bytes and their intended standing role.

A filename, portal URL, database identifier, account name, or storage path is not evidence identity.

If provenance needed to interpret an evidence object is itself authority-critical, that provenance must be contained in authenticated/retained Civic material or in another exact authority-required referenced object.

It must not exist only in operator memory.

## Authority-required evidence

`authority_evidence` contains only evidence objects whose exact bytes are necessary for a verifier to establish the accepted standing relationship under the governing profile.

Every authority-evidence reference must have exact matching retained bytes available to the authority-state reconstruction mechanism.

Where those bytes are external to the signed history record itself, they must be represented as authority-required content through the Epoch Manifest/object-index/object-store model.

Missing, corrupt, wrong-length, or wrong-hash authority evidence causes standing verification to fail.

This is intentional.

A participant replica is not complete merely because it retains the evidence hash while losing bytes that are necessary to verify standing.

## Supplementary evidence

`supplementary_evidence` preserves identities of evidence associated with the standing determination but not required to reconstruct and verify the accepted authority relationship.

Examples may include additional corroborating material retained for later Diagnostics.

Supplementary evidence:

- may be locally absent from a participant authority-state replica;
- does not become authority-required merely because its hash is mentioned;
- must not be necessary for the standing verifier to reach a successful result;
- may produce a Diagnostics indication when unavailable if a diagnostic policy cares about it.

This preserves the distinction:

~~~text
evidence associated with standing
    !=
evidence required for authority reconstruction
~~~

The classification must follow the governing profile.

The implementation must not downgrade required evidence to supplementary merely because the bytes are inconvenient to retain.

## Voluntary participation

The `participation` map represents the profile-defined voluntary-participation condition separately from substantive civic qualification.

This separation is mandatory.

It prevents a participation mechanism from being mistaken for the underlying legal or civic status.

### required

If:

~~~text
participation.required = false
~~~

then:

~~~text
policy_id = null
valid_from_ms = null
valid_until_ms = null
authority_evidence = []
supplementary_evidence = []
~~~

The governing profile must permit participation to be unnecessary for that standing class.

If:

~~~text
participation.required = true
~~~

then `policy_id`, `valid_from_ms`, and the profile-required participation semantics must be present.

### Kane SASE profile

For the current Kane participation model, the governing profile defines a fresh Self-Addressed Stamped Envelope as the voluntary initiation or renewal act.

Conceptually:

~~~text
fresh accepted SASE
    -> operator-attested voluntary participation
    -> bounded participation interval
~~~

The standing record stores the resulting participation interval and the profile-defined participation-policy identifier.

It does not define:

~~~text
SASE is required by condominium law
~~~

or:

~~~text
SASE is required by every Civic deployment
~~~

SASE is a Kane Civic participation mechanism.

The substantive standing class remains source-derived.

### Operator-attested participation

For the Kane SASE profile, the current operator may authoritatively record the bounded fact:

~~~text
this participant voluntarily initiated or renewed
through the required SASE process
and this participation interval resulted
~~~

That is distinct from certifying the truth of every substantive qualification claim.

The operator does not need to continuously investigate participant-maintained claims merely because the operator attests the SASE participation event.

### Participation evidence

A governing profile may permit the signed standing record and explicit operator provenance to constitute the required participation attestation without requiring a scanned envelope or other raw physical artifact to become authority-required content.

If the profile requires additional exact evidence objects, those objects belong in:

~~~text
participation.authority_evidence
~~~

Additional non-required corroboration belongs in:

~~~text
participation.supplementary_evidence
~~~

The architecture therefore does not force every physical SASE artifact into every participant replica.

## Temporal semantics

The standing record contains:

~~~text
valid_from_ms
valid_until_ms
~~~

These describe the interval in which this standing assertion is semantically current under the governing profile.

The interval is half-open:

~~~text
valid_from_ms <= evaluation_time_ms < valid_until_ms
~~~

when `valid_until_ms` is non-null.

If `valid_until_ms = null`, the governing profile must explicitly permit open-ended currentness subject to supersession or another published validity rule.

The standing record does not create an independent trusted-time oracle.

Its time values are authenticated assertions interpreted together with the profile and accepted authority history.

## Participation interval and overall standing interval

When participation is required:

~~~text
participation.valid_from_ms
participation.valid_until_ms
~~~

describe the bounded participation interval.

The overall standing interval must not claim currentness outside a required participation interval.

Therefore, for a required bounded participation interval:

~~~text
valid_from_ms >= participation.valid_from_ms
~~~

and when the participation end is non-null:

~~~text
valid_until_ms != null

valid_until_ms <= participation.valid_until_ms
~~~

A profile may impose a shorter overall standing interval because some other required qualification expires sooner.

The implementation must not extend standing merely because the SASE interval remains active.

## Evaluation time

Standing verification is explicitly time-parameterized.

Conceptually:

~~~text
verify_standing(record, manifest, evaluation_time_ms)
~~~

Two evaluation contexts are important.

### Epoch-effective evaluation

To determine whether the standing record was current when the Epoch Manifest became effective:

~~~text
evaluation_time_ms = manifest.effective_time_ms
~~~

A record outside its valid interval fails standing-currentness at that epoch effective time.

### Present or later evaluation

A later verifier may evaluate the same immutable standing record at a later time.

A standing record that was current at the epoch effective time may later be expired.

That does not alter the historical record or invalidate its signature.

Therefore:

~~~text
historically valid standing
    != necessarily current standing now
~~~

This is a deliberate Diagnostics surface.

## Manifest membership does not override expiration

The Epoch Manifest is an authenticated positive statement of the participant set selected for that epoch.

It is not a perpetual override of standing validity.

Therefore this state is representable:

~~~text
participant still appears in accepted Epoch Manifest
    +
standing record verifies cryptographically
    +
standing interval has expired at evaluation time
    =
accepted historical membership remains intact
but present standing verification fails
~~~

The verifier must expose that discrepancy.

It must not:

- silently extend the standing interval;
- silently remove the participant from historical records;
- rewrite the manifest;
- fabricate a renewal;
- treat device possession as renewal.

## Renewal, correction, and supersession

A standing record is immutable.

Renewal, correction, qualification change, standing-class change, or changed evidence creates new authority material.

For Kane participation, a new accepted SASE produces a new bounded participation determination.

If the current participant descriptor must reference the renewed standing record, a successor accepted Epoch Manifest carries the new:

~~~text
standing_record_sha256
~~~

The previous standing record remains historical evidence.

Expiration does not delete it.

A later record must not mutate its validity interval retroactively merely to make current state convenient.

## Recording operator

The body contains:

~~~text
recording_operator_participant_record_sha256
~~~

For v1 it must equal:

~~~text
manifest.operator.participant_record_sha256
~~~

This identifies the current participant acting in the bounded operator role when the standing determination was recorded.

The operator is not:

- the permanent HOA Civic identity;
- the Signing Node;
- automatically a superior participant;
- automatically the factual guarantor of every substantive claim.

The operator may also be the subject participant if the manifest says so.

That fact does not relax the evidence/profile rules.

## Permitted signer kinds

The permitted generic signer kinds are:

~~~text
participant
signing_node
~~~

No other signer kind is valid.

### Participant signer

If:

~~~text
record.signer.kind = "participant"
~~~

the signer must be the current manifest operator:

~~~text
record.signer.participant_record_sha256
    == record.body.recording_operator_participant_record_sha256

record.body.recording_operator_participant_record_sha256
    == manifest.operator.participant_record_sha256
~~~

The generic history verifier already verifies that participant signature against the accepted epoch participant key.

The subject participant may not unilaterally create an accepted standing record merely by signing it with the subject key unless that participant is also the current manifest operator.

Participant-maintained claims remain attributable as participant claims through the body/provenance rules; they do not become accepted standing solely through a self-signature.

### Signing Node signer

If:

~~~text
record.signer.kind = "signing_node"
~~~

the generic history verifier requires the signer key to equal the accepted Epoch Manifest Signing Node key and verifies the signature.

The body must still require:

~~~text
record.body.recording_operator_participant_record_sha256
    == manifest.operator.participant_record_sha256
~~~

The Signing Node is the cryptographic signer for the accepted standing record.

The current operator remains the recorded operator provenance.

The Signing Node signature does not certify every participant-maintained fact.

## Cryptographic signer versus semantic attester

The standing design separates:

~~~text
who cryptographically signed the exact accepted record?
~~~

from:

~~~text
who bears responsibility for a particular assertion?
~~~

and from:

~~~text
which evidence objects support the profile-defined qualification?
~~~

For example, one Kane standing record may have:

~~~text
cryptographic signer:
    authorized Signing Node

recording operator:
    current manifest operator

participation fact:
    operator-attested SASE renewal

substantive ownership claim:
    participant_claimed

supporting authority evidence:
    exact profile-required evidence objects
~~~

Those roles must not be collapsed.

## Accepted-history requirement

The standing record is an accepted-history authority record.

Its authenticated predecessor relationship must satisfy the accepted-history chain.

For genesis:

~~~text
predecessor_record_sha256 = null
~~~

For every successor:

~~~text
predecessor_record_sha256 =
    SHA-256(exact preceding accepted-history record bytes)
~~~

The exact standing record must be reachable on the selected linear accepted-history branch whose final record equals:

~~~text
manifest.history.accepted_history_head_sha256
~~~

A signature alone is insufficient.

A hash reference alone is insufficient.

Accepted branch membership is required.

## Relationship to participant issuance

Standing and issuance remain separate records.

The required exact bindings are:

~~~text
manifest participant.standing_record_sha256
    == exact accepted standing-record hash

manifest participant.issuance_record_sha256
    == exact accepted issuance-record hash

issuance.body.standing_record_sha256
    == manifest participant.standing_record_sha256
~~~

The standing verifier does not verify participant issuance.

The issuance verifier does not reinterpret standing semantics.

A higher-level current-participant verification composes the two results.

Conceptually:

~~~text
verified standing at evaluation time
    +
verified participant issuance
    +
both exact manifest descriptor bindings
    +
accepted history
    +
accepted Epoch Manifest
    =
verified participant authority relationship
~~~

## No circular self-authorization

The standing record does not derive authority merely from its own presence.

The profile and required source/evidence relationships must verify independently of the record's signature.

Therefore:

~~~text
valid standing-record signature
    != sufficient standing

manifest references standing record
    != sufficient standing

operator recorded standing
    != sufficient standing
~~~

The type-specific verifier must apply the profile, temporal, evidence, and provenance rules in addition to cryptographic verification.

## Same-and-Equal relationship

The Epoch Manifest defines its participant array as current Same-and-Equal participant descriptors.

The standing record provides the participant-specific input needed for that claim.

The profile-defined `standing_class`, qualification path, state/currentness rules, and governing profile determine whether participants are comparable under the applicable Same-and-Equal policy.

The standing verifier does not create a universal equality relation.

A later Same-and-Equal verifier may compare verified standings under the published policy.

Two participants may still be Same-and-Equal for one civic purpose and not another.

## Authority-state reconstruction

The exact accepted standing record is authority-required content.

Because it is an accepted-history record, its exact signed bytes are retained as part of the accepted history required by reconstruction.

Every `authority_evidence` object whose bytes are necessary to verify standing is also authority-required reconstruction content.

Where such evidence is external to history, the replica must retain the exact bytes under their SHA-256 identity through the object-store/required-object mechanism.

The baseline 1-of-N property therefore requires that any one surviving current participant replica can supply enough authenticated material to verify:

~~~text
the accepted manifest lineage
the accepted standing record
the governing profile/source material required to interpret it
all authority-required standing evidence
the accepted issuance record
the accepted history linkage
~~~

Supplementary evidence is excluded from this mandatory set unless another accepted authority rule independently makes it required.

## Missing authority objects are visible failure

If the standing record requires an evidence object and the replica contains only its hash but not the exact required bytes, reconstruction is incomplete.

The implementation must not:

- substitute a later download without verifying exact identity;
- accept a filename as identity;
- trust an inaccessible portal reference;
- silently omit the evidence check;
- downgrade the object to supplementary after the fact.

This failure is useful operational Diagnostics evidence.

## Verification order

A future type-specific verifier should apply the standing contract in this order:

1. verify the generic signed-history envelope;
2. require exact `record_type`;
3. require authenticated `history_link.stream = "accepted"`;
4. require exact v1 body fields and field types;
5. resolve exactly one participant descriptor by `participant_record_sha256`;
6. require exact `record_sha256 == manifest participant.standing_record_sha256`;
7. require body governing-profile descriptor to equal the manifest governing profile;
8. require `standing_class` and qualification path to be recognized by that exact profile;
9. validate recording-operator provenance;
10. validate the permitted signer case;
11. validate participation semantics required by the profile;
12. validate qualification claim responsibility;
13. validate all authority-evidence descriptors and required exact bytes;
14. preserve supplementary evidence as non-required references;
15. validate overall and participation temporal relationships;
16. evaluate currentness at the supplied `evaluation_time_ms`;
17. require the exact signed standing record to lie on the selected accepted-history branch;
18. return the verified standing result without performing participant-issuance verification.

Failure at any required step fails standing verification for that evaluation context.

## Failure conditions

The standing record fails type-specific verification if any required condition is not satisfied.

Examples include:

- wrong `record_type`;
- wrong history stream;
- unknown body field;
- missing required body field;
- malformed participant identity;
- participant not present exactly once in the manifest;
- record hash differs from `manifest.participants[].standing_record_sha256`;
- governing-profile mismatch;
- unknown standing class under the exact profile;
- unknown qualification path;
- unpermitted claim-responsibility value;
- recording operator differs from the manifest operator;
- participant signer is not the current manifest operator;
- Signing Node signer does not verify through the generic envelope;
- profile-required participation is missing;
- participation fields are populated when `required = false`;
- invalid or impossible temporal interval;
- overall standing interval exceeds a required participation interval;
- standing is outside its valid interval at the requested evaluation time;
- missing authority-required evidence bytes;
- authority-evidence hash or byte length mismatch;
- authority evidence fails profile-specific interpretation;
- required governing-profile/source bytes are unavailable;
- exact standing record is not on the selected accepted-history branch.

Failures are explicit.

They are not silently repaired.

## What successful verification means

Successful type-specific standing verification at evaluation time `t` means:

~~~text
this exact accepted standing record
for this exact participant
under this exact HOA root and epoch
uses this exact governing profile/source context
asserts this profile-defined standing class
through this qualification path and provenance
has all authority-required evidence available and valid
has the required voluntary-participation state
is current at evaluation time t
was recorded with explicit current-operator provenance
and lies on the selected accepted-history branch
~~~

It does not mean:

- every participant-maintained claim is objectively true for all purposes;
- the operator guarantees every evidence source;
- the Signing Node is the legal authority for ownership;
- SASE is a universal legal requirement;
- the participant is permanently current;
- the participant is current at a different evaluation time;
- the standing alone proves accepted participant issuance;
- the standing is a universal person identity;
- the standing automatically grants a vote or other legal right.

## Diagnostics consequences

The architecture intentionally makes several disagreement states visible.

Examples:

~~~text
manifest lists participant
but standing expired

issuance verifies
but standing authority evidence is missing

standing record verifies cryptographically
but qualification path is not valid under the governing profile

operator recorded participant_claimed qualification
but supplementary evidence later contradicts the claim

historical standing was valid
but present standing is no longer current
~~~

These are not conditions to normalize away.

They are inspectable Civic Diagnostics inputs.

## Production-signing boundary

This architecture does not enable production signing.

Current restrictions remain:

~~~text
production_signing_enabled = false
production_key_created = false
annales_mutated = false
~~~

No Civic production private key is created by this step.

No Civic Signing Node is activated on `annales`.

Fixture-only signing remains the current implementation boundary.

## Decision summary

Civic participant standing v1 is now architecturally defined as:

~~~text
source-derived/profile-defined standing meaning
    +
explicit participant subject
    +
explicit standing class
    +
explicit qualification path and claim responsibility
    +
separate profile-defined voluntary participation
    +
bounded temporal currentness
    +
authority-required evidence identities and retained bytes
    +
supplementary non-authority evidence identities
    +
explicit current-operator provenance
    +
permitted participant-operator or Signing Node signature
    +
accepted-history membership
    +
exact manifest standing_record_sha256 binding
~~~

The record is independently verifiable from participant issuance.

Standing verification is explicitly time-dependent.

Historical validity is preserved after expiration.

Current Epoch Manifest membership does not silently override expired or insufficient standing.

Only evidence required to reconstruct and verify accepted authority becomes mandatory replicated authority content.

## Next bounded step

Review this architecture before implementation.

Do not implement the standing verifier in the same step.

After architecture acceptance, the next bounded repository step may implement the type-specific verifier against this contract, followed separately by focused tests and CT102 acceptance.
