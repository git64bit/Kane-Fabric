# Civic Signing Node Future Service Attachment Boundaries

## Status

Architecture boundary. Documentation only.

This document records future service classes that may attach to an HOA-local Civic Signing Node without becoming part of the baseline authority core.

The baseline signing-node implementation remains intentionally smaller than the fully developed future node.

## Baseline principle

The first implementation should provide only the authority functions already accepted for the HOA-local Civic Signing Node.

Future services may improve transport, endpoint authentication, communication, publication, storage, and evidentiary durability.

They must not silently become the source of HOA Civic authority.

Conceptually:

~~~text
                    HOA-local Civic Signing Node
                              |
          +-------------------+-------------------+
          |                   |                   |
     future CA/TLS       future mail         future IPFS
       attachment         attachment          attachment
          |                   |                   |
     transport/endpoint    communication       content-addressed
       authentication        transport            storage

          none of these independently defines Civic authority
~~~

## Baseline signing-node core

The baseline authority core remains:

1. one autonomous HOA-local Civic authority domain;
2. operator-owned and operator-funded Civic Signing Node;
3. governing-source binding to Illinois statute and valid condominium instruments;
4. authority-epoch awareness;
5. independent epoch-specific keys on current Same-and-Equal participant devices (ESP32-S3 is the current reference implementation, not the required platform);
6. replicated authenticated HOA authority state;
7. Civic Issuance Records;
8. operator and signing-node provenance;
9. source-derived governance-event records;
10. Same-and-Equal electorate/comparison inputs;
11. authority proofs/signatures and verification;
12. sequence, lineage, correction, supersession, and historical preservation;
13. continuity/recovery from current participant-device state.

No future attached service is required to define this baseline authority model.

## Attachment rule

A future service may become a supported attachment when it provides a useful capability without changing the accepted authority hierarchy.

Every attachment must preserve:

~~~text
service availability != Civic authority
service identity     != participant identity
service credential   != civic standing
service custody      != ownership of HOA Civic Identity
~~~

If loss of an attached service would destroy the HOA Civic Identity, prevent reconstruction of the current authority epoch, or make another HOA/root authoritative by default, the proposed attachment violates the baseline architecture.

## User-owned public verification material on participant edges

Future CA, mail, and IPFS services are not prerequisites for storing public key material on a participant-owned edge.

A participant edge may already hold and serve user-owned, openly readable public verification material such as:

- CA certificates and CA/public verification keys;
- OpenPGP public keys;
- SSH public keys;
- participant-device and authority-epoch public verification keys;
- other explicitly public user-owned artifacts.

These artifacts are data held by the participant. Their presence does not turn the edge into the CA, mail provider, or central authority, and it does not require secure-element or eFuse custody.

## Kane County CA node

A future Kane County CA node may provide TLS/SSL certificates for Civic Infrastructure endpoints.

The name describes the Kane Civic Infrastructure deployment role. It does not imply that the node is an official Kane County governmental certificate authority unless separately established by an actual governmental authority.

Its function is endpoint/transport authentication.

It may eventually provide certificates for:

- HOA-local Civic Signing Node endpoints;
- participant-facing Civic web endpoints;
- local or county Civic service endpoints;
- other approved Kane Fabric services.

Its authority boundary is:

~~~text
CA certificate
    proves/attests endpoint-key binding under the CA policy

CA certificate
    does NOT by itself prove:
        HOA Civic authority
        operator election
        Same-and-Equal standing
        participant affordance
        truth of a Civic record
~~~

The current authority epoch and its governing records remain the source of local Civic authority.

A TLS certificate may authenticate a channel to the current signing node, but it must not replace the signing node's Civic authority proof.

## Kane-local email service

A future mail service may support Civic correspondence and evidence workflows.

The intended boundary presently includes outbound communication restricted to approved `kane-il.us` addresses.

The exact mail topology, domains/subdomains, account model, DANE/PGP policy, retention policy, and delivery-evidence model are future work.

Its authority boundary is:

~~~text
email delivery
    = communication/evidence transport

email address
    != civic identity

successful delivery
    != civic standing

message from an approved domain
    != operator authority
~~~

Email may later carry:

- SASE-related notices or confirmations;
- election/meeting notices;
- Civic Issuance Record notifications;
- operator-transition notices;
- peer-scrubbing observations;
- links/references to immutable artifacts;
- other source-governed communications.

But participation, operator authority, Same-and-Equal standing, and authority-epoch state remain established by their own Civic records and governing procedures.

## IPFS node

A future IPFS node may provide content-addressed storage and distribution for Civic artifacts.

Potential future artifacts include:

- statute/bylaw source snapshots where lawful and appropriate;
- governing-profile documents;
- Epoch Manifests;
- Civic Issuance Records or public projections;
- meeting notices/minutes where appropriate;
- peer-scrubbing evidence;
- ESP32-S3 witness/attestation records;
- hashes or immutable copies of supporting documents;
- other public or selectively disclosed Civic artifacts.

The IPFS authority boundary is:

~~~text
CID
    = identity of exact content bytes

CID
    != truth of those bytes
    != legality of publication
    != civic standing
    != operator authority
    != currentness
~~~

Content-addressed storage therefore strengthens immutability/provenance without becoming an adjudicator.

The signing/attestation provenance surrounding an IPFS object determines what the object means in Civic Infrastructure.

A participant-owned edge assisting with **pinning user-owned CIDs** is a future wish-list capability. The mechanism is deliberately undefined. No current design assumes that an ESP32-S3 runs a full IPFS node, and no current authority or storage contract depends on edge-side pinning. Future work may define a bounded pin request/reference/cache role if it can remain platform-neutral, user-controlled, and optional.


## RAG/LLM Diagnostics relationship

RAG/LLM Diagnostics may later consume source/evidence objects, derived text, chunk manifests, embeddings, and Civic history.

It is not a Signing Node authority attachment in the same sense as CA/mail/IPFS. It is a replaceable analytical consumer of the same content-addressed evidence substrate.

No model vendor, embedding service, or RAG runtime becomes a prerequisite for interpreting an Epoch Manifest or reconstructing HOA Civic authority.

See `docs/CIVIC_RAG_LLM_DIAGNOSTICS_BOUNDARY.md`.

## Failure isolation

Each optional attachment must fail independently.

Examples:

~~~text
CA unavailable
    -> existing Civic authority/history remains interpretable

mail unavailable
    -> existing Civic authority/history remains interpretable

IPFS unavailable
    -> locally retained authority/history remains interpretable

signing node lost
    -> current participant-device state supports authority reconstruction
~~~

Future implementations may temporarily lose a convenience or transport path when an attachment is unavailable, but they must not lose the underlying HOA Civic Identity.

## Cross-HOA autonomy

Future services may be shared at the Kane Fabric level only when sharing does not merge HOA authority roots.

For example:

- several HOAs may trust certificates from the same Kane County CA;
- several HOAs may use the same Kane-local mail infrastructure;
- several HOAs may publish to or retrieve from the same IPFS network.

None of those shared services may make one HOA authoritative over another.

~~~text
shared transport or storage
    != shared civic root
~~~

Each HOA retains its own authority epochs, Same-and-Equal participant set, operator history, and Civic Signing Node identity.

## No mandatory future dependency

The existence of these planned services does not mean the baseline implementation must wait for them.

The first signing-node implementation should not require:

- Kane County CA availability;
- Kane-local mail availability;
- IPFS availability.

Those services can be developed and attached later through explicit interfaces.

## Future integration test

Before any future service becomes a baseline dependency, answer:

1. Does this service merely transport/store/authenticate an endpoint, or does it silently acquire Civic authority?
2. Can the HOA reconstruct its Civic Identity if the service is unavailable?
3. Can the service be replaced without changing the HOA Civic root?
4. Does the service preserve per-HOA autonomy?
5. Does a credential from the service remain distinct from participant/operator standing?
6. Is any newly introduced central dependency justified and explicitly accepted?

If these questions cannot be answered consistently with the accepted authority model, the service remains optional or must be redesigned.

## Baseline decision

The initial implementation proceeds with the accepted Civic Signing Node baseline.

The Kane County CA node, restricted Kane-local email service, and IPFS node are documented future attachments, not blockers for the baseline implementation.

No code or deployment change is authorized by this document.
