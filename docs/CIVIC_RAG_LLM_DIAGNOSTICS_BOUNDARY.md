# Civic RAG / LLM Diagnostics Boundary

## Status

Accepted architecture boundary. Documentation only.

This document defines how a future RAG-based LLM participates in HOA Diagnostics without becoming a governing, statutory, or cryptographic authority.

## Purpose

HOA Diagnostics is the human-facing diagnostic layer of Civic Infrastructure.

It is intended to help participants inspect and understand, among other things:

- failures of voluntary statutory compliance;
- gaps between statutory guarantees and practical enforcement;
- failures or contradictions in Board, Property Manager, professional, vendor, or participant conduct;
- participant nonparticipation, indifference, or inconsistent action where relevant to the observed civic process;
- differences between published governing sources and actual operational behavior;
- provenance of records, notices, decisions, payments, communications, and other evidence.

A RAG-based LLM may assist with analysis and explanation of these materials, including statutory and governing-source responsibilities of relevant HOA actors such as directors, officers, Property Managers, law firms, contractors, and unit owners where the governing source assigns duties or rights.

The LLM is an analytical interface over evidence. It is not the source of those duties.

## Authority separation

~~~text
Illinois statute + valid governing instruments
    = governing source

Civic authority records
    = attributable issuance/governance/provenance

observed evidence
    = factual/diagnostic input

RAG retrieval + LLM output
    = derived diagnostic/advisory material
~~~

An LLM statement does not become true, legally controlling, or Civic authority merely because it is stored, signed, replicated, or repeatedly retrieved.

## Common object substrate

RAG uses the same content-addressed object substrate as the rest of Civic Infrastructure.

Original source objects retain exact-byte identity:

~~~text
sha256
byte_length
media_type
source/provenance metadata
~~~

Sources may be plain text or binary.

Examples include:

- statutes and regulations;
- declarations/bylaws/rules;
- court filings and orders;
- letters and email;
- meeting notices/minutes;
- ledgers and invoices;
- PDFs and scans;
- photographs;
- exported messages;
- public keys/certificates;
- participant witness records;
- Diagnostics reports.

## Derived text

When text is extracted from a binary source, the extraction is a new derived object.

It records at minimum:

~~~text
source_object_sha256
extractor_id
extractor_version
extracted_text_sha256
extraction_time_ms
diagnostics / warnings
~~~

The extracted text never replaces the source bytes.

## RAG corpus manifest

A RAG corpus snapshot is itself a deterministic Civic record containing:

~~~text
format
version
corpus_id
source_object_set
extracted_text_set
chunking_profile
chunk_set
embedding_profile
embedding_object_set
created_time_ms
predecessor_corpus_sha256
~~~

The corpus snapshot can therefore be reproduced or challenged.

### Chunks

Each chunk identifies:

- source object hash;
- extracted-text hash;
- chunk hash;
- exact byte/character span in the extracted representation;
- chunker identity/version;
- semantic metadata used for retrieval.

### Embeddings

Embeddings are derived binary data.

Their record identifies:

- embedding model identifier/version;
- input chunk hash;
- vector dimension;
- scalar representation;
- exact binary vector-object SHA-256.

Embeddings do not become authority. They may be discarded and regenerated.

No authority record depends on one proprietary embedding provider remaining available.

## LLM advisory record

A retained LLM output is stored as a Diagnostics/advisory record, not an authority record.

It records at minimum:

~~~text
query/request
model identifier
model/runtime version where known
RAG corpus identity
retrieval procedure/profile
retrieved chunk identities
source object identities
response text
created_time_ms
diagnostic classifications
limitations/warnings
~~~

The response should cite the source records/chunks it relied upon.

If an answer concerns a statutory requirement, duty, right, deadline, or governing procedure, the advisory output should identify the underlying governing source rather than citing another LLM answer as authority.

## Diagnostics-first failure model

The RAG/LLM system is expected to fail in observable ways.

Examples:

- retrieval misses a controlling source;
- extraction corrupts a table;
- a model hallucinates a duty;
- two models reach inconsistent interpretations;
- a statute changes;
- a source document is later shown to be incomplete;
- a participant supplies contradictory evidence;
- a diagnostic classification is challenged.

These are valuable Diagnostics signals.

The system should preserve enough provenance to reproduce the failure and compare the answer against the source corpus.

The default response is not to hide the failure behind a proprietary guardrail, central moderation service, or inaccessible model state. The project first records what failed, why it can be detected, and what bounded change would improve functionality.

## Privacy and publication boundary

Diagnostics-first does not mean publish every byte indiscriminately.

Public, restricted, and private classifications remain separate from authority.

A diagnostic record may publicly expose:

- hashes;
- public source references;
- non-sensitive failure classes;
- reproducible software/version information;
- redacted excerpts where appropriate.

Private source content remains governed by its applicable access policy.

The ability to diagnose a failure does not itself authorize disclosure of confidential or legally protected material.

## LLM independence

The Civic Infrastructure must not require one hosted model vendor or one proprietary RAG platform.

The durable assets are:

- source objects;
- content identities;
- corpus manifests;
- extraction/chunk provenance;
- advisory records;
- citations.

A different local or hosted model may consume the same corpus later.

Changing the model does not change historical Civic authority.

## Relationship to the participant edge

The participant-owned edge may retain:

- Civic authority records;
- public verification keys;
- witness records;
- selected source/evidence objects;
- selected RAG corpus objects;
- Diagnostics/advisory records appropriate to that participant;
- future references to user-owned IPFS CIDs.

The edge is not required to execute the LLM.

The LLM runtime is a replaceable computation service over user/Civic-owned data and published contracts. Its physical placement does not become Civic identity.

## Decision

RAG/LLM capability is accepted as a future diagnostics/education layer using the same deterministic, content-addressed evidence substrate.

It remains:

~~~text
source-grounded
provenance-preserving
replaceable
non-authoritative
diagnostics-first
platform-neutral
~~~

No RAG runtime, embedding model, model vendor, or IPFS service is a prerequisite for the baseline Signing Node or Epoch Manifest.
