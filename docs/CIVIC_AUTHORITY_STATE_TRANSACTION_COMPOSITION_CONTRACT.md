# Civic Authority-State Transaction and Composition Contract

## Status

Architecture contract for Kane Fabric Civic reference closure piece 5.

Documentation only.

This contract does **not**:

- create a production Civic private key;
- enable production Civic signing;
- activate a Civic Signing Node;
- mutate annales;
- define Annales containers, services, paths, networking, or concrete key locations;
- replace the accepted Epoch-1, ceremony, governance, signing, history, or authority-state formats;
- define the platform-neutral Signing Node deployment/conformance boundary reserved for closure piece 6.

Current production boundary remains:

~~~text
production_signing_enabled = false
production_key_created = false
annales_mutated = false
~~~

## Purpose

Civic now has accepted contracts for:

- deterministic authority objects;
- Epoch Manifests;
- signed history records and append-only history;
- participant/operator/Signing Node authority records;
- participant authority-state replicas;
- Epoch-1 bootstrap;
- canonical ceremony records;
- source-bound governance policy and proof verification;
- production-capable private-key generation and signing semantics.

What remains is the transition from a collection of individually valid candidate artifacts to **one newly accepted current authority state**.

The central problem is transactional:

~~~text
many candidate bytes
    + several signatures
    + content-addressed objects
    + history linkage
    + one final Epoch Manifest
    + one reconstructable replica

must become current
    all together
or
    not at all
~~~

This document freezes that composition and acceptance boundary.

## Governing contracts

This contract must preserve:

- `docs/CIVIC_EPOCH_MANIFEST_FORMAT.md`;
- `docs/CIVIC_HISTORY_RECORD_FORMAT.md` where applicable;
- `docs/CIVIC_PARTICIPANT_AUTHORITY_STATE_RECONSTRUCTION.md`;
- `docs/CIVIC_EPOCH1_BOOTSTRAP_CONTRACT.md`;
- `docs/CIVIC_CEREMONY_RECORD_CONTRACT.md`;
- `docs/CIVIC_GOVERNANCE_POLICY_PROOF_CONTRACT.md`;
- `docs/CIVIC_PRODUCTION_SIGNING_KEY_LIFECYCLE_CONTRACT.md`;
- the accepted type-specific participant, standing, operator-selection, and Signing Node authorization record contracts.

Transaction machinery may coordinate these objects.

It may not weaken their verification requirements.

## Core invariant

A Civic authority transition is accepted only when one exact closed candidate state has been completely verified and atomically selected as current.

Therefore:

~~~text
candidate artifact exists
    != accepted authority

candidate key signs
    != accepted authority

candidate history verifies
    != accepted authority

candidate manifest signature verifies
    != accepted authority

complete candidate closure verifies
    + atomic accepted-state selection
    =
locally accepted current authority
~~~

The transaction system is not itself a new source of governance authority.

## Key generation remains separate from authority activation

Closure piece 4 remains binding:

~~~text
key generation
    != authority activation
~~~

A candidate participant key or Signing Node key may exist before the transaction starts.

A candidate key may be used to compose exact candidate bytes where the accepted contracts permit candidate signing.

The key becomes current authority only because the newly accepted epoch binds that exact canonical public key and key ID.

No transaction API may promote a key merely by changing keystore metadata.

## Authority-state transaction is not a new canonical authority record

Piece 5 does not introduce a new signed "transaction record."

The authoritative objects remain the already accepted Civic objects:

- governance policy and proofs;
- ceremony;
- signed accepted-history records;
- Epoch Manifest;
- signed Epoch Manifest;
- retained exact authority objects;
- participant authority-state replica inventory.

A transaction implementation may maintain local staging metadata, journals, locks, generation counters, or temporary identifiers.

Those are operational state.

They are not Civic authority and must not be required for independent public verification.

## Transaction states

A conforming implementation may name states differently, but it must preserve the following semantic phases:

~~~text
BUILDING
    candidate inputs/artifacts may still be added

SEALED
    all identity-bearing candidate bytes are fixed

VERIFIED
    complete candidate authority closure has passed

COMMITTED
    local accepted-state selector atomically names candidate state

ABORTED
    candidate remains non-authoritative
~~~

A transition must never expose BUILDING or SEALED state as current authority.

## BUILDING state

During BUILDING:

- candidate keys may be generated;
- authority source/evidence bytes may be gathered;
- candidate participant/operator/Signing Node core state may be assembled;
- governance proofs may be collected;
- deterministic unsigned projections may be recomputed;
- candidate content-addressed objects may be persisted;
- incomplete candidate artifacts may be discarded.

Nothing in BUILDING is current authority.

## SEALED state

SEALED means every exact byte identity that determines the candidate authority state is fixed.

At minimum this includes:

- exact governance policy bytes;
- exact governance proof bytes;
- exact ceremony bytes;
- exact new signed accepted-history record bytes;
- exact resulting accepted-history sequence bytes;
- exact Epoch Manifest payload bytes;
- exact signed Epoch Manifest bytes;
- exact participant authority-state replica bytes;
- every authority-required external object byte set used by verification.

After sealing, mutation is forbidden.

A semantic correction creates a new candidate transaction.

## VERIFIED state

VERIFIED means the candidate was checked from the exact retained bytes using the complete Civic authority verifier defined by this contract.

Verification must be repeatable through the same content-addressed loader that will remain available after commit.

Verification from temporary in-memory bytes while the durable store contains different or missing bytes is insufficient.

## COMMITTED state

COMMITTED means one platform-local accepted-state selector has changed atomically from the expected prior accepted state to the exact newly verified replica.

The selector is local operational state, not Civic authority.

The authority remains the verified objects it selects.

## ABORTED state

An aborted candidate:

- does not change current authority;
- does not activate candidate keys;
- does not retire current keys;
- does not rewrite accepted history;
- may retain immutable artifacts for Diagnostics;
- may garbage-collect unreferenced candidate artifacts later.

No heuristic converts ABORTED state into authority.

## Two identities at the final boundary

Two different content identities are important.

### Epoch Manifest payload identity

