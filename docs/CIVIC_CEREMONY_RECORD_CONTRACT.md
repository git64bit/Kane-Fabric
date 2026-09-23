# Civic Canonical Ceremony Record Contract

## Status

Architecture contract for closure piece 2 of the Civic authority-reference milestone.

This document freezes the canonical v1 ceremony object identified by:

~~~text
manifest.ceremony.ceremony_record_sha256
~~~

It resolves the ceremony-record self-reference problem explicitly.

It is subordinate to:

- `docs/CIVIC_EPOCH1_BOOTSTRAP_CONTRACT.md`;
- `docs/CIVIC_AUTHORITY_EPOCH_CEREMONY.md`;
- `docs/CIVIC_EPOCH_MANIFEST_FORMAT.md`;
- `docs/CIVIC_CRYPTOGRAPHIC_BASELINE.md`;
- `docs/CIVIC_ACCEPTED_SIGNING_NODE_AUTHORIZATION_RECORD.md`;
- `docs/CIVIC_HISTORY_HEAD_SEMANTICS.md`.

This document does not:

- define governance-proof semantics;
- create a production Civic key;
- enable production signing;
- mutate `annales`;
- define Linux/container deployment details;
- make the ceremony object a self-authorizing authority statement.

Closure piece 3 defines the governance-proof contract and verifier.

## Purpose

Every generic signed Civic history record carries:

~~~text
ceremony_record_sha256
~~~

inside its authenticated authority context.

The Epoch Manifest also carries:

~~~text
ceremony = {
  "ceremony_record_sha256": bytes(32),
  "governance_proof_sha256": [ + bytes(32) ]
}
~~~

Therefore the ceremony object must exist independently of the generic signed-history envelope.

If the ceremony object itself contained its own `ceremony_record_sha256`, direct content-hash self-reference would result.

The v1 solution is:

~~~text
canonical ceremony payload
    -> deterministic CBOR
    -> SHA-256 exact bytes
    -> ceremony_record_sha256

ceremony payload itself
    DOES NOT contain ceremony_record_sha256
~~~

The resulting hash is then carried by the Epoch Manifest and every ceremony-bound generic history record.

## Ceremony is a canonical authority object, not a history record

The v1 ceremony record is a standalone deterministic-CBOR object.

It is **not**:

- a generic `kane-civic-history-record`;
- a CBOR Sequence item merely because accepted history exists;
- a COSE_Sign1 object;
- a Signing Node self-authorization;
- a participant vote by itself;
- a replacement for governance proofs;
- the Epoch Manifest.

Its authority comes from the complete relationship:

~~~text
canonical ceremony bytes
        +
verified governance proofs
        +
accepted authority records
        +
signed Epoch Manifest
        +
manifest lineage / bootstrap closure
        =
ceremony accepted as part of the authority state
~~~

The ceremony object supplies one exact common commitment that all ceremony-bound records can reference without recursion.

## Why the ceremony object is not separately signed in v1

A separate ceremony signature is not required in v1.

Signing the ceremony with the candidate Signing Node would prove only that the candidate node signed it. It would not establish that the node was authorized.

Signing it with one participant would likewise not establish that the applicable governance rule was satisfied.

Those facts belong in the governance-proof layer.

The accepted authority chain already supplies:

- cryptographic attribution of accepted-history records;
- Signing Node proof of possession through its authorization record;
- participant signatures where a type-specific record permits them;
- signed Epoch Manifest attribution;
- source-derived governance proof semantics.

Adding a ceremony signature would duplicate attribution while risking confusion between:

~~~text
signed
~~~

and:

~~~text
authorized
~~~

Therefore the v1 ceremony identity is the SHA-256 of its exact canonical payload bytes, not the hash of a signed wrapper.

A future ceremony version may add another authentication layer only through an explicit versioned contract.

## Canonical representation

The ceremony payload uses the accepted Kane Civic deterministic-CBOR profile.

The exact v1 media type is:

~~~text
application/kane-civic-ceremony+cbor
~~~

