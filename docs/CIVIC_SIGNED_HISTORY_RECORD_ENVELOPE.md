# Civic Signed History Record Envelope

## Status

Accepted architecture contract for the generic individually authenticated Civic history-record envelope.

This document defines the common signed wrapper needed by accepted, witness, diagnostics, and knowledge history streams. It does not define the substantive body schema or governance authorization rules for every record type.

It is subordinate to:

- `docs/CIVIC_CRYPTOGRAPHIC_BASELINE.md`;
- `docs/CIVIC_EPOCH_MANIFEST_FORMAT.md`;
- `docs/CIVIC_HISTORY_HEAD_SEMANTICS.md`;
- `docs/CIVIC_PARTICIPANT_AUTHORITY_STATE_RECONSTRUCTION.md`.

## Purpose

Long-lived Civic history is already defined as an append-only CBOR Sequence of individually authenticated records.

The missing contract is the common record envelope that makes `history_link` authenticated content rather than merely structurally plausible data.

The v1 record path is:

~~~text
type-specific Civic event body
    -> generic deterministic-CBOR history payload
    -> COSE_Sign1
    -> ESP256 (-9)
    -> exact signed record bytes
    -> SHA-256 record identity
    -> append-only CBOR Sequence
~~~

One complete COSE_Sign1 object is one history-sequence item.

## Record identity

The logical history identity remains:

~~~text
record_sha256 = SHA-256(exact complete COSE_Sign1 record bytes)
~~~

This intentionally follows `docs/CIVIC_HISTORY_HEAD_SEMANTICS.md`.

The unsigned deterministic-CBOR payload may also be hashed for diagnostics or type-specific purposes, but its hash does not replace the signed record identity used for predecessor links and history heads.

Re-signing an otherwise identical payload creates different signed record bytes and therefore a different history-record identity.

## COSE profile

The generic Civic history record uses:

~~~text
container        COSE_Sign1
tag              18
algorithm        ESP256
COSE alg id      -9
signature        64-byte P1363 r || s
external AAD     empty
unprotected      empty map
payload          embedded
content type     application/kane-civic-history-record+cbor
~~~

The protected header contains exactly:

~~~text
{
  1: -9,
  3: "application/kane-civic-history-record+cbor",
  4: signer_key_id
}
~~~

The COSE `kid` is exactly 32 bytes and must equal the SHA-256 identifier of the public key used to verify the signature.

The existing Epoch Manifest content type:

~~~text
application/kane-civic-epoch+cbor
~~~

remains distinct and must not be reused for history records.

## Generic deterministic-CBOR payload

Every v1 signed Civic history record has exactly these top-level payload fields:

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

Unknown top-level fields are invalid in v1.

The complete payload is deterministic Civic CBOR. Floating-point values, indefinite-length encoding, duplicate keys, non-NFC text, and other encodings already forbidden by the Civic deterministic-CBOR contract remain forbidden.

## Why the record does not contain current_manifest_sha256

A history record must not require the SHA-256 of the Epoch Manifest whose `history` map may itself name that record as a stream head.

That would permit a circular dependency:

~~~text
Epoch Manifest hash
    depends on history head

history record hash
    depends on payload containing Epoch Manifest hash
~~~

Instead, a history record binds to a non-circular epoch context already committed by the accepted Epoch Manifest:

~~~text
hoa_root_id
epoch_sequence
ceremony_record_sha256
~~~

A verifier resolves that tuple against the accepted verified Epoch Manifest lineage.

This permits a ceremony/event record to be signed before the final Epoch Manifest bytes exist while still allowing the completed manifest to name the resulting signed record as a history head.

## Authority-context binding

For a verified history record, the verifier must locate exactly one accepted Epoch Manifest in the retained lineage for which:

~~~text
manifest.hoa_root_id == record.hoa_root_id
manifest.epoch_sequence == record.epoch_sequence
manifest.ceremony.ceremony_record_sha256
    == record.ceremony_record_sha256
~~~

If no accepted manifest matches, the record is not valid in that reconstructed authority lineage.

If multiple candidate manifests are presented outside one accepted lineage, the verifier does not choose heuristically. The divergence is preserved as Diagnostics evidence.

The authority-context tuple identifies the epoch under which the record claims to have been made without introducing a content-hash cycle.