~~~text
manifest_sha256
    = SHA-256(exact canonical Epoch Manifest payload)
~~~

This is the canonical epoch-state identity already used by Civic lineage.

### Participant authority-state replica identity

~~~text
replica_sha256
    = SHA-256(exact canonical authority-state replica bytes)
~~~

This identifies the complete retained-state inventory used for local reconstruction.

The local accepted-state selector should identify the exact replica state.

The canonical current epoch remains identified by the replica's:

~~~text
current_manifest_sha256
~~~

The replica identity does not replace the Epoch Manifest identity.

## Accepted-state selector

Every conforming mutable implementation requires exactly one logical current-state selector for one HOA root.

The selector must be capable of atomically identifying:

- no accepted state; or
- one exact accepted authority-state replica identity.

A local implementation may additionally cache:

- replica byte length;
- current manifest SHA-256;
- current epoch sequence;
- a local generation counter.

Those caches must be verified against the selected replica.

They are not authority.

## Selector encoding is not protocol

This contract does not freeze whether the selector is implemented as:

- an atomic file replacement;
- a database compare-and-swap row;
- an embedded key/value transaction;
- a journaled local metadata record;
- another owner-controlled atomic mechanism.

The required semantics are what matter:

~~~text
expected prior selector
    ->
atomic compare-and-select
    ->
new verified replica
~~~

No platform-specific selector path or database product is part of Civic identity.

## Bootstrap selector rule

For Epoch 1, commit requires:

~~~text
expected prior accepted state = none
~~~

If any accepted state already exists for that local authority domain, bootstrap cannot be used to replace it.

If the selector already names the exact same replica from a completed prior commit, a retry may report idempotent success.

That does not reopen bootstrap authority.

## Successor selector rule

For a successor transition, commit requires the currently selected accepted state to be exactly the predecessor state against which the candidate was built and verified.

At minimum:

~~~text
current accepted manifest SHA-256
    ==
candidate.predecessor_manifest_sha256
~~~

The implementation must also ensure that the local selected replica has not changed since the candidate transaction took its predecessor snapshot.

If it changed, the candidate is stale.

A stale candidate is not silently rebased.

## Why compare-and-select is required

Without a predecessor compare at commit time, two concurrent valid candidates could both be built from the same current epoch and then overwrite each other according to process timing.

That would make filesystem timing a governance mechanism.

Civic instead requires:

~~~text
both candidates built from E
        |
        +-- candidate A
        |
        +-- candidate B

first exact candidate committed
        ->
current state becomes successor of E

second candidate commit attempt
        ->
predecessor comparison fails
        ->
fork/stale-candidate Diagnostics
~~~

The implementation must not silently choose the later writer.

## Candidate input snapshot

A successor transaction begins by verifying and freezing one exact predecessor authority state.

The input snapshot includes at least:

- predecessor authority-state replica bytes;
- predecessor current Manifest identity;
- exact predecessor signed Manifest bytes;
- exact accepted-history sequence and head;
- exact current participant public authority state;
- exact governing/profile/source state needed by the candidate transition.

The candidate transition is built against that exact predecessor.

A later change to local current state invalidates the candidate's commit eligibility.

## Bootstrap candidate input

Bootstrap has no predecessor Civic state.

Its frozen initial inputs include:

- candidate opaque HOA root ID;
- governing profile;
- governing sources;
- governance policy;
- candidate participant identities and keys;
- candidate operator identity;
- candidate Signing Node key;
- authority evidence required by standing/governance.

These are candidate inputs until the complete Epoch-1 closure is committed.

## Exact-byte object rule

Every dependency entering the transaction is represented by exact bytes and SHA-256 identity where its existing Civic contract defines content identity.

A transaction must not substitute:

- a filename for a digest;
- a URI for bytes;
- a CID for Civic SHA-256 identity;
- a JSON projection for canonical CBOR;
- a database object for exact stored bytes;
- a mutable network resource for a required retained object.

A retrieval identifier may help locate bytes.

It does not replace content identity.

## Immutable object persistence is safe before acceptance

Content-addressed authority objects may be written to durable storage before the transition is accepted.

This is not authority activation because storage presence does not determine current authority.

Therefore the safe storage rule is:

~~~text
persist immutable candidate bytes first
select current state last
~~~

A crash may leave unreferenced candidate objects.

That is acceptable.

A crash must not leave a partially selected current authority state.

## Content-addressed write rule

For an object whose identity is SHA-256:

1. compute exact digest and byte length;
2. if absent, write exact bytes;
3. verify the written bytes by digest and length;
4. if the digest already exists, verify existing bytes exactly;
5. never overwrite different bytes under the same digest.

Any detected digest/path inconsistency is a hard failure and Diagnostics event.

## Dependency closure

A candidate is not closed merely because every manifest field has a value.

Closure means every authority-required reference resolves to exact retained bytes or valid inline bytes.

For the candidate epoch, closure includes at least:

- canonical governing profile;
- governing sources;
- governance policy;
- governance proofs;
- ceremony;
- governance authority evidence;
- participant-standing authority evidence;
- all objects declared authority-required in the candidate Manifest object index;
- complete accepted-history sequence;
- signed candidate Epoch Manifest;
- all earlier lineage material required by the resulting authority-state replica.

Private keys are excluded.

## Transitive closure rule

If authority object A requires exact object B for its accepted verifier, and B requires C, the candidate transaction must retain the full transitive closure.

The implementation must not stop at the first-level object index.

Examples include:

~~~text
standing record
    -> governing profile
    -> governing source set

standing record
    -> authority evidence

ceremony
    -> governance policy
    -> governing sources

governance proof
    -> authority evidence
~~~

The exact accepted verifiers, not application convenience, define the closure.

## Object metadata conflict

One SHA-256 identity must resolve to one exact byte string.

If two candidate references assign incompatible authority metadata to the same digest, such as conflicting:

- byte length;
- media type where the relevant contract binds it;
- semantic role where the relevant contract binds it;

the transaction fails.

It must not create duplicate object-index entries for the same digest to hide the conflict.

## Authority-state replica required_objects