The exact v1 object-index semantic role is:

~~~text
ceremony-record
~~~

The exact identity is:

~~~text
ceremony_record_sha256 =
    SHA-256(exact deterministic-CBOR ceremony payload bytes)
~~~

The payload does not contain its own digest.

A JSON rendering may be generated for diagnostics, but it is non-authoritative and must never be reserialized to reconstruct ceremony authority bytes.

## Top-level schema

The canonical v1 ceremony payload contains exactly:

~~~text
{
  "format": "kane-civic-ceremony-record",
  "version": 1,
  "crypto_profile": "kane-civic-ecdsa-p256-sha256-v1",

  "transition_kind": "bootstrap" / "successor",

  "hoa_root_id": bytes(32),
  "epoch_sequence": uint,
  "predecessor_manifest_sha256": bytes(32) / null,
  "effective_time_ms": uint,

  "governing_profile": {
    "profile_id": text,
    "profile_sha256": bytes(32),
    "source_set_sha256": bytes(32)
  },

  "participants": [
    + {
      "participant_record_sha256": bytes(32),
      "participant_key_id": bytes(32),
      "participant_public_key": bytes(65)
    }
  ],

  "operator_participant_record_sha256": bytes(32),

  "signing_node": {
    "key_id": bytes(32),
    "public_key": bytes(65)
  },

  "governance_policy": {
    "policy_id": text,
    "policy_sha256": bytes(32)
  },

  "governance_proof_sha256": [
    + bytes(32)
  ]
}
~~~

Unknown top-level fields are invalid in v1.

Unknown fields inside defined child maps are invalid in v1.

## format

Exact UTF-8 text:

~~~text
kane-civic-ceremony-record
~~~

## version

Unsigned integer:

~~~text
1
~~~

## crypto_profile

Exact UTF-8 text:

~~~text
kane-civic-ecdsa-p256-sha256-v1
~~~

The ceremony itself is not signed, but the cryptographic profile identifies the representation rules for public keys and key identifiers committed by the ceremony.

## transition_kind

Exact UTF-8 text, one of:

~~~text
bootstrap
successor
~~~

The value is not merely descriptive.

For `bootstrap`:

~~~text
epoch_sequence = 1
predecessor_manifest_sha256 = null
~~~

For `successor`:

~~~text
epoch_sequence > 1
predecessor_manifest_sha256 = bytes(32)
~~~

Any inconsistent combination is invalid.

## hoa_root_id

Exactly 32 bytes.

For bootstrap, this is the candidate opaque HOA root identifier governed by `CIVIC_EPOCH1_BOOTSTRAP_CONTRACT.md`.

For a successor ceremony, it must equal the predecessor accepted Epoch Manifest `hoa_root_id`.

It is not derived from a person, machine, key, hostname, address, association name, or deployment path.

## epoch_sequence

Unsigned integer greater than zero.

For bootstrap it is exactly 1.

For a successor ceremony it must equal:

~~~text
predecessor_manifest.epoch_sequence + 1
~~~

when evaluated with the predecessor manifest.

## predecessor_manifest_sha256

For bootstrap:

~~~text
null
~~~

For a successor ceremony:

~~~text
SHA-256(exact canonical predecessor Epoch Manifest payload bytes)
~~~

This is the payload identity defined by the Epoch Manifest contract, not a hash of the COSE_Sign1 wrapper.

## effective_time_ms

Unsigned 64-bit Unix time in milliseconds.

This is the ceremony's asserted effective time.

The Epoch Manifest must carry the exact same value.

It is not an independent trusted-time proof.

A verifier may establish that the bytes consistently assert one time; it must not claim that cryptography independently proves wall-clock truth.

## governing_profile

Exact map:

~~~text
{
  "profile_id": text,
  "profile_sha256": bytes(32),
  "source_set_sha256": bytes(32)
}
~~~

It must exactly equal:

~~~text
manifest.governing_profile
~~~

The profile and source-set identities are therefore committed before accepted-history records use the ceremony hash as authority context.

