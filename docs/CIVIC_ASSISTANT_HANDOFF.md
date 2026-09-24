# Civic Assistant Handoff

## Purpose

This document is the starting point for a new Assistant continuing the Kane Fabric Civic authority work.

Read this document first, then docs/CURRENT_STATE.json, then the specific architecture document for the next bounded task.

The GitHub repository is the software authority.

Do not reconstruct project state from chat memory when repository state is available.

## Repository and acceptance state

Repository:

~~~text
git64bit/Kane-Fabric
~~~

Last CT102-tested Civic code head:

~~~text
0a79ca8cef3095c43dbf23eee0e3a54a68a6cfbf
~~~

Accepted Civic test result at that head:

~~~text
143 tests run
143 passed
0 failed
0 skipped
~~~

The CT102 acceptance covers the canonical ceremony record, governance-policy/proof primitives, the complete governance-transition evaluator, and all previously accepted Civic components.

Repository documentation commits may exist after the last CT102-tested code head.

Therefore:

~~~text
latest GitHub main
    != automatically
latest CT102-accepted code head
~~~

A new Assistant must preserve that distinction.

## Host topology

### srv-b

~~~text
role: Proxmox host
address: 10.110.0.12
container command: pct
~~~

### CT102 kane-fabric

~~~text
address: 10.20.0.12
repository checkout: /tmp/kane-fabric-ms2
operational data: /var/lib/kane-fabric
~~~

CT102 is the current acceptance environment for Civic repository work.

### fw

~~~text
address: 10.110.0.4
type: bare Ubuntu
~~~

It is not the current Civic repository acceptance environment.

### annales

~~~text
address: 10.110.0.9
type: Ubuntu/LXD
container command: lxc
~~~

Future logical topology:

~~~text
annales
├── firmware-authority
└── civic-signing-node
~~~

These are separate roles.

Never merge Civic identity, Civic keys, Civic authority state, or Civic signing semantics with Firmware Release Authority.

No Civic Signing Node has been created on annales.

No production Civic private key has been created.

Annales production implementation is outside the present Kane Fabric reference-closure work. It begins as a separate project only after the platform-neutral Kane Fabric Civic Authority Reference is closed.

Do not encode Annales-specific LXD names, service units, filesystem paths, networking, or concrete key locations into the Kane Fabric reference contracts.

Do not mutate annales unless the user explicitly reaches that separate deployment project.

### Wiregate

~~~text
CT103
address: 10.20.0.13
~~~

Not part of the present Civic authority-record development loop.

## Development discipline

The user prefers small bounded steps.

Default cadence:

~~~text
1. architecture before implementation when semantics are not frozen
2. one file or tightly coupled change
3. commit
4. verify repository state
5. CT102 fast-forward when implementation is ready
6. run the focused/full Civic gate
7. record acceptance in CURRENT_STATE.json
8. stop/report
~~~

Do not batch unrelated work.

Do not jump ahead to production deployment.

Reliability is more important than speed.

## Governing design principle

Civic specifies what must be verifiable.

It does not prescribe procedures that properly belong to the applicable governing source, owner-operator, place, or time.

In particular:

~~~text
verification invariant
    != universal ceremony mechanism
~~~

Applicable law, condominium instruments, and the published Civic profile may determine the procedure.

Civic should preserve the evidence and verify the invariant without inventing substantive authority.

## Civic authority model

One participating HOA is one autonomous Civic authority domain.

The HOA Civic Identity is not:

- the operator;
- the Signing Node;
- a hostname;
- a server;
- an ESP32;
- one permanent private key.

The current Signing Node is a replaceable authority appliance.

The durable HOA Civic Identity is reconstructable from authenticated replicated authority state retained by current Same-and-Equal participant devices.

## Reconstruction semantics

Accepted reconstruction model:

1. any one surviving current Same-and-Equal participant can provide the complete current authenticated Civic authority state;
2. every current participant holds the same complete authority-state replica;
3. each participant retains only that participant's own epoch-specific private key;
4. reconstruction does not recover other participants' private keys;
5. reconstruction does not recover an old Signing Node private key;
6. there is no permanent HOA master private key;
7. full Civic authority lineage and authority-required objects are replicated;
8. bulky non-authoritative evidence may be retained separately by exact SHA-256/provenance where appropriate.

