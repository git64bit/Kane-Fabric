# Civic Accepted Signing Node Authorization Record

## Status

Architecture contract for the first type-specific Civic accepted-history record.

This document defines the accepted-history record that binds one epoch's Signing Node public key to the governance evidence authorizing that key.

It is subordinate to:

- `docs/CIVIC_CRYPTOGRAPHIC_BASELINE.md`;
- `docs/CIVIC_EPOCH_MANIFEST_FORMAT.md`;
- `docs/CIVIC_HISTORY_HEAD_SEMANTICS.md`;
- `docs/CIVIC_SIGNED_HISTORY_RECORD_ENVELOPE.md`;
- `docs/CIVIC_PARTICIPANT_AUTHORITY_STATE_RECONSTRUCTION.md`.

This contract does not enable production signing.

## Purpose

The Epoch Manifest already contains:

~~~text
signing_node = {
  "key_id": bytes(32),
  "public_key": bytes(65),
  "authorization_record_sha256": bytes(32)
}
~~~

The missing semantic contract is the record identified by:

~~~text
authorization_record_sha256
~~~

That record must establish all of the following without conflating them:

~~~text
1. this exact Signing Node key exists;
2. the holder proved possession of the corresponding private key;
3. source-derived governance evidence authorized this key for this epoch;
4. the exact authorization record belongs to the accepted history;
5. the accepted Epoch Manifest explicitly references that exact record.
~~~

A Signing Node signature proves only item 2.

It does not create items 3, 4, or 5 by itself.

## Record type

The exact v1 `record_type` is:

~~~text
kane-civic-accepted-signing-node-authorization-v1
~~~

A verifier must not treat another record type as equivalent.

## Required generic-envelope values

The record uses the generic Civic signed-history envelope.

For this type:

~~~text
history_link.stream = "accepted"

signer.kind = "signing_node"

signer.participant_record_sha256 = null
~~~

The generic envelope already requires:

~~~text
signer.key_id == protected COSE kid
~~~

and resolves the signer public key from the accepted Epoch Manifest identified by:

~~~text
hoa_root_id
epoch_sequence
ceremony_record_sha256
~~~

Participant-signed records are not valid instances of this record type.

A participant may contribute governance evidence through a separately defined record type, but a participant signature does not substitute for Signing Node proof of possession.

## Body schema

The v1 body contains exactly:

~~~text
{
  "authorized_key_id": bytes(32),
  "authorized_public_key": bytes(65),

  "governance_proof_sha256": [
    + bytes(32)
  ]
}
~~~

Unknown body fields are invalid in v1.

The governance-proof array is:

- non-empty;
- sorted by bytewise ascending SHA-256 value;
- duplicate-free.

Private key material is forbidden.

## Signing Node key binding

For the referenced accepted Epoch Manifest:

~~~text
record.body.authorized_key_id
    == manifest.signing_node.key_id

record.body.authorized_public_key
    == manifest.signing_node.public_key

record.signer.key_id
    == manifest.signing_node.key_id

SHA-256(record.body.authorized_public_key)
    == record.body.authorized_key_id
~~~

The generic signed-envelope verifier additionally proves that the exact record payload was signed by the private key corresponding to:

~~~text
manifest.signing_node.public_key
~~~

Therefore the record proves possession of the key that the Epoch Manifest names as its Signing Node.

It does not prove governance authorization merely because the same key signed the record.

## Exact authorization-record binding

After complete signed-record verification:

~~~text
record_sha256 =
    SHA-256(exact complete COSE_Sign1 record bytes)
~~~

The type-specific verifier requires:

~~~text
record_sha256
    == manifest.signing_node.authorization_record_sha256
~~~

A semantically equivalent re-encoding, a re-signature of the same payload, or another authorization record for the same public key is not interchangeable.

The Epoch Manifest identifies one exact signed authorization record.

## Governance-proof binding

For v1, the authorization record uses the same governance-proof set committed by the referenced Epoch Manifest ceremony:

~~~text
record.body.governance_proof_sha256
    == manifest.ceremony.governance_proof_sha256
