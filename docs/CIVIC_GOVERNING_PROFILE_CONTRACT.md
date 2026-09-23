# Civic Governing Profile Contract

## Status

Architecture contract. Documentation only.

This document freezes the canonical machine-readable governing-profile representation required by accepted participant-standing verification.

It defines:

- the exact governing-profile byte representation;
- the exact `profile_sha256` identity;
- the exact `source_set_sha256` derivation;
- the minimum profile tables used to recognize standing classes, qualification paths, participation policies, evidence roles, and temporal constraints;
- the source-provenance boundary for profile rules;
- the generic semantic-validator contract.

It does not define a complete universal civic-affordance taxonomy, a universal legal rule engine, a production signing workflow, or a production Civic key.

It is subordinate to:

- `docs/CIVIC_EPOCH_MANIFEST_FORMAT.md`;
- `docs/CIVIC_CRYPTOGRAPHIC_BASELINE.md`;
- `docs/CIVIC_ACCEPTED_PARTICIPANT_STANDING_RECORD.md`;
- `docs/CIVIC_AFFORDANCE_AUTHORITY_CONTRACT.md`;
- `docs/CIVIC_PARTICIPATION_RENEWAL.md`;
- `docs/CIVIC_SAME_AND_EQUAL_POLICY.md`;
- `docs/CIVIC_PARTICIPANT_AUTHORITY_STATE_RECONSTRUCTION.md`;
- `docs/HOA_GOVERNING_SOURCE_INHERITANCE.md`.

This contract does not enable production signing.

## Why this contract is needed

The accepted Epoch Manifest already binds:

~~~text
manifest.governing_profile = {
    profile_id,
    profile_sha256,
    source_set_sha256
}
~~~

The accepted participant-standing record repeats the same descriptor and requires profile-specific semantic validation.

Before this document, those three fields identified an exact profile conceptually, but the repository had not frozen:

- what exact bytes `profile_sha256` hashes;
- how `source_set_sha256` is recomputed;
- how a verifier recognizes one standing class or qualification path;
- how required and supplementary evidence roles are expressed;
- how a required participation policy constrains the standing record;
- how source-derived rules are distinguished from Civic mechanism choices.

The accepted participant-standing verifier therefore exposes an explicit semantic-validator seam.

That seam was intentional.

It must not become an excuse for hidden ad hoc policy.

This document supplies the missing canonical data contract.

## Fundamental boundary

The governing profile is a compiled, published verification policy derived from an explicit source context.

Conceptually:

~~~text
governing sources
    -> source-derived interpretation
    -> canonical governing profile
    -> participant-standing semantic verification
~~~

The profile is not itself the underlying statute, declaration, bylaw, public record, or other substantive source.

Therefore:

~~~text
profile rule
    != underlying law

profile mechanism
    != underlying law

successful profile validation
    != independent proof that every participant-maintained factual claim is true
~~~

The profile tells a verifier what Civic requires before it will recognize the standing assertion under that exact profile.

## Scope of v1

Governing Profile v1 is intentionally narrow.

It contains only the machine-readable semantics needed by the accepted participant-standing contract:

- recognized standing classes;
- permitted qualification paths for each class;
- whether voluntary participation is required;
- permitted participation policies;
- whether open-ended standing is allowed;
- optional maximum standing duration;
- permitted claim-responsibility classes;
- authority-evidence requirements;
- supplementary-evidence permissions;
- participation attestation mode;
- participation interval rule;
- explicit rule provenance.

It does not serialize the complete broader Affordance Authority Contract.

A future profile version may add broader relationship-tuple, derivation, surface, or Same-and-Equal semantics when implementation requires them.

## Canonical profile format

The exact v1 format identifier is:

~~~text
kane-civic-governing-profile
~~~

The exact v1 version is:

~~~text
1
~~~

The canonical profile is encoded as RFC 8949 core-deterministic CBOR using the same Civic deterministic-CBOR rules as the Epoch Manifest.