Important:

~~~text
1-of-N reconstruction
    !=
1-of-N unilateral governance
~~~

Recovery of state is not governance authority.

## Cryptographic profile

Accepted profile:

~~~text
profile identity       kane-civic-ecdsa-p256-sha256-v1
signature algorithm    ECDSA
curve                  NIST P-256 / secp256r1
digest                  SHA-256
public key              uncompressed SEC1 point
public key length       65 bytes = 0x04 || X(32) || Y(32)
signature               fixed 64-byte P1363 r||s
key identifier          SHA-256(exact 65 public-key bytes)
COSE algorithm          ESP256 / -9 / RFC 9864
~~~

ES256 / -7 is not the accepted Civic algorithm.

Current signing implementation is fixture-only.

Do not convert fixture signing into production signing without an explicit later decision.

## Canonical Civic data path

~~~text
structured Civic data
    -> deterministic CBOR
    -> SHA-256 exact-byte identity
    -> COSE_Sign1
    -> P-256/SHA-256 Civic signature
    -> append-only CBOR Sequence history
    -> generated JSON diagnostic projection
~~~

Deterministic CBOR rules include:

- UTF-8 NFC;
- no floats;
- no duplicate map keys;
- no indefinite lengths;
- shortest deterministic integer representation;
- deterministic map ordering.

## Epoch Manifest

Primary architecture:

docs/CIVIC_EPOCH_MANIFEST_FORMAT.md

Top-level fields:

~~~text
format
version
crypto_profile
hoa_root_id
epoch_sequence
predecessor_manifest_sha256
effective_time_ms
governing_profile
governing_sources
participants
operator
signing_node
history
ceremony
object_index
~~~

Manifest identity is SHA-256 of the exact canonical payload bytes.

The signed envelope embeds that payload.

The JSON projection is derived and non-authoritative.

## Participant descriptor

Each current participant descriptor is:

~~~text
{
  "participant_record_sha256": bytes(32),
  "participant_key_id": bytes(32),
  "participant_public_key": bytes(65),
  "standing_record_sha256": bytes(32),
  "issuance_record_sha256": bytes(32)
}
~~~

The precise type-specific meaning of:

~~~text
standing_record_sha256
~~~

is now defined by docs/CIVIC_ACCEPTED_PARTICIPANT_STANDING_RECORD.md and enforced by civic/accepted_participant_standing.py.

Do not infer standing merely from manifest membership: current standing remains time- and profile-dependent.

## Operator descriptor

~~~text
operator = {
  "participant_record_sha256": bytes(32),
  "selection_record_sha256": bytes(32)
}
~~~

The operator must be a current participant.

The exact operator selection/election mechanism is profile-specific and source-derived.

## Signing Node descriptor

~~~text
signing_node = {
  "key_id": bytes(32),
  "public_key": bytes(65),
  "authorization_record_sha256": bytes(32)
}
~~~

Signing Node key material is separate from participant keys.

The Signing Node key is replaceable.

## Ceremony

Manifest ceremony contains:

~~~text
ceremony = {
  "ceremony_record_sha256": bytes(32),
  "governance_proof_sha256": [ * bytes(32) ]
}
~~~

Do not attempt to make the ceremony record be a generic signed history record if doing so creates direct self-reference through ceremony_record_sha256.

The exact ceremony representation remains intentionally separate where necessary.

Do not over-specify ceremony mechanics.

## History model

Architecture:

docs/CIVIC_HISTORY_HEAD_SEMANTICS.md

Streams:

~~~text
accepted
witness
diagnostics
knowledge
~~~

Record identity is:

~~~text
SHA-256(exact deterministic-CBOR sequence item bytes)
~~~

For a signed history record, this means hashing the exact signed COSE object, not the unsigned payload.

Authenticated history linkage is inside the signed payload:

~~~text
history_link = {
  "stream": text,
  "predecessor_record_sha256": bytes(32) / null
}
~~~

Genesis predecessor is null.

Each successor names the exact preceding record hash.

The stream head is the final record hash.

Forks are preserved as evidence.

The accepted Epoch Manifest selects the accepted history head.

## Generic signed history envelope

Architecture:

docs/CIVIC_SIGNED_HISTORY_RECORD_ENVELOPE.md

Generic payload:

~~~text
{
  "format": "kane-civic-history-record",
  "version": 1,
  "crypto_profile": "kane-civic-ecdsa-p256-sha256-v1",
  "hoa_root_id": bytes(32),
  "epoch_sequence": uint,
  "ceremony_record_sha256": bytes(32),
  "record_type": text,
  "history_link": {
    "stream": text,
    "predecessor_record_sha256": bytes(32) / null
  },
  "signer": {
    "kind": text,
    "key_id": bytes(32),
    "participant_record_sha256": bytes(32) / null
  },
  "body": map
}
~~~

Supported generic signer kinds:

~~~text
signing_node
participant
~~~

A valid signature proves cryptographic attribution.

It does not by itself prove legal truth, governance sufficiency, factual truth, or acceptance into current authority.

Type-specific verification provides the next semantic layer.

## Accepted Signing Node authorization

Architecture:

docs/CIVIC_ACCEPTED_SIGNING_NODE_AUTHORIZATION_RECORD.md

Implementation:

civic/accepted_signing_node_authorization.py

Record type:

~~~text
kane-civic-accepted-signing-node-authorization-v1
~~~

Core semantics:

- accepted history only;
- Signing Node signer only;
- exact key ID/public-key binding;
- exact manifest.signing_node.authorization_record_sha256 binding;
- governance proof set equals the manifest ceremony governance-proof set;
- Signing Node signature proves possession/attribution, not self-authorization;
- governance and accepted lineage establish authority conditions.

A forged replacement node cannot gain useful Civic authority merely by generating internally consistent data.

Do not describe forgery as impossible.

A compromised legitimate current key remains a real security event.

## Accepted operator selection

Architecture:

docs/CIVIC_ACCEPTED_OPERATOR_SELECTION_RECORD.md

Implementation:

civic/accepted_operator_selection.py

Record type:

~~~text
kane-civic-accepted-operator-selection-v1
~~~

Core semantics:

- accepted history only;
- selected participant equals manifest.operator.participant_record_sha256;
- exact record hash equals manifest.operator.selection_record_sha256;
- signer may be participant or Signing Node;
- signer attribution does not define selection authority;
- selection proof hashes are a subset of ceremony governance proofs;
- empty proof subset is permitted;
- proof sufficiency is source-derived;
- no universal election/ballot/meeting/consent procedure is imposed.

## Accepted participant issuance

Architecture:

docs/CIVIC_ACCEPTED_PARTICIPANT_ISSUANCE_RECORD.md

Implementation:

civic/accepted_participant_issuance.py

Record type:

~~~text
kane-civic-accepted-participant-issuance-v1
~~~

Core distinction:

~~~text
issuance
    !=
standing
~~~

The issuance record binds:

- exact participant identity;
- exact epoch participant public key/key ID;
- exact standing-record hash;
- current issuing-operator provenance;
- exact participant issuance_record_sha256;
- accepted history;
- HOA root / epoch / ceremony context.

Signer modes:

### Participant signer

The participant signer must be the current manifest operator.

### Signing Node signer

The signer must be the manifest Signing Node.

In both cases, the body still preserves the current issuing operator.

The issuance signature does not silently certify every participant-maintained claim.

Standing remains a separately verified obligation.

## Accepted participant standing

Architecture:

docs/CIVIC_ACCEPTED_PARTICIPANT_STANDING_RECORD.md

Implementation:

civic/accepted_participant_standing.py

Focused tests:

civic/tests/test_accepted_participant_standing.py

Record type:

~~~text
kane-civic-accepted-participant-standing-v1
~~~

Accepted CT102 head:

~~~text
1956848dccee0630bc7c0f80fd91c0ca20d1a0ae
~~~

Accepted gate:

~~~text
11 focused participant-standing tests passed
102 complete Civic tests passed
0 failed
0 skipped
~~~

Core distinction:

~~~text
standing
    !=
issuance
    !=
participant-maintained claims
    !=
operator certification of every fact
    !=
Epoch Manifest membership by itself
~~~

The standing verifier binds the exact manifest standing-record identity, participant subject, governing-profile descriptor, recording-operator provenance, permitted signer, authority evidence, participation interval, qualification responsibility, and evaluation-time currentness.

Authority evidence must resolve to exact retained bytes through the manifest authority object model. Supplementary evidence may remain unavailable locally and must not become an implicit reconstruction dependency.