The resulting participant authority-state replica must continue to satisfy the accepted replica contract.

Its `required_objects` array represents exact externally retained authority bytes required by the complete retained lineage that are not already available inline under the accepted replica rules.

The composer must derive this inventory from the resulting lineage and object indexes.

It must not rely on a hand-maintained list that can silently omit a dependency.

## Signed Manifest lineage

For bootstrap, the replica lineage begins with exactly one signed Epoch-1 Manifest.

For successor transition from epoch E to E+1:

~~~text
new lineage
    =
exact predecessor replica lineage
    + exact signed Manifest for E+1
~~~

Earlier signed Manifest bytes are never regenerated.

Their exact signed-envelope identities and lengths are preserved.

## History sequence semantics

The accepted-history stream is cumulative.

For bootstrap:

~~~text
prior accepted sequence = empty
prior accepted head = null
~~~

For successor:

~~~text
prior accepted sequence
    = exact accepted sequence from selected predecessor replica

prior accepted head
    = predecessor Manifest accepted_history_head_sha256
~~~

The candidate transaction appends new epoch records to those exact bytes.

It never rewrites earlier sequence bytes.

## Mandatory new accepted-history records per epoch

The current Epoch Manifest requires epoch-local accepted records for:

- Signing Node authorization;
- operator selection;
- participant standing for every current participant;
- participant issuance for every current participant.

The type-specific verifiers bind these records to the candidate epoch sequence and ceremony.

Therefore a successor transaction cannot satisfy the new manifest by merely pointing at prior-epoch standing, issuance, operator-selection, or Signing Node authorization records.

The new epoch requires its own exact current-epoch records.

## Canonical reference construction order

The reference composer uses one deterministic order for the mandatory new accepted-history records:

~~~text
1. Signing Node authorization

2. operator selection

3. participant standing records
   sorted bytewise by participant_record_sha256

4. participant issuance records
   sorted bytewise by participant_record_sha256
~~~

The first new record names the predecessor accepted-history head.

Each later record names the exact SHA-256 identity of the immediately prior signed history record.

For bootstrap, the Signing Node authorization record names a null predecessor.

For successor, it names the predecessor epoch's accepted-history head.

## Why this order is not authority precedence

The new records are accepted atomically as one epoch transition.

Their sequence order is a deterministic construction/linkage rule.

It does **not** mean that the first record was already authoritative while later records were still candidates.

In particular:

~~~text
candidate Signing Node authorization record appears first
    !=
candidate node became current before the transaction committed
~~~

Every new record remains candidate material until final atomic acceptance.

## Participant standing before issuance dependency

Participant issuance records contain the exact:

~~~text
standing_record_sha256
~~~

for that participant.

Therefore every participant standing record must be signed and have its final exact identity before the corresponding issuance record is composed.

The canonical order satisfies this dependency.

## Record-signature identity is final

The identity of an accepted-history record is the SHA-256 of its exact signed record bytes.

Once a signed record is used as:

- a history predecessor;
- a manifest standing/issuance/selection/authorization reference;
- a history head;

those exact signed bytes are sealed.

The implementation must never re-sign or normalize the record afterward.

## Randomized signing retry consequence

Piece 4 permits a conforming provider whose valid ECDSA signatures are randomized.

Therefore the transaction layer must not assume:

~~~text
re-sign same payload
    -> same signed bytes
~~~

Once exact signed bytes have been incorporated into a candidate dependency graph, retries for that candidate must reuse those exact bytes.

If they were lost before durable retention, the implementation must restart candidate composition from the earliest affected identity boundary rather than pretending a newly signed replacement is the same candidate.

## Deterministic RFC 6979 does not weaken this rule

The accepted reference software provider currently uses RFC 6979 deterministic signing.

Piece 5 still treats signed bytes as sealed identities.

A future conforming provider may be randomized.

Transaction correctness must not depend on deterministic signature reproduction.

## Governance subject before final proof set

The governance transition subject intentionally excludes governance-proof hashes.

Therefore the construction order is:

~~~text
freeze candidate transition core
        ->
derive canonical governance subject
        ->
collect/sign governance proofs over that subject
        ->
compute exact proof hashes
        ->
finalize canonical ceremony with exact proof set
~~~

A placeholder proof hash may be used internally only if the subject derivation is proven to exclude it exactly.

The final retained ceremony must contain the real exact proof hashes.

## Governance proofs before accepted history

Every accepted-history record carries:

~~~text
ceremony_record_sha256
~~~

Therefore the final ceremony identity must exist before accepted-history records are signed.

This is a hard dependency.

## Ceremony before accepted-history record identities

The ceremony deliberately excludes:

- standing record hashes;
- issuance record hashes;
- operator-selection record hash;
- Signing Node authorization record hash;
- accepted-history head.

This anti-self-reference property permits the transaction to finalize ceremony bytes first and then create the history identities.

Piece 5 must not add a local requirement that reintroduces one of those hashes into the ceremony.

## Candidate context for record signing

During composition, the new epoch is not accepted yet.

Record composition may nevertheless use the already frozen candidate public authority context to resolve the expected signer key.

That candidate context includes:

- HOA root;
- candidate epoch sequence;
- exact ceremony identity;
- candidate participant identities/public keys;
- candidate operator identity;
- candidate Signing Node public key.

The production signing layer must use an explicit candidate binding.

It must not require the candidate key to be marked current.

## Candidate context is not a substitute for final verification

Using candidate context to choose the expected signing key is construction logic.

After the Manifest is finalized, every signed history record must be reverified against the exact final candidate Manifest using the accepted generic and type-specific verifiers.

A record that cannot be reverified against the final Manifest is rejected even if it was successfully signed during construction.

## Object index construction

Before Manifest finalization, the composer builds the exact sorted object index required by all accepted contracts.

At minimum it must include the exact descriptors required for:

- governing profile where the profile contract requires it;
- canonical ceremony;
- governance policy;
- governance proofs;
- authority evidence that accepted verifiers require through the object index;
- any additional authority-required object selected by the candidate profile.

Every descriptor is deduplicated by SHA-256.