Therefore profile encoding inherits these requirements:

- UTF-8 text;
- NFC text normalization;
- no duplicate map keys;
- no floating-point values;
- no indefinite-length items;
- shortest integer encodings;
- deterministic map-key ordering;
- deterministic array ordering where this contract specifies sorting;
- no alternate semantically equivalent encoding accepted as the same object.

The exact profile identity is:

~~~text
profile_sha256 =
    SHA-256(exact deterministic-CBOR governing-profile bytes)
~~~

The profile does not contain its own `profile_sha256`.

That avoids self-reference.

## Canonical v1 top-level schema

The exact top-level map is:

~~~text
{
  "format": "kane-civic-governing-profile",
  "version": 1,

  "profile_id": text,
  "source_set_sha256": bytes(32),

  "standing_classes": [
    * standing_class_definition
  ],

  "qualification_paths": [
    * qualification_path_definition
  ],

  "participation_policies": [
    * participation_policy_definition
  ]
}
~~~

Unknown top-level fields are invalid in v1.

Private key material is forbidden.

Executable code, scripts, bytecode, network endpoints, and dynamically loaded validator modules are not part of the v1 profile.

The profile is authority data, not executable authority.

## profile_id

`profile_id` is nonempty NFC text.

It is a stable published profile-family identifier.

It is not the exact content identity.

Therefore:

~~~text
same profile_id
+
different profile_sha256
=
different exact profile revision
~~~

A verifier must bind both.

A semantic change requires different profile bytes and therefore a different `profile_sha256`.

Historical records remain interpreted under the exact profile hash they originally referenced.

## Governing source-set identity

The Epoch Manifest already carries:

~~~text
manifest.governing_sources
~~~

Each manifest source descriptor includes:

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

The governing profile must bind the semantic source set without making mutable or retrieval-oriented metadata part of source-set identity.

Therefore v1 derives a canonical source-set object from the manifest source descriptors.

## Canonical source-set object

The exact derived object is:

~~~text
{
  "format": "kane-civic-governing-source-set",
  "version": 1,

  "sources": [
    * {
        "source_id": text,
        "role": text,
        "sha256": bytes(32),
        "byte_length": uint,
        "media_type": text
      }
  ]
}
~~~

The source array is sorted by UTF-8 byte ordering of `source_id`.

`source_id` values are unique.

Unknown fields are invalid in the canonical source-set object.

The object is deterministically CBOR encoded.

The source-set identity is:

~~~text
source_set_sha256 =
    SHA-256(exact deterministic-CBOR canonical source-set bytes)
~~~

## title and source_uri are excluded from source-set identity

The manifest fields:

~~~text
title
source_uri
~~~

are intentionally excluded from the canonical source-set object.

They remain authenticated manifest metadata.

They are not semantic content identity.

A URI may disappear, redirect, or move.

A title may be corrected without changing the exact governing source bytes or the role assigned to those bytes.

The source-set identity instead commits to:

- source identifier;
- semantic source role;
- exact source SHA-256;
- exact byte length;
- media type.

Changing any of those fields changes `source_set_sha256`.

## No separately retained source-set object is required

The canonical source-set bytes are a deterministic projection of the accepted Epoch Manifest's `governing_sources`.

Therefore v1 does not require a separate stored source-set object.

A verifier reconstructs the canonical source-set bytes from the manifest and recomputes the hash.

This avoids duplicate authority objects while preserving exact verification.

## Three-way profile binding

A conforming verifier requires:

~~~text
profile.source_set_sha256
    == manifest.governing_profile.source_set_sha256

SHA-256(canonical source-set bytes)
    == manifest.governing_profile.source_set_sha256

SHA-256(exact profile bytes)
    == manifest.governing_profile.profile_sha256
~~~

and:

~~~text
profile.profile_id
    == manifest.governing_profile.profile_id
