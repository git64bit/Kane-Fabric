# Civic History Head and Predecessor Semantics

## Status

Accepted architecture contract for Civic append-only history linkage.

This document defines only the minimum semantics needed to bind Epoch Manifest history heads to append-only Civic CBOR Sequence records. It does not define the substantive schema of accepted, witness, diagnostics, or knowledge records.

It is subordinate to:

- `docs/CIVIC_EPOCH_MANIFEST_FORMAT.md`;
- `docs/CIVIC_CRYPTOGRAPHIC_BASELINE.md`;
- `docs/CIVIC_INFRASTRUCTURE_PRINCIPLES.md`;
- `docs/CURRENT_STATE.json`.

## Purpose

The physical CBOR Sequence is append-only storage.

The logical Civic history is a hash-linked sequence of independently identifiable records.

These are related but not identical concepts:

~~~text
physical storage
    exact record bytes || exact record bytes || exact record bytes

logical history
    H1 <- H2 <- H3

Epoch Manifest
    history head = H3
~~~

A Civic history head identifies the final accepted record in one logical stream. It does not identify the pathname, filesystem, storage device, CBOR Sequence file, or hash of the entire accumulated file.

## Record identity

For every Civic history record:

~~~text
record_sha256 = SHA-256(exact deterministic-CBOR sequence-item bytes)
~~~

The exact bytes used as one item in the CBOR Sequence are the record identity bytes.

Re-encoding an equivalent data structure is not a substitute for preserving those exact bytes.

If a record is carried as a signed Civic envelope, the record identity is the SHA-256 of the exact signed sequence item, not merely the unsigned application payload.

## Independent streams

Epoch Manifest v1 exposes four logical history streams:

~~~text
accepted
witness
diagnostics
knowledge
~~~

They correspond to:

~~~text
accepted     -> accepted_history_head_sha256
witness      -> witness_head_sha256
diagnostics  -> diagnostics_head_sha256
knowledge    -> knowledge_head_sha256
~~~

The streams are independent. A predecessor link never crosses from one stream into another.

## Required linkage metadata

Every record that participates in one of these linked history streams must include this linkage information inside its authenticated record content:

~~~text
history_link = {
  "stream": text,
  "predecessor_record_sha256": bytes(32) / null
}
~~~

The exact `stream` value is one of:

~~~text
accepted
witness
diagnostics
knowledge
~~~

The linkage metadata is part of the record's authenticated content. It must not exist only in an unprotected COSE header, filesystem metadata, database column, filename, transport wrapper, or other unsigned side channel.

This document freezes the linkage field names and meanings, but does not otherwise freeze the surrounding record schema.

## Genesis record

The first record in a logical stream has:

~~~text
predecessor_record_sha256 = null
~~~

Its own record identity is still:

~~~text
SHA-256(exact deterministic-CBOR sequence-item bytes)
~~~

A stream has exactly one genesis record in its accepted linear history.

## Successor record

For every later record:

~~~text
predecessor_record_sha256 =
    SHA-256(exact sequence-item bytes of the immediately preceding record)
~~~

Therefore:

~~~text
record 1
  predecessor_record_sha256 = null
  identity = H1

record 2
  predecessor_record_sha256 = H1
  identity = H2

record 3
  predecessor_record_sha256 = H2
  identity = H3
~~~

Appending record 3 does not alter record 1 or record 2.

## History-head meaning

A non-null history head is exactly the SHA-256 identity of the final record in that logical stream.

For example:

~~~text
accepted_history_head_sha256 = H3
~~~

means that the current accepted-history head is the record whose exact sequence-item bytes hash to `H3`.

The head is not:

- a hash of the complete CBOR Sequence file;
- a Merkle root;
- a hash of concatenated record hashes;
- a filesystem object identifier;
- a CID;
- a database revision;
- a Signing Node identity.

Those mechanisms may exist separately, but they do not redefine Civic history-head semantics.

## Empty-stream meaning

