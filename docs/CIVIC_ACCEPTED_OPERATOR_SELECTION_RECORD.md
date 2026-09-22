# Civic Accepted Operator Selection Record

## Status

Architecture contract for the type-specific Civic accepted-history record that binds one Epoch Manifest operator to the evidence of that operator's selection.

This document defines only the invariants Civic must be able to verify.

It does not define how an HOA selects, elects, appoints, rotates, replaces, or otherwise chooses an operator.

Those mechanics remain source-derived and profile-specific.

This document is subordinate to:

- `docs/CIVIC_CRYPTOGRAPHIC_BASELINE.md`;
- `docs/CIVIC_EPOCH_MANIFEST_FORMAT.md`;
- `docs/CIVIC_HISTORY_HEAD_SEMANTICS.md`;
- `docs/CIVIC_SIGNED_HISTORY_RECORD_ENVELOPE.md`;
- `docs/CIVIC_PARTICIPANT_AUTHORITY_STATE_RECONSTRUCTION.md`;
- `docs/HOA_GOVERNING_SOURCE_INHERITANCE.md`;
- `docs/CIVIC_OPERATOR_PEER_SCRUTINY.md`.

This contract does not enable production signing.

## Existing operator invariants

The accepted Civic architecture already requires:

~~~text
operator is not a permanent administrator
operator must be an active participant
any eligible active participant may operate
operator authority is bounded by published procedure
operator election/selection rule is source-derived
exact election/selection rule is profile-specific
~~~

Epoch Manifest v1 already contains:

~~~text
operator = {
  "participant_record_sha256": bytes(32),
  "selection_record_sha256": bytes(32)
}
~~~

The manifest validator already requires:

~~~text
manifest.operator.participant_record_sha256
    belongs to manifest.participants
~~~

This record contract defines the meaning of:

~~~text
manifest.operator.selection_record_sha256
~~~

without defining the selection ceremony itself.

## Purpose

The record must make it possible to verify that:

~~~text
1. one exact current participant is named as operator;
2. one exact accepted-history record describes that selection;
3. the record is cryptographically attributable;
4. the record identifies any selection evidence it relies upon;
5. that evidence remains subordinate to the applicable governing sources;
6. the Epoch Manifest explicitly binds to the exact record;
7. the operator role does not become the HOA Civic Identity.
~~~

The record does not create selection authority merely because it is signed.

## Record type

The exact v1 `record_type` is:

~~~text
kane-civic-accepted-operator-selection-v1
~~~

A verifier must not treat another record type as equivalent.

## Required generic-envelope values

The record uses the generic Civic signed-history envelope.

For this type:

~~~text
history_link.stream = "accepted"
~~~

The signer may be either:

~~~text
signer.kind = "participant"
~~~

or:

~~~text
signer.kind = "signing_node"
~~~

The generic envelope resolves and verifies either signer against the accepted Epoch Manifest for the record's authority-context tuple.

No other signer kind is valid.

## Why signer identity does not define selection authority

The signer authenticates the exact operator-selection record.

The signer does not become the electorate, appointing authority, board, association, statute, bylaws, or governing process merely by signing.

Therefore:

~~~text
record signer
    != selection authority
~~~

and:

~~~text
valid signature
    != valid operator selection
~~~

A participant signer means only that one current participant authenticated the exact record.

A Signing Node signer means only that the accepted epoch Signing Node authenticated the exact record.

Neither signature, standing alone, proves that the selected participant was properly chosen.

The source-derived governance layer decides that question.

This permits different owner-operators and governance profiles to use different legitimate procedures without changing the Civic record identity model.

## Body schema

The v1 body contains exactly:

~~~text
{
  "selected_participant_record_sha256": bytes(32),

  "selection_proof_sha256": [
    * bytes(32)
  ]
}
~~~

Unknown body fields are invalid in v1.

Private key material is forbidden.

## Selected participant binding

The record must satisfy:

~~~text
record.body.selected_participant_record_sha256
    == manifest.operator.participant_record_sha256
~~~

The selected participant identity must occur exactly once in:

~~~text
manifest.participants
~~~

The Epoch Manifest participant descriptor remains the authoritative current-epoch source for that participant's public key and other current participant references.

The operator-selection record does not duplicate the participant public key.

## Exact selection-record binding

After complete signed-record verification:

~~~text
record_sha256 =
    SHA-256(exact complete COSE_Sign1 record bytes)
~~~

The type-specific verifier requires:

~~~text
record_sha256
    == manifest.operator.selection_record_sha256
~~~

