# Civic Production Signing and Key-Lifecycle Contract

## Status

Architecture contract for Kane Fabric Civic reference closure piece 4.

Documentation only.

This contract does **not**:

- create a production Civic private key;
- enable production signing;
- activate a Civic Signing Node;
- mutate annales;
- select an Annales container, service unit, path, network, or concrete key location;
- select a mandatory hardware security product;
- replace the accepted Civic cryptographic profile;
- define authority-state transaction/commit mechanics reserved for closure piece 5.

Current production boundary remains:

~~~text
production_signing_enabled = false
production_key_created = false
annales_mutated = false
~~~

## Purpose

The earlier Civic contracts define:

- one autonomous HOA Civic authority domain;
- deterministic authority objects;
- the P-256/SHA-256 Civic cryptographic profile;
- current authority epochs;
- canonical ceremony records;
- source-bound governance policy and proofs;
- standing-based electorate reconstruction;
- complete governance-transition verification;
- participant-held authority-state continuity;
- a replaceable HOA-local Civic Signing Node.

This document freezes the production private-key and signing semantics required to implement those contracts without turning one machine, provider, file format, hardware token, or permanent secret into Civic identity.

The central rule is:

~~~text
private-key custody
    = local operational state

current Civic authority
    = accepted epoch-bound public authority state
~~~

Possessing a private key is not sufficient to create Civic authority.

## Governing contracts

This contract is subordinate to and must preserve:

- `docs/CIVIC_CRYPTOGRAPHIC_BASELINE.md`;
- `docs/CIVIC_AUTHORITY_CONTINUITY_DECISION.md`;
- `docs/CIVIC_AUTHORITY_EPOCH_CEREMONY.md`;
- `docs/CIVIC_EPOCH_MANIFEST_FORMAT.md`;
- `docs/CIVIC_EPOCH1_BOOTSTRAP_CONTRACT.md`;
- `docs/CIVIC_CEREMONY_RECORD_CONTRACT.md`;
- `docs/CIVIC_GOVERNANCE_POLICY_PROOF_CONTRACT.md`;
- `docs/CIVIC_PARTICIPANT_AUTHORITY_STATE_RECONSTRUCTION.md`;
- `docs/CIVIC_OWNER_OPERATED_SIGNING_NODE.md`.

Where this document discusses production signing, it does not weaken any governance, standing, ceremony, lineage, or reconstruction requirement in those contracts.

## Cryptographic profile remains unchanged

Production Civic signing v1 uses the already accepted profile:

~~~text
profile identity       kane-civic-ecdsa-p256-sha256-v1
signature algorithm    ECDSA
curve                  NIST P-256 / secp256r1
digest                  SHA-256
public key              uncompressed SEC1 point
public key length       65 bytes = 0x04 || X(32) || Y(32)
signature               IEEE P1363 fixed 64-byte r || s
key identifier          SHA-256(exact 65 public-key bytes)
COSE algorithm          ESP256 / -9
~~~

This piece does not introduce:

- ES256 / -7;
- another curve;
- another digest;
- certificate-based Civic key identity;
- a low-S-only verification rule;
- algorithm negotiation inside one epoch.

A future cryptographic-profile change requires an explicit profile decision and source-governed epoch transition.

## Key roles are distinct

Civic uses cryptographically similar P-256 keys for different authority roles.

At minimum, production implementations must distinguish:

~~~text
participant epoch key
Signing Node key
Firmware Release Authority key
other non-Civic service keys
~~~

Using the same algorithm does not merge these roles.

A Civic participant key must not silently become a Signing Node key merely because its public key is technically usable for ECDSA.

A Signing Node key must not become a Firmware Release Authority key.

Role meaning comes from authenticated Civic authority state and record context, not merely from possession of a scalar.

Local key-provider metadata may also tag a key with its intended role as a defense against accidental cross-role use, but that local tag is not the source of Civic authority.

## There is no HOA root private key

The stable `hoa_root_id` is an opaque public identifier.

It has no corresponding required private key.

The production implementation must not introduce:

- `hoa_root_private_key`;
- a root signing scalar;
- a permanent HOA master signing key;
- a shared HOA recovery signing key;
- a hidden seed from which all participant or Signing Node keys are derived.

Conceptually:

~~~text
hoa_root_id
    != public key
    != key identifier
    != private-key seed
    != recovery secret
~~~

The HOA Civic Identity survives key replacement because continuity is carried by authenticated authority lineage, not because one permanent secret survives.

## Secure randomness service

Production key generation requires a cryptographically secure random source.

A conforming production implementation must obtain randomness from either:

- the operating system cryptographic random facility; or
- a cryptographic provider whose key-generation implementation uses an equivalent cryptographically secure random source.

It must not generate production private scalars from:

- timestamps;
- process IDs;
- MAC addresses;
- hostnames;
- serial numbers;
- HOA identifiers;
- participant identifiers;
- hashes of public authority state;
- ordinary pseudo-random generators intended for simulation;
- deterministic repository fixture values.

For direct scalar generation, the scalar must be sampled uniformly from:

~~~text
1 <= d < n
~~~

for the P-256 group order `n`.

Rejection sampling or a provider's standard P-256 key-generation primitive is acceptable.

Modulo reduction of biased arbitrary integers is not the reference requirement.

## Bootstrap root randomness

Where the Epoch-1 contract requires a new opaque 32-byte `hoa_root_id`, it must be generated from the same class of cryptographically secure random source.

The root identifier is public after creation.

Its randomness prevents accidental or chosen identity collision; it does not create a secret signing authority.

The root identifier must not be derived from a private key.

## ECDSA per-signature nonce

Production ECDSA must use a cryptographically sound nonce implementation.

A conforming provider may use either:

1. deterministic ECDSA nonce derivation equivalent to RFC 6979 with SHA-256; or
2. fresh cryptographically secure per-signature randomness supplied by a standard cryptographic provider.

The Civic authority contract does not assign semantic meaning to which permitted nonce method is used.

The production signing API must not expose an application-supplied nonce scalar.

The explicit nonce API in `civic/ecdsa.py` is fixture-only and must not be reused as a production signing API.

If secure nonce generation fails, signing fails.

There is no fallback to predictable nonce material.

## Signature-byte consequences

Civic does not require two valid production signatures over the same payload to be byte-identical.

Therefore:

~~~text
same payload
    + same key
    may produce
different valid signature bytes
~~~

when a randomized provider is used.

This does not change the payload identity.

For authority objects whose identity includes the complete signed envelope, the exact returned signed bytes are the identity-bearing bytes for that specific act.

A caller must not assume that retrying a signing call will reproduce the same signed-object SHA-256.

Transaction/finalization semantics for preventing ambiguous duplicate authority acts belong to closure piece 5.

## No new low-S rule

Civic v1 does not add a new low-S canonicalization requirement in this contract.

A production signature must:

- be mathematically valid P-256 ECDSA over SHA-256 of the exact Sig_structure;
- encode `r` and `s` as the accepted fixed-width 64-byte P1363 representation;
- satisfy the existing Civic verifier.

A provider adapter must not silently create a new verifier requirement that historical or otherwise valid v1 signatures use one additional S-normalization rule.

Any future change to signature canonicalization must be an explicit cryptographic-profile decision.

## Production signer-provider abstraction

Production Civic code must interact with private keys through a platform-neutral signer-provider abstraction.

The abstract capability is:

~~~text
generate_key(role)
    -> opaque local key reference

public_key(key_ref)
    -> canonical 65-byte SEC1 public key

sign_sig_structure(key_ref, exact_sig_structure_bytes)
    -> 64-byte P1363 ECDSA signature

destroy_or_retire(key_ref)
    -> local custody action
~~~

Optional capabilities may include:

~~~text
export_private_key(key_ref)
import_private_key(...)
provider_status(...)
unlock(...)
lock(...)
~~~

Those optional operations are local implementation capabilities.

They are not Civic authority records.

## Opaque key reference

A `key_ref` identifies private-key custody inside one implementation.

It may be:

- an internal database identifier;
- a pathname-independent software-keystore identifier;
- a provider object handle;
- a PKCS #11 object reference;
- another implementation-local token.

The `key_ref` must not become:

- the Civic key identifier;
- the HOA root identity;
- a field in canonical authority records;
- a required cross-platform serialization.

Only the canonical public key and its derived Civic key identifier cross the authority boundary.

## Public-key derivation and key identity

Immediately after generation or import, the provider must expose or derive the canonical public key.

The implementation must verify:

1. the public key is a valid P-256 point;
2. it is represented canonically as the accepted 65-byte uncompressed SEC1 point;
3. `key_id = SHA-256(public_key)`;
4. the provider can produce a signature that verifies under that public key before the key is relied upon for authority composition.

The implementation must not accept a caller-supplied key identifier that conflicts with the derived public key.

## Provider self-test at key admission

A newly generated or imported production key must pass a local cryptographic admission self-test before becoming usable by Civic composition code.

The self-test must demonstrate, without publishing an authority record:

~~~text
provider key handle
    -> canonical public key
    -> Civic key ID
    -> sign fixed local test bytes
    -> verify under canonical public key
    -> signature shape = 64-byte P1363
~~~

Failure makes the local key unusable.

The test bytes are not Civic authority.

The test signature is not an authority proof.

## Production signing interface boundary

The provider signs exact Sig_structure bytes.

It does not decide:

- which Civic record type is being authorized;
- which protected COSE headers belong to that record;
- which content type applies;
- whether the signer has current Civic authority;
- whether a governance threshold was met;
- whether a ceremony is accepted;
- which history predecessor is current.

Those decisions belong to canonical Civic composition and verification layers.

Conceptually:

~~~text
canonical Civic payload
    -> canonical COSE protected header
    -> exact Sig_structure
    -> production signer provider
    -> 64-byte signature
    -> exact COSE_Sign1 bytes
~~~

The signer provider must not rewrite the payload or protected headers.

## Sign exact bytes, not an ambiguous object

The external production signer interface accepts bytes, not a language-native dictionary, JSON object, ORM object, or mutable record.

This prevents provider-specific serialization from entering authority semantics.

For Civic v1 the provider computes ECDSA over:

~~~text
SHA-256(exact Sig_structure bytes)
~~~

A lower-level provider may internally expose a pre-hashed API, but the Civic production adapter must preserve the exact SHA-256 semantics and must not permit hash-algorithm substitution.

## Post-sign verification is mandatory

Before a newly produced Civic signed object is returned to authority composition code, the implementation must verify the produced signature using the canonical public verification path.

The required sequence is:

~~~text
sign exact Sig_structure
    -> receive 64-byte P1363 signature
    -> verify same Sig_structure + canonical public key
    -> only then construct/return successful signed result
~~~

If self-verification fails, signing fails.

The implementation must not publish, persist as accepted authority, or silently retry with another algorithm.

## Expected-key binding is mandatory

A record-specific production signing operation must know the exact expected Civic key identity from its authority context.

Before signing, it must require:

~~~text
provider_public_key == expected_public_key
derive_key_id(provider_public_key) == expected_key_id
~~~

Examples include:

### Epoch Manifest

The production Signing Node key must exactly match:

~~~text
manifest.signing_node.public_key
manifest.signing_node.key_id
~~~

### Participant governance proof

The participant signing key must exactly match the participant key permitted by the governance-transition context:

~~~text
bootstrap
    -> candidate participant epoch key

successor
    -> predecessor participant epoch key
~~~

### Accepted history records

The signing key must match the signer resolved by the accepted record-type and epoch context.

A provider key that is cryptographically valid but contextually wrong must be rejected before signing.

## Candidate composition versus current authority

A production key can exist before it is accepted as current Civic authority.

The implementation must distinguish:

~~~text
candidate composition capability
    !=
current authority capability
~~~

This distinction is necessary for bootstrap and successor creation.

### Candidate Signing Node key

A newly generated candidate Signing Node key may sign candidate epoch material to prove possession and bind exact candidate bytes.

That signature does not self-authorize the key.

Until complete governance/ceremony/epoch acceptance:

~~~text
candidate Signing Node signature
    = cryptographic attribution / possession

candidate Signing Node signature
    != accepted current authority
~~~

### Current Signing Node key

A Signing Node key may perform current-authority operations only when the accepted current epoch binds that exact public key/key ID and the required Signing Node authorization relationship verifies.

### Candidate participant key

A new successor participant key does not authorize its own admission.

The successor governance proof for a continuing participant is signed by the predecessor epoch participant key as defined by piece 3.

The new participant key becomes current only through the accepted successor epoch.

## Local custody state versus authority-binding state

Implementations must not collapse key storage and Civic authority into one status flag.

For one local key:

~~~text
local custody state:
    absent
    available
    unavailable
    destroyed

authority binding for epoch E:
    unbound
    candidate
    current
    retired
~~~

These are different dimensions.

Examples:

~~~text
available + unbound
    -> generated key exists, no Civic authority

available + candidate
    -> candidate epoch binds it, transition not yet accepted

available + current
    -> accepted epoch binds it as current authority

available + retired
    -> retained old key exists, but old epoch is historical

unavailable + current
    -> current authority key is lost/unusable; recovery transition required
~~~

A local keystore flag cannot turn `candidate` into `current`.

Only accepted Civic authority state can do that.

## Participant-key lifecycle

Participant keys are epoch-specific.

For a continuing participant entering a successor epoch, the accepted ceremony contract requires a new participant key.

Therefore:

~~~text
participant P in Epoch E:
    key P_E

participant P continues in Epoch E+1:
    key P_E+1

P_E+1 != P_E
~~~

The implementation must generate independent new key material.

It must not derive the successor key from the predecessor key.

It must not copy the same participant private scalar into the successor epoch.

The old participant private key may remain locally stored as historical private material, but it must not authorize current acts after the successor epoch becomes current.

Historical verification requires public authority state, not retention of old private keys.

## Signing Node key lifecycle

The Signing Node key is replaceable and epoch-bound as authority material.

Unlike continuing participant keys, the canonical ceremony contract permits deliberate reuse of the same Signing Node key across a successor epoch when the node is intentionally retained.