Epoch Manifest v1 already requires:

~~~text
accepted_history_head_sha256 = bytes(32)
~~~

Therefore a valid Epoch Manifest has at least one accepted-history record.

The other v1 stream heads are nullable:

~~~text
witness_head_sha256
diagnostics_head_sha256
knowledge_head_sha256
~~~

For those streams:

~~~text
null = no current record exists in that stream
bytes(32) = identity of the current final record
~~~

An empty stream is represented by no CBOR Sequence items and a null head.

## Sequence-order verification

For a complete stored stream, physical CBOR Sequence order and logical predecessor order must agree.

A verifier walks records in storage order and checks:

1. each item is valid deterministic Civic CBOR;
2. each item's SHA-256 identity is computed from its exact item bytes;
3. each record declares the expected stream;
4. the first record declares a null predecessor;
5. every later record names the exact SHA-256 identity of the immediately preceding item;
6. the final record identity equals the expected Epoch Manifest history head.

Any mismatch fails verification.

The verifier does not silently reorder records, repair links, skip malformed items, or substitute another branch.

## Append operation

Given a verified stream with current head `Hn`, appending one successor means:

~~~text
new_record.history_link.stream = existing stream
new_record.history_link.predecessor_record_sha256 = Hn

Hn+1 = SHA-256(exact new record sequence-item bytes)

new head = Hn+1
~~~

The append operation preserves all prior sequence bytes exactly.

For a nullable stream with no records, the first append uses a null predecessor and establishes the first non-null head.

## Competing successors and forks

Two different records may independently name the same predecessor hash. Their existence is evidence of a fork or competing successor.

The accepted logical stream represented by one Epoch Manifest remains linear and has exactly one current head.

A verifier must not merge competing branches or choose between them heuristically.

A competing branch may be preserved as evidence or Diagnostics input without becoming the accepted history represented by the manifest head.

## Storage independence

The same logical stream may be copied between:

- participant devices;
- the Civic Signing Node;
- removable media;
- ordinary filesystems;
- content-addressed stores;
- future IPFS distribution.

Moving or duplicating the records does not alter record identities or the history head.

A CBOR Sequence file is therefore a storage projection of the logical history, not the root of Civic identity.

## Partial history

A suffix or isolated record can still be identified by its own SHA-256 and can expose the predecessor it expects.

However, possession of a suffix alone does not prove the complete chain back to genesis.

Full stream verification requires either:

- all predecessor records back to the genesis record; or
- a separately authenticated earlier checkpoint whose record identity is already trusted by the verifier.

Checkpoint mechanics are not defined by this document.

## Signature boundary

Long-term Civic history records are individually authenticated according to their record format.

The history linkage must be covered by that authentication.

The predecessor hash is not a substitute for signature verification, and signature verification is not a substitute for predecessor verification.

They answer different questions:

~~~text
signature/authentication
    -> who authorized or attested to these exact record contents

predecessor link
    -> which prior record this record claims to follow

history head
    -> which final record the Epoch Manifest currently names
~~~

## Failure is Diagnostics

The following are explicit verification failures:

- malformed CBOR Sequence item;
- non-deterministic Civic CBOR item;
- unsupported or missing history-link metadata;
- wrong stream identifier;
- non-null predecessor on a genesis record;
- null predecessor after genesis;
- predecessor hash mismatch;
- physical record order inconsistent with predecessor order;
- final record hash inconsistent with the expected manifest head;
- branch ambiguity presented as one linear accepted stream.

These failures are preserved as Diagnostics evidence rather than silently repaired.

## Decision

Civic history v1 now uses this minimal model:

~~~text
deterministic signed record bytes
    -> per-record SHA-256 identity
    -> authenticated predecessor link
    -> append-only CBOR Sequence storage
    -> final record SHA-256 as stream head
    -> Epoch Manifest history-head reference
~~~

This contract is sufficient to implement history-link verification without freezing the substantive event schemas that will use it.
