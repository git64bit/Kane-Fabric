# Civic Participant Authority-State Replication and Reconstruction

## Status

Accepted architecture contract for participant-held Civic authority-state replication and reconstruction.

This document intentionally adopts a generous baseline. Fine-grained retention optimization may be introduced later only if it preserves the same reconstruction result and does not weaken participant independence.

It refines, but does not replace:

- `docs/CIVIC_AUTHORITY_CONTINUITY_DECISION.md`;
- `docs/CIVIC_AUTHORITY_EPOCH_CEREMONY.md`;
- `docs/CIVIC_EPOCH_MANIFEST_FORMAT.md`;
- `docs/CIVIC_HISTORY_HEAD_SEMANTICS.md`;
- `docs/CIVIC_OWNER_OPERATED_SIGNING_NODE.md`;
- `docs/CIVIC_SAME_AND_EQUAL_POLICY.md`.

## Decision

Every current Same-and-Equal participant holds a complete independently verifiable replica of the Civic authority state needed to reconstruct the HOA Civic Identity and its accepted authority lineage.

The baseline is not partial replication, threshold secret sharing, or dependence on one current operator.

For authority-state continuity:

~~~text
Participant A replica
Participant B replica
Participant C replica

        each independently contains
        the complete replicated
        Civic authority state

             |
             v

any one current surviving participant
can supply the authority state required
to reconstruct continuity
~~~

This is the meaning of 1-of-N continuity.

It does not mean 1-of-N governance power.

## Same-and-Equal replication property

Current participant replicas are Same-and-Equal with respect to authority-state continuity.

No current participant is assigned a privileged fragment that another current participant must obtain in order to reconstruct the accepted authority state.

A participant may have different local diagnostics, witness evidence, or private material, but the common authority-state replica is complete.

## What is reconstructed

Reconstruction restores authenticated Civic authority state.

At minimum, the reconstruction result includes:

- the stable HOA Civic root identity;
- the complete accepted Epoch Manifest lineage through the current epoch;
- current epoch sequence and predecessor relationship;
- governing profile identity;
- exact governing-source identities and all authority-required governing-source objects;
- the current Same-and-Equal participant set;
- current participant public keys and key identifiers;
- current participant standing and issuance record identities and required records;
- the current operator designation and required selection record;
- the current Civic Signing Node public identity and required authorization record;
- ceremony and governance provenance required by the accepted epochs;
- accepted, witness, diagnostics, and knowledge history needed by the retained authority lineage;
- current history heads;
- all authority-required objects referenced through Epoch Manifest `object_index`;
- the cryptographic and format information required to verify those artifacts.

Reconstruction restores what the Civic Infrastructure recognizes and why it recognizes it.

It does not reconstruct one permanent HOA signing secret.

## Full authority-lineage replication

The baseline participant replica retains the complete accepted Civic authority lineage, not merely the current snapshot.

That includes the signed Epoch Manifest for every accepted epoch from genesis through the current epoch and all authority records required to verify those epoch transitions.

The replica therefore supports verification of:

~~~text
genesis epoch
    -> successor epoch
    -> successor epoch
    -> ...
    -> current epoch
~~~

The current Epoch Manifest remains the positive statement of current authority.

Historical epochs remain evidence of prior authority state and transition provenance.

## Full authority-record replication

Every object required to verify, interpret, or reconstruct accepted Civic authority state is mandatory replica content.

This includes exact object bytes when the Epoch Manifest or authority lineage depends on those bytes.

SHA-256 descriptors are not substitutes for locally retaining authority-required bytes under this baseline.

The content-addressed object store may determine where those bytes are stored physically, but storage location does not change Civic identity.

## History replication

Participant authority-state replicas retain the complete accepted linked Civic authority history required by the accepted lineage.

For each retained history stream, the replica preserves the exact deterministic record bytes necessary to verify predecessor links and the stream head named by the relevant Epoch Manifest.

A participant must not claim complete reconstruction from only a final history-head hash when the predecessor records required by the accepted authority lineage are unavailable.