A participant signer must be the current manifest operator. The Signing Node is also a permitted signer, while the body still preserves current operator provenance.

Manifest membership does not override standing expiration. A record may remain valid historical authority material while failing present standing evaluation.

Profile-specific standing class, qualification path, participation policy, evidence-role, provenance, and temporal semantics have a canonical data-driven verifier in civic/governing_profile.py. The accepted participant-standing verifier consumes that canonical verifier directly; the earlier caller-supplied semantic callback is no longer part of accepted participant-standing verification.

## Accepted canonical governing profile

Architecture:

docs/CIVIC_GOVERNING_PROFILE_CONTRACT.md

Implementation:

civic/governing_profile.py

Focused tests:

civic/tests/test_governing_profile.py

Accepted CT102 head:

~~~text
af17dc4a39cd4d32c07208a0dbcd65fa25490152
~~~

Accepted gate:

~~~text
14 focused governing-profile tests passed
116 complete Civic tests passed
0 failed
0 skipped
~~~

The accepted module freezes and verifies deterministic-CBOR profile bytes, exact profile SHA-256 identity, deterministic governing-source-set derivation, source-set binding, standing-class/qualification-path/participation-policy tables, provenance, evidence rules, UTC calendar-month temporal semantics, profile referential integrity, and data-driven standing semantics.

The governing profile is authority data, not executable policy code.

The participant-standing verifier now consumes the canonical governing-profile module directly. It verifies exact profile bytes against the Epoch Manifest and applies mandatory data-driven standing semantics internally.

The former caller-supplied semantic callback is no longer part of accepted participant-standing verification.

Accepted direct-integration head:

~~~text
ac76abc4f44a6d38b128f2c6de661d4ec3de8dc3
~~~

Accepted integration gate:

~~~text
11 focused participant-standing integration tests passed
116 complete Civic tests passed
0 failed
0 skipped
~~~

## Civic reference closure: pieces 1-3

The current reference-closure sequence is:

~~~text
1. Epoch-1 / bootstrap contract
2. canonical ceremony-record contract
3. governance-policy / proof / verification contract
4. production signing / key-lifecycle contract
5. authority-state transaction / composition contract
6. platform-neutral Signing Node conformance / deployment boundary
~~~

### Piece 1 — Epoch-1 / bootstrap contract

Architecture:

docs/CIVIC_EPOCH1_BOOTSTRAP_CONTRACT.md

Architecture head:

~~~text
89c8695686c73747664e741f375170c58533691b
~~~

Status: architecture frozen.

Core boundary:

~~~text
candidate cryptographic consistency
    !=
accepted bootstrap authority
~~~

Epoch 1 requires complete source-grounded bundle closure. There is no root private key and no self-authorization shortcut.

### Piece 2 — canonical ceremony record

Architecture:

docs/CIVIC_CEREMONY_RECORD_CONTRACT.md

Implementation:

civic/ceremony.py

Focused tests:

civic/tests/test_ceremony.py

Accepted CT102 head:

~~~text
8b3d06ac4f7cba0417dd7e4efdbae56dc102bab1
~~~

Accepted gate:

~~~text
9 focused ceremony tests passed
125 complete Civic tests passed
0 failed
0 skipped
~~~

The canonical ceremony is a standalone deterministic-CBOR authority object. It binds the exact manifest transition projection, governance policy, governance-proof hash set, object-index descriptor, predecessor identity, and continuing-participant key rotation without introducing a ceremony/proof hash cycle.

### Piece 3 — governance policy, proof, and transition verification

Architecture:

docs/CIVIC_GOVERNANCE_POLICY_PROOF_CONTRACT.md

Implementation:

civic/governance.py

Focused primitive tests:

civic/tests/test_governance.py

Focused transition tests:

civic/tests/test_governance_transition.py

Primitive acceptance head:

~~~text
214d47c5927554de0e31b81568910a58250efd08
~~~

Final piece-3 CT102 acceptance head:

~~~text
0a79ca8cef3095c43dbf23eee0e3a54a68a6cfbf
~~~

Final accepted gate:

~~~text
9 focused governance-transition tests passed
143 complete Civic tests passed
0 failed
0 skipped
~~~

Accepted semantics include:

- canonical non-recursive governance-transition subject;
- canonical source-bound governance-policy bytes and identity;
- signed governance-proof COSE verification;
- bootstrap signer resolution from candidate participant keys;
- successor signer resolution from predecessor participant keys;
- standing-based exact electorate reconstruction;
- exact ceremony-listed proof-set verification;
- duplicate non-null decision rejection;
- authority-evidence deduplication and exact-byte verification;
- evidence-only authorization where the policy requires it;
- exact integer quorum and approval semantics.

The generic verifier does not invent a universal majority rule, electorate, weight, or legal procedure. Those remain source-derived policy data.

Closure piece 3 is complete.

## Broader Civic Issuance Record

Existing semantic architecture:

docs/CIVIC_ISSUANCE_RECORD.md

This broader model includes concepts such as:

- subject lineage;
- appliance issuance;
- relationship tuples;
- participation window;
- claim provenance;
- revalidation;
- disclosure policy;
- supersession/correction lineage.

Do not force all of that into the minimal accepted participant-issuance authority record prematurely.

Real HOA deployment should inform which broader fields become necessary in canonical authority representation.

## Participation renewal

Architecture:

docs/CIVIC_PARTICIPATION_RENEWAL.md

Current Kane profile uses a fresh self-addressed stamped envelope (SASE) every six months as the voluntary participation renewal act.

No passive or automatic renewal.

Historical records remain historical records after participation expires.

The six-month SASE rule is a Kane Civic participation rule, not a claim that condominium law universally requires such renewal.

## Same-and-Equal

Architecture:

docs/CIVIC_SAME_AND_EQUAL_POLICY.md

Same-and-Equal is:

- relational;
- scoped;
- temporal;
- policy-dependent.

It is not a universal permanent attribute of a person.

The same pair of participants may be Same-and-Equal for one purpose and not another.

Operator status does not automatically change unrelated Same-and-Equal standing.

## Governing-source boundary

Architecture:

docs/HOA_GOVERNING_SOURCE_INHERITANCE.md

For the HOA profile, substantive procedure should be derived in this order:

~~~text
Illinois statute
    -> condominium instruments
    -> Civic/HOA Diagnostics instrumentation
~~~

Civic instrumentation must not silently become the source of a substantive legal rule.

## Authority-state reconstruction

Architecture:

docs/CIVIC_PARTICIPANT_AUTHORITY_STATE_RECONSTRUCTION.md

Implementation:

civic/authority_state.py

Replica schema:

~~~text
format = kane-civic-participant-authority-state-replica
version = 1
hoa_root_id
current_epoch_sequence
current_manifest_sha256
epoch_lineage
history_streams
required_objects
~~~

The verifier:

- loads exact retained bytes by SHA-256;
- verifies hash and byte length;
- cryptographically verifies every signed Epoch Manifest;
- verifies HOA root and contiguous predecessor-manifest lineage;
- verifies required external authority objects;
- verifies current history descriptors against the current manifest;
- cryptographically authenticates retained history records;
- validates signed predecessor linkage;
- validates the final history head.

Private keys are not part of replicated authority-state content.

## Object identity and retention

Implementation:

civic/object_store.py

SHA-256 of exact bytes is the Civic content identity.

CID may later be attached as a retrieval/distribution identifier.

CID does not replace Civic SHA-256 identity.

Authority-required bytes must be reconstructable.

An authority-critical standing record must not exist only in an inaccessible portal, private operator memory, transient database row, or unverifiable path.

## Production-signing boundary

Current status:

~~~text
production_signing_enabled = false
production_key_created = false
annales_mutated = false
~~~

Fixture-only P-256 signing exists for deterministic tests.

Do not create a production Civic key as an incidental next step.

Do not activate annales as a Civic signer merely because record semantics are increasingly complete.

## Hardware portability boundary

Civic must not depend on:

- ATECC608A-class secure-element custody;
- ESP eFuse commitments;
- one permanent hardware-backed master key.

Software-held private-key custody is permitted.

Optional hardening is acceptable only if it can be removed without changing:

- Civic identity;
- authority semantics;
- records;
- reconstruction;
- independent operation.

The separate Firmware Authority still contains older hardware-backed assumptions elsewhere in the repository.

Do not accidentally reconcile or modify that unrelated deferred inconsistency while working on Civic.

## Diagnostics boundary

