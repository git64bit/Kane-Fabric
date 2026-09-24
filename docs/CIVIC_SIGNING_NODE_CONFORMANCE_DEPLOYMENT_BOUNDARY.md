# Civic Signing Node Conformance and Deployment Boundary

## Status

Architecture contract for Kane Fabric Civic reference closure piece 6.

Documentation only.

This is the final architecture piece required before Kane Fabric Civic Authority Reference v1 closure.

This contract does **not**:

- deploy a production Civic Signing Node;
- create a real HOA Civic private key;
- enable production Civic signing;
- activate a Civic authority domain;
- mutate annales;
- select a mandatory operating system, container runtime, service manager, database, filesystem layout, network port, or hardware platform;
- define Annales-specific deployment instructions.

Current production boundary remains:

~~~text
production_signing_enabled = false
production_key_created = false
annales_mutated = false
~~~

## Purpose

The earlier Civic closure pieces define:

1. Epoch-1 bootstrap authority;
2. canonical ceremony records;
3. governance policy/proof and complete transition verification;
4. production private-key/signing lifecycle;
5. authority-state transaction composition and atomic acceptance.

Piece 6 defines what an implementation must provide to be called a conforming Civic Signing Node.

The node is a replaceable local authority appliance.

It is not the permanent HOA Civic Identity.

The permanent continuity substrate is the authenticated Civic authority lineage and exact replicated authority state.

## Governing contracts

A conforming Signing Node must preserve:

- `docs/CIVIC_CRYPTOGRAPHIC_BASELINE.md`;
- `docs/CIVIC_AUTHORITY_CONTINUITY_DECISION.md`;
- `docs/CIVIC_AUTHORITY_EPOCH_CEREMONY.md`;
- `docs/CIVIC_OWNER_OPERATED_SIGNING_NODE.md`;
- `docs/CIVIC_EPOCH_MANIFEST_FORMAT.md`;
- `docs/CIVIC_SIGNED_HISTORY_RECORD_ENVELOPE.md`;
- `docs/CIVIC_HISTORY_HEAD_SEMANTICS.md`;
- `docs/CIVIC_PARTICIPANT_AUTHORITY_STATE_RECONSTRUCTION.md`;
- `docs/CIVIC_EPOCH1_BOOTSTRAP_CONTRACT.md`;
- `docs/CIVIC_CEREMONY_RECORD_CONTRACT.md`;
- `docs/CIVIC_GOVERNANCE_POLICY_PROOF_CONTRACT.md`;
- `docs/CIVIC_PRODUCTION_SIGNING_KEY_LIFECYCLE_CONTRACT.md`;
- `docs/CIVIC_AUTHORITY_STATE_TRANSACTION_COMPOSITION_CONTRACT.md`.

Piece 6 composes these accepted contracts.

It does not redefine their authority semantics.

## Core conformance rule

A Civic Signing Node is conforming only if it can establish, from exact local bytes and an accepted signer provider, all of the following independently:

~~~text
which HOA authority state is selected
        +
whether that selected state completely verifies
        +
which Signing Node public key is current in that state
        +
whether the local provider actually controls that exact key
        +
whether the requested operation is permitted in its authority context
~~~

Only then may current-authority signing be enabled.

## Node identity is not machine identity

The following are deployment identifiers, not Civic authority:

- hostname;
- IP address;
- MAC address;
- container identifier;
- virtual-machine identifier;
- filesystem path;
- Unix user;
- service name;
- database row identifier;
- hardware serial number.

A replacement machine may host the same accepted HOA Civic authority state.

A new machine does not become authorized merely because it reuses the prior hostname or storage path.

## One HOA authority domain per node instance

The baseline conforming node instance serves one `hoa_root_id` authority domain at a time.

A software product may run multiple isolated node instances on one physical machine, but each instance must have separate:

- accepted-state selector;
- authority-state root;
- signing-provider authority context;
- transaction serialization boundary;
- Diagnostics state.

Cross-HOA batching must not merge authority roots.

## Required logical components

A baseline conforming Civic Signing Node consists of five logical capabilities:

~~~text
1. immutable authority object store
2. accepted-state selector
3. complete authority-state verifier
4. production signer provider
5. authority transaction/composition coordinator
~~~

Optional user interfaces, HTTP services, replication transports, databases, dashboards, or hardware security devices may surround these capabilities.

