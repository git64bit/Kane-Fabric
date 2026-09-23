# Civic Epoch-1 Bootstrap Contract

## Status

Architecture contract for closure piece 1 of the Civic authority-reference milestone.

This document defines how one HOA-local Civic authority domain may establish its first accepted authority epoch without pretending that an already-existing Civic authority authorized its own creation.

It is documentation only.

It does not:

- create a production Civic private key;
- enable production Civic signing;
- mutate `annales`;
- define the canonical ceremony-record bytes;
- define governance-proof record/object schemas;
- select Linux paths, services, containers, or deployment tooling;
- turn a candidate Signing Node into accepted authority merely because it possesses a private key.

The exact ceremony-record contract is closure piece 2.

The governance-proof contract and semantic verifier are closure piece 3.

Production signing/key lifecycle, authority-state transaction composition, and platform-neutral Signing Node conformance remain closure pieces 4, 5, and 6.

## Purpose

Every later Civic authority epoch can point backward to an accepted predecessor Epoch Manifest.

Epoch 1 cannot.

Therefore the initial authority domain has a special problem:

~~~text
later epoch
    predecessor accepted authority
        ->
    source-governed transition
        ->
    successor accepted authority

epoch 1
    no predecessor Civic authority exists
~~~

Epoch 1 must not solve that absence by silently elevating one of the following into a permanent root of authority:

- the bootstrap operator;
- the first Signing Node;
- the first participant;
- a machine hostname;
- a server;
- an ESP32;
- one private key;
- a Kane Fabric account;
- a central service;
- a hidden database row;
- repository ownership;
- the implementation that happened to create the first files.

The bootstrap authority boundary is instead:

~~~text
applicable governing sources
        +
published source-derived bootstrap/governance semantics
        +
retained governance evidence
        +
canonical ceremony commitment
        +
candidate epoch keys and records
        +
complete cross-consistency verification
        =
accepted Epoch 1
~~~

The cryptography proves attribution, exact bytes, and linkage.

The governing-source/proof layer establishes or fails to establish why the initial authority state is acceptable.

## Core rule

Epoch 1 is accepted only as a **closed bootstrap authority bundle**.

No individual artifact inside the bundle is independently sufficient to create Civic authority.

In particular:

~~~text
candidate Signing Node key exists
    !=
Signing Node is authorized

candidate participant key exists
    !=
participant is accepted

candidate operator is named
    !=
operator is validly selected

candidate Epoch Manifest is signed
    !=
Epoch 1 is accepted

candidate ceremony exists
    !=
governance requirements were satisfied
~~~

Only the complete verified bundle establishes the initial accepted Civic authority state.

## Bootstrap is a one-time authority condition

Bootstrap semantics apply only when:

~~~text
epoch_sequence = 1
predecessor_manifest_sha256 = null
~~~

Once Epoch 1 has been accepted, a later epoch must use ordinary continuity and successor-epoch semantics.

A later implementation must not invoke "bootstrap" to bypass an existing authority lineage.

Therefore:

~~~text
accepted Epoch 1 exists
    ->
bootstrap path is closed for that HOA root
~~~

A new machine, replacement Signing Node, replacement operator, participant-set change, or governing-profile change is not a new bootstrap merely because infrastructure was lost or replaced.

Those are continuity/recovery/epoch-transition cases.

## Candidate state versus accepted authority

A bootstrap implementation may create candidate material before authority exists.

Examples include:

- a candidate 32-byte HOA root identifier;
- candidate participant epoch keys;
- a candidate Signing Node key;
- candidate governance-evidence objects;
- a candidate ceremony record;
- candidate accepted-history records;
- a candidate Epoch Manifest;
- a candidate signed Epoch Manifest.

This material is **staging state**.

It does not become accepted Civic authority until the complete bootstrap verifier succeeds.

This distinction permits practical construction without circular reasoning:

~~~text
generate candidate material
        ->
construct internally consistent candidate bundle
        ->