Conflicting metadata is a hard failure.

## Governing source retention

Governing sources remain bound by the Manifest's `governing_sources` descriptors even when they are not represented as duplicate object-index entries.

The transaction's dependency-closure calculation must still retain their exact bytes unless already available inline through an accepted representation.

A URI alone is insufficient.

## Manifest finalization boundary

The Epoch Manifest payload is finalized only after all values it references are known.

That includes:

- final ceremony hash;
- exact governance proof hashes;
- exact participant standing record hashes;
- exact participant issuance record hashes;
- exact operator-selection record hash;
- exact Signing Node authorization record hash;
- final accepted-history head;
- final object-index descriptors;
- carried-forward or explicitly supplied optional history heads.

After deterministic encoding, the Manifest payload bytes are immutable.

A change to any of these inputs creates a different Manifest identity and therefore a different candidate.

## Optional history streams

The authority transition must preserve the accepted `witness`, `diagnostics`, and `knowledge` stream state represented by the predecessor replica.

The minimum reference transition composer carries their heads and exact retained sequence bytes forward unchanged unless another accepted contract explicitly supplies validated new records for one of those streams.

Piece 5 does not invent new mutation semantics for optional streams.

Bootstrap may use null optional heads when no accepted optional-stream content exists.

## Signed Manifest production

After the Manifest payload is final and passes deterministic/schema checks, the candidate Signing Node signs the exact Epoch Manifest Sig_structure.

The signing operation must use:

- the exact Signing Node public key/key ID in the candidate Manifest;
- an explicit candidate authority binding for the candidate epoch;
- the production signing contract from piece 4.

For a retained Signing Node key in a successor epoch, the same local key may be used under a new explicit candidate binding for E+1.

The predecessor epoch's current binding does not by itself sign for the successor authority context.

## Signed Manifest does not commit by itself

Persisting a valid signed candidate Manifest does not change current authority.

It remains candidate content until complete closure verification and selector commit.

This preserves the Epoch-1 and successor anti-self-authorization rules.

## Candidate signed Manifest persistence

The exact signed Manifest bytes must be content-addressed and retained before commit.

The resulting authority-state replica lineage descriptor records:

- epoch sequence;
- canonical Manifest payload SHA-256;
- signed Manifest SHA-256;
- signed Manifest byte length.

Those exact bytes must be loadable through the post-commit object loader.

## Building the resulting authority-state replica

After all candidate epoch bytes are fixed, the composer constructs the new participant authority-state replica.

For bootstrap it contains:

- the new root;
- current epoch sequence 1;
- one-entry signed Manifest lineage;
- complete accepted-history sequence descriptor;
- optional stream descriptors;
- exact externally required object inventory.

For successor it contains:

- the same HOA root;
- predecessor lineage unchanged plus one new lineage entry;
- current epoch sequence incremented by exactly one;
- current Manifest identity equal to the candidate Manifest;
- accepted-history descriptor for the cumulative sequence ending at the new head;
- carried-forward optional streams unless explicitly changed under an accepted contract;
- complete required-object inventory for the resulting lineage.

## Replica is deterministic retained-state inventory

The authority-state replica is not a second governance decision.

It inventories the exact bytes needed to reconstruct the accepted authority.

Its identity may be used by the local selector because verification of the replica deterministically reaches the signed authority lineage.

## Complete pre-commit verifier

A candidate may become VERIFIED only after a complete verifier establishes every applicable layer.

The minimum verification sequence is described below.

## 1. Verify predecessor/current snapshot

For successor:

- verify the selected predecessor authority-state replica;
- verify its complete signed Manifest lineage;
- verify its retained history;
- require candidate predecessor Manifest identity to equal that current state.

For bootstrap:

- require no existing accepted state for the transaction's authority domain.

## 2. Verify exact retained objects

Load all candidate authority-required bytes by exact SHA-256 and length.

Reject missing, corrupt, conflicting, or mutable substitutions.

## 3. Verify candidate Manifest schema and signature

Verify:

- deterministic canonical Manifest payload;
- schema;
- key-ID/public-key bindings;
- signed COSE envelope;
- candidate Signing Node signature.

Signature validity is necessary but not sufficient.

## 4. Verify canonical ceremony

Verify the exact ceremony bytes against the candidate Manifest and predecessor Manifest where required.

Require exact object-index binding.

## 5. Verify governance policy and proofs

Verify:

- policy exact bytes;
- source-set identity;
- proof exact bytes;
- proof signatures;
- exact ceremony proof set;
- proof signer authority under bootstrap/successor rules.

## 6. Verify complete accepted history

Verify the cumulative accepted CBOR Sequence from genesis through the candidate head.

For every record:

- verify deterministic exact bytes;
- verify generic signed-history envelope;
- verify authenticated predecessor linkage;
- resolve exactly one epoch authority context.

Require the final record identity to equal the candidate Manifest accepted-history head.

## 7. Verify mandatory candidate-epoch record inclusion

The exact new-epoch records referenced by the candidate Manifest must all be members of that verified accepted-history chain.

At minimum:

- Signing Node authorization;
- operator selection;
- every participant standing record;
- every participant issuance record.

A valid signed record outside the selected chain does not satisfy the Manifest.

## 8. Verify type-specific accepted records

Apply the accepted type-specific verifier to each required candidate-epoch record.

Require exact:

- participant identities and keys;
- standing identities;
- issuance identities;
- operator identity/provenance;
- Signing Node key/proof binding;
- epoch/root/ceremony context.

## 9. Verify participant standing

For every current participant, evaluate the exact accepted standing at the candidate effective time where the governing contract requires that evaluation.

Load and verify all authority-required standing evidence.

Do not infer standing from Manifest membership alone.

## 10. Verify complete governance transition

Apply the closure-piece-3 transition evaluator using:

- exact verified policy;
- exact verified ceremony;
- exact complete governance proof set;
- exact candidate Manifest;
- exact predecessor Manifest for successor;
- verified standing records from the selected accepted-history chain;
- exact authority-object loader.

Require successful electorate reconstruction, evidence sufficiency, quorum where applicable, and approval where applicable.