The canonical governing-profile verifier remains authoritative for interpreting this descriptor.

## participants

The ceremony commits to the **non-recursive core projection** of the current participant set.

Each entry is exactly:

~~~text
{
  "participant_record_sha256": bytes(32),
  "participant_key_id": bytes(32),
  "participant_public_key": bytes(65)
}
~~~

The array:

- is non-empty;
- is sorted bytewise ascending by `participant_record_sha256`;
- contains no duplicate participant identifiers;
- contains no duplicate participant key identifiers;
- contains only valid accepted 65-byte uncompressed SEC1 P-256 public keys;
- requires `participant_key_id = SHA-256(exact participant_public_key bytes)`.

The ceremony participant projection must exactly equal the projection of:

~~~text
manifest.participants
~~~

onto those same three fields.

The ceremony deliberately does **not** contain:

~~~text
standing_record_sha256
issuance_record_sha256
~~~

because those accepted-history records contain `ceremony_record_sha256`.

Including their hashes in the ceremony would create a content-hash cycle.

Those exact record identities remain bound by the Epoch Manifest and the accepted-history verification layer.

## Participant-record identifier construction boundary

The ceremony requires each `participant_record_sha256` value to be available before ceremony bytes are finalized.

Therefore a v1 object format whose own identity is used as `participant_record_sha256` must not depend on this same ceremony hash in a way that creates recursion.

The current accepted participant issuance and standing contracts treat `participant_record_sha256` as the opaque participant identity they bind; they do not define a ceremony-dependent participant-record object.

If a future participant-record format introduces such a dependency, it must preserve this anti-self-reference invariant or introduce a new ceremony version.

## Epoch-specific participant-key rule

Participant keys are epoch-specific authority material.

For a successor ceremony, if a `participant_record_sha256` is present in both the predecessor and successor participant sets, the successor must use a new participant key:

~~~text
successor participant_key_id
    != predecessor participant_key_id

successor participant_public_key
    != predecessor participant_public_key
~~~

Historical keys remain verification material for their historical epochs.

This requirement does not imply destruction of old private keys; it prevents an old epoch credential from becoming current merely by carrying the same participant forward.

## operator_participant_record_sha256

Exactly 32 bytes.

It must identify exactly one entry in the ceremony `participants` array.

It must exactly equal:

~~~text
manifest.operator.participant_record_sha256
~~~

The ceremony does not contain:

~~~text
manifest.operator.selection_record_sha256
~~~

because the operator-selection record contains the ceremony hash through its generic signed-history envelope.

The exact selection-record identity remains bound by the Epoch Manifest and accepted history.

The ceremony commits to **who is proposed as current operator**, while the governance-proof and accepted-record layers establish or fail to establish why that designation is authorized.

## signing_node

Exact map:

~~~text
{
  "key_id": bytes(32),
  "public_key": bytes(65)
}
~~~

The public key must be the accepted 65-byte uncompressed SEC1 P-256 representation.

The key identifier must satisfy:

~~~text
key_id = SHA-256(exact public_key bytes)
~~~

The map must exactly equal the projection of:

~~~text
manifest.signing_node
~~~

onto:

~~~text
key_id
public_key
~~~

The ceremony deliberately does **not** contain:

~~~text
manifest.signing_node.authorization_record_sha256
~~~

because the Signing Node authorization record carries the ceremony hash.

The exact authorization-record identity remains bound by the Epoch Manifest and accepted history.

The ceremony commits to **which candidate/current Signing Node key the transition concerns**.

It does not self-authorize that key.

## Signing Node key reuse across epochs

The ceremony contract does not require a new Signing Node key for every successor epoch.

If the same Signing Node key is deliberately retained, the successor epoch must still have:

- its own ceremony record;
- its own governance-proof evaluation;
- its own exact Signing Node authorization-record relationship;
- its own accepted Epoch Manifest.

Key reuse is never implicit authority carry-forward.

A replacement Signing Node normally introduces a new key identifier.

## governance_policy

Exact map:

~~~text
{
  "policy_id": text,
  "policy_sha256": bytes(32)
}
~~~

The policy identifier is human/diagnostic identity.

The SHA-256 identifies the exact canonical governance-policy bytes defined by closure piece 3.

The ceremony binds one exact policy interpretation to the transition.

The policy object must be retained as authority-required content and independently retrievable by exact SHA-256.

Closure piece 3 defines:

- the canonical governance-policy format;
- its media type and object-index semantic role;
- how it binds governing sources;
- how its semantics are evaluated.

The ceremony contract does not invent those semantics.

## governance_proof_sha256

A non-empty array of exact 32-byte SHA-256 values.

The array:

- is sorted bytewise ascending;
- is duplicate-free;
- exactly equals `manifest.ceremony.governance_proof_sha256`.

Each digest identifies one exact governance-proof object whose canonical form and semantics are defined by closure piece 3.

Every proof object must be retained as authority-required content.

A proof hash is content identity only.

It does not by itself establish sufficiency.

## Required exclusions: anti-self-reference set

The v1 ceremony payload MUST NOT contain any field whose value depends on an accepted-history record that itself contains this ceremony's hash.

The following values are therefore deliberately excluded from the ceremony payload:

~~~text
ceremony_record_sha256
current manifest_sha256
signed-manifest SHA-256
accepted_history_head_sha256
witness_head_sha256
diagnostics_head_sha256
knowledge_head_sha256

participant standing_record_sha256
participant issuance_record_sha256

operator selection_record_sha256
Signing Node authorization_record_sha256
~~~

The Epoch Manifest binds those values after the ceremony identity exists.

This is the central anti-self-reference rule.

A future field may be added only through a new ceremony version if its dependency graph is proven acyclic.

## Dependency graph

The intended construction graph is:

~~~text
governing sources
        |
        v
governing profile + governance policy
        |
        v
governance proof objects
        |
        v
candidate participant keys / operator identity / Signing Node key
        |
        v
canonical ceremony payload
        |
        v
ceremony_record_sha256
        |
        +-----------------------------+
        |                             |
        v                             v
accepted-history records         Epoch Manifest fields
(contain ceremony hash)          (reference record hashes)
        |                             ^
        v                             |
accepted-history record hashes ------+
        |
        v
accepted history head
        |
        v
complete Epoch Manifest
        |
        v
signed Epoch Manifest
~~~

No edge points from an accepted-history record hash back into the ceremony payload.

Therefore the graph is constructible without fixed-point hashing.

## Epoch Manifest binding

A ceremony object is valid for one candidate/accepted Epoch Manifest only when all applicable fields agree.

The verifier requires:

~~~text
ceremony.hoa_root_id
    == manifest.hoa_root_id

ceremony.epoch_sequence
    == manifest.epoch_sequence

ceremony.predecessor_manifest_sha256
    == manifest.predecessor_manifest_sha256

ceremony.effective_time_ms
    == manifest.effective_time_ms

ceremony.governing_profile
    == manifest.governing_profile

ceremony participant core projection
    == manifest participant core projection

ceremony.operator_participant_record_sha256
    == manifest.operator.participant_record_sha256

ceremony.signing_node
    == manifest signing_node key/public-key projection

ceremony.governance_proof_sha256
    == manifest.ceremony.governance_proof_sha256

SHA-256(exact ceremony bytes)
    == manifest.ceremony.ceremony_record_sha256
~~~

The governance-policy descriptor is bound indirectly because it is inside the exact ceremony bytes whose hash the manifest commits.

## Object-index binding

The Epoch Manifest `object_index` must contain exactly one descriptor whose:

~~~text
sha256
    == ceremony_record_sha256

byte_length
    == len(exact ceremony bytes)

media_type
    == "application/kane-civic-ceremony+cbor"

semantic_role
    == "ceremony-record"
~~~

If `inline` is non-null, it must equal the exact verified ceremony bytes.

If `inline` is null, the exact bytes must be independently available from the authority-required object store/replica.

