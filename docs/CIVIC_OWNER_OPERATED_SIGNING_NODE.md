# Owner-Operated Civic Signing Node

## Status

Architecture contract. Documentation only.

This document defines the physical/local authority boundary for HOA participation in Kane Fabric.

## Core rule

Every participating HOA must have its own Civic Signing Node before that HOA can use Civic Infrastructure for operator selection/election, voting, participant issuance, peer scrubbing, or other local authoritative civic acts.

The node is owned and operated locally by the HOA's Civic operator.

The owner-operator assumes the node's costs.

~~~text
HOA A
  └─ Civic Signing Node A

HOA B
  └─ Civic Signing Node B

Node A != Node B
authority root A != authority root B
local history A != local history B
~~~

This physical/logical separation is an autonomy boundary.

## Why one node per HOA

A county-wide shared civic signer would create a common administrative dependency across associations.

That would make one operator, service, outage, compromise, policy dispute, or capture event capable of affecting multiple otherwise independent HOAs.

Per-HOA signing nodes instead preserve:

- local authority;
- local operator accountability;
- local issuance history;
- local election/vote provenance;
- local Same-and-Equal comparisons;
- local peer scrutiny;
- local costs and operational responsibility;
- independent failure and recovery domains.

## Owner-operated means locally borne responsibility

The Civic Infrastructure is owner-operated.

The operator who owns/operates the local Civic Signing Node assumes its expenses, including the hardware, connectivity, storage, maintenance, replacement, and other ordinary operating costs required by the adopted profile.

Kane Fabric does not create a central subscription dependency merely to preserve local civic operation.

The exact cost-sharing or reimbursement arrangements inside one HOA remain an HOA/profile question; this document only fixes that the infrastructure is locally owned/operated rather than centrally rented as mandatory tenancy.

## Node is required before Civic governance

The local signing node must exist before participants rely on Civic Infrastructure to:

- initiate/renew signed participation;
- select or elect a Civic operator;
- record votes;
- establish operator provenance;
- issue Civic Issuance Records;
- publish peer confirmations/challenges;
- scrub operator acts;
- attest source-bound HOA procedures;
- later create or anchor ESP32-S3 witness/attestation records.

This ordering prevents governance from depending on a signing authority that is only created after the governance act it is supposed to authenticate.

## Node does more than produce a cryptographic signature

The node is the local authority appliance for a bounded HOA Civic profile.

Its responsibilities eventually include at least:

- preserving the HOA-local authority/root identity;
- binding each act to the applicable Illinois statute and condominium instruments;
- applying the accepted Affordance Authority Contract;
- issuing participant/appliance records;
- recording operator provenance;
- recording governance events such as operator election/selection and votes;
- preserving sequence, lineage, correction, and supersession;
- supporting Same-and-Equal electorate/comparison policy;
- publishing or retaining evidence sufficient for peer scrubbing;
- supporting ESP32-S3 attestation/witness provenance;
- producing authority proofs/signatures for those records.

Signing is one operation of the node, not its entire purpose.

## Legal/source authority versus Civic authority

The node does not become the source of Illinois law.

For HOA Diagnostics:

~~~text
Illinois statute + valid condominium instruments
        = substantive governing authority

local Civic Signing Node
        = provenance + local issuance + observation + attestation
          + source binding + governance-record authority
~~~

The node's credibility comes from faithfully referencing and applying the authoritative source chain, preserving what local participants actually issued/observed, and making deviations inspectable.

It must never represent a Civic-added mechanism as though Illinois statute itself created that mechanism.

## Distinct from Firmware Release Authority

The local Civic Signing Node is not the common Firmware Release Authority.

### Firmware Release Authority

Authorizes software releases intended for Civic appliances.

### HOA-local Civic Signing Node

Authorizes and preserves HOA-local civic records and governance provenance.

Therefore:

~~~text
common firmware authenticity
    != HOA-local civic authority
~~~

One common firmware release can run on many HOA-local signing nodes without merging their civic authority.

## HOA root identity

Each node belongs to one HOA-local Civic root/profile.

The HOA root must not be derived merely from:

- IP address;
- MAC address;
- hostname;
- one human operator's name;
- a central Kane account.

The local-root continuity model is authority-epoch based. The HOA Civic Identity is reconstructed from authenticated replicated authority state held by current Same-and-Equal participant devices. Each device uses independent epoch-specific key material; no permanent HOA master/recovery private key is required.

The important invariant is that one HOA root cannot silently become another HOA root.

## Operator ownership and operator replacement