## 11. Verify operator and Signing Node authority

Require the exact candidate operator-selection record and Signing Node authorization record to match the Manifest and governance context.

Cryptographic possession alone is insufficient.

## 12. Verify Epoch-1 or successor closure

For bootstrap, apply the complete Epoch-1 bootstrap closure.

For successor, require:

- same HOA root;
- epoch sequence predecessor + 1;
- exact predecessor Manifest identity;
- continuing-participant key rotation;
- exact governance authorization of the proposed transition.

## 13. Verify resulting authority-state replica

Using the same post-commit object loader, apply the accepted authority-state replica verifier to the exact candidate replica bytes.

Require:

- complete signed Manifest lineage;
- required-object coverage;
- history stream/head consistency;
- exact byte availability.

## 14. Recheck commit predecessor

Immediately before selector commit, re-read the local accepted-state selector.

Require it still equals the transaction's expected predecessor selector.

This closes the race between verification and commit.

## Full verification must precede selection

The selector may not point at candidate state first and "finish validation afterward."

The required direction is:

~~~text
persist
    ->
verify complete candidate
    ->
atomic selector switch
~~~

not:

~~~text
selector switch
    ->
hope remaining validation succeeds
~~~

## Durable-before-visible rule

Every byte required to reconstruct the new selected state must be durably available before the selector can make that state current.

The exact platform mechanism may use:

- filesystem durability primitives;
- database durability;
- transactional storage;
- another equivalent mechanism.

Piece 5 freezes the outcome, not the specific syscall:

> after successful commit returns, a restart must either expose the old complete accepted state or the new complete accepted state.

It must not expose a partially installed hybrid.

## Atomicity boundary

The only mutable authority-selection operation is the final selector change.

All authority artifacts beneath it are immutable content-addressed bytes.

This reduces the atomicity problem to:

~~~text
many immutable writes
    +
one atomic pointer change
~~~

rather than attempting an atomic rewrite of every authority object.

## Crash before selector commit

If a process crashes after writing some or all candidate objects but before selector commit:

~~~text
current accepted authority = predecessor
candidate artifacts = unreferenced staging content
~~~

On restart, the implementation must not infer that the candidate was accepted because its files exist.

## Crash during selector commit

The selector mechanism must provide atomic old-or-new behavior.

After restart:

- old selector means predecessor remains current;
- new selector means the complete candidate replica must verify and is current;
- malformed/torn selector state is a hard local integrity failure.

The implementation must not choose whichever replica directory appears newest.

## Crash after selector commit

If commit succeeded and a later process crashes before cleanup or notification:

- the new selector remains current;
- candidate keys bound by the new accepted epoch are current by authority context;
- superseded bindings are historical/retired;
- cleanup may resume later.

Cleanup is not part of authority acceptance.

## Restart verification

At process startup, a conforming Signing Node must not trust the selector blindly.

It must:

1. load the selected replica bytes;
2. verify the replica identity;
3. verify enough of the accepted authority state to establish the current epoch and signer binding before current-authority signing is enabled.

Closure piece 6 will define the minimum startup conformance gate.

If selected state cannot verify, signing fails closed.

## Idempotent exact retry

If commit is retried and the selector already names the exact same candidate replica, the operation may return idempotent success after verification.

No new signing is required.

No new authority object is created.

## Retry before sealing

Before signed identities are incorporated into dependent objects, deterministic candidate construction steps may be repeated.

Recomputed deterministic bytes must be byte-identical.

A mismatch is a failure, not an invitation to choose one arbitrarily.

## Retry after sealing

After SEALED:

- exact signed bytes are reused;
- exact ceremony bytes are reused;
- exact history sequence bytes are reused;
- exact Manifest bytes are reused;
- exact replica bytes are reused.

Retry is transport/storage/commit retry, not semantic recomposition.

## Lost sealed artifact

If a sealed identity-bearing artifact is lost before acceptance and cannot be recovered by its SHA-256 identity, that candidate is incomplete.

The implementation must not silently re-sign one record and preserve downstream hashes as though nothing changed.

It must rebuild from the earliest dependency affected by that missing identity.

The rebuilt result is a new candidate.

## Duplicate candidate artifacts

Writing the same exact object more than once is idempotent.

Multiple copies do not give an object more authority.

Storage replica count is not governance weight.

## Duplicate complete candidate

The same exact complete candidate may be presented repeatedly.

If not yet current and the expected predecessor still matches, it may be verified and committed.

If already current, it is an idempotent replay.

If the current state has advanced beyond it, it is historical/stale and must not roll the selector backward.

## Replay of an old accepted state

A previously accepted valid replica remains historically valid evidence.

It does not automatically become current again.

The selector must not move backward merely because an older state verifies cryptographically.

Rollback requires whatever new source-governed transition the applicable contracts require; old bytes alone cannot authorize rollback.

## Competing successors from the same predecessor

Two different complete successor candidates may both be internally valid against the same predecessor.

Civic does not choose between them by:

- later timestamp;
- lexical hash order;
- more copies;
- filesystem mtime;
- process ID;
- machine administrator preference;
- "last writer wins."

After one exact successor is committed, the other becomes a conflicting fork/stale candidate.

That conflict is Diagnostics evidence.

It is not silently merged.

## Same ceremony, different signed-history bytes

Because signature bytes can differ between valid signers/providers, two independently composed candidates could share one ceremony while producing different signed-history record hashes and therefore different Manifest identities.

They are different candidates.

Semantic similarity does not make their byte identities interchangeable.

Replicas must distribute and install the one exact accepted candidate rather than independently re-compose "equivalent" bytes.

## No independent replica recomposition

A participant receiving an accepted authority update must receive or retrieve the exact accepted bytes.

It must not reconstruct a semantically equivalent Manifest or history sequence by re-signing or reordering records.

Verification is independent.

Composition of accepted bytes is singular for one candidate.

## Replica installation on participant devices

A receiving participant may use the same abstract transaction rule:

~~~text
receive exact candidate replica + dependencies
    ->
verify complete state
    ->
require expected predecessor/current lineage
    ->