verify complete bundle
        ->
atomically accept Epoch 1
~~~

Failure before the final acceptance step leaves candidate material non-authoritative.

## HOA root identity

Epoch 1 establishes exactly one stable:

~~~text
hoa_root_id = bytes(32)
~~~

The v1 bootstrap root identifier is an opaque 32-byte value generated once for the candidate authority domain using a cryptographically strong random source.

The root identifier is public identity material, not a secret.

It must not be derived from:

- Signing Node public or private key;
- participant public or private key;
- operator identity;
- legal name of a participant;
- postal address;
- condominium unit number;
- association name;
- IP address;
- MAC address;
- hostname;
- LXD/container identifier;
- filesystem path;
- machine serial number;
- repository commit;
- governing-profile hash.

The root identifier becomes authoritative only when the complete Epoch-1 bundle is accepted.

After acceptance, the exact `hoa_root_id` remains stable across:

- operator changes;
- Signing Node replacement;
- participant changes;
- hardware replacement;
- network changes;
- storage migration;
- successor authority epochs.

No permanent HOA root private key is created or implied.

## Initial governing-source boundary

Before Epoch 1 may be accepted, the candidate epoch must identify the exact governing material under which initial standing and governance are evaluated.

At minimum the bootstrap bundle must retain and bind:

~~~text
governing_profile
governing_sources
canonical source-set identity
source-derived governance semantics
~~~

The already accepted canonical governing-profile contract continues to govern participant-standing semantics.

Bootstrap/governance semantics that are not standing semantics must not be smuggled into an arbitrary callback, implementation constant, administrator decision, or hidden configuration file.

Closure piece 3 must make the governance-proof semantics independently inspectable and reproducible.

## Initial participant set

Epoch 1 must contain at least one current participant because the accepted Epoch Manifest requires a current operator and the operator must resolve to a current participant.

Each participant in the initial manifest must have:

- one opaque participant identity;
- one epoch-specific participant public key and key identifier;
- one exact accepted participant-standing record;
- one exact accepted participant-issuance record.

For every initial participant, bootstrap verification must establish the already accepted participant invariants:

~~~text
manifest participant descriptor
    <->
exact issuance record
    <->
exact standing record
    <->
canonical governing profile
    <->
authority-required evidence
~~~

Initial participant keys may be generated before the epoch is accepted.

Key generation does not itself admit the participant.

Initial standing and issuance records may be created as candidate records using the candidate Epoch Manifest as cryptographic context.

They become authoritative only when the complete bootstrap bundle closes successfully.

## Initial standing evaluation time

For bootstrap acceptance, every initial participant's standing must be evaluated at:

~~~text
evaluation_time_ms = Epoch Manifest effective_time_ms
~~~

This provides one deterministic currentness point for the initial authority snapshot.

An initial participant whose accepted standing is not current at the candidate Epoch Manifest effective time cannot be included in the accepted Epoch-1 participant set.

Historical or future standing may still exist as evidence, but it does not satisfy current bootstrap membership.

## Initial operator

Epoch 1 names exactly one current operator:

~~~text
manifest.operator.participant_record_sha256
~~~

That identity must resolve to exactly one participant in the initial participant set.

The exact operator-selection record identified by:

~~~text
manifest.operator.selection_record_sha256
~~~

must satisfy the already accepted operator-selection record contract.

However, structural validity of the operator-selection record is not enough to create bootstrap authority.

The bootstrap verifier must also establish that the source-derived governance evidence is sufficient to designate the initial operator under the closure-piece-3 governance-proof contract.

Therefore:

~~~text
operator-selection record verifies
    != by itself
initial operator is source-authorized
~~~

The bootstrap process must not silently interpret "person who ran the software" or "owner of the machine" as operator authorization.

## Initial Signing Node

A candidate Signing Node key may be generated before Epoch 1 exists.

Its public identity is:

~~~text
public_key = accepted 65-byte SEC1 P-256 public key
key_id = SHA-256(exact public_key bytes)
~~~

The candidate private key is not part of replicated authority state.

The candidate node may use its private key to prove possession and to sign candidate Civic objects before the bootstrap bundle has been accepted.

That activity remains candidate activity.

The exact Signing Node authorization record identified by:

~~~text
manifest.signing_node.authorization_record_sha256
~~~

must satisfy the already accepted Signing Node authorization record contract.

The node signature proves possession and attribution.

It does not prove bootstrap authorization.

The bootstrap verifier must separately establish that the exact governance-proof set committed by the ceremony authorizes that candidate Signing Node for Epoch 1.

## No self-authorization

The following bootstrap argument is invalid:

~~~text
the candidate node created a key
the candidate node signed its authorization record
the candidate node signed the Epoch Manifest
therefore the node and manifest are authoritative
~~~

The correct relationship is:

~~~text
candidate node signature
    -> proves possession / attribution

source-derived governance proof
    -> proves or fails to prove authorization conditions

ceremony record
    -> commits the bootstrap authority decision and proof context

accepted-history records
    -> bind participant/operator/node facts

Epoch Manifest
    -> selects the complete candidate authority snapshot

complete bundle verification
    -> accepts or rejects Epoch 1
~~~

## Ceremony boundary

Epoch 1 requires one exact canonical ceremony object identified by:

~~~text
manifest.ceremony.ceremony_record_sha256
~~~

This bootstrap contract requires that the ceremony record, when closure piece 2 freezes it, bind enough information to prevent ambiguity about the candidate genesis authority state.

At minimum its semantics must commit to:

- the exact `hoa_root_id`;
- `epoch_sequence = 1`;
- absence of a predecessor manifest;
- the candidate governing-profile/source context;
- the initial participant set or an exact commitment to it;
- the initial operator or an exact commitment to it;
- the candidate Signing Node key identity;
- the exact governance-proof set;
- the governance-proof semantic-policy identity;
- the asserted effective time.

The exact fields, canonical encoding, media type, hash calculation, and anti-self-reference construction are deliberately deferred to closure piece 2.

The ceremony record is not automatically a generic Civic history record.

## Governance-proof boundary

The Epoch Manifest already carries:

~~~text
ceremony.governance_proof_sha256
~~~

For Epoch 1, each proof hash must resolve to exact retained authority-required content.

A digest proves only exact content identity.

It does not prove governance sufficiency.

Closure piece 3 must therefore define:

- canonical governance-proof object/record forms;
- the exact proof-policy identity used for interpretation;
- how governing sources bind that policy;
- proof roles;
- threshold or sufficiency semantics where applicable;
- signer/attester provenance where applicable;
- evidence retention requirements;
- deterministic failure behavior;
- how the bootstrap verifier decides whether the initial participant/operator/node state is authorized.

Until that contract verifies, an Epoch-1 bundle is not semantically complete.

## Genesis accepted-history requirement

A valid Epoch-1 manifest has a non-null:

~~~text
accepted_history_head_sha256
~~~

Therefore bootstrap must construct one complete accepted history from genesis.

At minimum, that accepted chain must contain the exact accepted-history records required by the initial manifest:

- one participant-standing record for every initial participant;
- one participant-issuance record for every initial participant;
- the exact operator-selection record;
- the exact Signing Node authorization record.

Every record must use:

~~~text
hoa_root_id = candidate Epoch-1 hoa_root_id
epoch_sequence = 1
ceremony_record_sha256 = exact bootstrap ceremony hash
history_link.stream = "accepted"
~~~

The first accepted-history record has:

~~~text
predecessor_record_sha256 = null
~~~

Every successor names the exact SHA-256 identity of the preceding signed record.

The final record identity must equal:

~~~text
manifest.history.accepted_history_head_sha256
~~~

This contract does not impose one universal semantic ordering among otherwise valid bootstrap record types.