Therefore both are valid architectural cases:

~~~text
retained node:
    NodeKey_E == NodeKey_E+1
    but each epoch separately binds/authorizes that key

replacement node:
    NodeKey_E != NodeKey_E+1
    successor governance authorizes the replacement
~~~

Reuse is never inferred merely because the old private key is still present.

The candidate successor ceremony must explicitly bind the retained public key and complete governance verification must accept the transition.

## Key generation never activates itself

Generating a new private key must not:

- replace the active key in place;
- rewrite current authority state;
- change the current manifest;
- change the current participant set;
- change the current Signing Node descriptor;
- start signing current-authority records automatically.

New key generation produces local candidate key material only.

Authority activation is a separate accepted-state transition.

This rule is critical for crash safety and governance separation.

## No in-place active-key overwrite

A conforming implementation must not overwrite the only active private-key object with newly generated candidate material before the successor transition is accepted.

Conceptually:

~~~text
current key K1 remains intact
    +
candidate key K2 created separately
    +
candidate transition composed and verified
    +
successor authority state accepted
    ->
K2 becomes current
K1 becomes retired
~~~

The exact atomic commit mechanics belong to closure piece 5.

## Failed candidate transition

If a candidate transition fails governance, verification, persistence, or composition:

~~~text
current accepted authority remains unchanged
candidate key remains non-authoritative
~~~

The candidate key may be retained for diagnostics or deliberately destroyed.

Its existence does not create an accepted fork by itself.

It must not silently replace the current key.

## Signing Node loss

If the current Signing Node private key becomes unavailable, the system does not reconstruct that private key from:

- `hoa_root_id`;
- participant private keys;
- replicated authority state;
- governing sources;
- a permanent HOA master secret.

The recovery path is:

~~~text
participant-held authenticated authority state
    -> reconstruct current Civic identity/lineage
    -> source-governed replacement procedure
    -> generate new candidate Signing Node key
    -> governance proof / ceremony
    -> successor epoch
    -> new Signing Node authorization
    -> accepted successor state
~~~

The lost Signing Node private key is not required for continuity.

## Planned Signing Node key migration

A provider may support deliberate export/import of the **same** Signing Node private key for controlled migration while custody of the current key is still intact.

This is an implementation portability feature, not Civic recovery authority.

If such migration is supported, the imported key must:

- derive the identical canonical public key;
- derive the identical Civic key ID;
- pass the production key admission self-test;
- remain bound to exactly the same Civic authority identity already represented by public state.

A different imported key is not a migration of the same Civic key. It is candidate replacement material requiring governance.

The reference architecture does not require private-key backup or restoration to preserve HOA continuity.

## Loss is not secret recovery

Once the implementation classifies the current Signing Node key as lost or unavailable, the reference recovery path is governed replacement, not searching for a hidden permanent recovery secret.

A deployment may have ordinary disaster-recovery copies of local machine data, but Civic authority must never depend on such a copy existing.

The protocol does not define a permanent Signing Node recovery seed.

## Compromise or suspected compromise

A compromised or credibly suspected-compromised current private key is not repaired by:

- changing its filename;
- re-encrypting the same scalar;
- moving it to different hardware;
- deleting one local copy;
- issuing a local keystore flag.

The required authority response is explicit transition/replacement under the applicable governance rules.

For a participant-key compromise, the current participant set and epoch must be reconsidered under the source-derived policy.

For a Signing Node compromise, a replacement node key and successor authority binding are required unless the applicable accepted governance process explicitly determines another permitted transition.

The old epoch remains historical evidence.

## No automatic shadow replacement

If a current key cannot be loaded, signing must fail.

The implementation must not automatically:

- generate a new key;
- substitute another local key;
- select the newest file;
- select a key by filename similarity;
- fall back to a default key;
- use another participant's key;
- use the Firmware Release Authority key.

Replacement requires an explicit candidate lifecycle operation and the applicable Civic governance transition.

## Key retirement

After a successor epoch becomes current, any superseded key is retired for current-authority use.

Retirement means:

~~~text
old key may still physically exist
but current signing code must not use it
for acts requiring the successor epoch
~~~

Historical verification does not require the old private key.

The deployment may later destroy retired private material according to its local security practice.

Private-key destruction is not itself a Civic authority act and does not rewrite history.

## Private-key destruction limitations

Civic does not claim that software can prove perfect physical erasure across:

- flash translation layers;
- SSD wear leveling;
- virtualized storage;
- snapshots;
- backups;
- swap;
- language runtimes.

Therefore the protocol does not make a cryptographic claim that retirement equals complete forensic erasure.

Authority is removed by the accepted successor epoch, not by pretending local deletion can retroactively invalidate an old public key.