They do not replace them.

## Required object-store capability

The node must be able to:

~~~text
put(exact_bytes) -> SHA-256 identity
get(SHA-256 identity) -> exact_bytes
verify(digest, byte_length, exact_bytes)
~~~

Required semantics:

- immutable content-addressed storage;
- SHA-256 identity over exact bytes;
- no overwrite of different bytes under one identity;
- missing/corrupt bytes fail closed;
- storage path is not authority;
- storage presence is not current-state selection.

The existing reference implementation is `civic/object_store.py`.

Alternative implementations may use another storage engine if the exact semantics are preserved.

## Required accepted-state selector capability

The node requires one logical mutable selector:

~~~text
read()
    -> no selected state
       or exact selected replica identity + verified metadata

compare_and_select(expected_predecessor, candidate)
    -> atomic old-or-new result
~~~

The selector:

- is local operational metadata;
- is not a canonical Civic authority record;
- must not decide governance;
- must not select by filesystem recency;
- must not use last-writer-wins for competing successors;
- must support exact idempotent retry.

The existing reference interface is `AcceptedStateSelector` in `civic/authority_transaction.py`.

## Required authority verifier capability

The node must verify the exact selected replica and its required retained bytes.

At minimum, verification reaches:

- signed Epoch Manifest lineage;
- predecessor continuity;
- exact authority-object closure;
- accepted-history sequence;
- current-epoch canonical history suffix;
- ceremony;
- governance policy;
- governance proofs;
- participant standing;
- participant issuance;
- operator selection;
- Signing Node authorization;
- complete governance transition.

The existing reference orchestration is `verify_persisted_authority_state(...)`.

A deployment may optimize caching.

Caching must not alter the verification result.

## Required production signer-provider capability

The node must integrate a provider conforming to the piece-4 `CivicSignerProvider` boundary.

The provider must supply:

~~~text
generate_key(role)
metadata(key_ref)
public_key(key_ref)
sign_sig_structure(key_ref, exact_bytes)
custody-state operations
~~~

The provider owns private-key custody.

It does not decide Civic authority.

A conforming node may use:

- the reference software provider;
- another owner-controlled software keystore;
- TPM/HSM/PKCS #11 or equivalent optional provider;
- another locally controlled provider preserving the same public contract.

No proprietary remote signer is required for baseline conformance.

## Required transaction/composition capability

The node must support the piece-5 authority transition model:

~~~text
immutable candidate bytes
    -> complete persisted verification
    -> compare expected predecessor
    -> atomic selector commit
    -> current authority
~~~

Candidate composition and current-authority operation must remain separate.

The existing reference implementation is `civic/authority_transaction.py`.

## Node operational states

A conforming implementation must expose semantics equivalent to:

~~~text
UNINITIALIZED
STATE_VERIFIED
READY_CURRENT
RECOVERY_REQUIRED
DEGRADED
FAILED_CLOSED
~~~

Exact enum names are implementation-specific.

The semantics are normative.

## UNINITIALIZED

The node is UNINITIALIZED when no accepted-state selector exists for the configured HOA authority domain.

Current-authority signing is disabled.

Permitted activities may include:

- Epoch-1 candidate preparation;
- candidate key generation;
- candidate object persistence;
- candidate verification;
- import of participant-held replica material for recovery.

UNINITIALIZED does not mean an HOA Civic identity has been created.

## STATE_VERIFIED

STATE_VERIFIED means:

- a selected accepted-state replica exists;
- exact selected bytes are available;
- complete authority verification succeeded;
- the current Signing Node public key/key ID is known from that state.

It does not yet mean local private-key custody is available.

## READY_CURRENT

READY_CURRENT means all STATE_VERIFIED conditions hold and:

- the configured signer provider exposes an available Signing Node key;
- provider public key exactly equals the current accepted Signing Node public key;
- derived key ID exactly equals the accepted current key ID;
- provider key role is Signing Node;
- provider admission/self-test semantics have succeeded;
- a current authority binding can be constructed from the verified state.

Only READY_CURRENT permits current-authority Signing Node operations.

## RECOVERY_REQUIRED

RECOVERY_REQUIRED means accepted public authority state can be reconstructed or verified, but the node cannot safely perform current-authority signing.

Examples:

- current Signing Node private key is unavailable;
- current Signing Node private key was destroyed;
- node replacement recovered public state but not current private key;
- provider has a different key than current authority;
- local selector was lost and verified participant-held state is being reconstructed.

RECOVERY_REQUIRED is not authority loss.

It is an operational inability to perform current Signing Node signing.

## DEGRADED

DEGRADED may be used for failures that do not invalidate accepted authority state and do not require current signing to be enabled.

Examples:

- optional publication unavailable;
- optional IPFS service unavailable;
- optional Diagnostics interface unavailable;
- optional network transport unavailable.

A degraded optional service must not silently become an authority failure.

If the failed subsystem is necessary for exact accepted-state verification or required signing, the node must instead enter RECOVERY_REQUIRED or FAILED_CLOSED as appropriate.

## FAILED_CLOSED

FAILED_CLOSED means the node cannot establish trustworthy current authority context.

Examples include:

- selected replica is missing;
- selected replica digest/length mismatch;
- selector metadata conflicts with replica;
- signed lineage fails;
- required object missing/corrupt;
- accepted history fails;
- ceremony/governance verification fails;
- current authority is ambiguous;
- selector is malformed/torn;
- an implementation invariant needed for atomicity is unavailable.

In FAILED_CLOSED:

~~~text
current-authority signing = disabled
automatic authority repair = prohibited
~~~

Diagnostics may report the failure.

## Startup gate

Every process start or equivalent authority-service activation must execute a startup gate before enabling current-authority signing.

The minimum startup sequence is:

~~~text
1. read accepted-state selector
2. if absent -> UNINITIALIZED
3. load exact selected replica
4. verify selector metadata against exact replica
5. verify complete persisted authority state
6. derive expected current Signing Node public key/key ID
7. inspect configured signer-provider custody
8. require exact provider/current-key match
9. construct current authority binding
10. enable current-authority signing
~~~

Steps 1 through 6 do not require private-key material.

## Startup must verify public authority before private custody

The node must not begin with:

~~~text
find local private key
    -> assume its public key is current
~~~

It must begin with:

~~~text
verify accepted public authority
    -> derive expected current key
    -> inspect local custody
    -> require exact match
~~~

This prevents a stale, replaced, or newly generated local key from defining authority.

## Selector absence on startup

If no selector exists:

- do not scan object storage and choose the newest replica;
- do not choose the highest epoch found on disk;
- do not choose the replica with most copies;
- do not choose based on timestamps.

The node remains UNINITIALIZED or enters explicit recovery/bootstrap workflow.

## Selected-state corruption on startup

If a selector exists but its selected replica does not verify:

- do not fall back automatically to an older replica;
- do not choose another replica from storage;
- do not rewrite the selector;
- do not activate any local signer key.

Enter FAILED_CLOSED and preserve evidence.

## Key mismatch on startup

If selected authority verifies but local signer provider exposes a different Signing Node key:

~~~text
verified authority = preserved
current signing = disabled
replacement key = not activated
~~~

The node enters RECOVERY_REQUIRED.

A new successor transition is required to authorize a different key.

## Current-key unavailable on startup

If the selected accepted state binds a Signing Node key but the provider reports that exact key unavailable:

- public verification remains possible;
- authority history remains intact;
- current-authority signing is disabled;
- no automatic replacement key is generated;
- recovery follows the piece-4 governed replacement procedure.

## Same-key provider migration

If the current Signing Node private key is deliberately migrated to another provider:

- imported key must derive the exact same public key;
- key ID must match;
- provider admission test must pass;
- selected authority state does not change;
- startup may return to READY_CURRENT.

This is custody migration, not a Civic transition.

## Current signing API boundary

A conforming Signing Node must not expose a generic operation equivalent to:

~~~text
sign_any_current_bytes(data)
~~~

Current authority signing must be context-specific.

Each operation must:

1. derive the expected signer from verified current state;
2. construct exact canonical payload and COSE context;
3. build exact Sig_structure;
4. request provider signing under the exact current binding;
5. perform mandatory post-sign public verification;
6. return exact signed bytes.

The provider never decides whether the act is authorized.

## Candidate signing API boundary

Candidate composition requires separate explicit candidate signing operations.

Candidate signing:

- may use candidate participant or Signing Node keys;
- must use candidate authority binding;
- must not reuse a current-authority API by pretending the candidate is current;
- does not activate the candidate key.