Future checkpoint or compaction rules may reduce retained bytes only if they are separately specified, authenticated, and proven to preserve equivalent reconstruction.

No such optimization is part of the baseline.

## Governing-source replication

Where exact governing-source bytes are required to interpret an accepted governing profile or authority act, those exact bytes are part of the mandatory authority-state replica.

A URI, filename, portal location, or future network retrieval path does not replace the required SHA-256 identity or the retained exact bytes.

This preserves reconstruction when an external website, portal, service, or operator disappears.

## Non-authoritative evidence boundary

Not every byte ever observed by Civic Infrastructure must be duplicated on every participant device.

Large evidence or source material that is not required to establish, interpret, or verify accepted Civic authority may remain outside the mandatory participant replica when its Civic record preserves the required content identity and provenance.

For such material, the authority replica may retain:

- SHA-256 content identity;
- byte length;
- media type;
- semantic role;
- provenance or retrieval metadata where applicable;
- optional future CID or other distribution attachment.

This exception must not be used to externalize an object that is required to reconstruct authority.

When uncertain, the generous baseline is to retain the exact bytes.

## Private-key boundary

Common replicated authority state contains no participant private keys.

Each participant retains only that participant's own epoch-specific private key material.

Therefore:

~~~text
Participant A replica
    common authenticated authority state
    + Participant A private key

Participant B replica
    common authenticated authority state
    + Participant B private key
~~~

Participant A does not need Participant B's private key.

Participant B does not need Participant A's private key.

No participant holds a required permanent HOA master private key.

No participant holds a required shared recovery private key.

## Signing Node private key is not reconstructed

Loss of the current Civic Signing Node does not cause a surviving participant to reconstruct or recover the lost Signing Node private key.

The surviving participant reconstructs the authenticated Civic authority state that identifies:

- the current HOA Civic root;
- the current epoch;
- the current participant set;
- the current operator;
- the lost or unavailable Signing Node's public identity;
- the authority lineage and governance provenance.

A replacement Signing Node generates new key material.

That replacement becomes authoritative only through the applicable source-governed ceremony and authority-epoch transition.

## Participant private key is not governance authority

Possession of one surviving current participant device and its private key is sufficient to supply one complete authority-state replica.

It is not sufficient by itself to:

- redefine the current Same-and-Equal set;
- elect or replace the operator;
- authorize a replacement Signing Node;
- create an accepted successor epoch;
- alter governing-source meaning;
- rewrite accepted history.

Those actions continue to require the applicable source-derived governance process.

## Reconstruction inputs

A baseline reconstruction begins with one current participant replica.

The reconstruction process must be able to obtain from that replica, without dependence on the failed Signing Node or former operator:

1. the current signed Epoch Manifest;
2. all predecessor signed Epoch Manifests back to genesis;
3. all mandatory authority objects referenced by those manifests;
4. all required linked history records;
5. all public verification material needed to validate the retained artifacts;
6. the participant's own current epoch credential and private key material, if that participant is to continue acting as a participant after recovery.

The participant's own private key is not needed merely to verify previously issued public authority state, but remains part of that participant's continuing epoch-specific identity.

## Reconstruction verification

A reconstruction is complete only when the retained state verifies.

At minimum, verification must establish:

- deterministic CBOR validity where required;
- COSE and Civic signature validity where required;
- Epoch Manifest payload identities;
- exact predecessor-manifest continuity;
- object SHA-256 and byte-length identities;
- participant public-key and key-identifier bindings;
- required authority-record identities;
- history predecessor-link continuity;
- history-head agreement;
- current epoch selection from the accepted lineage.

Failure of one required authority object or verification relationship makes reconstruction incomplete.

The implementation must not silently substitute current network content, regenerate authoritative bytes from JSON, skip a missing predecessor, or infer an authority record from operator memory.

## Reconstruction output

A successful reconstruction produces an independently usable authority-state replica whose verified current state is identical in Civic meaning and content identity to the state represented by the surviving participant.