atomically select exact replica
~~~

The participant's own private key remains outside the common replicated state.

Installing a replica does not import other participants' private keys or the Signing Node private key.

## Catch-up across more than one epoch

A participant that is behind by multiple epochs may receive a complete later replica containing the full signed lineage.

A conforming catch-up implementation must verify every missing lineage transition and all required retained material before selecting the later replica.

It must not skip semantic transition verification merely because the final signed Manifest is valid.

The exact batching/transport mechanism is not frozen here.

## No partial participant replication

A current participant replica must not advertise a new current Manifest while lacking authority-required bytes needed to reconstruct it.

Distribution may stage objects first.

Current-state selection happens last.

This is the same immutable-data-plus-one-selector rule used by the Signing Node.

## Accepted key binding after commit

After selector commit, current key authority is derived from the newly selected accepted state.

The implementation may update local caches, but those caches are projections.

For a newly accepted Signing Node:

~~~text
accepted Manifest signing_node key
    ->
current production signing binding
~~~

For superseded keys:

~~~text
not selected by current authority context
    ->
not current
~~~

A keystore mutation is not the authority transition.

## Failure before commit leaves keys unchanged in authority

If a candidate transition fails after generating new keys:

- predecessor current keys remain current;
- candidate keys remain candidate/unbound;
- no current key is retired;
- no candidate key is promoted.

This applies even if candidate keys successfully signed candidate artifacts.

## Failure after commit does not restore predecessor automatically

Once the atomic selector successfully commits the new accepted state, a later operational failure must not silently roll back to the predecessor.

The predecessor remains historical authority.

Returning to an earlier substantive state requires a new valid transition, not local rollback by file copy.

## Transaction cancellation

Cancellation before commit means ABORTED.

It may:

- release locks;
- stop composition;
- remove local staging metadata;
- optionally remove unreferenced candidate objects;
- optionally destroy candidate private keys under local policy.

Cancellation does not modify accepted authority.

## Candidate-object garbage collection

Unreferenced candidate artifacts may eventually be garbage-collected.

Garbage collection must first prove the bytes are not required by:

- any accepted authority-state replica in retained lineage;
- any current participant replica retention obligation;
- any retained Diagnostics policy that deliberately preserves the failed candidate.

The reference contract does not require preservation of every failed candidate forever.

It does require preservation of accepted authority material.

## Accepted-object retention

No object required to verify the accepted lineage may be garbage-collected merely because:

- it belongs to an old epoch;
- its private key was destroyed;
- the current operator changed;
- a newer profile exists;
- a newer Signing Node exists.

Historical public verification depends on retained accepted bytes.

## Transaction lock semantics

A conforming composer must serialize local commit attempts for one HOA authority domain or provide equivalent compare-and-swap isolation.

It need not globally prevent another machine from constructing a competing candidate.

The protocol makes such competition visible through predecessor/fork verification rather than assuming a universal distributed lock.

## One HOA domain per transaction

A transaction belongs to exactly one `hoa_root_id` authority domain once that root is known.

It must not atomically merge or co-commit two HOAs as though they shared one authority root.

Cross-HOA batch tooling may execute independent transactions, but failure/authority boundaries remain separate.

## Effective time is not transaction commit time

The candidate ceremony/Manifest `effective_time_ms` is an asserted authority field under existing contracts.

The local transaction may also record operational timestamps in staging/journal metadata.

Those are not interchangeable.

The transaction layer must not rewrite `effective_time_ms` to match the local commit clock.

## Source changes during composition

Once the candidate governing source/profile/policy exact bytes are frozen, a newly discovered or modified source does not mutate the candidate in place.

If that source materially belongs to the transition, abort/rebuild a new candidate with new exact identities.

This prevents mutable external interpretation from changing an already signed authority graph.

## Network retrieval failure

Missing required bytes cause verification failure.

The transaction may retry retrieval.

It must not:

- accept URI metadata instead of bytes;
- substitute a newer web version;
- omit an unavailable authority object;
- commit first and fetch later.

Authority-required reconstruction bytes must be present before commit.

## Signing-provider failure during composition

If a production signing provider becomes unavailable:

- do not substitute another key;
- do not auto-generate replacement authority;
- do not mark candidate current;
- preserve predecessor authority.

A deliberate provider migration using the same exact key remains piece-4 local custody behavior.

A different key requires a new candidate authority transition.

## History append failure

If a signed record is produced but cannot be durably appended to the candidate sequence:

- current accepted sequence remains unchanged;
- retain/recover the exact signed record if retrying the same candidate;
- do not advance the Manifest head independently.

The Manifest is finalized only from the exact successfully retained candidate sequence bytes.

## Manifest signing failure

If candidate Manifest signing fails:

- no selector change occurs;
- accepted predecessor remains current;
- candidate records and objects remain non-authoritative;
- the implementation may retry with the same candidate key/provider if piece 4 permits;
- if signed bytes change, treat the resulting signed envelope identity accordingly when building the replica.

The canonical Manifest payload identity itself does not change merely because its signature attempt failed.

## Replica construction failure

If replica encoding or closure derivation fails after a signed Manifest exists:

- the signed Manifest remains candidate content;
- current authority remains predecessor;
- fix/rebuild the candidate transaction;
- never point the selector directly at a signed Manifest without a reconstructable replica.

## Verification disagreement

If two conforming verification paths disagree about the same exact candidate bytes, the transaction must not commit based on "one passed."

The disagreement is Diagnostics.

The candidate remains non-authoritative until the discrepancy is resolved.

## No "best effort" acceptance

The transaction layer must not have a mode that commits while recording warnings for failed authority invariants.

Warnings may exist for non-authority operational conditions.

Any required authority verification failure prevents commit.

## Full current-state read consistency

A reader performing a current-authority operation should resolve the selector once and verify/read from that selected replica snapshot.

It must not combine:

- current Manifest from one replica;
- history sequence from another;
- object inventory from a third candidate.

This prevents torn logical reads even when immutable objects are shared.

## Publication boundary

A deployment may publish candidate material for review before commit, but it must be clearly non-authoritative.

