# Civic Authority Epoch and Key-Signing Ceremony

## Status

Architecture contract. Documentation only.

This document defines the continuity model for one HOA-local Civic authority.

## Core rule

The HOA Civic Identity is not anchored to one permanent operator key or one permanent participant device.

It is reconstructed from the current authority epoch represented across the Same-and-Equal participant ESP32-S3 devices.

A key-signing ceremony creates:

- a new authority epoch;
- the current Same-and-Equal participant set for that epoch;
- `N` epoch-bound participant devices/credentials;
- the current HOA-local authority statement/history head;
- the relationship between that epoch and its predecessor.

## Padlock analogue

The design follows the physical 1-of-N gate-lock principle:

~~~text
Device A ─┐
Device B ─┼─ any one current device can recover/reconstruct
Device C ─┘  the HOA Civic Identity state for this epoch
~~~

The other devices do not need to surrender their keys or participate merely to make the identity state recoverable.

This **does not** mean one device may unilaterally perform every governance act.

Recovery/continuity and governance authorization remain separate.

## Authority epoch

An epoch is the bounded period during which one defined Same-and-Equal device set is recognized as current.

Conceptually:

~~~text
Epoch E1
  HOA identity statement
  Same-and-Equal set = {A, B, C}
  device credentials = {KA1, KB1, KC1}
  operator = O1
  accepted history head = H1

Epoch E2
  predecessor = E1
  Same-and-Equal set = {A, C, D}
  device credentials = {KA2, KC2, KD2}
  operator = O2 or O1
  accepted history head = H2
~~~

## Trust change creates a new ceremony

When any device owner is no longer trusted for the current authority class, or otherwise leaves the current Same-and-Equal set, the preferred operation is:

~~~text
current epoch
    ↓
trust/membership change
    ↓
new key-signing ceremony
    ↓
new epoch
    ↓
new keys/credentials for the new current N-device set
~~~

The old device is not required to surrender, erase, or destroy historical material.

It simply does not possess credentials for the new epoch.

## No retroactive invalidation

Old epochs remain valid evidence of what the Civic Infrastructure recognized at that time.

A device from an old epoch may still prove:

- that it belonged to that earlier epoch;
- what issuance/history it held;
- what it witnessed or attested while current;
- what operator/participant state existed then.

It may not be treated as a current authority device merely because it was trusted previously.

## Current authority is epoch-bound

Every authority-bearing act must eventually identify the epoch under which it was made.

Examples:

- participant issuance;
- operator election/selection;
- vote;
- peer confirmation/challenge;
- signing-node authorization;
- witness/attestation acceptance;
- recovery/continuity statement.

A verifier must distinguish:

~~~text
valid historical act under E1
        !=
current act requiring E2
~~~

## Recovery does not equal governance

Any one current device may be sufficient to reconstruct or recover the HOA Civic Identity state.

But changing current authority still follows the source-derived governance rule.

For example:

~~~text
one current device
    → recover identity/history

required Same-and-Equal electorate + prescribed vote
    → elect/select operator
    → authorize new signing node
    → create next governance act
~~~

This preserves the 1-of-N resilience of the gate-lock analogy without turning every device into a unilateral government.

## What is reconstructed

The reconstructed HOA Civic Identity should be understood as authoritative state, not necessarily one recoverable permanent private key.

It includes at least:

- HOA/root identity;
- authority epoch identity;
- governing-source/profile identity;
- current Same-and-Equal class/set statement;
- accepted history head/lineage;
- current operator designation;
- current Civic Signing Node identity;
- verification material needed to interpret the epoch.

The exact representation is not yet frozen.

## Key material

The architecture requires new epoch-specific key material at each ceremony.

It deliberately does **not** yet decide whether the cryptographic mechanism is:

- independent device signing keys plus replicated authority state;
- one shared recovery secret independently wrapped to each device;
- another 1-of-N construction;
- a hybrid.

The mechanism must satisfy the epoch rule: credentials from an old epoch cannot establish current authority in a later epoch.

## Why not permanent individual revocation

A permanently growing revocation list would make current authority depend on accumulating exceptions.

The epoch model instead states positively:

> These are the devices/participants recognized for the current epoch.

When the set changes, publish a new complete current set.

This matches the wider Civic Issuance Record principle: complete current snapshots and preserved historical lineage rather than destructive rewriting.

## Ceremony triggers

A new ceremony may be required when the current trusted/equal device set materially changes, including:

- participant becomes untrusted;
- participant ceases to qualify for the relevant Same-and-Equal class;
- participant leaves participation;
- device is lost or compromised;
- new participant enters the current class where the profile requires re-epoching;
- operator/node transition requires a new authority epoch;
- governing-source/profile change requires a new authority set.

The exact mandatory trigger policy remains profile-specific and is not frozen here.

## Ceremony authority

The ceremony itself must be authorized by the applicable source-derived governance profile and current Same-and-Equal electorate.

One operator cannot unilaterally redefine the trusted participant set merely by generating new keys.

The ceremony records the result of the accepted civic/governance process.

## Relationship to the operator-owned signing node

The HOA-local Civic Signing Node operates inside the current authority epoch.

It is not the permanent HOA Civic Identity.

The current epoch recognizes which signing node/operator is authoritative.

If the signing node is lost or the operator changes, the Same-and-Equal device set can reconstruct the HOA Civic Identity state and, through the applicable governance rule, authorize a replacement node.

## Relationship to participant ESP32-S3 devices

Participant devices are therefore more than passive credential holders.

They become distributed continuity witnesses for the HOA Civic Identity.

Each current device should eventually retain enough epoch-bound state to support:

- identity reconstruction/recovery;
- verification of current/past authority lineage;
- participation in source-derived votes where applicable;
- later witness/attestation provenance;
- detection of divergent/counterfeit authority histories.

## Divergence

If old and new devices present conflicting authority histories, the conflict is diagnostic.

The system must not silently choose whichever device responds first.

Epoch identity, source-derived governance records, Same-and-Equal electorate evidence, and peer scrubbing provide the basis for determining which lineage is recognized as current.

The exact conflict-resolution algorithm remains future work.

## Design consequence

The durable HOA Civic Identity is best modeled as:

~~~text
HOA identity
  + ordered authority epochs
  + source-bound governance transitions
  + distributed current-device state
  + preserved historical evidence
~~~

not as:

~~~text
one permanent operator private key
~~~

## Next design boundary

Before implementation, the project should compare at least two concrete cryptographic realizations of this accepted epoch model:

1. independent device keys + replicated authority-state recovery;
2. independent device keys + 1-of-N wrapped recovery material;

and evaluate both against ESP32-S3 capabilities, ceremony simplicity, operator replacement, compromised-device behavior, and cost.

No implementation code is authorized by this document.