## Private-key export format

Private-key serialization is not Civic authority format.

A software implementation that supports export/import should use an open standard representation appropriate to its platform, such as PKCS #8.

The Civic contract does not require one encryption wrapper, passphrase format, or filesystem representation.

Whatever representation is used must not alter:

- the canonical public key;
- the Civic key identifier;
- record semantics;
- verification behavior;
- epoch authority.

Provider-specific private formats are permitted only as implementation details and must not become mandatory for cross-platform verification.

## Private material must not enter replicated authority state

Private key bytes, seeds, provider recovery secrets, or private-key export blobs must never be included in:

- Epoch Manifests;
- ceremony records;
- governance policies;
- governance proofs;
- accepted history records;
- object-index authority objects;
- participant common authority-state replicas;
- diagnostic JSON projections;
- RAG/LLM source material;
- repository fixtures intended as production state;
- logs or error messages.

Current participant replicas contain public authority state plus only that participant's own independently held private key outside the common replicated state.

## Local access control

A production implementation must restrict private-key operations to the local principal responsible for the signer role.

For software-held keys, default storage/access must not be world-readable or casually shared across unrelated local services.

The exact operating-system permission model is implementation-specific.

The protocol does not require:

- one Unix username;
- one filesystem path;
- one container;
- one access-control product.

A production deployment may add passphrase encryption, encrypted storage, TPM/HSM-backed wrapping, or another local protection mechanism.

Such hardening must remain optional from the Civic protocol perspective.

## No raw private key in ordinary application interfaces

Normal record-composition code should receive an opaque signer/key reference rather than raw private scalar bytes.

Raw private-key import/export, when supported, is a separate lifecycle/administrative capability.

It must not be required for routine signing.

This reduces accidental logging, serialization, copying, and role confusion without turning non-exportability into a Civic requirement.

## Hardware-backed custody is optional

A conforming Civic implementation may use:

- software-held keys;
- a TPM;
- an HSM;
- a PKCS #11 token;
- a secure element;
- another owner-controlled cryptographic provider.

No such hardened mechanism is mandatory.

A conforming implementation must still expose the same canonical public key and produce the same accepted signature semantics.

Optional hardening must not change:

- HOA Civic identity;
- key ID derivation;
- authority-record schemas;
- governance semantics;
- reconstruction semantics;
- verifier requirements.

## Remote mandatory signing is prohibited as a baseline dependency

The baseline Civic Signing Node must not require a remote proprietary signing service or cloud account in order to exercise HOA-local authority.

A deployment may deliberately attach remote operational services, but loss of those services must not redefine the Civic protocol or create a central Civic authority.

The reference implementation must remain reproducible using owner-controlled local signing capability.

## Production fixture separation

The following existing helpers are explicitly non-production:

- `public_key_from_private_scalar(...)` when used with hand-selected fixture scalars;
- `sign_sig_structure_fixture(...)`;
- `sign_epoch_manifest_fixture(...)`;
- fixture-only governance-proof signing helpers;
- fixture-only signed-history helpers.

Production signing code must not call fixture-signing functions.

Tests may continue using them for deterministic vectors.

A production implementation must make the fixture/production boundary mechanically apparent in module/API structure.

## Error semantics

Production signing fails closed.

At minimum, these conditions are hard failures:

- secure randomness unavailable during key generation;
- provider key generation failure;
- malformed or invalid canonical public key;
- key-ID/public-key mismatch;
- wrong key for requested Civic authority context;
- key unavailable or locked;
- unsupported cryptographic profile;
- provider algorithm mismatch;
- signature length/encoding mismatch;
- signature self-verification failure;
- candidate key presented as current without accepted authority binding;
- retired key requested for a current-epoch act;
- provider returns ambiguous or incomplete result.

The implementation must not repair these failures by silently choosing another key or algorithm.

## Failure reporting and Diagnostics

A signing failure may emit diagnostic metadata sufficient to understand the failure, including:

- operation type;
- expected role;
- expected key ID;
- observed public key ID where safely available;
- provider class/name where appropriate;
- failure category;
- Civic epoch/context identifier;
- timestamp as ordinary diagnostic metadata.

It must not emit:

- private scalar;
- private-key export bytes;
- seed material;
- signing nonce;
- provider unlock secret;
- passphrase;
- raw secret recovery material.

A diagnostic timestamp is not a trusted Civic authority timestamp merely because it appears in a signing failure report.

## Crash and restart semantics

A process restart must not change which key is Civic-authoritative.

After restart, current-authority selection must be reconstructed from accepted Civic state plus local custody availability.

The implementation must not select a key merely because it is:

- newest by filesystem timestamp;
- first in a directory;
- most recently generated;
- provider default;
- the only key currently loadable.

If accepted state says key `K1` is current and only `K2` is locally available, the result is:

~~~text
current key K1 unavailable
candidate/unbound key K2 available
    ->
signing failure / recovery required
~~~

not automatic activation of `K2`.

## Authority after restart

For a current operation, the implementation must establish all of:

~~~text
accepted current epoch verifies
requested signer role is permitted
expected public key/key ID comes from accepted authority context
local provider exposes matching key
signature verifies
~~~

Only then is a successful current-authority signature possible.

The local keystore is never the source of which key is current.

## Concurrency boundary

Two local processes must not independently treat different candidate keys as current merely because both keys are available.

Current authority comes from one accepted authority state.

Detailed locking, compare-and-swap, journaling, and atomic state installation belong to closure piece 5.

Piece 4 freezes only the key rule:

> candidate generation must never mutate current key authority in place.

## Current key reuse and repeated signing

Repeated use of one current Signing Node key within its accepted epoch is permitted for the authority acts assigned to that node.

Repeated use of one participant epoch key is permitted only for acts that the accepted authority model permits that participant key to sign.

Cryptographic key possession does not widen role permissions.

## Key-use scope must be explicit

Production signing code must not expose a generic "sign arbitrary bytes with any current key" authority API to ordinary Civic composition code.

The low-level provider can sign bytes, but the Civic layer must call it through role/context-specific checks.

This preserves the distinction between:

~~~text
cryptographic capability
    !=
Civic authorization
~~~

An administrative test tool may exercise a key self-test, but its output must not be accepted as a Civic authority record.

## No private-key derivation hierarchy

The Civic reference does not define HD-wallet-style or hierarchical deterministic derivation.

Participant keys and replacement Signing Node keys are independently generated.

The implementation must not derive:

~~~text
participant key
from Signing Node key

Signing Node key
from participant key

successor participant key
from predecessor participant key

HOA root ID
from a private-key hierarchy
~~~

This limits cross-role and cross-epoch secret coupling.

## Participant continuity does not copy private keys

Same-and-Equal participant replicas are Same-and-Equal for common authority-state continuity, not for secret custody.

Therefore:

~~~text
Participant A replica:
    common authority state
    + A's private key

Participant B replica:
    common authority state
    + B's private key
~~~

Participant A does not receive B's private key.

Participant B does not receive A's private key.

The Signing Node private key is not replicated as part of participant common authority state.

## Historical public verification survives key loss

All accepted historical signatures remain verifiable from retained public authority state even if the corresponding private key is:

- retired;
- lost;
- destroyed;
- stored on failed hardware.

This is a required consequence of the public authority-state model.

A verifier must never require historical private-key recovery.

## Key compromise does not rewrite historical verification

If a private key is later compromised, historical records signed under that key remain cryptographically verifiable as records attributed to that key.

The compromise may affect trust interpretation and Diagnostics.

It does not authorize silent rewriting of historical bytes.

A later authority transition can record replacement and current-state consequences.

## Time is not a key authority source

Key lifecycle decisions must not depend solely on local wall-clock time.

Time may be:

- ceremony effective-time data;
- standing validity data;
- operational metadata;
- diagnostics.

But a key does not become current merely because a timestamp has passed.

Accepted authority state and governance establish current key authority.

## Production key metadata

An implementation may retain local non-authoritative metadata such as:

~~~text
key_ref
role_hint
canonical_public_key
key_id
provider_identifier
created_at
last_used_at
local_custody_status
exportability_capability
~~~

These fields are operational metadata.

They do not replace the canonical authority records.

If such local metadata conflicts with accepted Civic authority state, authority state wins and the conflict is Diagnostics.

## Import semantics

If private-key import is supported:

1. parse using the provider's standard format;
2. derive the canonical public key;
3. derive the Civic key ID;
4. run the key admission self-test;
5. assign only local candidate/custody metadata;
6. resolve Civic authority from accepted epoch state separately.

Importing a key does not authorize it.

Importing an old retired key does not make it current.

Importing a different key under the filename of a current key does not preserve authority identity.

## Export semantics

If private-key export is supported, export is an explicit administrative operation.

Routine Civic signing must not require periodic export.

Exported private material must never be written into Civic authority objects or ordinary Diagnostics.

The protocol does not claim that export is always available; hardware-backed providers may legitimately refuse it.

Provider non-exportability is acceptable only when it remains an optional deployment choice and is not required for Civic interoperability or continuity.

## Provider replacement

Changing cryptographic provider while retaining the same private key is an implementation migration if the canonical public key and key ID remain identical.

Changing provider and generating a different key is a key replacement and requires the appropriate governance/epoch transition before the new key is current.

Therefore:

~~~text
provider identity
    != Civic key identity

Civic key identity
    = SHA-256(canonical public key)
~~~

## Signing Node hardware replacement