A candidate signature is cryptographic attribution, not acceptance.

## No generic local-admin authority shortcut

A local administrator may operate the machine and storage.

That does not grant a Civic bypass such as:

~~~text
--force-current-key
--skip-governance
--trust-local-manifest
--select-latest
--ignore-history
~~~

A low-level operator can always corrupt a machine outside the protocol.

Conforming normal Civic tooling must not convert that machine privilege into accepted authority semantics.

## Candidate creation capability

A baseline node must be able to host the exact artifacts needed for:

- Epoch-1 candidate composition; or
- successor candidate composition.

The node may delegate user interaction or evidence collection to another application.

But the final candidate must enter the accepted piece-5 composition and verification boundary before selection.

## Candidate keys remain separately addressable

The node must permit current and candidate keys to coexist locally.

It must not overwrite the current provider key merely because a replacement candidate is generated.

Conceptually:

~~~text
current key K1
candidate key K2
candidate authority state S2
current accepted authority remains S1
~~~

until S2 is committed.

## Commit activation rule

After piece-5 atomic selector commit succeeds:

- the newly selected state becomes the node's current public authority state;
- current key binding is re-derived from the new state;
- the provider is checked against the new expected key;
- only then may current-authority signing resume.

Commit does not bypass post-commit key binding.

## Post-commit signer failure

If a successor state commits successfully but the newly accepted Signing Node key is unexpectedly unavailable immediately afterward:

- do not roll selector back;
- successor authority remains selected;
- enter RECOVERY_REQUIRED;
- resolve custody or perform a later governed replacement.

Selector rollback is not a substitute for governance.

## Required public verification mode

A conforming node must support verification of accepted Civic authority state without requiring possession of the Signing Node private key.

This is necessary for:

- participant scrutiny;
- node replacement;
- historical verification;
- Diagnostics;
- recovery.

Private custody is necessary for signing, not for verification.

## Participant replica export capability

A baseline node must support export of the exact accepted authority-state closure needed by a participant to reconstruct the current HOA Civic identity.

Export logically consists of:

~~~text
exact authority-state replica bytes
    +
every exact externally required object
    +
every exact signed Manifest named by lineage
    +
every exact history sequence named by replica
~~~

Inline bytes need not be duplicated as separate objects.

## Export is exact-byte transfer, not recomposition

Export must preserve:

- exact replica bytes;
- exact signed Manifest bytes;
- exact history bytes;
- exact required-object bytes;
- SHA-256 identities;
- byte lengths.

The exporting node must not re-sign, re-encode, reorder, or semantically regenerate accepted objects.

## Export transport is not authority

Piece 6 does not freeze whether replica closure is transported by:

- removable media;
- local network;
- HTTPS;
- SSH/SCP;
- IPFS;
- message attachment;
- another owner-controlled transport.

Transport integrity may be useful.

Civic acceptance still verifies exact SHA-256 identities and signed authority semantics.

## Participant replica import capability

A baseline node must support importing exact participant-held authority-state closure into immutable unselected storage.

Import means:

~~~text
receive exact bytes
    -> verify SHA-256/length
    -> persist immutable content
    -> verify complete authority state
    -> keep unselected
~~~

Import by itself does not change current authority.

## Import must not auto-select

The node must never treat:

~~~text
successful replica import
    =
current authority activation
~~~

Import establishes availability and verifiability only.

Selection is a separate operation.

## Recovery from participant-held accepted state

When a Signing Node is lost, one current participant may provide enough accepted replicated state to reconstruct the HOA Civic identity.

The recovery node may:

1. import exact replica closure;
2. verify the complete lineage and authority state;
3. establish the expected HOA root and current epoch;
4. retain the verified state as recovery basis.

This is 1-of-N continuity.

It is not 1-of-N governance.

## Recovery root binding

A replacement node must not accept an arbitrary valid HOA replica when it is being recovered for a known HOA authority domain.

The expected `hoa_root_id` must be supplied or established through the recovery context.

A valid replica for another HOA is rejected.

## Recovery selection of already accepted state

A replacement node with no local selected state may restore a previously accepted verified replica as its local selected reconstruction state when:

- the expected HOA root matches exactly;
- the complete replica closure verifies;
- no conflicting candidate for the same claimed current position is being silently ignored;
- the operation is explicitly a recovery restore, not a new governance transition.