After commit, publication/distribution of the exact selected replica and dependencies may proceed.

Publication is not acceptance.

Failure to publish to a remote service does not undo a successful local Civic authority commit.

## IPFS boundary

Future IPFS pinning may distribute exact authority objects after or during staging.

A CID remains retrieval metadata.

The transaction commits Civic SHA-256 identities and exact bytes, not "whatever the CID resolves to" without verification.

Loss of IPFS availability does not change the local accepted authority if required bytes remain reconstructable elsewhere.

## RAG/Diagnostics boundary

A RAG/LLM system may observe:

- candidate composition failures;
- missing dependencies;
- stale candidates;
- competing forks;
- failed commit preconditions;
- replica divergence.

It does not decide which candidate becomes current.

The source-governed Civic verifier and atomic selector rules remain authoritative.

## Reference composer logical algorithm

A reference implementation should follow the sequence below.

### Phase A — freeze predecessor

For successor:

1. read selected replica;
2. verify it;
3. retain exact predecessor selector identity;
4. retain exact current Manifest identity and history state.

For bootstrap:

1. require no selected replica;
2. generate/freeze candidate root ID.

### Phase B — freeze source and candidate core

Freeze exact:

- governing sources;
- governing profile;
- governance policy;
- participant identities;
- candidate participant public keys;
- operator identity;
- candidate Signing Node public key;
- effective time;
- transition kind/predecessor identity.

### Phase C — governance subject and proofs

1. derive canonical non-recursive transition subject;
2. collect/sign exact governance proofs;
3. verify proof syntax/signatures;
4. persist exact proof/evidence bytes;
5. compute sorted exact proof hash set.

### Phase D — ceremony

1. construct final ceremony with exact governance proof set;
2. deterministic-encode;
3. compute ceremony SHA-256;
4. persist exact ceremony bytes.

### Phase E — accepted-history records

Starting from predecessor accepted-history head or null:

1. compose/sign Signing Node authorization;
2. compose/sign operator selection;
3. compose/sign standing for participants in sorted participant-identity order;
4. compose/sign issuance for participants in the same sorted order using exact standing hashes;
5. append each exact signed record to candidate accepted sequence;
6. retain every exact record identity;
7. set candidate accepted-history head to final record identity.

### Phase F — object index and Manifest

1. compute exact authority-required object closure;
2. construct sorted deduplicated object index;
3. populate exact participant standing/issuance record hashes;
4. populate exact operator selection record hash;
5. populate exact Signing Node authorization record hash;
6. populate final accepted-history head;
7. carry forward permitted optional history heads;
8. deterministic-encode final Manifest;
9. compute Manifest payload SHA-256.

### Phase G — sign Manifest

1. resolve exact candidate Signing Node binding;
2. sign exact Manifest Sig_structure;
3. self-verify production signature;
4. build exact COSE_Sign1;
5. persist exact signed Manifest bytes.

### Phase H — build replica

1. append exact new signed Manifest descriptor to lineage;
2. describe exact cumulative accepted-history sequence;
3. carry forward optional sequence descriptors;
4. derive complete external required-object inventory;
5. deterministic-encode replica;
6. compute replica SHA-256;
7. persist exact replica bytes.

### Phase I — complete verification

Run the complete pre-commit verifier from exact persisted bytes.

No in-memory shortcut satisfies this phase.

### Phase J — atomic commit

1. re-read current selector;
2. compare with expected predecessor selector;
3. if mismatch, fail stale/forked;
4. atomically select exact verified replica;
5. report commit success.

### Phase K — post-commit projection

After successful commit:

- derive current key bindings from selected authority state;
- permit current-authority signing only after current state verifies;
- replicate exact accepted bytes to participants;
- perform cleanup asynchronously.

Post-commit projection is not part of the authority decision itself.

## Bootstrap composition specialization

For bootstrap:

~~~text
predecessor selector = none
predecessor Manifest = null
prior accepted sequence = empty
prior accepted head = null
epoch sequence = 1
~~~

The final commit must fail if accepted state appeared while bootstrap was being constructed.

The candidate root does not gain authority before the selector commit.

## Successor composition specialization

For successor:

~~~text
candidate.hoa_root_id
    = predecessor.hoa_root_id

candidate.epoch_sequence
    = predecessor.epoch_sequence + 1

candidate.predecessor_manifest_sha256
    = exact predecessor Manifest payload SHA-256
~~~

The accepted sequence is predecessor sequence plus the canonical new record suffix.

The candidate cannot be committed if the selected predecessor changes before commit.

## Retained Signing Node specialization

When the same Signing Node key is deliberately retained:

- candidate ceremony names the same public key/key ID;
- new epoch has a new Signing Node authorization record;
- new Manifest is signed under an explicit candidate binding for the successor epoch;
- commit establishes the new epoch binding.

The old local private key does not need to be copied or regenerated.

## Replacement Signing Node specialization

When the Signing Node is replaced:

- generate separate candidate key material;
- candidate ceremony names the replacement key;
- governance proofs authorize the transition;
- new authorization record binds that key;
- candidate Manifest is signed by that candidate node key;
- old node remains current until final commit;
- after commit, old node key is no longer current under the selected authority state.

There is no interval where both keys become current merely because both are locally available.

## Continuing participant specialization

A continuing participant in a successor epoch receives a newly generated participant key as required by the ceremony contract.

The candidate standing/issuance records bind the new key.

Successor governance proofs remain signed using the predecessor participant key where piece 3 requires that signer.

This preserves:

~~~text
predecessor key
    -> authorizes transition as electorate member

successor key
    -> becomes current only after transition acceptance
~~~

## New participant specialization

A participant not present in the predecessor electorate cannot authorize its own admission merely by signing with a new candidate key.

Its new standing/issuance records are candidate records.

Governance authorization comes from the source-derived transition semantics.

## Removed participant specialization

A participant omitted from the successor Manifest remains historical in prior epochs.

The successor transaction does not delete its prior records or public keys.

Its prior private key, if still physically present, is not current authority under the successor state.

## Operator-change specialization

