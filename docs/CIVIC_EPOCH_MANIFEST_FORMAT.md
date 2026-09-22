# Civic Epoch Manifest Canonical Format

## Status

Accepted implementation architecture decision. Documentation only; no production Civic key is created by this decision.

This document freezes the canonical v1 representation of the HOA Civic Authority Epoch Manifest and its signed envelope.

It is subordinate to:

- `docs/CIVIC_INFRASTRUCTURE_PRINCIPLES.md`;
- `docs/CIVIC_INFRASTRUCTURE_ANTI_CAPTURE.md`;
- `docs/CIVIC_AUTHORITY_CONTINUITY_DECISION.md`;
- `docs/CIVIC_AUTHORITY_EPOCH_CEREMONY.md`;
- `docs/CIVIC_CRYPTOGRAPHIC_BASELINE.md`.

## Design objective

The Epoch Manifest is a durable, self-describing authority snapshot designed for decades of participant witnessing.

The representation is deliberately not minimized for byte-count reasons. The current ESP32-S3 is a reference platform with sufficient capability for the intended structured authority records, and future conforming platforms may have substantially more storage.

The design therefore optimizes for:

1. deterministic verification;
2. long-lived interoperability;
3. mixed text/binary data;
4. append-only historical preservation;
5. human diagnostic projection;
6. simple implementation on constrained and general-purpose platforms;
7. separation of source evidence, Civic authority, Diagnostics, and derived RAG/LLM material.

## Selected canonical representation

The canonical Civic record representation is **deterministically encoded CBOR** based on RFC 8949 core deterministic encoding requirements.

The signed container is **COSE_Sign1** using the already accepted Civic cryptographic profile:

~~~text
payload encoding      deterministic CBOR
signature container   COSE_Sign1
COSE algorithm        ESP256 / -9
curve                 P-256
digest                SHA-256
signature bytes       64-byte R || S
key identifier        32-byte SHA-256 of canonical 65-byte SEC1 public key
~~~

The Epoch Manifest payload is embedded in the COSE_Sign1 object rather than detached. A stored signed manifest is therefore self-contained.

The unprotected COSE header map is empty in v1.

The protected header contains:

~~~text
alg           -9
kid           32-byte Civic key identifier
content type  application/kane-civic-epoch+cbor
~~~

External AAD is the zero-length byte string in v1.

## Deterministic CBOR profile

Kane Civic deterministic CBOR v1 applies these rules:

- RFC 8949 core deterministic encoding;
- preferred shortest integer and length encodings;
- definite-length strings, arrays, and maps only;
- duplicate map keys are invalid;
- map keys are UTF-8 text strings only;
- signed text is valid UTF-8 and NFC-normalized before encoding;
- floating-point values are prohibited in v1 signed Civic records;
- numeric values are integers when numeric semantics are required;
- arbitrary binary is represented directly as CBOR byte strings, never base64 inside the canonical CBOR payload;
- null is used only where the schema explicitly permits it;
- unknown required fields are a version/schema error rather than silently ignored;
- arrays whose semantic meaning is a set have a schema-defined bytewise sort order;
- arrays whose semantic meaning is chronological history preserve defined sequence order.

This removes avoidable cross-language ambiguity while retaining native text and binary support.

## Manifest identity

The **Epoch Manifest identity** is:

~~~text
manifest_sha256 = SHA-256(exact canonical Epoch Manifest payload bytes)
~~~

The manifest does not contain its own digest.

The containing COSE_Sign1 signature authenticates the canonical payload and protected signature metadata.

This gives two independent useful identities:

~~~text
manifest_sha256
    -> exact authority-state payload identity

COSE signature
    -> attributable authorization/provenance for that payload
~~~

## Epoch Manifest v1 fields

The top-level payload is a CBOR map with these exact required fields:

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

### format

UTF-8 text:

~~~text
kane-civic-epoch-manifest
~~~

### version

Unsigned integer:

~~~text
1
~~~

### crypto_profile

UTF-8 text:

~~~text
kane-civic-ecdsa-p256-sha256-v1
~~~

### hoa_root_id

Exactly 32 bytes.

This is the stable opaque HOA Civic root identity established by the bootstrap/continuity process. The Epoch Manifest does not derive this identity from a physical device, address, hostname, operator, or key.

### epoch_sequence

Unsigned integer greater than or equal to 1.

The initial authority epoch is 1. Each accepted successor increments by exactly one.

### predecessor_manifest_sha256

For epoch 1: null.

For later epochs: exactly 32 bytes containing the SHA-256 identity of the predecessor canonical Epoch Manifest payload.

### effective_time_ms

Unsigned integer containing Unix time in milliseconds as asserted by the ceremony record.

This is an attributable recorded time, not an independent trusted-time proof.

### governing_profile

Map:

~~~text
{
  "profile_id": text,
  "profile_sha256": bytes(32),
  "source_set_sha256": bytes(32)
}
~~~

### governing_sources

Array of source descriptors.

Each descriptor is:

~~~text
{
  "source_id": text,
  "role": text,
  "sha256": bytes(32),
  "byte_length": uint,
  "media_type": text,
  "title": text / null,
  "source_uri": text / null
}
~~~

The array is sorted by UTF-8 byte ordering of `source_id`.

A URI is provenance/retrieval information. It is not content identity. The SHA-256 is the content identity used by the manifest.

### participants

Array of current Same-and-Equal participant descriptors.

Each descriptor is:

~~~text
{
  "participant_record_sha256": bytes(32),
  "participant_key_id": bytes(32),
  "participant_public_key": bytes(65),
  "standing_record_sha256": bytes(32),
  "issuance_record_sha256": bytes(32)
}
~~~

The array is sorted by bytewise ascending `participant_record_sha256`.

The participant record identity is not derived from device MAC address, serial number, network address, or physical platform.

### operator

Map:

~~~text
{
  "participant_record_sha256": bytes(32),
  "selection_record_sha256": bytes(32)
}
~~~

### signing_node

Map:

~~~text
{
  "key_id": bytes(32),
  "public_key": bytes(65),
  "authorization_record_sha256": bytes(32)
}
~~~

The Signing Node public identity is current-epoch authority material, not the permanent HOA Civic Identity.

### history

Map:

~~~text
{
  "accepted_history_head_sha256": bytes(32),
  "witness_head_sha256": bytes(32) / null,
  "diagnostics_head_sha256": bytes(32) / null,
  "knowledge_head_sha256": bytes(32) / null
}
~~~

These are content identities of the current accepted heads of their respective append-only record streams.

### ceremony

Map:

~~~text
{
  "ceremony_record_sha256": bytes(32),
  "governance_proof_sha256": [ * bytes(32) ]
}
~~~

The proof array is sorted bytewise ascending.

### object_index

Array of content descriptors required to interpret or reconstruct the epoch.

Each descriptor is:

~~~text
{
  "sha256": bytes(32),
  "byte_length": uint,
  "media_type": text,
  "semantic_role": text,
  "name": text / null,
  "cid": text / null,
  "inline": bytes / null
}
~~~

The array is sorted bytewise ascending by `sha256`.

`inline` may contain the exact object bytes. There is no protocol-level small-size assumption. An implementation may retain large objects separately in a content-addressed local store while keeping the descriptor in the manifest.

`cid` is optional and reserved for a future content-addressed distribution attachment such as IPFS. A CID does not replace the required SHA-256 field and does not become Civic authority.

## Text and binary evidence

Plain text is stored as UTF-8.

Binary evidence is stored as bytes.

The infrastructure does not force PDFs, images, email files, certificates, OpenPGP keys, SSH keys, archives, or other binary objects through a textual base64 representation merely to fit a JSON model.

Examples:

~~~text
text/plain
text/markdown
application/pdf
message/rfc822
application/pgp-keys
application/ssh-key
application/pkix-cert
image/png
image/jpeg
application/octet-stream
~~~

Media type describes interpretation. SHA-256 identifies the exact bytes.

## Human-readable projection

Every canonical Civic CBOR record may have a generated JSON diagnostic projection.

The JSON projection is for:

- human inspection;
- browser display;
- debugging;
- RAG ingestion where text form is convenient;
- evidence export.

The JSON projection is **not** the signed authority object.

Binary values are represented in the projection as lowercase hexadecimal or base64url together with explicit field/type metadata. The projection must always expose the SHA-256 of the canonical CBOR bytes from which it was generated.

A verifier never reconstructs authority bytes by reserializing arbitrary JSON.

## Append-only long-term record streams

The Epoch Manifest is a current authority snapshot; it is not required to contain decades of every witnessed event inline.

Long-lived Civic history uses individually canonicalized records stored as a CBOR Sequence compatible with RFC 8742:

~~~text
signed record 1
signed record 2
signed record 3
...
~~~

Appending a later record does not rewrite earlier records.

Each record has its own SHA-256 identity. Stream heads are referenced by the Epoch Manifest `history` map.

This supports decades of witnessing while preserving small, independently verifiable units.

## Object store

Large or reusable content is stored by content identity:

~~~text
SHA-256
    -> exact bytes
    -> metadata descriptor
    -> zero or more record references
~~~

Physical path, filesystem, IP address, device model, and storage medium are not part of the content identity.

An object can therefore move between:

- ESP32-S3 internal storage;
- another participant appliance;
- a Signing Node;
- removable storage;
- ordinary filesystem storage;
- future IPFS pinning;

without changing the Civic record that references it.

## Parser/verification behavior

A conforming v1 verifier rejects:

- non-deterministic CBOR for a signed Civic record;
- duplicate map keys;
- indefinite-length items;
- floating-point fields;
- text that violates required UTF-8/NFC normalization;
- incorrect fixed byte lengths;
- unsorted set-semantic arrays;
- unknown `format` or unsupported `version`;
- a COSE algorithm other than ESP256 (-9) for this profile;
- a `kid` that does not match the verification key;
- malformed or invalid signatures;
- content hashes that do not match referenced object bytes.

These are explicit Diagnostics results. The verifier does not repair the input silently.

## No speculative size wall

The protocol does not impose an artificially small Epoch Manifest or Civic record limit merely because the first reference edge is an ESP32-S3.

Implementations may publish capacity limits appropriate to their physical resources, but capacity is not Civic identity and another conforming platform may accept substantially larger records.

If actual field evidence shows that a particular representation causes resource exhaustion or denial-of-service behavior, that evidence becomes a Diagnostics input for a later bounded size-policy decision.

## Decision

Civic authority records now have a complete baseline stack:

~~~text
structured authority/evidence data
    -> deterministic CBOR
    -> SHA-256 content identity
    -> COSE_Sign1
    -> ESP256 (-9) / Civic P-256 key
    -> append-only CBOR Sequence history
    -> optional human JSON projection
~~~

The next implementation step is to encode/validate this contract in repository code and tests before production Civic key generation.