~~~

The standing record separately repeats the same manifest profile descriptor under the accepted standing contract.

Therefore one standing verification is bound to:

~~~text
exact standing record
+
exact Epoch Manifest
+
exact governing profile bytes
+
exact governing source set
~~~

## Profile object retention

The exact governing-profile bytes are authority-required content.

The current Epoch Manifest `object_index` must contain the profile object identified by:

~~~text
sha256 = manifest.governing_profile.profile_sha256
~~~

For v1 the profile object descriptor uses:

~~~text
media_type = "application/kane-civic-governing-profile+cbor"
semantic_role = "governing-profile"
~~~

The exact bytes must verify against:

- SHA-256;
- byte length;
- deterministic-CBOR profile schema.

The profile must be independently available from one complete participant authority-state replica.

A URI is not a substitute.

## Common provenance descriptor

Standing-class, qualification-path, and participation-policy definitions each carry:

~~~text
"provenance": {
  "kind":
      "governing_source"
    | "derived_profile_parameter"
    | "civic_mechanism",

  "source_ids": [ * text ]
}
~~~

`source_ids` is sorted by UTF-8 bytes and contains no duplicates.

Every named `source_id` must exist in the canonical source set.

### governing_source

~~~text
kind = "governing_source"
~~~

means the profile rule directly represents a substantive condition derived from the named governing source or sources.

At least one `source_id` is required.

### derived_profile_parameter

~~~text
kind = "derived_profile_parameter"
~~~

means the Civic mechanism or profile parameter is project-defined, but its substantive parameter is intentionally inherited from the named governing source or sources.

At least one `source_id` is required.

This is the machine-readable form of the established distinction:

~~~text
source fact
    != Civic mechanism

but

Civic mechanism parameter
    may be derived from source fact
~~~

### civic_mechanism

~~~text
kind = "civic_mechanism"
~~~

means the rule is a Civic participation/provenance mechanism and is not represented as a statutory or condominium-instrument requirement.

`source_ids` may be empty.

It may also contain contextual sources when useful, but those sources do not convert the mechanism itself into law.

This distinction is mandatory for mechanisms such as SASE participation when the underlying source does not itself require SASE.

## standing_class_definition

Each standing-class definition contains exactly:

~~~text
{
  "standing_class": text,

  "qualification_path_ids": [ * text ],

  "participation_required": bool,
  "participation_policy_ids": [ * text ],

  "allow_open_ended_standing": bool,

  "maximum_standing_duration": null
      / {
          "kind": "fixed_duration_ms"
                / "calendar_months",
          "value": uint
        },

  "provenance": provenance_descriptor
}
~~~

Unknown fields are invalid.

The `standing_classes` array is sorted by UTF-8 bytes of `standing_class`.

Standing-class identifiers are unique.

## standing_class

`standing_class` is the exact text identifier permitted in:

~~~text
accepted standing record.body.standing_class
~~~

Its meaning exists only under the exact governing profile hash.

A verifier must not compare the text across profile hashes and assume identical standing.

## qualification_path_ids

`qualification_path_ids` is a nonempty sorted unique array.

Every identifier must resolve to exactly one definition in:

~~~text
profile.qualification_paths
~~~

The accepted standing record's:

~~~text
qualification.path_id
~~~

must be one of the path identifiers permitted by the selected standing class.

No path is implicitly permitted.

## participation_required

If:

~~~text
participation_required = false
~~~

then:

~~~text
participation_policy_ids = []
~~~

and the standing record must satisfy the accepted standing contract's no-participation form:

~~~text
required = false
policy_id = null
valid_from_ms = null
valid_until_ms = null
authority_evidence = []
supplementary_evidence = []
~~~

If:

~~~text
participation_required = true
~~~

then `participation_policy_ids` must be nonempty.

The standing record must name exactly one permitted policy.

## allow_open_ended_standing

If:

~~~text
allow_open_ended_standing = false
~~~