Closure piece 5 may define a deterministic construction order for the reference composition implementation.

Regardless of construction order, the complete selected accepted-history chain must contain every exact record referenced by the Epoch-1 manifest.

## Candidate-manifest context is permitted

Several accepted Civic record verifiers resolve signer keys and authority context from an Epoch Manifest.

During bootstrap, no accepted manifest exists yet.

It is therefore permitted to use the **candidate Epoch-1 manifest** as provisional cryptographic context while constructing and verifying candidate signed records.

This does not mean the candidate manifest is already accepted.

The rule is:

~~~text
candidate manifest may resolve candidate cryptographic context

but

candidate manifest becomes accepted authority
only after the complete bootstrap closure verifies
~~~

This is a dependency graph, not a claim of prior authority.

No content-hash self-reference is introduced because accepted-history records bind the authority-context tuple and ceremony hash, not the final Epoch Manifest hash.

## Signed Epoch Manifest

After the candidate manifest payload is complete, the candidate Signing Node may produce its COSE_Sign1 signature using the accepted Civic cryptographic profile.

The signature proves that the candidate node possessing the private key corresponding to:

~~~text
manifest.signing_node.public_key
~~~

signed the exact manifest payload.

The signed manifest is not accepted merely because the signature verifies.

Bootstrap acceptance also requires all other closure conditions in this document.

## Bootstrap authority bundle

The minimum Epoch-1 authority bundle consists of exact retained bytes sufficient to reconstruct and independently verify:

1. the signed Epoch-1 Manifest;
2. the canonical bootstrap ceremony record;
3. every authority-required governance-proof object;
4. the governance-proof semantic-policy object or exact bound policy identity required by closure piece 3;
5. the canonical governing profile;
6. all governing-source objects required by the profile and bootstrap governance semantics;
7. the complete accepted-history chain back to its genesis record;
8. every authority-required evidence object referenced by participant standing or bootstrap governance;
9. all other objects declared authority-required by the Epoch-1 object index.

Private keys are not members of the authority bundle.

A participant replica may separately retain that participant's own private key for future participation.

The Signing Node separately retains its private key under the production key-lifecycle contract.

## Bootstrap verification closure

A conforming Epoch-1 verifier must treat the candidate bundle as non-authoritative until all applicable checks succeed.

Conceptually:

~~~text
verify deterministic encodings
        +
verify object hashes and lengths
        +
verify canonical governing profile
        +
verify governing-source bindings
        +
verify ceremony record
        +
verify governance proofs semantically
        +
verify complete accepted-history linkage
        +
verify every initial participant standing
        +
verify every initial participant issuance
        +
verify initial operator selection
        +
verify Signing Node authorization
        +
verify signed Epoch Manifest
        +
verify every manifest cross-reference
        =
accepted Epoch 1
~~~

No subset is sufficient.

## Bootstrap verification algorithm

A reference verifier should perform at least the following logical steps.

### 1. Load candidate bundle

Load exact candidate signed-manifest bytes, accepted-history bytes, ceremony bytes, profile bytes, governing sources, governance proofs, and authority-required objects.

Do not fetch mutable network content as a silent substitute for missing authority bytes.

### 2. Parse candidate Epoch Manifest

Verify deterministic canonical encoding and v1 schema.

Require:

~~~text
epoch_sequence = 1
predecessor_manifest_sha256 = null
~~~

Reject any attempt to use the bootstrap verifier for a later epoch.

### 3. Verify root identity shape

Require exactly 32 bytes.

Require the same root identifier across every bootstrap object whose schema carries `hoa_root_id`.

The verifier does not attempt to infer the root identifier from a person, device, key, hostname, or address.

### 4. Verify governing profile and sources

Apply the accepted canonical governing-profile verifier.

Require exact profile/source-set/object identities and all authority-required source bytes.

### 5. Verify ceremony

Apply closure piece 2.

Require exact ceremony hash equality with:

~~~text
manifest.ceremony.ceremony_record_sha256
~~~