The candidate ceremony commits the new operator participant identity.

The canonical operator-selection record binds that identity and the relevant proof subset.

Current operator authority changes only with final transaction commit.

The old operator does not lose historical attribution.

## Profile/source-change specialization

A successor may change governing profile/source state only when:

- candidate ceremony commits the new profile descriptor;
- governance policy/proofs authorize the exact transition;
- all new required source/profile bytes are retained;
- participant standing under the new profile satisfies the applicable candidate-time semantics;
- complete closure verification succeeds.

The transaction layer does not infer legal equivalence between old and new sources.

## Diagnostics classifications

A reference implementation should distinguish at least:

~~~text
candidate-incomplete
candidate-invalid
candidate-stale
candidate-fork-conflict
dependency-missing
dependency-conflict
signature-failure
history-link-failure
governance-failure
standing-failure
replica-closure-failure
commit-precondition-failure
selector-integrity-failure
~~~

These classifications aid Diagnostics.

They do not change authority semantics.

## No automatic fork resolution

If two replicas each claim to be successors of the same accepted predecessor, the node must not auto-resolve by hash order, timestamp, or storage count.

A selected current successor remains selected locally.

The competing branch remains explicit fork evidence.

A later source-governed transition may resolve consequences, but the transaction engine does not invent that governance.

## No rollback by operator preference

An operator cannot make an old replica current simply by changing the selector through an administrative shortcut exposed by normal Civic tooling.

Any ordinary current-state transition must pass the same accepted governance/transaction requirements.

Low-level disaster-recovery access may exist outside normal Civic operation, but if it produces state inconsistent with authenticated lineage the system must fail verification rather than bless the change.

## Recovery after storage loss

If the Signing Node loses its local accepted objects but a current participant supplies a complete accepted replica:

1. import exact immutable bytes as unselected reconstruction data;
2. verify complete lineage and authority;
3. establish which replica is recognized as current under the recovery/governance context;
4. atomically select only after verification.

Importing bytes is not authority by itself.

Replacement of a lost Signing Node private key remains the governed piece-4 recovery path.

## Implementation boundary

A future implementation should expose a clear separation between:

~~~text
candidate composer
complete verifier
immutable object store
accepted-state selector
production signer provider
~~~

No one module should be able to create current authority merely by writing a key file or a Manifest file.

## Minimum implementation acceptance properties

Before piece 5 implementation is accepted, focused tests must establish at least:

1. bootstrap begins only from no accepted selector;
2. successor begins from one verified predecessor replica;
3. canonical accepted-history record suffix order is deterministic;
4. standing records precede their issuance dependencies;
5. successor accepted sequence preserves predecessor bytes exactly;
6. ceremony is finalized before history records bind its hash;
7. Manifest is finalized only after exact record hashes/history head exist;
8. all immutable dependencies are persisted before selector commit;
9. complete verification runs against persisted exact bytes;
10. selector commit is compare-and-swap against expected predecessor;
11. crash/failure before selector commit leaves predecessor selected;
12. exact retry of already committed replica is idempotent;
13. stale candidate cannot overwrite a newer current state;
14. competing successor is surfaced as fork/stale failure;
15. no key generation or candidate signature activates authority;
16. signed record bytes are reused after sealing rather than silently re-signed;
17. missing required object prevents commit;
18. corrupted retained object prevents commit;
19. failed governance prevents commit;
20. failed standing prevents commit;
21. wrong history head prevents commit;
22. wrong Manifest predecessor prevents commit;
23. replica closure failure prevents commit;
24. restart/current read does not choose state by filesystem recency;
25. accepted state exposes one complete old-or-new snapshot, never a hybrid.

Fault-injection tests should exercise failure at multiple boundaries between immutable writes and selector commit.

## No real HOA activation during implementation tests

Piece-5 implementation tests may create:

- temporary object stores;
- temporary selectors;
- ephemeral software-provider keys;
- fixture authority bundles;
- deterministic test history.

They must not create or activate a real HOA production authority.

Repository implementation acceptance remains distinct from deployment.

## Relationship to closure piece 6

Piece 6 will define the minimum platform-neutral behavior of a production Civic Signing Node.

It should require capabilities derived from piece 5, including:

- immutable authority-object retention;
- complete candidate verification;
- atomic accepted-state selection;
- fail-closed startup verification;
- production signer-provider integration;
- participant replica export/import;
- recovery from participant-held accepted state.

Piece 6 must not redefine the transaction semantics frozen here.

## Annales boundary

This contract intentionally contains no Annales-specific:

- hostname;
- LXD container name;
- systemd unit;
- filesystem path;
- Unix account;
- network address/port;
- key path;
- database choice;
- backup directory;
- deployment command.

Those belong to the later separate Annales production implementation project.

## Decision summary

The accepted transaction model is:

~~~text
verified predecessor snapshot
        |
        v
freeze candidate source/core state
        |
        v
governance subject
        |
        v
exact governance proofs
        |
        v
final ceremony
        |
        v
canonical accepted-history suffix
        |
        v
final accepted-history head
        |
        v
final Epoch Manifest
        |
        v
signed Epoch Manifest
        |
        v
complete authority-state replica
        |
        v
verify all exact persisted bytes
        |
        v
compare expected predecessor selector
        |
        v
ATOMIC SELECTOR COMMIT
        |
        v
new current authority

anything fails before selector commit
        ->
predecessor remains current
~~~

The durable implementation principle is:

~~~text
immutable bytes first
complete verification second
one atomic current-state selection last
~~~

This preserves source-derived governance, exact-byte identity, append-only history, participant reconstruction, and the piece-4 rule that private-key custody never defines current Civic authority.

## Closure result

This document freezes closure piece 5 at the architecture level.

It authorizes a later bounded implementation of:

- candidate composition;
- complete transition verification orchestration;
- immutable candidate persistence;
- local atomic accepted-state selection;

using ephemeral test authority only until a later deployment project explicitly creates real HOA production state.

After piece-5 implementation/test acceptance, the final Kane Fabric reference-closure item is piece 6:

> platform-neutral Civic Signing Node conformance and deployment boundary.
