# Civic Cryptographic Baseline

## Status

Accepted implementation architecture decision. Documentation only; no production key is created by this decision.

This document selects the first portable cryptographic profile for HOA-local Civic authority functions. It is subordinate to the Civic Infrastructure principles, anti-capture contract, authority-continuity decision, and authority-epoch ceremony.

## Selection criterion

The selection criterion is **functionality first**.

Cryptography exists here to provide:

- attributable acts;
- public verification;
- deterministic key identity;
- epoch-bound authority proofs;
- inspectable provenance;
- interoperability across user-owned platforms.

The baseline is not selected to build a maximal defensive wall around participant devices or operators.

Security hardening requires evidence. A demonstrated failure, exploit, operational weakness, or attack becomes Diagnostics evidence. The project preserves and publishes attributable failure evidence where publication is lawful and does not expose private key material or unrelated private data, then evaluates the smallest architectural or implementation change justified by that evidence.

A failure is therefore information about the system, not a reason to pre-install proprietary custody or central control.

## Civic profile v1

The first Civic signature profile is:

~~~text
profile identity       kane-civic-ecdsa-p256-sha256-v1
signature algorithm    ECDSA
curve                  NIST P-256 / secp256r1
message digest         SHA-256
public key             uncompressed SEC1 EC point
public key length      65 bytes: 0x04 || X(32) || Y(32)
signature encoding     IEEE P1363 fixed-width r || s
signature length       64 bytes: r(32) || s(32)
key identifier         lowercase SHA-256 of exact 65 public-key bytes
text binary projection base64url without padding where a JSON/text field is required
~~~

The existing provisional firmware-authorization implementation already proves that the pinned ESP-IDF/PSA environment can verify the same P-256/SHA-256/P1363 primitive. Modern browser WebCrypto provides ECDSA signing/verification and raw elliptic-curve public-key import. This existing compatibility is engineering evidence, not authority precedent.

## Why this profile

P-256/SHA-256 is selected because the same minimal primitive can be implemented without proprietary hardware across:

- browser WebCrypto;
- the current ESP32-S3/ESP-IDF PSA reference stack;
- ordinary Linux/OpenSSL-class systems;
- common programming-language cryptography libraries;
- future user-owned platforms capable of implementing the published contract.

It does not require:

- ATECC608A-class hardware;
- security-eFuse provisioning;
- HSM or token custody;
- a remote signer;
- a cloud account;
- a vendor-specific key service.

The project is deliberately not selecting a different primitive merely to increase theoretical security margins when no evidenced functional requirement demands it.

## Public-key representation

The **Civic canonical public-key identity** is the exact uncompressed 65-byte SEC1 point.

This representation is intentionally small, explicit, and independent of certificates, ASN.1 containers, vendor objects, or account systems.

Standard projections may be produced when useful:

- SubjectPublicKeyInfo DER/PEM for ordinary cryptographic tooling;
- JSON/WebCrypto import projections;
- human-readable hexadecimal or base64url display.

Those are projections of the same key. They do not change the Civic key identifier.

CA certificates/public keys, OpenPGP public keys, SSH public keys, and similar user-owned public artifacts stored on an edge retain their own native standard formats. They are not required to be converted into the Civic key format merely because the edge stores them.

## Private-key representation and custody

The Civic wire/authority contract does **not** make one private-key file format part of Civic identity.

A conforming implementation may use ordinary software-held key material and may export/import a standard software representation such as PKCS #8 when portability or recovery requires it.

Provider-specific internal storage is allowed only as an implementation detail. It must not alter:

- the public key;
- the key identifier;
- the signature bytes;
- the authority epoch;
- the record interpretation;
- reconstruction on another conforming platform.

Hardware-enforced non-exportability is not required.

## Signed bytes

A Civic signature applies to the **exact canonical byte representation defined by the signed record's contract**.

The cryptographic profile does not silently invent a second serialization.

Therefore:

~~~text
logical Civic record
    -> record-specific canonical bytes
    -> SHA-256
    -> ECDSA P-256 signature
~~~

A verifier must know both:

1. the record format/version that defines canonical bytes; and
2. the cryptographic profile identity.

The Epoch Manifest serialization remains a separate implementation decision and must be frozen before production signing.

## One profile per authority epoch

Each Civic authority epoch declares one current cryptographic profile.

There is no silent algorithm fallback or verifier negotiation inside an epoch.

If Diagnostics or platform evolution justifies replacing the cryptographic profile:

~~~text
accepted evidence
    -> explicit profile decision
    -> new profile identity
    -> source-governed transition
    -> new authority epoch / new current keys where Civic authority keys change
~~~

Historical epochs remain verifiable under the profile they declared.

This provides algorithm agility without making every verifier accept an open-ended collection of algorithms.

## Verification failure is Diagnostics

A failed signature, unknown key, malformed key, wrong epoch, inconsistent history head, or unsupported profile must fail explicitly.

The implementation must not silently:

- substitute another key;
- try weaker/alternate algorithms until one passes;
- rewrite the record;
- suppress the discrepancy;
- make a central service the arbiter of what happened.

The failure and the inputs needed to reproduce it become Diagnostics evidence, subject to the project's evidence/publication and privacy boundaries.

A successful cryptographic verification means only that the signature is valid for the specified bytes and key under the declared profile. It does not independently prove legal truth, civic standing, current authority, or correctness of the underlying claim.

## Relationship to other key systems

The Civic profile does not replace future CA/TLS, OpenPGP, SSH, email, or IPFS mechanisms.

Those systems may use their own standard key/record formats.

The cohesive stack comes from clear role separation and common primitives where useful, not by forcing every key in the infrastructure into one schema.

The Firmware Release Authority remains a distinct logical authority. It may reuse this primitive if separately accepted, but reuse of an algorithm does not merge authority roots or key roles.

## Current implementation consequence

For Civic authority implementation, the algorithm/key-representation interrogation is closed for v1:

~~~text
ECDSA P-256
+ SHA-256
+ 65-byte uncompressed public key
+ 64-byte P1363 signature
+ SHA-256 public-key identifier
~~~

Remaining work includes:

- Epoch Manifest canonical representation;
- software key generation/storage/recovery mechanics;
- signing-node record store;
- participant-device replicated authority-state representation;
- verification behavior and Diagnostics evidence;
- operator-node replacement/recovery;
- implementation reconciliation and tests.

No production Civic private key should be generated until those record/lifecycle mechanics are accepted.