Replacing the physical machine does not necessarily require a new Civic key if a controlled same-key migration is deliberately performed and allowed by local policy.

However, Civic continuity never requires same-key migration.

A deployment may instead generate a new Signing Node key and use the governed replacement path.

Physical hardware identity is not Civic authority identity.

## Participant hardware replacement

Participant hardware replacement does not copy authority automatically.

A participant credential is epoch-specific.

Where a replacement participant device/key changes the current participant credential, the applicable source-derived ceremony/epoch rules govern that transition.

The protocol does not infer authority from device serial number or ownership of old hardware.

## Bootstrap production sequence boundary

Piece 4 freezes the cryptographic/key lifecycle portion of a bootstrap sequence:

~~~text
secure random HOA root ID
securely generate candidate participant keys
securely generate candidate Signing Node key
derive canonical public keys / key IDs
run local key admission self-tests
compose source-grounded bootstrap authority bundle
candidate keys may prove possession where required
verify governance / ceremony / complete bootstrap closure
accept Epoch 1 atomically
only then treat Epoch-1 key bindings as current authority
~~~

The final atomic acceptance mechanics belong to piece 5.

No candidate key self-authorizes bootstrap.

## Successor production sequence boundary

For a successor transition:

~~~text
verify accepted current authority state
determine source-governed transition
generate required new participant keys
generate replacement Signing Node key if node changes
or explicitly retain current Signing Node public identity
construct candidate successor ceremony
collect governance proofs under the correct predecessor/candidate signer rules
verify complete governance transition
compose successor authority state
accept successor atomically
retire superseded current key bindings
~~~

Again, piece 5 defines atomic composition/commit mechanics.

## Signing Node key retention across successor

If the current Signing Node remains intentionally authorized:

- no new node key is required merely because the epoch sequence increments;
- the successor ceremony must bind the same canonical node public key/key ID;
- the successor accepted authorization relationship is new epoch authority;
- local key custody may continue using the same key reference.

This is a new authority binding to an existing key, not a claim that the old epoch remains current.

## Participant key rotation across successor

For every continuing participant, successor key rotation is mandatory under the canonical ceremony contract.

The implementation must reject successor composition that attempts to reuse that continuing participant's predecessor key.

This remains true even if the old key is still secure and locally available.

## Key ID collision handling

If newly generated key material somehow derives a key ID already assigned to a different canonical public key, the implementation must fail.

It must not choose identity based solely on key ID when canonical public-key bytes conflict.

A SHA-256 collision is not expected operationally, but the implementation must preserve explicit byte equality checks rather than silently merging contradictory keys.

## Random-source failure

If the secure random source is unavailable or reports failure:

~~~text
generate_key
    -> hard failure
~~~

The implementation must not:

- wait for a predictable seed;
- substitute ordinary PRNG output;
- derive a key from existing authority state;
- reuse a retired key as an implicit replacement.

Existing current keys may continue to sign only if their normal signing provider remains sound and the requested act is otherwise authorized.

## Provider health failure

If a provider reports an internal failure, inconsistent public key, invalid signature, or corrupted key object, the key must be treated as unavailable for that operation.

The system must not keep retrying indefinitely while emitting multiple candidate authority objects.

Operational retry policy may exist, but every completed signed object is exact distinct evidence and piece 5 must control publication/acceptance.

## Signing result boundary

A successful low-level signing call establishes only:

~~~text
this provider possessing this private key
produced a valid signature
over these exact Sig_structure bytes
~~~

It does not establish:

- current standing;
- governance sufficiency;
- legal truth;
- accepted history inclusion;
- accepted epoch status;
- factual truth of a claim.

Those meanings remain at higher Civic verification layers.

## Verification remains public and provider-independent

Production signing-provider choice must not alter verification.

A verifier needs:

- canonical signed bytes;
- canonical public key;
- accepted Civic cryptographic profile;
- relevant public authority context.

It must not need:

- the signing provider;
- the private-key file format;
- the original machine;
- the original operator account;
- the original token/HSM;
- a vendor API.

This is the principal portability test for the production key architecture.

## Required production implementation separation

The future production implementation should introduce a module boundary distinct from fixture cryptography.

Conceptually:

~~~text
civic production signing adapter
    -> signer-provider interface
    -> one software provider implementation
    -> optional future hardened providers
~~~

The reference implementation must include at least one owner-controlled software provider so Civic production signing does not depend on special hardware.

Optional providers may be added later without changing the canonical authority formats.

This document does not freeze Python module names.

## Minimum production implementation acceptance properties

Before production signing can be declared implemented, repository tests must establish at least:

1. secure production key generation through the production provider API;
2. canonical 65-byte public-key derivation;
3. SHA-256 key-ID derivation;
4. 64-byte P1363 signature production;
5. public verification of every production signature;
6. wrong expected key/public-key rejection;
7. no fixture-signing function on the production path;
8. unavailable key fails without automatic replacement;
9. candidate key existence does not make it current;
10. retired key is rejected for current-authority operations;
11. participant successor key rotation is enforced;
12. deliberate Signing Node key retention can remain valid when the successor ceremony explicitly reauthorizes it;
13. new Signing Node replacement key does not self-authorize;
14. imported same-key migration, if implemented, preserves exact public key/key ID;
15. private key bytes do not appear in authority-state serialization;
16. random-source/provider failure is fail-closed;
17. signing result self-verification is mandatory.

Focused tests may use controllable fake providers to exercise failure cases.

Production success-path tests must exercise the actual software production provider selected by the implementation.

## No production activation during implementation acceptance

Repository implementation and CT102 acceptance of production-signing code do not themselves authorize creation of a real HOA production key.

The following remain separate later actions:

~~~text
implement production provider
test production provider
accept repository implementation
choose production deployment
create real HOA candidate key material
conduct source-governed bootstrap/transition
accept production epoch
~~~

A repository test key is not an HOA production key.

## Relationship to closure piece 5

Piece 4 freezes:

- how keys are generated;
- how local custody is represented abstractly;
- how exact bytes are signed;
- how expected key identity is enforced;
- how key availability/loss/retirement behaves;
- how candidate versus current authority is distinguished.

Piece 5 must freeze the transaction/composition rules that make multi-object authority changes safe.

In particular, piece 5 must address:

- candidate bundle construction;
- exact dependency closure;
- signing order;
- object persistence order;
- history-head updates;
- manifest finalization;
- crash/retry behavior;
- atomic acceptance of bootstrap/successor state;
- prevention of partially installed current authority.

Piece 5 must not weaken the piece-4 rule that generating a key never activates it.

## Relationship to closure piece 6

Piece 6 defines the platform-neutral Signing Node conformance/deployment boundary.

It may specify required functional capabilities such as:

- production signer-provider availability;
- local authority-state verification;
- object retention;
- deterministic record composition;
- recovery inputs/outputs.

It must not redefine the key semantics accepted here.

Concrete Annales deployment belongs to a later separate project.

## Annales boundary

This reference contract intentionally contains no Annales-specific:

- hostname requirement;
- LXD container name;
- systemd unit;
- filesystem key path;
- Unix account;
- network port;
- service topology;
- concrete key filename;
- backup directory.

Those choices belong to the separate Annales production implementation project after Kane Fabric Civic Authority Reference closure.

## Security hardening boundary

Optional hardening may be valuable.

Examples include:

- full-disk encryption;
- encrypted key stores;
- TPM/HSM custody;
- secure boot;
- measured boot;
- dedicated service accounts;
- memory locking;
- process sandboxing;
- offline backups;
- access-audit tooling.

None of these may become a hidden prerequisite for Civic authority interoperability unless a later accepted architecture decision explicitly changes the baseline.

The minimum reference remains owner-controlled, reproducible, software-capable, and platform-neutral.

## Diagnostics from key-lifecycle failures

Key-lifecycle failures are high-value Diagnostics evidence.

Examples:

- expected current key is unavailable;
- keystore contains a conflicting public key;
- provider produces invalid signatures;
- current authority state references a key not locally present;
- retired key is requested for a current act;
- candidate key appears in local storage without accepted authority;
- signing node was replaced without a valid successor transition;
- participant successor reused an old epoch key;
- two replicas disagree about the accepted current key binding.

Diagnostics may preserve those observations without repairing authority state.

## Decision summary

The production signing/key-lifecycle contract is:

~~~text
Civic identity
    != private key
    != key file
    != provider
    != machine

secure randomness
    -> independent P-256 key generation
    -> canonical public key
    -> SHA-256 key ID
    -> local candidate custody

accepted governance + ceremony + epoch
    -> current authority binding

exact canonical payload/header context
    -> exact Sig_structure
    -> context-matched production signer
    -> P-256/SHA-256 signature
    -> 64-byte P1363
    -> mandatory public self-verification

participant successor
    -> new participant key

Signing Node successor
    -> explicit same-key retention
       OR governed replacement with new key

lost/compromised key
    -> no shadow substitution
    -> no HOA master recovery secret
    -> governed replacement

historical verification
    -> retained public authority state
    -> no historical private-key recovery

provider/hardware/storage
    -> replaceable implementation detail
~~~

## Closure result

This document freezes closure piece 4 at the architecture level.

It authorizes a later bounded implementation of a production signer-provider abstraction and owner-controlled software provider **without** creating or activating real HOA production key material.

The next closure piece after implementation/test acceptance of this contract is piece 5:

> authority-state transaction and composition semantics.