then:

~~~text
standing.valid_until_ms
~~~

must be non-null.

If:

~~~text
allow_open_ended_standing = true
~~~

the standing record may use a null end only when all other applicable qualification and participation rules permit it.

This field does not override a required bounded participation policy.

## maximum_standing_duration

`maximum_standing_duration` limits how far the overall standing interval may extend from:

~~~text
standing.valid_from_ms
~~~

If null, this class defines no additional maximum duration.

If present, the standing end must be non-null and must not exceed the calculated maximum.

A shorter interval is permitted.

This allows the accepted standing record to reflect the earliest applicable expiration among multiple conditions.

### fixed_duration_ms

~~~text
{
  "kind": "fixed_duration_ms",
  "value": uint
}
~~~

requires:

~~~text
valid_until_ms
    <= valid_from_ms + value
~~~

Unsigned overflow is invalid.

`value` must be greater than zero.

### calendar_months

~~~text
{
  "kind": "calendar_months",
  "value": uint
}
~~~

uses the deterministic UTC calendar-month rule defined below.

`value` must be greater than zero.

## qualification_path_definition

Each qualification-path definition contains exactly:

~~~text
{
  "path_id": text,

  "permitted_claim_responsibility": [
    * "participant_claimed"
      / "operator_attested"
      / "other_published_attestation"
  ],

  "authority_evidence": [
    * evidence_requirement
  ],

  "supplementary_evidence": [
    * evidence_requirement
  ],

  "provenance": provenance_descriptor
}
~~~

Unknown fields are invalid.

The `qualification_paths` array is sorted by UTF-8 bytes of `path_id`.

Path identifiers are unique.

## permitted_claim_responsibility

This array is nonempty, sorted by UTF-8 bytes, and contains no duplicates.

Only the three responsibility values already frozen by the accepted standing-record contract are valid.

The standing record's:

~~~text
qualification.claim_responsibility
~~~

must appear in the selected path's permitted set.

In particular:

~~~text
operator signed record
    != automatically
operator_attested qualification
~~~

`operator_attested` is accepted only when the exact profile path explicitly permits it.

## evidence_requirement

The exact v1 evidence-requirement map is:

~~~text
{
  "semantic_role": text,
  "min_count": uint,
  "max_count": uint / null,
  "media_types": [ * text ]
}
~~~

Unknown fields are invalid.

Requirements are sorted by UTF-8 bytes of `semantic_role`.

A semantic role may appear at most once within one requirement array.

`media_types` is sorted by UTF-8 bytes and contains no duplicates.

An empty `media_types` array means:

~~~text
any nonempty media_type is permitted
~~~

If nonempty, the evidence reference's `media_type` must exactly match one listed value.

## Authority-evidence requirement semantics

For an `authority_evidence` requirement:

~~~text
min_count >= 1
~~~

`max_count`, when non-null, must be greater than or equal to `min_count`.

The accepted standing record must contain at least `min_count` and at most `max_count` matching evidence references for the semantic role.

If `max_count = null`, no profile maximum is imposed.

Every authority-evidence reference in the standing section must match exactly one permitted requirement.

No undeclared authority-evidence role is accepted.

The exact referenced bytes remain mandatory participant-replica content under the accepted standing and reconstruction contracts.

## Supplementary-evidence requirement semantics

For a `supplementary_evidence` requirement:

~~~text
min_count = 0
~~~

This is mandatory.

A supplementary evidence rule cannot make the evidence required for successful authority verification.

`max_count` may limit how many references of that role are accepted.

Every supplementary evidence reference in the standing section must match exactly one permitted requirement.

No undeclared supplementary role is accepted.

The bytes may remain locally unavailable.

This preserves:

~~~text
supplementary evidence
    != hidden authority dependency
~~~

## Evidence count is section-local

Evidence requirements are evaluated separately for:

- qualification;
- participation.