~~~

The equality is exact after applying the already required canonical bytewise ordering.

This intentionally avoids two competing descriptions of which governance evidence authorized the epoch Signing Node.

The authorization record does not get to choose a weaker subset.

The Signing Node does not get to invent an additional private proof set.

## Governance proof is not a hash-only permission

A SHA-256 value proves content identity, not governance sufficiency.

Every item named in:

~~~text
governance_proof_sha256
~~~

must resolve to retained authority-required content and must satisfy the applicable governance-proof semantic contract.

Until the governance-proof record/object types have been verified, this Signing Node authorization record is not semantically sufficient to authorize authoritative Civic state.

Therefore:

~~~text
valid Signing Node signature
    + matching public key
    + matching proof hashes

does not yet mean

authorized governance transition
~~~

The source-derived governance layer remains decisive.

## Accepted-history requirement

A Signing Node authorization record is an `accepted` stream record.

Its authenticated `history_link` must therefore satisfy the accepted-history chain:

~~~text
genesis:
  predecessor_record_sha256 = null

successor:
  predecessor_record_sha256 =
      SHA-256(exact preceding accepted-history record bytes)
~~~

The record's exact signed identity must lie on the linear accepted-history path ending at:

~~~text
manifest.history.accepted_history_head_sha256
~~~

A valid authorization record existing elsewhere in storage is insufficient.

A valid signed fork is also insufficient unless the accepted authority lineage selects the branch containing it.

## What advances authority

This record does not independently advance authoritative Civic state.

The minimum relationship is:

~~~text
verified source-derived governance proof
    +
verified Signing Node authorization record
    +
verified accepted-history predecessor chain
    +
accepted Epoch Manifest referencing the exact authorization record
    +
verified Epoch Manifest lineage
    =
Signing Node key recognized for that accepted epoch
~~~

The Epoch Manifest remains the current authority-state selector.

The authorization record supplies one required authority fact within that state.

This distinction prevents:

~~~text
"I possess a valid Signing Node private key"
~~~

from becoming:

~~~text
"I may unilaterally define current HOA Civic authority."
~~~

## Signer semantics

For this record type, the Signing Node signature has one narrow semantic role:

~~~text
proof of possession and attribution
~~~

It establishes that the holder of the private key corresponding to the manifest's Signing Node public key signed these exact authorization-record bytes.

The signature does not establish:

- that the operator was validly selected;
- that participant standing was valid;
- that a vote or consent threshold was met;
- that a governing source permits the transition;
- that the ceremony was valid;
- that the epoch should be accepted;
- that the signed facts are legally true merely because the node signed them.

Those are separate governance and authority-state questions.

## No self-authorization

The following reasoning is invalid:

~~~text
the Signing Node signed its own authorization record
therefore the Signing Node is authorized
~~~

The valid reasoning path is:

~~~text
the node signature proves possession of the candidate key

the governance-proof set proves or fails to prove
source-derived authorization

the accepted history proves or fails to prove
that the exact authorization record belongs to the selected lineage

the Epoch Manifest proves or fails to prove
that this exact authorization record and key define the epoch Signing Node
~~~

All required relationships must verify.

## Forged-node consequence

A forged or substitute node may create arbitrary bytes.

It may also create a self-consistent private history.

Neither gives those bytes Civic authority.

To become useful as the accepted Signing Node for an existing authority lineage, the substitute would need an authorization record satisfying all of the following:

~~~text
correct HOA root
correct epoch
correct ceremony context
correct Signing Node key binding
valid ESP256 signature
valid accepted-history predecessor
exact authorization-record reference from the Epoch Manifest
verified governance-proof set
verified Epoch Manifest lineage
current participant reconstruction agreement with that lineage
~~~

This security property follows from ordinary reconstruction and authority utility requirements.

It is not a separate device-locking mechanism.

A compromised legitimate private key remains a real security event. The architecture does not claim that cryptographic key compromise is impossible. Instead, the resulting activity remains attributable to a specific key, epoch, signed record, predecessor chain, governance proof set, and manifest lineage.

## Replacement Signing Node