A semantically equivalent record, a re-encoding, or another signature over an equivalent body is not interchangeable.

The Epoch Manifest identifies one exact signed operator-selection record.

## Selection proof set

The body field:

~~~text
selection_proof_sha256
~~~

is a deterministic list of zero or more SHA-256 content identities.

If present, the values must be:

- exactly 32 bytes each;
- sorted by bytewise ascending value;
- duplicate-free.

Every listed selection-proof hash must also appear in:

~~~text
manifest.ceremony.governance_proof_sha256
~~~

Therefore:

~~~text
record.body.selection_proof_sha256
    subset-of
manifest.ceremony.governance_proof_sha256
~~~

The selection record may identify only the governance proofs relevant to operator selection rather than being forced to repeat unrelated ceremony evidence.

## Why the selection-proof array may be empty

Civic must not invent an election requirement where the applicable governing source does not require one.

An empty:

~~~text
selection_proof_sha256 = []
~~~

does not mean:

~~~text
the operator selection is valid without governance
~~~

It means only:

~~~text
this record identifies no separate proof objects beyond
the accepted ceremony/profile/governing-source context
~~~

The source-derived governance verifier must still decide whether the applicable governing sources and ceremony evidence are sufficient.

This preserves profile and owner-operator freedom without weakening verification.

## Selection evidence is not self-interpreting

A SHA-256 value establishes content identity.

It does not establish that the referenced content is:

- legally sufficient;
- procedurally sufficient;
- timely;
- signed by the correct electorate;
- supported by the required vote;
- consistent with bylaws;
- consistent with statute;
- consistent with the applicable Civic governing profile.

Those questions belong to the type-specific/source-derived governance layer.

Civic therefore separates:

~~~text
evidence identity
    from
evidence sufficiency
~~~

## Accepted-history requirement

An operator-selection record belongs to:

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

The record must lie on the selected accepted-history branch ending at:

~~~text
manifest.history.accepted_history_head_sha256
~~~

A valid signed record stored elsewhere is not enough.

A valid signed fork is not enough.

## Manifest relationship

For the same accepted Epoch Manifest, the verifier requires all of:

~~~text
record.hoa_root_id
    == manifest.hoa_root_id

record.epoch_sequence
    == manifest.epoch_sequence

record.ceremony_record_sha256
    == manifest.ceremony.ceremony_record_sha256

record.body.selected_participant_record_sha256
    == manifest.operator.participant_record_sha256

record.record_sha256
    == manifest.operator.selection_record_sha256
~~~

This binds the selected operator, the exact record, and the authority epoch together.

## Operator is not Civic Identity

Successful verification of this record means only:

~~~text
this accepted epoch names this participant as its operator
under the evidence and governing context associated with this selection record
~~~

It does not mean:

~~~text
operator identity == HOA Civic Identity
~~~

The stable HOA Civic identity remains independent of:

- the operator;
- the operator's participant key;
- the Signing Node;
- the Signing Node key;
- hostname;
- IP address;
- ESP32 serial number;
- physical device.

Operator transition therefore does not require transferring a permanent operator master key.

## Operator and Signing Node are separate roles

The accepted architecture currently permits the local Civic operator to own and fund the local Signing Node.

That operational relationship does not collapse the identities.

The operator-selection record binds:

~~~text
current participant -> operator role
~~~

The Signing Node authorization record binds:

~~~text
current Signing Node public key -> authorized node role
~~~

They are independent authority facts in the same accepted epoch.

A valid operator-selection record does not authorize a Signing Node key.

A valid Signing Node authorization record does not prove that the operator was validly selected.

## Signer cases

### Participant signer

For:

~~~text
signer.kind = "participant"
~~~

the generic history verifier already requires that the signer resolve to exactly one current participant in the referenced epoch and verifies the signature using that participant's public key.

The participant signer need not be the selected operator.

Requiring that relationship would impose an acceptance or self-attestation ceremony that the governing source may not require.

A participant signature therefore means only:

~~~text
this current participant authenticated these exact selection-record bytes
~~~

### Signing Node signer

For:

~~~text
signer.kind = "signing_node"
~~~

the generic verifier already requires the signer key to match the referenced Epoch Manifest Signing Node and verifies the signature under that key.

The Signing Node signature means only:

~~~text
the accepted epoch Signing Node authenticated these exact selection-record bytes
~~~

It does not mean the Signing Node chose the operator.

## No self-selection inference

The following reasoning is invalid:

~~~text
the selected participant signed the record
therefore the participant validly selected themself
~~~

The following is also invalid:

~~~text
the Signing Node signed the record
therefore the Signing Node validly appointed its operator
~~~