This selector restoration does not create a new epoch.

It restores local knowledge of an already accepted state.

## Recovery restore does not authorize a replacement key

If the current accepted state names Signing Node key K1 and the replacement node does not possess K1:

~~~text
recovered accepted state = valid
replacement local key K2 = candidate only
current-authority signing = disabled
~~~

The replacement node remains RECOVERY_REQUIRED.

A source-governed successor transition must authorize K2.

## Conflicting recovery replicas

If recovery inputs contain two different valid replicas that claim incompatible successors from the same predecessor or otherwise disagree about current lineage:

- do not choose by highest epoch alone;
- do not choose by timestamp;
- do not choose by which participant supplied it;
- do not choose by lexical hash;
- do not merge the forks.

Enter explicit conflict/Diagnostics state.

Governance/source scrutiny is required before a node resumes current-authority operation.

## Older valid recovery replica

An older valid historical replica proves history.

It does not prove that no later accepted state exists.

Therefore a recovery tool must distinguish:

~~~text
cryptographically valid
    != known-current
~~~

If the recovery context knows a later accepted Manifest or replica identity, an older replica cannot be selected as current.

## Recovery after selector loss but object survival

If immutable object storage survives but the selector is lost:

- do not scan and automatically choose the highest epoch;
- require explicit recovery workflow;
- verify candidate replica closure;
- require expected HOA root;
- restore only one exact recovery state;
- surface conflicting valid states if present.

Filesystem discovery is not governance.

## Replica import from current participant

A participant's replica supply role is evidence of continuity, not an authority rank.

The participant does not become operator or Signing Node by providing the bytes.

The participant's private key need not be transferred to the Signing Node.

## Participant private keys remain excluded

Replica export/import must not include:

- participant private keys;
- Signing Node private key;
- provider key references;
- provider unlock secrets;
- passwords;
- recovery seed;
- any invented HOA master key.

The replica closure is public/authenticated authority material plus retained source/evidence objects.

## Signing Node private key backup boundary

Private-key backup/export is a signer-provider concern under piece 4.

It is not part of participant authority-state replication.

A deployment may support same-key private backup if its provider permits it.

Loss of that backup must not destroy HOA identity continuity.

## Required recovery modes

A conforming node must support these conceptual cases:

### Case A — state and current key survive

~~~text
verify selected state
    + exact current key available
    -> READY_CURRENT
~~~

### Case B — state survives, key is lost

~~~text
verify selected state
    + current key unavailable
    -> RECOVERY_REQUIRED
    -> governed replacement transition
~~~

### Case C — node lost, participant replica survives, current key also recoverable

~~~text
import exact participant replica
    -> verify
    -> explicit recovery restore
    -> import/admit exact same current key
    -> READY_CURRENT
~~~

### Case D — node lost, participant replica survives, current key lost

~~~text
import exact participant replica
    -> verify
    -> explicit recovery restore
    -> RECOVERY_REQUIRED
    -> generate candidate replacement key
    -> governed successor
    -> READY_CURRENT
~~~

### Case E — conflicting participant replicas

~~~text
verify each
    -> conflict visible
    -> no automatic current-state choice
    -> current signing disabled
~~~

## Node replacement semantics

Replacing the physical/software node does not itself create a new Civic epoch.

A node can be replaced without authority transition if:

- exact accepted state is reconstructed;
- the same current Signing Node private key is safely migrated/admitted;
- public key/key ID remain exact;
- all startup checks pass.

If a different Signing Node key is used, a successor epoch is required.

## Portability requirement

Kane Fabric Civic conformance is defined by behavior and exact public formats, not by one deployment stack.

A conforming implementation must be possible on general-purpose owner-controlled systems without changing Civic authority semantics.

Implementation-specific choices may include:

- operating system;
- process model;
- filesystem;
- database;
- programming language;
- containerization;
- service manager;
- local IPC;
- network API;
- backup tooling.

These are deployment choices.

## No mandatory central service

Baseline conformance must not require a central Kane service for:

- state verification;
- key generation;
- signing;
- selector commit;
- replica recovery;
- governance verification.

Optional shared services may exist.

Their failure must not destroy the HOA's Civic identity.

## Optional future services remain attachments

The baseline node does not require:

- Kane County CA/TLS;
- Kane-local restricted email;
- IPFS;
- RAG/LLM Diagnostics;
- a public forum;
- cloud object storage.

These may attach later.

None becomes the source of Civic authority.

## Network independence of authority

A conforming node must be able to verify already-retained accepted state without network access.

Network access may be required to retrieve missing candidate evidence or publish artifacts.

A network outage must not change the meaning of already accepted local authority bytes.

## Clock boundary

The node may require a local clock for operational scheduling and user interface.

The local clock does not override authenticated Civic effective-time fields.

A bad clock must not cause the node to rewrite canonical accepted timestamps.

Where current standing must be evaluated at a transaction's ceremony effective time, use the accepted contract's time semantics.

## Diagnostics boundary

Diagnostics may report:

- startup verification failure;
- missing object;
- signer mismatch;
- unavailable current key;
- stale candidate;
- fork conflict;
- failed recovery import;
- selector corruption;
- governance failure.

Diagnostics may not:

- activate a key;
- select a replica;
- bypass governance;
- repair a fork heuristically.

## Audit/logging boundary

Operational logs should record enough non-secret information to diagnose:

- selected replica digest;
- current Manifest digest;
- current epoch sequence;
- expected/current Signing Node key ID;
- verification result;
- transition result;
- selector generation;
- failure classification.

Logs must not contain:

- private scalars;
- exported private-key bytes;
- provider unlock secrets;
- passwords;
- raw secrets from another role.

## Secret-free authority replication

The common participant-held authority replica and node export surface must remain secret-free.

This enables:

- independent verification;
- participant continuity;
- offline backup;
- public historical inspection where policy permits.

Private-key custody remains separate.

## Capability discovery

A conforming implementation may expose a capability/status endpoint or API.

It should report at least:

- software/reference version;
- supported Civic cryptographic profile;
- whether an accepted state is selected;
- selected HOA root identifier;
- current epoch sequence;
- current Manifest identity;
- current operational state;
- signer-provider availability;
- current expected key ID;
- whether current-authority signing is enabled.

Such status is diagnostic projection.

It is not authority.

## Conformance versioning

The first closed reference should identify itself as:

~~~text
Kane Fabric Civic Authority Reference v1
~~~

A node implementation may declare conformance only to a specific published reference version and exact accepted code/reference head.

Future Kane Fabric changes must not silently change the meaning of v1.

## Reference implementation versus production deployment

The Kane Fabric repository provides:

- canonical contracts;
- reference implementation;
- conformance tests;
- interoperability/reference behavior.

A production deployment provides:

- actual machine/process placement;
- actual storage paths;
- actual service manager;
- actual network exposure;
- actual provider configuration;
- actual private-key custody;
- backup/restore procedures;
- monitoring;
- owner/operator procedures.

These are different layers.

## Reference implementation may remain inactive

The Kane Fabric reference can implement production-capable code while:

~~~text
production_signing_enabled = false
production_key_created = false
~~~

This is intentional.

Repository acceptance proves conformance behavior.

It does not authorize a real HOA deployment.

## Deployment activation event

A real deployment begins only when a separate production project explicitly:

- selects a concrete host/runtime;
- selects concrete storage locations;
- configures an accepted signer provider;
- deliberately generates/imports real key material;
- establishes the intended HOA authority domain;
- performs bootstrap or recovery under the published contracts;
- records deployment evidence.

That work is outside this reference closure.

## Annales project boundary

Annales is one future production implementation of the published contracts.

Kane Fabric piece 6 must not specify:

- Annales hostname;
- LXD/container identifier;
- systemd unit name;
- directory paths;
- network addresses;
- firewall rules;
- Unix accounts;
- concrete key-file locations;
- concrete backup directories;
- deployment commands.

Annales may choose these later without changing Civic v1 authority semantics.

## Required software interfaces for the reference implementation

The final reference implementation should expose one orchestration surface that composes existing modules without duplicating them.

Conceptually:

~~~text
CivicSigningNode
    |
    +-- object_store
    |
    +-- accepted_state_selector
    |
    +-- signer_provider
    |
    +-- verify_startup()
    |
    +-- import_replica_closure(...)
    |
    +-- export_selected_replica_closure(...)
    |
    +-- verify_candidate(...)
    |
    +-- commit_candidate(...)
    |
    +-- current_signing_binding()
    |
    +-- status()