A replacement Signing Node does not inherit authority merely by copying the old node's files or network identity.

The replacement path remains:

~~~text
reconstruct accepted authority state
    ->
apply source-derived governance procedure
    ->
generate replacement Signing Node key
    ->
produce required governance proof
    ->
produce a new authorization record
    ->
complete the applicable ceremony/epoch transition
    ->
publish and replicate the successor accepted authority state
~~~

The old Signing Node private key is not required to be recovered.

The replacement key has a new key identifier.

Old signed records remain historically verifiable under their historical epochs.

## Cross-epoch rule

A Signing Node authorization record authorizes only the Signing Node named by the accepted Epoch Manifest for the record's own authority-context tuple.

It does not authorize that key for another epoch.

Even if the same physical machine or same public key were deliberately reused, each epoch still requires its own exact authorization-record relationship and applicable governance proof.

Key reuse is therefore not an implicit authority carry-forward mechanism.

## Failure conditions

This record fails type-specific verification if any of the following is true:

- `record_type` is not the exact v1 value;
- `history_link.stream` is not `accepted`;
- signer kind is not `signing_node`;
- signer participant reference is non-null;
- body fields differ from the exact v1 body schema;
- authorized key ID is not exactly 32 bytes;
- authorized public key is not the accepted 65-byte P-256 representation;
- public-key SHA-256 does not equal the authorized key ID;
- authorized key differs from the referenced Epoch Manifest Signing Node;
- signer key differs from the authorized key;
- exact record SHA-256 differs from `manifest.signing_node.authorization_record_sha256`;
- governance-proof array is empty, unsorted, or contains duplicates;
- governance-proof array differs from `manifest.ceremony.governance_proof_sha256`;
- any required governance proof is missing or fails its semantic contract;
- the signed record is not on the selected accepted-history chain;
- generic COSE/signature verification fails;
- epoch authority-context resolution fails;
- predecessor linkage fails;
- the accepted-history final head fails.

Failures are preserved as Diagnostics evidence rather than repaired heuristically.

## Ceremony-record self-reference boundary

This contract intentionally does not define the object identified by:

~~~text
manifest.ceremony.ceremony_record_sha256
~~~

as this same generic history-record type.

Every generic signed-history record currently carries:

~~~text
ceremony_record_sha256
~~~

inside its own authenticated authority-context tuple.

If the record were also required to be the exact object whose SHA-256 equals that field, a direct self-reference would result:

~~~text
record bytes contain ceremony_record_sha256
    ->
record SHA-256 depends on record bytes
    ->
ceremony_record_sha256 would have to equal that same record SHA-256
~~~

The ceremony-record representation therefore remains a separate architecture question and must be defined without introducing self-reference.

No implementation should silently assume that the ceremony record itself can use this generic envelope until that question is resolved explicitly.

## Verification order

After generic signed-history verification succeeds, the type-specific verifier performs:

1. require exact `record_type`;
2. require authenticated stream `accepted`;
3. require signer kind `signing_node`;
4. validate the exact body schema;
5. validate authorized public-key representation;
6. derive and verify the authorized key identifier;
7. require body key to equal the referenced manifest Signing Node key;
8. require signer key to equal the authorized key;
9. require exact record SHA-256 to equal `manifest.signing_node.authorization_record_sha256`;
10. require non-empty sorted unique governance-proof hashes;
11. require the proof list to equal `manifest.ceremony.governance_proof_sha256`;
12. verify every governance proof under its type-specific/source-derived contract;
13. require the record to satisfy authenticated accepted-history linkage;
14. require the complete selected accepted history to terminate at the manifest head.

Only after all applicable checks succeed may the Signing Node key be treated as the authorized Signing Node key for that accepted epoch.

## Production boundary

This document defines semantics only.

It does not:

- generate a production Civic key;
- enable production signing;
- mutate `annales`;
- create a Civic Signing Node service;
- change Firmware Release Authority;
- change participant devices;
- change the accepted cryptographic profile.

Fixture-only cryptographic work remains the implementation boundary until a later explicit production-signing decision.