Physical paths, storage devices, hostnames, container identifiers, IP addresses, or replacement hardware may differ.

The Civic authority identity does not.

## Replica convergence

All current participant replicas should converge on the same accepted common authority state for an epoch.

If two current participants present different candidate current states, the implementation must preserve both claims and expose the divergence.

It must not resolve the difference by:

- choosing the newest filesystem timestamp;
- trusting the current operator automatically;
- trusting the Signing Node automatically;
- taking a majority of byte copies without governance context;
- overwriting one replica with another before verification.

Resolution depends on authenticated epoch lineage, governing provenance, and the applicable Civic governance rules.

Divergence is Diagnostics evidence.

## New epoch replication

When a valid ceremony creates a successor epoch, each participant in the new current Same-and-Equal set receives or constructs the complete new authority-state replica.

The new replica includes the prior accepted lineage plus the successor epoch and all new authority-required objects.

Only after the successor state verifies is it accepted as the participant's current authority state.

Participants excluded from the successor epoch may retain prior replicas as historical evidence, but their old epoch credentials do not establish current authority.

## Storage implementation freedom

This contract does not require one physical archive format.

A participant implementation may use:

- ordinary files;
- a SHA-256 content-addressed object store;
- deterministic CBOR Sequence files;
- removable media;
- replicated filesystem layouts;
- future IPFS attachments;
- another open and independently implementable storage arrangement.

The required invariant is the reconstructable authenticated content, not one filesystem layout.

## Reference-device capacity

The ESP32-S3 remains a reference participant platform, not a protocol size limit.

The architecture does not weaken reconstruction merely to fit an artificially small local storage assumption.

A participant implementation may use attached storage or another user-owned platform while preserving the same published authority-state contract.

Resource exhaustion or inadequate storage is an observable deployment failure and may become Diagnostics evidence.

## Loss cases

### Signing Node lost

~~~text
current participant replica
    -> verify complete authority state
    -> reconstruct current Civic identity/lineage
    -> conduct required governance procedure
    -> create replacement Signing Node key
    -> authorize through new ceremony/epoch
    -> replicate successor authority state
~~~

The lost Signing Node private key is not recovered.

### One participant lost

Other current participants already possess complete authority-state replicas.

Continuity is unchanged.

If the participant set changes, the applicable governance rule may require a new ceremony and epoch.

### All but one participant lost

The surviving current participant can still supply the complete replicated authority state.

This preserves continuity.

It does not waive governance requirements for creating the successor authority state.

### Operator lost or unavailable

Current participant replicas preserve the authority state independently of the operator.

A replacement operator is selected under the applicable source-derived governance rule.

### External evidence store unavailable

Authority reconstruction continues if the unavailable material was genuinely non-authoritative and non-required for reconstruction.

If missing external bytes were actually required to establish or verify authority, the replica was incomplete and reconstruction fails visibly.

## No silent weakening

A future implementation may optimize storage, add checkpoints, introduce additional replication tiers, or distribute bulky evidence.

It may not redefine the baseline result.

Any optimization must preserve the ability of one current surviving participant to produce a complete independently verifiable reconstruction of accepted Civic authority state without:

- a permanent HOA master private key;
- another participant's private key;
- the failed Signing Node private key;
- the former operator;
- a proprietary hosted service;
- a vendor account;
- a central Civic signing service.

## Decision summary

The Civic continuity baseline is:

~~~text
one HOA
    -> one autonomous Civic authority domain

one current participant
    -> one complete authority-state replica
    -> one independent epoch-specific participant private key

all current participants
    -> Same-and-Equal complete authority-state replicas

one surviving current participant
    -> complete state reconstruction capability

reconstruction
    != unilateral governance authority
    != recovery of another participant's private key
    != recovery of the old Signing Node private key
    != recovery of a permanent HOA master key

replacement Signing Node
    -> new key
    -> source-governed ceremony
    -> new epoch
    -> complete successor replicas
~~~

This is the baseline to implement with full conviction. Storage optimizations may come later; continuity semantics do not depend on them.