A single exact evidence hash may appear in both sections only when each section's selected profile definition independently permits the semantic role used there.

That constitutes the explicit multiple-role authorization required by the accepted standing architecture.

## Evidence content and factual responsibility

Governing Profile v1 deliberately does not define a universal parser for arbitrary evidence content.

The generic verifier establishes:

- exact evidence identity;
- exact byte length;
- declared media type;
- declared semantic role;
- required-vs-supplementary classification;
- profile-permitted count;
- authority-byte availability where required;
- claim responsibility.

It does not infer that an arbitrary PDF, image, court record, deed, email, or public record proves a substantive legal fact merely because the bytes are present.

That factual boundary remains explicit.

For:

~~~text
participant_claimed
~~~

the participant remains responsible for the substantive claim.

For:

~~~text
operator_attested
~~~

the profile expressly makes the operator responsible for the bounded qualification assertion.

For:

~~~text
other_published_attestation
~~~

the required authority evidence must carry the published attestation discipline needed by that profile path.

A future content-specific machine parser requires its own separately frozen format/rule contract.

It must not be hidden inside an opaque local callback.

## participation_policy_definition

Each participation-policy definition contains exactly:

~~~text
{
  "policy_id": text,

  "attestation_mode":
      "recording_operator"
    / "authority_evidence",

  "interval_rule": {
    "kind":
        "explicit_bounded"
      / "fixed_duration_ms"
      / "calendar_months"
      / "open_ended",

    "value": uint / null
  },

  "authority_evidence": [
    * evidence_requirement
  ],

  "supplementary_evidence": [
    * evidence_requirement
  ],

  "provenance": provenance_descriptor
}
~~~

Unknown fields are invalid.

The `participation_policies` array is sorted by UTF-8 bytes of `policy_id`.

Policy identifiers are unique.

## attestation_mode

### recording_operator

~~~text
attestation_mode = "recording_operator"
~~~

means the accepted standing record's current-operator provenance is the authoritative attestation that the participation event occurred.

The profile may still require additional authority evidence.

This mode supports the accepted Kane principle that the operator may attest receipt/renewal participation without thereby certifying every substantive qualification claim.

### authority_evidence

~~~text
attestation_mode = "authority_evidence"
~~~

means operator provenance alone is insufficient to establish participation.

At least one participation `authority_evidence` requirement must exist.

The exact required evidence bytes must be available for standing verification and reconstruction.

## interval_rule

The participation interval rule determines the permitted relationship between:

~~~text
participation.valid_from_ms
participation.valid_until_ms
~~~

It does not create a trusted-time oracle.

It constrains the authenticated time assertions contained in the standing record.

### explicit_bounded

~~~text
{
  "kind": "explicit_bounded",
  "value": null
}
~~~

requires:

~~~text
valid_until_ms != null
valid_until_ms > valid_from_ms
~~~

The profile does not impose an exact duration beyond boundedness.

### fixed_duration_ms

~~~text
{
  "kind": "fixed_duration_ms",
  "value": uint
}
~~~

requires a non-null end and:

~~~text
valid_until_ms
    == valid_from_ms + value
~~~

`value` must be greater than zero.

Unsigned overflow is invalid.

### calendar_months

~~~text
{
  "kind": "calendar_months",
  "value": uint
}
~~~

requires a non-null end equal to the deterministic UTC calendar-month addition defined below.

`value` must be greater than zero.

This representation can express a policy stated in calendar months without silently translating it to an arbitrary fixed number of days.

### open_ended

~~~text
{
  "kind": "open_ended",
  "value": null
}
~~~

requires:

~~~text
valid_until_ms = null
~~~

A standing class using this participation policy must also permit open-ended standing.

## Deterministic UTC calendar-month addition

For a `calendar_months` rule:

1. Interpret `valid_from_ms` as a Unix timestamp in milliseconds at UTC.
2. Convert it to a UTC Gregorian calendar date and time with millisecond precision.
3. Add the specified positive number of calendar months to the year/month pair.
4. Preserve hour, minute, second, and millisecond.
5. Preserve the original day-of-month when that day exists in the target month.
6. If the target month has fewer days, clamp to the last valid day of the target month.
7. Convert the resulting UTC instant back to Unix milliseconds.
8. The record's `valid_until_ms` must equal that exact value.

If the input or result cannot be represented by the implementation's supported exact Unix-millisecond domain, verification fails explicitly.

A verifier must not silently substitute:

- 30 days per month;
- 365/12 days;
- local wall-clock time;
- daylight-saving offsets;
- implementation-dependent calendar arithmetic.

## Profile table referential integrity

A valid v1 profile requires all of the following:

- every standing class has at least one qualification path;
- every referenced qualification path exists exactly once;
- every participation-required standing class has at least one participation policy;
- every referenced participation policy exists exactly once;
- participation-not-required classes reference no participation policies;
- every provenance `source_id` exists in the canonical source set;
- all identifier arrays are sorted and unique;
- all definition arrays are sorted and unique by their primary identifier;
- all evidence-requirement arrays are sorted and unique by semantic role.

Unused qualification-path or participation-policy definitions are invalid in v1.

This keeps the exact profile minimal and prevents dead policy material from being silently carried as authority semantics.

## Semantic validation against one standing record

After generic history, signature, manifest, record-identity, signer, operator, authority-object, and currentness checks, the profile-semantic layer performs the following deterministic checks.

### 1. Verify profile identity

Verify:

~~~text
SHA-256(exact profile bytes)
    == manifest.governing_profile.profile_sha256
~~~

and exact `profile_id`.

### 2. Verify source-set identity

Derive the canonical source-set object from:

~~~text
manifest.governing_sources
~~~

and require its SHA-256 to equal both:

~~~text
manifest.governing_profile.source_set_sha256
profile.source_set_sha256
~~~

### 3. Resolve standing class

Resolve exactly one:

~~~text
profile.standing_classes[].standing_class
~~~

matching the standing record.

Unknown class fails.

### 4. Resolve qualification path

Resolve the standing record's `qualification.path_id`.

Require that path to be listed by the selected standing class.

Unknown or unpermitted path fails.

### 5. Validate claim responsibility

Require the standing record's `claim_responsibility` to appear in the selected path's permitted set.

### 6. Validate qualification evidence policy

Group qualification evidence by `semantic_role`.

Require every authority and supplementary reference to satisfy the selected path's exact count and media-type rules.

Required authority evidence must already have exact verified bytes.

Supplementary evidence bytes are not required.

### 7. Validate participation requirement

Require:

~~~text
record.participation.required
    == selected_class.participation_required
~~~

A mismatch fails.

### 8. Resolve participation policy

If participation is required, resolve exactly one policy matching the record's `policy_id` and require that it be listed by the selected standing class.

If participation is not required, require the no-participation null/empty representation.

### 9. Validate participation attestation/evidence

Apply the selected policy's `attestation_mode` and evidence requirements.

### 10. Validate participation interval rule

Apply the selected policy's exact interval rule.

### 11. Validate open-ended standing permission

If the standing end is null, require:

~~~text
selected_class.allow_open_ended_standing = true
~~~

and no participation rule that requires a bounded end.

### 12. Validate maximum standing duration

If the class defines `maximum_standing_duration`, require the standing end to remain within that maximum.

The standing may end earlier.

### 13. Preserve accepted standing temporal composition

The separate accepted standing verifier still enforces:

~~~text
standing.valid_from_ms >= participation.valid_from_ms
~~~

when participation is required, and the standing end must not extend beyond a bounded participation end.

The governing profile does not weaken that invariant.

## Generic validator interface

The architecture separates profile parsing from standing evaluation.

Conceptually:

~~~text
verified_profile =
    verify_governing_profile(
        exact_profile_bytes,
        epoch_manifest
    )

validate_standing_against_profile(
    verified_profile,
    standing_request
)
~~~

The first operation verifies canonical bytes, schema, source-set binding, and referential integrity.

The second evaluates one already authenticated standing request against those verified profile tables.

## No hidden validator authority

The current accepted standing implementation requires an explicit `validate_profile_semantics` callback because canonical profile serialization had not yet been frozen.

After this contract, that callback is an implementation seam, not protocol authority.

A conforming implementation must not make successful standing verification depend on:

- undocumented local callback behavior;
- operator memory;
- network-fetched code;
- a SaaS rules engine;
- mutable web content;
- an LLM answer;
- an opaque database rule;
- a portal permission.

The mandatory v1 checks defined by this document must be reproducible from:

- exact profile bytes;
- the accepted Epoch Manifest;
- exact authority-required governing sources;
- exact accepted standing record;
- exact authority-evidence bytes required by that record.

An implementation may expose additional diagnostic callbacks.

Those callbacks must not weaken or replace mandatory v1 semantic checks.

## Profile is data, not executable code

The governing profile must not contain executable expressions or arbitrary code.

This protects long-term reconstruction.

A participant recovering authority state years later must not need to execute an unknown historical script merely to determine what the profile meant.

The v1 profile therefore uses:

- exact identifiers;
- enumerated modes;
- bounded evidence requirements;
- explicit temporal rule forms;
- explicit source provenance.

If a future semantic need cannot be expressed safely by v1, it requires a new published profile-format version or a separately frozen rule contract.

It must not be smuggled into a text field and interpreted ad hoc.

## Relationship to Affordance Authority Contract

`docs/CIVIC_AFFORDANCE_AUTHORITY_CONTRACT.md` defines a broader logical source-of-meaning for Civic relationships.

This Governing Profile v1 is narrower.

It is the canonical standing-verification projection needed by current accepted authority records.

Therefore:

~~~text
broader Affordance Authority Contract
    may contain more semantic material

Governing Profile v1
    contains only the canonical subset
    required for accepted participant standing
~~~

The two must not be conflated.

A future serialization of the complete Affordance Authority Contract may either incorporate or supersede this profile format through an explicit versioned architecture decision.

## Relationship to HOA governing-source inheritance

For an HOA profile, substantive rules continue to follow:

~~~text
applicable statute
    -> applicable condominium instruments
    -> published Civic profile
    -> Civic standing verification
~~~

The profile's provenance descriptors make that boundary machine-visible.

A verifier does not decide that a bylaw overrides statute merely because both source IDs are present.

The source-derived profile authoring process remains responsible for producing a valid published profile from the applicable source hierarchy.

Civic verification then verifies the exact profile that was accepted.

## No silent legal derivation

Governing Profile v1 must not silently create derivations such as:

~~~text
CONDO_UNIT_OWNER -> HOA_MEMBER
PROPERTY_TAXPAYER -> CURRENT_RESIDENT
CURRENT_RESIDENCE -> CURRENT_RESIDENT
device possession -> civic standing
SASE participation -> condominium ownership
~~~

If such a substantive relationship is needed, it belongs in the broader published authority-contract/profile architecture and must have explicit source provenance.

The standing profile does not infer it from correlation.

## Profile revision and epoch history

A change to any canonical profile field changes the exact profile bytes and therefore changes:

~~~text
profile_sha256
~~~

A change to any canonical governing-source-set field changes:

~~~text
source_set_sha256
~~~

Because the profile itself contains `source_set_sha256`, a source-set change also changes `profile_sha256`.

Historical accepted standing records remain bound to the historical profile/source-set identities they referenced.

They are not reinterpreted under a later profile merely because the same `profile_id` text is reused.

A successor current profile belongs in a successor accepted authority state according to the existing Epoch Manifest/continuity rules.

## Reconstruction requirements