The current operator owns/operates the node, but operator office and HOA-local root identity must remain distinguishable.

Otherwise replacing an operator would accidentally replace the HOA's Civic identity.

Operator transition is constrained by the authority-epoch model: when the recognized authority/device set changes, a source-governed key-signing ceremony creates the new current epoch and independent current-device keys. Exact cryptographic algorithm, storage, and custody mechanics remain implementation work.

An operator change must preserve the HOA authority lineage and be authorized by the applicable source-derived Same-and-Equal governance procedure.

The current operator-owned node may be replaced rather than treated as the HOA identity. The accepted participant-device epoch state provides continuity; the transition record and next epoch identify the newly authorized operator/node. Exact device-custody and hardware-replacement mechanics remain implementation work.

## Bootstrap requirement

A participating HOA needs an initial owner-operator and local signing node before Civic-governed operator selection/election can occur.

That initial bootstrap does not permanently privilege the bootstrap operator.

Once active participation and the source-derived governance profile exist, later operator selection, replacement, votes, and scrutiny must occur through the local Civic process.

The exact bootstrap acceptance/transition record remains to be designed.

## Same and Equal is local to the HOA authority domain

For HOA-local governance, the relevant Same-and-Equal electorate is evaluated inside that HOA's domain and applicable source-derived profile.

Participants in another HOA do not become part of the electorate merely because they hold analogous roles elsewhere.

This preserves association autonomy.

## Peer scrutiny stays local but inspectable

Participant scrubbing of operator conduct occurs against the local node's records, applicable statute, association instruments, participant evidence, and witness/attestation records.

A different HOA may use the same software and same statutory model but does not acquire authority over this HOA's operator.

## Failure isolation

Loss or compromise of one HOA-local signing node must not invalidate another HOA's civic history or operator authority.

Likewise, one HOA's internal governance dispute must not require shutting down or reissuing another HOA's node.

Cross-HOA interoperability may exist later through published contracts, but it must not collapse local authority roots.

## Expenses and anti-capture

Local ownership has a cost, and that cost is intentional.

The owner-operator's assumption of expenses removes a central provider's ability to threaten participation by withdrawing a mandatory hosted signing service.

This is part of the anti-capture model:

~~~text
local cost
    buys
local custody + local continuity + local autonomy
~~~

The infrastructure should therefore remain small enough, reproducible enough, and documented enough that a qualified participant can assume the operator role without dependence on a proprietary central platform.

## Relationship to future ESP32-S3 roles

Participant ESP32-S3 appliances and the HOA-local Civic Signing Node have different roles.

The local signing node establishes/records civic authority and provenance.

Participant ESP32-S3 appliances later carry their issued context and may assemble witness/attestation records.

Those witness records can then be anchored/accepted within the HOA-local authority domain without making the operator the author of the witnessed event.

## Remaining implementation interrogation

The civic continuity design is closed sufficiently for implementation planning.

Implementation work must still determine:

1. minimum reproducible hardware/software boundary for one HOA-local node;
2. cryptographic algorithm and key representation;
3. operator-node key custody and rotation mechanics;
4. local record/evidence storage and backup;
5. operator-election/vote record encoding;
6. peer confirmation/challenge record encoding;
7. exact participant ESP32-S3 storage and verification behavior;
8. recovery procedure after signing-node loss;
9. cost/reproducibility requirements appropriate for owner-operators.

These choices must preserve the accepted architecture in `docs/CIVIC_AUTHORITY_CONTINUITY_DECISION.md`.


## Authority epochs

HOA continuity is further defined in `docs/CIVIC_AUTHORITY_EPOCH_CEREMONY.md`.

A key-signing ceremony creates the current epoch and `N` Same-and-Equal participant-device credentials. Any one current device may be sufficient to reconstruct/recover the HOA Civic Identity state, while governance changes still require the prescribed Same-and-Equal voting/selection procedure.

When a current device owner becomes untrusted or leaves the applicable class, a new ceremony creates a new epoch and new current keys. Old epochs remain historical evidence; old credentials do not establish current authority.


## Future service attachments

The baseline Civic Signing Node intentionally excludes several planned services that can attach later:

- Kane County CA / TLS certificate service;
- Kane-local restricted email service;
- IPFS content-addressed storage/distribution.

These services may strengthen transport, communication, endpoint authentication, and evidence durability, but none becomes the source of HOA Civic authority.

See `docs/CIVIC_SIGNING_NODE_FUTURE_SERVICE_BOUNDARIES.md`.