Require ceremony semantics to describe this candidate Epoch-1 authority context.

### 6. Verify governance proofs

Apply closure piece 3.

Require exact proof-set equality or other exact relationship defined by the ceremony/governance-proof contracts.

Require semantic sufficiency for bootstrap authorization.

### 7. Verify accepted history

Verify the complete `accepted` stream from null predecessor to the exact manifest head.

Require every manifest-referenced accepted authority record to lie on that selected chain.

A valid signed record stored elsewhere is insufficient.

### 8. Verify initial participants

For every manifest participant:

- verify exact issuance record;
- verify exact standing record;
- evaluate standing at `manifest.effective_time_ms`;
- verify participant key binding;
- verify recording/issuing operator provenance;
- verify authority-required evidence availability.

Reject duplicate or unresolved participant identities.

### 9. Verify initial operator

Require the manifest operator to resolve to exactly one current participant.

Verify the exact operator-selection record.

Require closure-piece-3 governance semantics to establish that the initial operator designation is sufficient.

### 10. Verify Signing Node

Verify the exact Signing Node authorization record.

Require exact key ID/public-key binding and proof-of-possession signature.

Require closure-piece-3 governance semantics to establish that the candidate node is authorized for Epoch 1.

### 11. Verify signed manifest

Verify the exact signed Epoch Manifest using the candidate Signing Node public key named by the manifest.

Signature validity remains attribution, not the sole authority condition.

### 12. Verify authority-state reconstructability

Require that the accepted Epoch-1 state can be represented as a complete participant authority-state replica under the already accepted reconstruction contract.

Missing authority-required bytes fail bootstrap acceptance.

### 13. Commit acceptance atomically

Only after every preceding check succeeds may the implementation designate the bundle as the accepted current Epoch-1 authority state.

Closure piece 5 defines the production transaction/composition mechanics for that atomic transition.

## Failure semantics

Bootstrap failure must be explicit.

The implementation must reject the candidate bundle if any required relationship fails, including:

- epoch sequence is not exactly 1;
- predecessor is non-null;
- root identity is malformed or inconsistent;
- profile or source-set identity fails;
- governing source bytes are missing or corrupt;
- ceremony bytes are missing, corrupt, or inconsistent;
- governance proof is missing, corrupt, undeclared, or semantically insufficient;
- accepted history is incomplete, forked, reordered, or terminates at the wrong head;
- manifest references a standing, issuance, operator-selection, or Signing Node authorization record outside the selected accepted history;
- an initial participant lacks current standing at the manifest effective time;
- participant key bindings fail;
- operator does not resolve to one current participant;
- operator-selection governance semantics fail;
- Signing Node authorization or proof-of-possession fails;
- signed manifest verification fails;
- an authority-required object is missing;
- complete participant authority-state reconstruction fails.

A failed candidate bootstrap is not repaired heuristically.

The implementation may preserve failed candidate artifacts as Diagnostics evidence, but it must not expose them as current accepted authority.

## No majority-by-files rule

If two different candidate Epoch-1 bundles exist for the same intended HOA, Civic must not select one merely because:

- one has a newer filesystem timestamp;
- one exists on more disks;
- one was created by the current machine administrator;
- one was signed later;
- one has more copied byte-identical replicas;
- one is hosted on the expected hostname.

Bootstrap authority follows the applicable governing/proof semantics and exact accepted bundle, not storage popularity.

If no bundle can establish the required source-derived bootstrap authority, there is no accepted Epoch 1 yet.

## No hidden institutional privilege

The bootstrap contract does not automatically grant authority to:

- an HOA board;
- a property manager;
- a management company;
- a Kane Fabric developer;
- the owner of `annales`;
- the person who runs the bootstrap command;
- the first SASE validator;
- a county-wide service operator.

If an applicable governing source gives a particular actor a relevant role, that role must enter through the published source-derived governance-proof semantics.