Sources, law, and condominium instruments are governing sources.

Civic records are authority/provenance records.

Observed evidence is factual diagnostic input.

RAG/LLM output is derived advisory or diagnostic output.

RAG/LLM output is never Civic authority.

Failures, forks, missing objects, contradictory records, and suspicious operator behavior should normally become inspectable diagnostic signals rather than being hidden by speculative repair logic.

## Emergent-feature watchlist

These are useful properties that fall out of the architecture.

They are not automatically protocol requirements.

### Core / already strategically important

#### One-participant reconstruction

Any one surviving current participant can provide the complete authenticated current authority state without possessing other participants' private keys.

#### Historical verification without historical key recovery

Historical signatures remain verifiable from retained public authority state.

Old private keys do not need to be recovered.

#### Replaceable operator and Signing Node

The HOA Civic Identity survives operator change, Signing Node replacement, and participant-device loss where the accepted continuity/governance process is followed.

#### Operator accountability independent of signing path

Participant-direct signing and Signing-Node signing both preserve explicit issuing-operator provenance.

A later verifier can distinguish:

~~~text
who cryptographically signed?
who was acting as operator?
~~~

#### Resistance to useful forged-node insertion

A substitute node can create data but cannot gain accepted Civic utility unless the required epoch key binding, authorization record, accepted-history predecessor chain, manifest references, and governance relationships also verify.

This is resistance, not impossibility.

### Candidate priority after live HOA deployment

#### Differential issuance auditing

Each accepted issuance exposes:

~~~text
participant identity
participant key
standing hash
issuing operator
exact issuance record
accepted-history position
~~~

This creates a natural diagnostic comparison surface across Same-and-Equal participants.

Potential uses:

- detect unexplained different issuance treatment;
- detect participant-key substitution;
- detect standing-record substitution;
- identify inconsistent operator behavior;
- compare renewal/reissuance handling across similarly situated participants.

This may become a priority if the first HOA deployment demonstrates practical value.

#### Standing-expiration diagnostics without historical deletion

Because historical issuance is preserved while current standing is separate and time/profile dependent, Diagnostics can distinguish:

~~~text
was valid historically
~~~

from:

~~~text
is current now
~~~

without rewriting old records.

#### Missing-authority-object detection as an operational alarm

Reconstruction already fails visibly when authority-required bytes are missing or corrupt.

That can later support a high-value operational health signal:

~~~text
replica is present
but authority state is not reconstructable
~~~

Do not silently repair this state.

### Nice but not currently priority

#### Multiple retrieval systems over one Civic identity

Because SHA-256 exact-byte identity is independent of storage location, the same authority object can later be distributed by filesystem, removable media, IPFS/CID, HTTP, or other transports without changing Civic identity.

#### Offline verification surface

The retained manifest lineage, public keys, signed history, and required objects permit substantial verification without contacting a central SaaS authority.

This should remain a consequence of the architecture, not a reason to introduce a central verification service.

## Immediate next task: closure piece 4

The next bounded task is architecture, not deployment.

Define the platform-neutral **production signing and key-lifecycle contract** before adding production-signing code.

The contract must freeze at least:

- cryptographically secure key generation / randomness requirements;
- production private-key custody and loading boundaries;
- signing interface and failure behavior;
- key replacement and epoch rotation semantics;
- explicit separation of participant keys, Signing Node keys, and HOA Civic identity;
- no permanent HOA master private key;
- no mandatory HSM, ATECC608A, ESP eFuse, or vendor-specific custody mechanism;
- portability between software-held and optionally hardened custody implementations;
- the rule that loss of a Signing Node private key leads to governed replacement, not secret recovery.

This is still Kane Fabric reference work.

Do not specify Annales-specific:

- LXD/container names;
- systemd unit names;
- filesystem paths;
- networking;
- concrete key locations.

Those belong to the later separate Annales production implementation project.

Production boundaries remain:

~~~text
production_signing_enabled = false
production_key_created = false
annales_mutated = false
~~~

Do not create a production Civic key or mutate annales while defining piece 4.

## Handoff invariant

A new Assistant should be able to continue from repository state using:

~~~text
this handoff
    -> CURRENT_STATE.json
    -> next architecture document
    -> one bounded implementation step at a time
~~~

No reliance on hidden chat state should be necessary.