The ceremony object is authority-required reconstruction material.

A URI, filename, JSON rendering, database row, or CID does not substitute for the exact bytes.

## Bootstrap-specific verification

For a `bootstrap` ceremony:

~~~text
transition_kind = "bootstrap"
epoch_sequence = 1
predecessor_manifest_sha256 = null
~~~

The verifier additionally applies `CIVIC_EPOCH1_BOOTSTRAP_CONTRACT.md`.

The ceremony provides the non-recursive common commitment to:

- candidate HOA root;
- initial current participant core set;
- initial operator identity;
- initial Signing Node key;
- governing profile/source-set identity;
- governance policy;
- governance-proof set;
- asserted effective time.

The complete bootstrap bundle, not the ceremony alone, determines whether Epoch 1 is accepted.

## Successor-specific verification

For a `successor` ceremony, the verifier must be given the verified predecessor Epoch Manifest.

It requires:

~~~text
ceremony.hoa_root_id
    == predecessor.hoa_root_id

ceremony.epoch_sequence
    == predecessor.epoch_sequence + 1

ceremony.predecessor_manifest_sha256
    == SHA-256(exact canonical predecessor manifest payload bytes)
~~~

It also verifies the epoch-specific participant-key rule for continuing participant identities.

The governance-proof layer determines whether the proposed changes to participant set, operator, Signing Node, governing profile, or other authority state are authorized.

The ceremony format itself does not impose one universal HOA transition procedure.

## Effective-time boundary

The ceremony's `effective_time_ms` is the one time assertion carried into the Epoch Manifest.

For bootstrap it is also the participant-standing evaluation time required by the bootstrap contract.

For successor epochs, type-specific/profile rules may determine additional temporal checks.

The ceremony record does not create trusted time.

If the asserted time is disputed, malformed, outside permitted policy bounds, or contradicted by evidence, the verifier or Diagnostics layer must expose that result rather than inventing a corrected timestamp.

## Governance-proof relationship

The ceremony commits to both:

~~~text
governance_policy
governance_proof_sha256
~~~

Closure piece 3 must define a verifier with the conceptual shape:

~~~text
verified_governance_policy =
    verify_governance_policy(
        exact_policy_bytes,
        governing_sources
    )

verify_governance_transition(
    verified_governance_policy,
    exact_governance_proof_objects,
    ceremony,
    predecessor_manifest_or_null
)
~~~

The ceremony is therefore the **subject of the governance decision**.

The proof layer must evaluate whether the supplied evidence authorizes this exact ceremony transition, not an approximate or reconstructed description of it.

## Ceremony record and Signing Node authorization

The accepted Signing Node authorization record already requires its:

~~~text
governance_proof_sha256
~~~

array to equal:

~~~text
manifest.ceremony.governance_proof_sha256
~~~

Under this contract, the same proof set is also committed inside the exact ceremony bytes.

Therefore the verifier can establish:

~~~text
authorization record proof set
    ==
manifest ceremony proof set
    ==
canonical ceremony proof set
~~~

The Signing Node cannot select a weaker private proof set.

Its signature remains proof of possession/attribution only.

## Ceremony record and operator selection

The ceremony commits to the selected operator participant identity but not the operator-selection record hash.

The accepted operator-selection record and Epoch Manifest bind that exact record separately.

Closure piece 3 determines whether the governance proof is sufficient for the operator designation committed by the ceremony.

This preserves:

~~~text
operator designation
    !=
proof that designation was authorized
~~~

## Ceremony record and participant standing

The ceremony commits to participant identities and epoch-specific public keys.

The Epoch Manifest and accepted history separately bind each participant's standing and issuance records.

For bootstrap, currentness is evaluated at the ceremony/manifest effective time.

For successor epochs, current standing remains profile- and time-dependent under the accepted standing verifier.

The ceremony itself is not a substitute for participant-standing verification.

## Deterministic validation rules

A conforming v1 ceremony validator rejects:

- non-map top-level values;
- missing or unknown top-level fields;
- unknown fields in defined child maps;
- unsupported format/version/crypto profile;
- non-NFC text;
- floating-point values;
- indefinite-length CBOR;
- duplicate CBOR map keys;
- non-shortest deterministic CBOR encodings;
- invalid transition-kind/predecessor combinations;
- malformed SHA-256 values;
- malformed public keys;
- key-ID/public-key mismatches;
- empty participant set;
- unsorted or duplicate participant identifiers;
- duplicate participant key identifiers;
- operator identity absent from participant set;
- empty governance-proof set;
- unsorted or duplicate governance-proof hashes;
- malformed governance-policy descriptor.

Encoding the parsed value must reproduce the exact input bytes.

Semantic verification against a manifest additionally applies every cross-binding rule in this contract.

## Identity and equality

Two ceremony records are identical only when their exact canonical CBOR bytes are identical.

Semantically similar ceremonies with different:

- effective time;
- participant key;
- participant set;
- operator;
- Signing Node key;
- governing profile;
- governance policy;
- governance proof;
- predecessor;

are different ceremony objects and have different SHA-256 identities.

The ceremony is not mutable.

A correction or changed transition produces new candidate ceremony bytes and a new identity.

## Retention and reconstruction

Every accepted epoch's exact ceremony bytes are authority-required historical material.

Participant authority-state reconstruction must retain or resolve them for every epoch in the accepted lineage.

A reconstruction that has signed manifests and accepted-history records but lacks the exact ceremony bytes required to evaluate their authority context is incomplete.

The ceremony must not exist only:

- on the Signing Node;
- in operator memory;
- in a proprietary portal;
- in a mutable web document;
- in a transient database;
- in a Diagnostics/RAG index.

## Failure and divergence

A malformed or inconsistent ceremony is not repaired silently.

If different replicas contain different candidate ceremony objects for the same proposed epoch, preserve the divergence.

Do not choose based on:

- filesystem timestamp;
- hostname;
- machine ownership;
- copy count;
- operator preference;
- Signing Node preference.

The accepted authority lineage selects one exact ceremony through the accepted Epoch Manifest and verified governance transition.

Competing candidate ceremonies remain Diagnostics evidence.

## Production boundary

This contract defines bytes and verification semantics only.

It does not specify:

- private-key generation;
- Signing Node key storage;
- participant private-key storage;
- signing APIs;
- transaction journals;
- filesystem layout;
- service users;
- LXD/container configuration;
- systemd services;
- backup tools;
- network transport;
- `annales` implementation.

Those remain closure pieces 4 through 6 and the later Annales project.

## Closure dependencies

After this document, the six-piece closure status is:

~~~text
1. Epoch-1 bootstrap contract
       architecture frozen

2. canonical ceremony-record contract
       architecture frozen by this document

3. governance-proof contract/verifier
       next unresolved authority-semantic dependency

4. production signing/key-lifecycle contract
       pending

5. authority-state transaction/composition contract
       pending

6. Signing Node conformance/deployment boundary
       pending
~~~

Closure piece 3 must consume the ceremony as an immutable transition subject.

It must not redefine the ceremony format or introduce a hidden callback that can override the exact committed governance policy.

## Decision summary

The canonical v1 ceremony model is:

~~~text
governing sources/profile
        +
governance policy
        +
governance proof objects
        +
participant epoch keys
        +
operator identity
        +
Signing Node key
        +
predecessor identity when applicable
        +
effective-time assertion
        ↓
deterministic-CBOR ceremony payload
        ↓
SHA-256 exact bytes
        ↓
ceremony_record_sha256
        ↓
accepted-history authority-context binding
        +
Epoch Manifest binding
~~~

The ceremony object is deliberately unsigned in v1.

Its role is deterministic common commitment, not self-authorization.

The decisive anti-self-reference invariant is:

~~~text
ceremony commits to non-recursive authority inputs

Epoch Manifest commits to
ceremony hash + recursive accepted-record hashes + history head
~~~

That dependency graph is acyclic and independently verifiable.