~~~

Exact Python class names are implementation details, but the separation is normative.

## Reference node must not own cryptographic primitives

The node orchestration layer must reuse the accepted:

- codec;
- COSE;
- ECDSA verification;
- production signing;
- authority-state;
- governance;
- transaction;

modules.

It must not embed a second competing implementation of Civic cryptography or authority verification.

## Reference node must not own canonical record schemas

The orchestration layer coordinates existing canonical objects.

It must not redefine:

- Epoch Manifest fields;
- ceremony fields;
- governance proof fields;
- accepted-history record schemas;
- replica schema.

## Startup result object

The reference implementation should expose an explicit startup result containing enough information to distinguish:

- no state;
- verified state with no usable current key;
- verified state with usable current key;
- failed state verification.

Callers must not infer readiness merely because construction of a node object succeeded.

## Current authority binding derivation

When selected state verifies, the node derives the current Signing Node authority binding from:

~~~text
selected current Manifest
    -> hoa_root_id
    -> epoch_sequence
    -> signing_node.public_key
    -> signing_node.key_id
    -> CURRENT binding
~~~

The binding is a projection of verified authority.

It is not loaded from provider metadata.

## Provider lookup boundary

The node needs an implementation-local mapping from accepted public key/key ID to provider key reference.

This mapping may be stored locally.

It is not canonical authority.

The node must verify the mapping every time it is admitted for current use:

~~~text
key_ref
    -> provider metadata
    -> exact public key/key ID
    == accepted current binding
~~~

A stale mapping fails closed.

## No key-ref in replicas

Provider `key_ref` must not appear in:

- Epoch Manifest;
- ceremony;
- governance proof;
- accepted history;
- authority-state replica;
- participant export.

It is deployment-local custody metadata.

## Replica closure export inventory

The reference implementation should derive export inventory from the selected replica rather than from arbitrary directory traversal.

The inventory includes exactly the externally referenced bytes needed by:

- signed Manifest lineage;
- history stream descriptors;
- `required_objects`.

It may include optional additional diagnostic objects only if they are clearly marked outside the authority-required closure.

## Import validation sequence

A baseline import follows:

~~~text
receive replica bytes
    -> canonical decode
    -> derive replica SHA-256
    -> receive referenced exact objects
    -> verify each digest/length
    -> persist immutable bytes
    -> run complete authority-state verification
    -> return VERIFIED-UNSELECTED result
~~~

Failure does not mutate the accepted-state selector.

## Recovery restore API boundary

Because restoring already accepted state on an empty replacement node is not the same operation as committing a new governance transition, the reference implementation should expose a distinct recovery operation.

Conceptually:

~~~text
restore_verified_state(
    expected_hoa_root_id,
    verified_replica
)
~~~

It is permitted only when:

- no state is currently selected;
- expected root matches;
- replica completely verifies;
- caller explicitly invokes recovery;
- no local conflicting selected state exists.

It must not generate or activate a replacement key.

## Recovery restore selector semantics

Recovery restore may create the local selector pointing at the exact verified recovered replica.

Its selector generation may begin at zero because selector generation is local operational metadata.

This does not imply Epoch 1.

The selected replica's own epoch sequence remains authoritative.

## Recovery restore and fork evidence

A recovery implementation may know only one supplied replica.

If later a conflicting valid branch is supplied, the node must preserve/report that conflict.

A previously restored local selector is not evidence that the other branch never existed.

The transaction layer still refuses automatic fork resolution.

## Export/import idempotence

Importing or exporting the same exact accepted replica closure repeatedly is idempotent.

No duplicate authority is created.

No signatures are regenerated.

No history is rewritten.

## No partial readiness

The node must not advertise READY_CURRENT while:

- selected state verification is incomplete;
- required object retrieval is pending;
- current provider key check is pending;
- signer self-verification is pending.

Readiness is all-or-nothing for current Signing Node authority.

## Concurrency boundary

Only one accepted-state commit or recovery-selector restore may mutate the selector at a time for one HOA domain.

Concurrent candidate construction may occur if isolated.

The selector compare-and-select remains the serialization point.

## Process crash during startup

A crash during startup verification cannot create authority because startup is read/verify only.

On restart the gate begins again.

## Process crash during candidate composition

Piece-5 semantics apply:

- immutable staged bytes may remain;
- accepted selector remains unchanged;
- candidate keys remain candidate;
- restart does not infer acceptance from artifacts.

## Process crash during current signing

A current signing API must not report success before exact signed bytes have passed mandatory post-sign verification.

Whether the caller subsequently persists/publishes those bytes is operation-specific.

The node must not treat an unreturned/failed signing operation as an accepted state transition.

## Process crash during selector commit

Piece-5 atomic old-or-new semantics apply.

The node must never recover by selecting the newest directory or highest epoch found.

## Process crash after selector commit

On restart, the startup gate verifies the selected new state again.

If the new current key is unavailable, state remains selected and the node enters RECOVERY_REQUIRED rather than rolling back.

## Minimum conformance status fields

A reference status projection should contain at least:

~~~text
reference_version
operational_state
accepted_state_selected
hoa_root_id
current_epoch_sequence
current_manifest_sha256
selected_replica_sha256
expected_signing_node_key_id
signer_provider_available
current_key_available
current_signing_enabled
~~~

Secret material is prohibited.

## Minimum implementation acceptance properties

Before closure piece 6 implementation is accepted, focused tests must establish at least:

1. no selector -> UNINITIALIZED and current signing disabled;
2. valid selected replica -> public authority verifies without private key;
3. valid selected replica + exact current key -> READY_CURRENT;
4. valid selected replica + unavailable current key -> RECOVERY_REQUIRED;
5. valid selected replica + wrong provider key -> RECOVERY_REQUIRED or fail-closed signing state;
6. corrupt selected replica -> FAILED_CLOSED;
7. missing authority-required object -> FAILED_CLOSED;
8. malformed selector -> FAILED_CLOSED;
9. startup never selects a replica by filesystem recency/highest epoch;
10. current binding derives only from verified selected Manifest;
11. provider key-ref never enters canonical/exported authority bytes;
12. generic arbitrary current-byte signing is absent;
13. candidate key generation does not change selected authority;
14. exact participant replica closure export contains all required external bytes;
15. export preserves exact accepted bytes;
16. import verifies exact digest/length before accepting bytes;
17. import failure leaves selector unchanged;
18. successful import leaves state unselected;
19. recovery restore requires empty selector;
20. recovery restore requires exact expected HOA root;
21. recovery restore of valid accepted state does not create a new epoch;
22. recovery restore does not activate a different local key;
23. recovered state + missing current key remains RECOVERY_REQUIRED;
24. same-key provider migration can return to READY_CURRENT without authority transition;
25. conflicting recovery state is not auto-selected over an existing state;
26. normal successor commit still uses piece-5 compare-and-select;
27. post-commit missing accepted key does not roll authority backward;
28. status projection contains no private key material;
29. all startup/current-signing failures are fail-closed;
30. complete Civic suite remains green.

## Reference test authority only

Piece-6 implementation tests may use:

- temporary object stores;
- temporary selectors;
- ephemeral software-provider keys;
- fixture authority roots;
- fixture bootstrap/successor states.

They must not create or activate a real HOA production authority.

## Conformance declaration

After piece-6 implementation and CT102 acceptance, Kane Fabric may publish one permanent reference checkpoint.

The checkpoint must identify:

~~~text
Kane Fabric Civic Authority Reference
version: v1
accepted code head: <exact final CT102 head>
complete Civic gate: <exact test count>/<exact test count>
~~~

That exact checkpoint becomes the implementation target for production projects.

## Production project declaration

A production implementation should state:

~~~text
This Signing Node implements
Kane Fabric Civic Authority Reference v1
at commit <exact accepted reference SHA>
~~~

The production project may then add platform-specific deployment details without modifying the frozen reference semantics.

## What closes with piece 6

After implementation/test acceptance of this contract, Kane Fabric Civic reference closure has frozen:

~~~text
bootstrap authority
canonical ceremony
governance proof/transition verification
production signing/key lifecycle
atomic authority-state transaction
Signing Node conformance boundary
~~~

At that point the remaining work is deployment/operation of a concrete implementation, not further redesign of the Civic authority foundation.

## Closure result

This document freezes closure piece 6 at the architecture level.

The next bounded repository step is implementation of the platform-neutral Signing Node orchestration surface using the already accepted Civic modules.

That implementation must remain inactive with respect to any real HOA production authority until a separate production deployment project explicitly activates it.