The signature proves attribution.

The selection proof and governing context establish or fail to establish selection authority.

## No mandatory election form

This contract deliberately does not require:

- paper ballots;
- electronic ballots;
- unanimous consent;
- majority vote;
- plurality vote;
- board resolution;
- meeting minutes;
- written consent;
- notarization;
- a particular notice period;
- a particular meeting platform;
- a particular software portal;
- a particular Signing Node workflow.

A governing profile may require one or more of these because the applicable statute or condominium instruments require them.

Civic itself does not invent the requirement.

## Selection mechanism freedom

Two participating HOAs may therefore produce records with identical Civic invariants while using different lawful procedures.

For example:

~~~text
HOA A
    -> source-derived meeting/election procedure
    -> proof objects
    -> accepted operator-selection record

HOA B
    -> source-derived written-consent procedure
    -> proof objects
    -> accepted operator-selection record
~~~

The procedure differs.

The Civic verification questions remain stable:

~~~text
who is selected?
what exact record says so?
who authenticated that record?
what evidence does it identify?
does the governing profile accept that evidence?
does the Epoch Manifest bind to that exact record?
is the record on accepted history?
~~~

## Replacement operator

A replacement operator is not created by editing the prior selection record.

The prior signed record remains historical evidence.

A valid replacement requires the applicable source-derived process and a new accepted authority-state relationship.

Where the change requires an epoch transition, the successor epoch records the new operator and exact new selection record.

The outgoing operator's private key is not required to transfer Civic identity.

## Cross-epoch rule

An operator-selection record binds only the operator named in its own accepted epoch.

Historical operator records remain verifiable.

They do not grant current operator authority in later epochs.

Therefore:

~~~text
historical operator status
    != current operator status
~~~

## Multiple-operator future compatibility

The wider Civic architecture may support multiple operators.

Epoch Manifest v1 currently contains one:

~~~text
operator
~~~

This v1 record therefore binds one manifest operator.

A future manifest/profile supporting multiple simultaneous operators may define a successor record type or extended manifest structure.

The v1 verifier must not infer multiple current operators from multiple valid selection records.

## Failure conditions

This record fails type-specific verification if any of the following is true:

- `record_type` is not the exact v1 value;
- authenticated history stream is not `accepted`;
- signer kind is neither `participant` nor `signing_node`;
- body fields differ from the exact v1 schema;
- selected participant identity is not exactly 32 bytes;
- selected participant does not equal `manifest.operator.participant_record_sha256`;
- selected participant is not exactly one current manifest participant;
- record HOA root differs from the manifest HOA root;
- record epoch differs from the manifest epoch;
- ceremony context differs from the manifest ceremony context;
- exact record identity differs from `manifest.operator.selection_record_sha256`;
- a selection-proof hash is malformed;
- selection-proof hashes are unsorted;
- selection-proof hashes contain duplicates;
- a selection-proof hash is absent from `manifest.ceremony.governance_proof_sha256`;
- generic COSE/signature verification fails;
- accepted-history predecessor linkage fails;
- accepted-history final-head verification fails;
- source-derived governance verification determines the selection evidence is insufficient.

Failures are preserved as Diagnostics evidence rather than repaired heuristically.

## Verification order

After generic signed-history verification succeeds, the type-specific verifier performs:

1. require exact `record_type`;
2. require authenticated stream `accepted`;
3. require signer kind `participant` or `signing_node`;
4. validate exact body schema;
5. validate selected participant identity;
6. require selected participant to equal the manifest operator participant identity;
7. require that identity to occur exactly once in current manifest participants;
8. require HOA root, epoch, and ceremony context to match the manifest;
9. require exact record SHA-256 to equal `manifest.operator.selection_record_sha256`;
10. validate sorted unique selection-proof hashes;
11. require each selection-proof hash to occur in the manifest ceremony governance-proof set;
12. require the record to lie on authenticated accepted history;
13. require the selected accepted-history chain to terminate at the manifest head;
14. pass the selection-proof identities and governing context to the source-derived governance verifier.

Only after the applicable governance verifier accepts the selection may the participant be treated as the authorized operator for that accepted epoch.

## Production boundary

This document defines semantics only.

It does not:

- define a universal operator election;
- define a universal ceremony;
- generate production Civic keys;
- enable production signing;
- mutate `annales`;
- create a Civic Signing Node service;
- change Firmware Release Authority;
- change participant devices;
- change the accepted cryptographic profile.

Fixture-only cryptographic work remains the implementation boundary until a later explicit production-signing decision.