## record_type

`record_type` is a nonempty text identifier for the substantive record schema.

Examples may eventually include issuance, operator selection, governance decision, witness observation, diagnostic finding, knowledge publication, correction, or supersession records.

This generic envelope does not authorize or define those schemas.

A type-specific implementation defines:

- the exact `record_type` value;
- the required `body` fields;
- which signer kinds are permitted;
- any governance prerequisites;
- any additional referenced object identities;
- any time or sequence semantics beyond generic history linkage.

Unknown required record types fail semantic interpretation rather than being silently treated as another type.

## history_link

The `history_link` map is the exact linkage contract already frozen in `docs/CIVIC_HISTORY_HEAD_SEMANTICS.md`:

~~~text
{
  "stream": "accepted" | "witness" | "diagnostics" | "knowledge",
  "predecessor_record_sha256": bytes(32) / null
}
~~~

Because this map is inside the COSE-authenticated payload, signature verification authenticates the claimed stream and predecessor link.

A verifier must not accept linkage copied from:

- an unprotected COSE header;
- filesystem metadata;
- a database column;
- a filename;
- a sidecar file;
- a transport wrapper;
- an unsigned projection.

After signature verification, this exact map is supplied to the linked-history verifier.

## signer

The generic signer descriptor is:

~~~text
{
  "kind": "signing_node" | "participant",
  "key_id": bytes(32),
  "participant_record_sha256": bytes(32) / null
}
~~~

The payload `signer.key_id` must exactly equal the protected COSE `kid`.

This intentional redundancy binds the semantic signer descriptor to the cryptographic envelope.

### Signing Node signer

For:

~~~text
kind = "signing_node"
~~~

the record requires:

~~~text
participant_record_sha256 = null
~~~

The verifier resolves the public key from the accepted Epoch Manifest identified by the authority-context tuple:

~~~text
record.signer.key_id
    == manifest.signing_node.key_id
~~~

The signature is then verified with:

~~~text
manifest.signing_node.public_key
~~~

A Signing Node signature proves that the current epoch Signing Node signed the exact record bytes.

It does not by itself prove that the substantive event was legally authorized or factually true.

### Participant signer

For:

~~~text
kind = "participant"
~~~

the record requires a non-null:

~~~text
participant_record_sha256
~~~

The verifier finds exactly one current participant descriptor in the referenced epoch for which:

~~~text
participant.participant_record_sha256
    == record.signer.participant_record_sha256

participant.participant_key_id
    == record.signer.key_id
~~~

The signature is verified with that participant descriptor's:

~~~text
participant_public_key
~~~

This permits participant devices to authenticate their own witness or other permitted records without routing authorship through the operator-owned Signing Node.

A participant signature proves attribution to that epoch participant key. It does not grant universal governance authority.

## Signer authorization boundary

Cryptographic signer resolution and substantive authorization are separate checks.

The generic envelope answers:

~~~text
which accepted epoch defined this signer?
which public key corresponds to this signer?
did that key sign these exact payload bytes?
what stream/predecessor did those signed bytes claim?
~~~

The record-type/governance layer answers:

~~~text
was this signer kind permitted to issue this record type?
was the required governance process satisfied?
does the body satisfy the type-specific schema?
what legal or civic meaning does the record have?
~~~

A valid signature must never be treated as an automatic substantive authorization.

## body

`body` is a text-keyed deterministic-CBOR map governed by `record_type`.

The generic envelope does not assign universal fields inside `body`.

This keeps one stable authentication/linkage wrapper while allowing bounded type-specific schemas to evolve independently.

Private key material is forbidden in `body` and elsewhere in the replicated common history record.

## Signing input

The signature input follows the accepted Civic COSE profile.

Conceptually:

~~~text
protected = deterministic_cbor({
    1: -9,
    3: "application/kane-civic-history-record+cbor",
    4: signer_key_id
})

payload = deterministic_cbor(generic_history_record_payload)

Sig_structure = deterministic_cbor([
    "Signature1",
    protected,
    b"",
    payload
])

signature = ECDSA-P256-SHA256(Sig_structure)
            represented as fixed 64-byte P1363 r || s
~~~

The complete stored record is:

~~~text
18([
    protected,
    {},
    payload,
    signature
])
~~~

## Verification order

A generic signed history record is verified in this order:

1. parse exactly one deterministic Civic CBOR item;
2. require COSE_Sign1 tag 18;
3. require an empty unprotected header;
4. require an embedded payload;
5. require protected algorithm ESP256 (-9);
6. require protected content type `application/kane-civic-history-record+cbor`;
7. require a 32-byte protected `kid`;
8. decode the embedded payload as deterministic Civic CBOR;
9. require generic payload format/version/profile;
10. validate `hoa_root_id`, `epoch_sequence`, and `ceremony_record_sha256`;
11. validate `record_type`, `history_link`, `signer`, and `body`;
12. require payload signer key ID to equal COSE `kid`;
13. resolve the accepted Epoch Manifest from the authority-context tuple;
14. resolve the signer public key from that manifest;
15. verify the ESP256 signature over the exact Sig_structure;
16. expose the now-authenticated `history_link` to linked-history verification;
17. apply type-specific body and authorization validation.

Failure at any step fails the record.

## History-sequence verification

For a complete stream, each CBOR Sequence item is one complete signed history-record envelope.

The verifier therefore performs:

~~~text
for each exact sequence item:
    compute record_sha256 over exact COSE bytes
    verify generic signed envelope
    extract authenticated history_link
    verify stream and predecessor relationship

after final item:
    require final record_sha256 == expected Epoch Manifest history head
~~~

This closes the distinction that previously existed between structural linkage verification and authenticated linkage verification.

## Cross-epoch history

A logical history stream may contain records from more than one authority epoch.

Each individual record carries its own non-circular authority-context tuple and is verified against the accepted manifest for that epoch.

A successor record may therefore name the SHA-256 identity of a predecessor record created under an earlier epoch.

The predecessor link authenticates record continuity.

The authority-context tuple authenticates which epoch defined the successor's signer.

Neither silently rewrites the other.

## Forks

Two valid signed records may name the same predecessor.

That is still a fork.

Valid signatures do not make both successors part of one accepted linear history.

The Epoch Manifest history head and the accepted authority lineage identify which linear history is currently represented as accepted.

Competing signed branches remain preservable evidence and Diagnostics input.

## Signature failure and historical key status

Historical records are verified using the public keys recorded in the accepted historical epoch that defines the signer.

A key no longer being current does not invalidate records validly made under its historical epoch.

An old key also does not confer authority in a later epoch.

This maintains:

~~~text
historical verification
    != current authority
~~~

## Content-type separation

Civic v1 therefore has at least two distinct COSE content types:

~~~text
Epoch Manifest:
application/kane-civic-epoch+cbor

Generic history record:
application/kane-civic-history-record+cbor
~~~

A parser must reject one where the other is required.

No silent content-type fallback is permitted.

## Failure is Diagnostics

Explicit failures include:

- malformed or non-deterministic COSE/CBOR;
- wrong COSE tag;
- wrong algorithm;
- wrong content type;
- nonempty unprotected header;
- detached payload;
- malformed or unknown generic record format/version;
- malformed history link;
- malformed signer descriptor;
- payload signer key ID differing from COSE `kid`;
- authority-context tuple not matching an accepted epoch;
- signer key not present in that epoch;
- signer kind inconsistent with the resolved key;
- invalid ESP256 signature;
- type-specific signer not authorized for that record type;
- predecessor-link mismatch;
- final history-head mismatch.

These failures are not silently repaired.

## Production-key boundary

This architecture contract does not enable production signing.

The existing fixture-only signing boundary remains in force.

No production Civic private key is created merely by defining or implementing this record envelope.

## Decision summary

Civic history v1 now uses:

~~~text
deterministic type-specific body
    -> generic history payload
       - HOA root
       - epoch sequence
       - ceremony identity
       - record type
       - authenticated history_link
       - semantic signer descriptor
    -> COSE_Sign1 / ESP256 (-9)
    -> signer kid bound to accepted epoch public key
    -> SHA-256 of exact signed envelope as record identity
    -> append-only CBOR Sequence
    -> linked-history verification
    -> Epoch Manifest stream head
~~~

The envelope provides common authentication and lineage semantics without turning cryptographic attribution into substantive governance authority.
