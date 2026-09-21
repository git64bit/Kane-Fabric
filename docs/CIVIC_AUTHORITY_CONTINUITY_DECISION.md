# HOA Civic Authority Continuity Decision

## Status

Accepted architecture decision. Documentation only.

This document closes the principal Civic authority-continuity design question for HOA Diagnostics.

It does not freeze a cryptographic algorithm, serialized record format, ESP32 storage layout, signing-provider implementation, or hardware bill of materials.

## Decision

The HOA Civic Identity is reconstructed from **replicated authority state held by the current Same-and-Equal participant ESP32-S3 devices**.

Each current participant device has its **own independent epoch-specific key material**.

There is no required permanent HOA master private key, no required shared recovery private key, and no requirement that multiple devices hold shares of one long-lived signing secret.

Conceptually:

~~~text
HOA Civic Identity
        |
   Authority Epoch E
        |
   +----+----+----+
   |         |    |
 ESP-A     ESP-B ESP-C
 Key A_E   Key B_E Key C_E
   |         |    |
   +-- replicated accepted epoch state --+
~~~

## What survives

The durable continuity object is not one secret.

It is the attributable lineage of:

- HOA identity;
- governing-source/profile identity;
- authority epochs;
- Same-and-Equal participant sets;
- operator designations;
- operator-owned Civic Signing Node identities;
- accepted history heads;
- source-governed transitions;
- participant/device attestations;
- correction and supersession history.

A device, key, operator, node, or participant may disappear without erasing that lineage.

## Independent device keys

During a key-signing ceremony, each current Same-and-Equal participant device receives or creates key material specific to that device and that authority epoch.

The design requirement is:

~~~text
Key A_E != Key B_E != Key C_E
~~~

A participant device does not need another participant's private key.

No participant device needs to contain a permanent HOA signing private key.

## Replicated authority state

Each current device retains enough authenticated authority state to reconstruct and explain the current HOA Civic Identity.

The state must eventually include at least:

- HOA/root identity;
- current authority-epoch identity;
- predecessor epoch identity;
- governing-source/profile identity;
- current Same-and-Equal set and device public identities;
- current operator identity;
- current operator-owned Civic Signing Node identity;
- accepted history/lineage head;
- verification material needed to interpret the epoch;
- source-governed transition record into the epoch.

Exact representation remains an implementation decision.

## 1-of-N continuity

The padlock analogy is accepted for **continuity/recovery**:

~~~text
Device A --+
Device B --+-- any one current surviving device
Device C --+   can provide the replicated HOA authority state
~~~

This does not mean one device has unilateral governance authority.

The device supplies the state needed to reconstruct continuity; it does not independently change the HOA's current authority.

## Governance remains source-derived

Changing the operator, trusted participant set, signing node, authority epoch, or another governance state still requires the applicable procedure inherited from:

~~~text
Illinois statute
    +
valid condominium instruments/bylaws
    +
published Same-and-Equal policy
~~~

Therefore:

~~~text
1-of-N continuity
    !=
1-of-N governance
~~~

A single device can preserve/recover state.

The prescribed Same-and-Equal electorate authorizes a governance transition.

## New ceremony on trust-set change

When a current device owner becomes untrusted or otherwise leaves the applicable current Same-and-Equal class, the preferred model is a new ceremony and new authority epoch.

~~~text
Epoch E
   |
trust/membership change
   |
source-governed authorization
   |
new key-signing ceremony
   |
Epoch E+1
   |
new independent device keys
new replicated current state
~~~

The prior device does not need to be confiscated or erased.

Its old key and old state remain historical evidence for the prior epoch.

They do not confer authority in the new epoch.

## No permanent revocation ledger required for current authority

Current authority is stated positively by the current epoch.

The system need not define current authority primarily as:

~~~text
all keys ever issued
minus every key ever revoked
~~~

Instead:

~~~text
current epoch
    = current recognized set
~~~

Historical exclusion/replacement remains visible through epoch lineage.

## Operator-owned signing node

Each participating HOA still requires its own operator-owned Civic Signing Node.

The node:

- performs current local authority operations;
- binds acts to statute/bylaws/profile;
- produces authority proofs/signatures;
- records issuance/governance provenance;
- supports peer scrubbing;
- supports participant ESP32-S3 witnessing/attestation.

But the node is not the permanent HOA Civic Identity.

Its authority is recognized within the current epoch.

If it is lost, replaced, or its operator changes, the HOA identity can be reconstructed from current participant-device state and a replacement node can be authorized through the governing process.

## Signing node versus participant devices