A complete participant authority-state replica must contain enough exact material to reproduce profile verification.

At minimum for each retained accepted profile context it requires:

- exact profile bytes;
- the accepted Epoch Manifest carrying the profile descriptor;
- exact authority-required governing source bytes;
- exact authority-required standing evidence bytes;
- accepted standing records;
- the deterministic source-set derivation algorithm defined here.

The canonical source-set bytes themselves need not be separately stored because they are reproducible from the accepted manifest.

Supplementary evidence bytes remain outside mandatory reconstruction unless another independent authority rule requires them.

## Failure conditions

Profile verification fails explicitly for at least:

- unsupported profile format or version;
- nondeterministic CBOR;
- unknown top-level field;
- empty or invalid `profile_id`;
- profile hash mismatch;
- source-set hash mismatch;
- malformed source-set derivation;
- duplicate source identifiers;
- unsorted canonical arrays;
- duplicate standing class;
- duplicate qualification path;
- duplicate participation policy;
- dangling qualification-path reference;
- dangling participation-policy reference;
- unused path or policy definition;
- invalid provenance kind;
- provenance source missing from source set;
- source-derived rule with empty required source list;
- invalid claim-responsibility value;
- invalid evidence requirement;
- undeclared authority evidence role;
- undeclared supplementary evidence role;
- required evidence count not satisfied;
- evidence media type not permitted;
- participation requirement mismatch;
- participation policy not permitted by standing class;
- invalid attestation mode;
- invalid interval rule;
- participation interval inconsistent with its rule;
- open-ended standing where not permitted;
- standing duration beyond the profile maximum;
- overflow or unrepresentable calendar computation.

The verifier must not silently repair any of these states.

## Successful profile-semantic verification means

Successful v1 profile-semantic verification means only that:

- the exact accepted profile bytes were used;
- the exact accepted governing source set was bound;
- the standing class is recognized by that profile;
- the qualification path is permitted for that class;
- claim responsibility is explicitly permitted;
- evidence roles/counts/media types satisfy the profile;
- required authority evidence remains available;
- participation requirements and interval semantics satisfy the profile;
- temporal bounds permitted by the profile are satisfied;
- every profile rule carries explicit source/mechanism provenance.

It does not independently mean that:

- every participant-maintained factual claim is objectively true;
- every governing-source interpretation is legally correct;
- the operator is a universal factual certifier;
- the Signing Node determines substantive law;
- SASE is a statutory requirement;
- the participant is Same-and-Equal for every Civic purpose;
- a later profile can reinterpret the historical record.

## Diagnostics consequences

The contract deliberately creates inspectable discrepancies.

Examples include:

~~~text
standing record names unknown standing_class
profile path does not permit participant_claimed responsibility
required evidence hash exists but semantic role is not permitted
supplementary evidence exists but is not authority-required
participation interval exceeds profile policy
profile source_set_sha256 does not match manifest sources
same profile_id appears with different profile_sha256
current manifest retains a standing record whose profile semantics no longer evaluate current at a later time
~~~

These conditions are diagnostics evidence.

They must remain visible rather than being normalized by convenience logic.

## Production boundary

This architecture does not change:

~~~text
production_signing_enabled = false
production_key_created = false
annales_mutated = false
~~~

No production Civic Signing Node is created by this document.

No production private key is created.

No firmware or participant appliance is changed.

## Next bounded step

Review this architecture before implementation.

After architecture acceptance, the next bounded repository step may implement:

~~~text
civic/governing_profile.py
~~~

with:

- canonical source-set derivation;
- deterministic profile decode/validation;
- profile SHA-256 binding;
- source-set SHA-256 binding;
- profile-table referential integrity;
- data-driven standing semantic validation primitives.

Do not modify the accepted participant-standing tests or CT102 acceptance state in the same implementation step.

Focused governing-profile tests and a new CT102 acceptance gate should remain separate subsequent steps.