Civic does not manufacture such authority itself.

## Relationship to source truth

Bootstrap verification is not a legal-truth oracle.

It can establish:

- exact source/evidence bytes;
- exact published policy identity;
- cryptographic attribution;
- record linkage;
- deterministic semantic satisfaction under the published contract;
- whether the retained bundle meets the Civic bootstrap contract.

It does not transform a disputed governing-source interpretation into unquestionable legal truth merely because software evaluated it.

Disagreement, contradiction, or missing authority remains inspectable Diagnostics material.

## Successor-epoch boundary

After Epoch 1 is accepted:

~~~text
Epoch 1 manifest_sha256
    ->
successor ceremony/governance transition
    ->
Epoch 2 predecessor_manifest_sha256 = Epoch 1 manifest_sha256
~~~

Successor epochs inherit the stable `hoa_root_id`.

They do not reuse the bootstrap exception.

A replacement Signing Node receives a new authorization relationship under the successor epoch.

A participant-set or operator change follows the applicable source-derived governance process.

Old Epoch-1 keys and records remain historical verification material but do not automatically establish current authority in later epochs.

## Separation from production key lifecycle

This contract specifies when candidate keys become part of accepted authority.

It does not define how a production implementation:

- generates entropy;
- stores private keys;
- sets filesystem permissions;
- encrypts private-key files;
- loads keys into memory;
- obtains signing nonces;
- rotates keys;
- destroys superseded key material;
- backs up or deliberately declines to back up Signing Node private keys.

Those are closure-piece-4 concerns.

No hardware security module, proprietary signer, ATECC608A-class secure element, or irreversible ESP eFuse state becomes a baseline requirement.

## Separation from transaction/composition implementation

This contract defines the logical closure condition.

It does not define:

- temporary filesystem paths;
- staging-directory names;
- journal format;
- database transaction mechanism;
- fsync strategy;
- lock files;
- crash-recovery commands;
- deterministic bootstrap record construction order;
- process boundaries;
- CLI syntax.

Those belong to closure piece 5.

The implementation must ultimately preserve the invariant:

~~~text
partially constructed bootstrap
    !=
accepted Epoch 1
~~~

## Separation from deployment

Nothing in this contract requires `annales`.

A conforming bootstrap implementation may run on another independently controlled platform.

The later Annales project may implement this contract, but it must not redefine it.

Kane Fabric remains the reference authority contract.

## Closure dependencies

This bootstrap architecture is complete only in combination with the remaining five closure pieces:

~~~text
1. Epoch-1 bootstrap contract
       [this document]

2. canonical ceremony-record contract
       supplies exact ceremony bytes and anti-self-reference form

3. governance-proof contract/verifier
       supplies source-derived authorization semantics

4. production signing/key-lifecycle contract
       supplies real candidate participant/node key generation and signing

5. authority-state transaction/composition contract
       supplies safe bundle construction and atomic acceptance

6. Signing Node conformance/deployment boundary
       supplies platform-neutral requirements for a production node
~~~

No Annales-specific operational decision belongs in this document.

## Decision summary

The accepted Epoch-1 bootstrap model is:

~~~text
no prior Civic authority
        ↓
freeze exact governing sources/profile
        ↓
create opaque candidate HOA root identifier
        ↓
generate candidate participant and Signing Node keys
        ↓
collect exact source-derived governance proof
        ↓
create canonical bootstrap ceremony
        ↓
construct candidate accepted-history authority records
        ↓
construct and sign candidate Epoch-1 Manifest
        ↓
verify complete closed authority bundle
        ↓
atomically accept Epoch 1
        ↓
replicate complete accepted authority state
~~~

The durable rule is:

~~~text
candidate cryptographic consistency
    !=
accepted bootstrap authority

accepted Epoch 1
    =
complete source-grounded bundle closure
~~~

This removes the bootstrap circularity without introducing a permanent master key, privileged machine, hidden administrator, or self-authorizing Signing Node.