~~~text
Same-and-Equal participant devices
    = distributed continuity witnesses

operator-owned Civic Signing Node
    = current local authority appliance

Firmware Release Authority
    = software-release authority

Illinois statute + valid condominium instruments
    = substantive governing source
~~~

These roles must remain distinct.

## Why the shared-recovery-secret alternative is rejected

A second design considered one common HOA recovery secret independently wrapped to several participant devices.

That design is not selected as the baseline because:

- compromise of any one device can expose the same common secret;
- removing one trusted participant still requires replacing that common secret;
- the epoch model already requires rekeying when the trusted set changes;
- a shared secret adds a powerful permanent object without providing necessary civic semantics;
- replicated public/authority state plus independent keys provides the desired 1-of-N continuity without a master recovery secret.

A future implementation may introduce an additional wrapped secret for a narrowly defined technical purpose, but it must not become the HOA Civic Identity or silently replace this continuity model.

## Failure interpretation

The accepted architecture produces simple failure semantics.

~~~text
one participant device lost
    -> continuity remains available from another current device

operator signing node lost
    -> current participant-device state supports reconstruction
    -> governance procedure authorizes replacement node

participant becomes untrusted
    -> source-governed transition
    -> new ceremony
    -> new epoch and keys

old device presents old epoch
    -> historically verifiable, not current authority

devices present conflicting current histories
    -> diagnostic divergence requiring source/lineage scrutiny
~~~

The system does not need to make disagreement impossible.

It needs to make the divergence attributable and inspectable.

## Ceremony output

Without freezing serialization, a successful ceremony must conceptually produce an **Epoch Manifest** containing or binding:

~~~text
HOA identity
epoch identity
predecessor epoch
governing-source/profile identity
Same-and-Equal current participant/device set
participant-device public identities
current operator
current Civic Signing Node public identity
effective time
accepted prior-history head
ceremony/governance provenance
authority proof(s)
~~~

Each current participant device retains the accepted Epoch Manifest or an authenticated representation sufficient to reconstruct it.

## Bootstrap

The initial HOA bootstrap remains exceptional only because no prior Civic epoch exists.

It creates the first HOA-local signing node, first accepted participant set, and first authority epoch.

Once that first epoch exists, later continuity does not depend on the bootstrap operator.

All later operator/node/trust-set transitions follow the normal source-derived governance and epoch rules.

The exact evidence required for first bootstrap remains profile/implementation work.

## SASE relationship

SASE establishes or renews voluntary Civic participation according to the active profile.

SASE cadence is a profile parameter and is separate from the cryptographic continuity decision in this document.

An HOA profile may derive a cadence from its governing-source model; changing that cadence does not change the authority-epoch architecture.

## ESP32-S3 witness role

The same participant ESP32-S3 can later assemble witness/attestation records.

Such records identify the authority epoch and civic context under which the device was operating.

The device authors the witnessed record.

The operator/signing node may later accept, anchor, or relate that record to HOA-local history without becoming the author of the observed event.

## What is now architecturally settled

The following are accepted design invariants:

1. each participating HOA is an autonomous Civic authority domain;
2. each participating HOA has its own operator-owned Civic Signing Node;
3. the signing node is not the permanent HOA Civic Identity;
4. the HOA Civic Identity is reconstructed from replicated current authority state;
5. current Same-and-Equal participant ESP32-S3 devices hold independent epoch-specific keys;
6. any one current device may provide continuity/recovery state;
7. one device does not gain unilateral governance power from that recovery capability;
8. governance transitions use the source-derived Same-and-Equal electorate/procedure;
9. trust-set change creates a new authority epoch and new current keys;
10. old epochs remain historical evidence and do not confer current authority;
11. no permanent HOA master/recovery private key is required;
12. cross-HOA authority roots remain separate;
13. operator/node/device replacement must not destroy HOA identity;
14. divergence is preserved as diagnostic evidence rather than silently overwritten.

## What remains implementation work

The following choices are intentionally **not** architecture blockers:

- cryptographic algorithm;
- key encoding;
- signature encoding;
- canonical serialization;
- key-generation API;
- ESP32 secure-storage mechanism;
- signing-node hardware/provider;
- exact Epoch Manifest byte layout;
- transport protocol;
- backup medium;
- UI/ceremony software;
- exact local database/storage schema;
- exact recovery command sequence.

Those implementation choices must preserve the accepted invariants above.

## Design closure

The HOA Civic authority-continuity problem is sufficiently specified to leave conceptual architecture and proceed later to implementation interrogation.

No implementation is authorized merely by this documentation checkpoint.
