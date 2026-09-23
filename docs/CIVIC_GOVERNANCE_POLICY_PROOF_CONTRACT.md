# Civic Governance Policy and Proof Contract

## Status

Architecture contract for closure piece 3 of the Civic authority-reference milestone.

This document freezes:

- the canonical v1 governance-policy object;
- the canonical v1 governance-transition subject;
- the canonical signed governance-proof object;
- source-set and provenance binding;
- electorate selection semantics;
- deterministic quorum and approval semantics;
- authority-evidence requirements;
- bootstrap and successor signer resolution;
- the conceptual governance verifier used by Epoch-1 bootstrap and successor-epoch verification.

It is subordinate to:

- `docs/CIVIC_EPOCH1_BOOTSTRAP_CONTRACT.md`;
- `docs/CIVIC_CEREMONY_RECORD_CONTRACT.md`;
- `docs/CIVIC_GOVERNING_PROFILE_CONTRACT.md`;
- `docs/CIVIC_ACCEPTED_OPERATOR_SELECTION_RECORD.md`;
- `docs/CIVIC_ACCEPTED_SIGNING_NODE_AUTHORIZATION_RECORD.md`;
- `docs/CIVIC_PARTICIPANT_AUTHORITY_STATE_RECONSTRUCTION.md`;
- `docs/HOA_GOVERNING_SOURCE_INHERITANCE.md`.

This document does not:

- claim one universal HOA election procedure;
- claim one universal voting threshold;
- define legal truth independently of governing sources;
- create a production Civic private key;
- define production key storage;
- enable production signing;
- mutate `annales`;
- define the authority-state transaction implementation.

Closure pieces 4, 5, and 6 remain separate.

## Fundamental boundary

Governance authorization is source-derived policy evaluated over exact authenticated evidence.

The generic Civic verifier must not contain hidden rules such as:

~~~text
"majority always wins"
"every participant gets one vote"
"the operator may appoint the next operator"
"the Signing Node may authorize itself"
"the HOA board always controls Civic"
"the first participant is permanently privileged"
~~~

Instead:

~~~text
governing sources
    ->
published source-derived governance policy
    ->
exact transition subject
    ->
signed governance proofs + exact evidence
    ->
deterministic policy evaluation
    ->
authorized / not authorized
~~~

The policy is authority data.

It is not executable code.

## Why a transition subject is required

The canonical ceremony record contains:

~~~text
governance_policy
governance_proof_sha256
~~~

A governance proof must attest to the exact proposed transition.

But a governance proof cannot contain:

~~~text
ceremony_record_sha256
~~~

because the ceremony hash depends on the governance-proof hashes.

That would create:

~~~text
proof contains ceremony hash
    ->
ceremony contains proof hash
    ->
content-hash cycle
~~~

The v1 solution is a derived canonical **governance transition subject**.

Conceptually:

~~~text
ceremony transition fields
    minus governance_proof_sha256
        ->
canonical governance subject
        ->
subject_sha256

governance proofs
    sign subject_sha256
        ->
proof_sha256 values

ceremony
    contains proof_sha256 values
        ->
ceremony_record_sha256
~~~

This dependency graph is acyclic.

## Canonical governance transition subject

The governance transition subject is a deterministic projection of one canonical ceremony record.

It is not separately retained as authority-required content because it can be reproduced exactly from the verified ceremony.

The exact v1 subject is:

~~~text
{
  "format": "kane-civic-governance-transition-subject",
  "version": 1,
  "crypto_profile": "kane-civic-ecdsa-p256-sha256-v1",

  "transition_kind": "bootstrap" / "successor",

  "hoa_root_id": bytes(32),
  "epoch_sequence": uint,
  "predecessor_manifest_sha256": bytes(32) / null,
  "effective_time_ms": uint,

  "governing_profile": {
    "profile_id": text,
    "profile_sha256": bytes(32),
    "source_set_sha256": bytes(32)
  },

  "participants": [
    + {
      "participant_record_sha256": bytes(32),
      "participant_key_id": bytes(32),
      "participant_public_key": bytes(65)
    }
  ],

  "operator_participant_record_sha256": bytes(32),

  "signing_node": {
    "key_id": bytes(32),
    "public_key": bytes(65)
  },

  "governance_policy": {
    "policy_id": text,
    "policy_sha256": bytes(32)
  }
}
~~~

The subject copies those values exactly from the canonical ceremony.

It omits only:

~~~text
governance_proof_sha256
~~~

from the ceremony's substantive transition data.

The exact subject identity is:

~~~text
subject_sha256 =
    SHA-256(exact deterministic-CBOR governance-transition-subject bytes)
~~~

A verifier reconstructs these bytes from the ceremony.

A stored subject object may exist as a convenience, but it is not authority-required and must not override the deterministic projection.

## Governance policy format

The exact v1 governance-policy format identifier is:

~~~text
kane-civic-governance-policy
~~~

The exact version is:

~~~text
1
~~~

The canonical policy uses the accepted deterministic-CBOR rules.

Its exact identity is:

~~~text
policy_sha256 =
    SHA-256(exact deterministic-CBOR governance-policy bytes)
~~~

The policy does not contain its own digest.

The exact v1 media type is:

~~~text
application/kane-civic-governance-policy+cbor
~~~

The exact object-index semantic role is:

~~~text
governance-policy
~~~

## Governance policy top-level schema

The canonical v1 policy contains exactly:

~~~text
{
  "format": "kane-civic-governance-policy",
  "version": 1,

  "policy_id": text,
  "source_set_sha256": bytes(32),

  "transition_kinds": [
    + "bootstrap" / "successor"
  ],

  "electorate": electorate_definition,

  "decision_rule": decision_rule,

  "authority_evidence": [
    * evidence_requirement
  ],

  "supplementary_evidence": [
    * evidence_requirement
  ],

  "provenance": provenance
}
~~~

Unknown top-level fields are invalid in v1.

Executable code, callback names, network endpoints, scripts, bytecode, dynamic imports, and opaque rule-engine expressions are forbidden.

## policy_id

Nonempty NFC text.

It is a published policy-family identifier.

It is not exact content identity.

Therefore:

~~~text
same policy_id
+
different policy_sha256
=
different exact governance-policy revision
~~~

The ceremony binds both values.

## source_set_sha256

Exactly 32 bytes.

It must equal:

~~~text
ceremony.governing_profile.source_set_sha256
~~~

and therefore the source-set identity bound by the candidate/accepted Epoch Manifest.

The governance policy may interpret only source IDs present in that exact governing source set.

A policy must not silently depend on an unlisted statute, bylaw, web page, operator memory, portal state, or external service.

If the governing basis changes, the governing source set and/or policy bytes must change explicitly.

## transition_kinds

A nonempty sorted unique array containing one or both of:

~~~text
bootstrap
successor
~~~

The ceremony `transition_kind` must occur in this array.

A bootstrap-only policy cannot authorize a successor transition.

A successor-only policy cannot authorize Epoch 1.

## Common provenance descriptor

The v1 provenance descriptor is:

~~~text
{
  "kind":
      "governing_source"
    / "derived_policy_parameter"
    / "civic_mechanism",

  "source_ids": [ * text ]
}
~~~

The array is sorted by UTF-8 byte ordering and duplicate-free.

For:

~~~text
kind = "governing_source"
kind = "derived_policy_parameter"
~~~

`source_ids` must be nonempty.

For:

~~~text
kind = "civic_mechanism"
~~~

`source_ids` may be empty.

Every named source ID must exist in the exact governing source set.

The meanings are:

### governing_source

The rule is represented as directly supplied by the named governing source or sources.

### derived_policy_parameter

The Civic mechanism is published by Civic, but the substantive parameter is derived from the named governing source or sources.

Examples can include a threshold, role, cadence, electorate qualification, or weight derived from a governing instrument.

### civic_mechanism

The rule is a Civic instrumentation mechanism rather than a claim that the governing source itself created that mechanism.

This mirrors the existing source-boundary principle:

~~~text
Civic mechanism
    !=
underlying law
~~~

## Electorate definition

The exact v1 electorate map is:

~~~text
{
  "basis":
      "candidate_participants"
    / "predecessor_participants",

  "standing_class": text,

  "membership_rule": "all_matching_standing_class",

  "weight_mode":
      "equal"
    / "explicit_uint",

  "members": [
    + {
      "participant_record_sha256": bytes(32),
      "weight": uint
    }
  ],

  "operator_must_be_elector": bool,

  "provenance": provenance
}
~~~

Unknown fields are invalid.

### basis

For a bootstrap ceremony:

~~~text
basis = "candidate_participants"
~~~

For a successor ceremony:

~~~text
basis = "predecessor_participants"
~~~

No other combination is permitted in v1.

This establishes a critical authority rule:

~~~text
new successor participants
    cannot authorize their own admission
    merely by appearing in the proposed successor ceremony
~~~

Successor governance comes from the predecessor accepted authority set.

Bootstrap has no predecessor set, so its candidate participants are evaluated under the bootstrap contract and exact governing profile before their governance proofs may count.

### standing_class

Nonempty text identifying the governing-profile standing class required for membership in this electorate.

A participant belongs in the electorate only if that participant's exact standing record:

- verifies under the applicable canonical governing profile;
- names this exact standing class;
- is current at the ceremony `effective_time_ms`.

For bootstrap, standing is evaluated against the candidate Epoch-1 context.

For successor, standing is evaluated from the predecessor participant's accepted standing context at the successor ceremony effective time.

If predecessor standing is expired at the proposed successor effective time, that participant does not satisfy the electorate class.

### membership_rule

The only v1 value is:

~~~text
all_matching_standing_class
~~~

The policy `members` array must contain exactly every participant in the applicable basis set whose verified standing satisfies `standing_class` at the ceremony effective time.

No qualifying participant may be silently omitted.

No non-qualifying participant may be silently added.

This rule prevents a policy compiler or operator from manufacturing a convenient electorate by selecting only preferred participants.

A future governance-policy version may add other source-derived membership rules if field evidence requires them.

### members

A nonempty array sorted bytewise ascending by:

~~~text
participant_record_sha256
~~~

Participant IDs are unique.

Each weight is a positive unsigned integer.

The member list is part of exact policy identity.

### weight_mode

For:

~~~text
equal
~~~

every member weight must equal exactly:

~~~text
1
~~~

For:

~~~text
explicit_uint
~~~

each member's positive integer weight is taken from the exact canonical policy.

The generic verifier does not infer a weight from unit number, property value, ownership percentage text, account balance, or another unstated source.

If weights originate from governing instruments or source-derived data, their provenance must be declared in the electorate provenance and the exact policy bytes become the reproducible compiled interpretation.

A different weight assignment produces a different policy hash.

### operator_must_be_elector

If true:

~~~text
ceremony.operator_participant_record_sha256
~~~

must occur in `electorate.members`.

If false, the operator still must satisfy all existing Epoch Manifest and participant-standing requirements, but this governance policy adds no electorate-membership requirement for the operator.

This field prevents the generic verifier from inventing the answer.

## Decision rule

The exact v1 decision-rule map is:

~~~text
{
  "quorum": threshold / null,
  "approval": threshold / null,
  "provenance": provenance
}
~~~

At least one of the following must be true:

- `approval` is non-null;
- `authority_evidence` contains at least one requirement with `min_count > 0`.

A policy may therefore describe:

- a participant-decision procedure;
- an evidence-only procedure;
- a procedure requiring both.

A null `approval` does not mean "automatic approval."

It means the policy does not require participant decision attestations and authorization instead depends on its required authority evidence.

## Governance decision values

A signed governance proof may carry one of:

~~~text
approve
reject
abstain
null
~~~

`null` means the proof is evidence-only and casts no governance decision.

For one exact transition subject and policy, one electorate participant may contribute at most one non-null decision.

Multiple evidence-only proofs by the same participant are permitted.

A participant may not inflate quorum or approval by signing the same decision repeatedly.

## Participating electorate

A participant is counted as **participating** only when there is exactly one valid non-null decision proof attributable to that electorate member for the exact subject and policy.

Evidence-only proofs do not count as participation.

The participating set therefore contains unique participant identities.

## Threshold forms

A threshold is one of the following exact maps.

### all

~~~text
{
  "kind": "all"
}
~~~

For approval, every electorate member must cast `approve`.

For quorum, every electorate member must cast a non-null decision.

### count_at_least

~~~text
{
  "kind": "count_at_least",
  "value": uint
}
~~~

`value` must be positive.

For quorum, at least `value` electorate members must participate.

For approval, at least `value` electorate members must cast `approve`.

### weight_at_least

~~~text
{
  "kind": "weight_at_least",
  "value": uint
}
~~~

`value` must be positive.

For quorum, participating electorate weight must be at least `value`.

For approval, approving electorate weight must be at least `value`.

### fraction_at_least

~~~text
{
  "kind": "fraction_at_least",
  "numerator": uint,
  "denominator": uint,
  "base":
      "electorate"
    / "participating"
}
~~~

Requirements:

~~~text
numerator > 0
denominator > 0
numerator <= denominator
~~~

No floating-point arithmetic is permitted.

For approval:

If:

~~~text
base = "electorate"
~~~

then approval succeeds exactly when:

~~~text
approving_weight * denominator
    >=
total_electorate_weight * numerator
~~~

If:

~~~text
base = "participating"
~~~

then approval succeeds exactly when:

~~~text
approving_weight * denominator
    >=
participating_weight * numerator
~~~

and participating weight must be nonzero.

For quorum, `base` MUST equal:

~~~text
electorate
~~~

and quorum succeeds exactly when:

~~~text
participating_weight * denominator
    >=
total_electorate_weight * numerator
~~~

No percentage rounding is performed.

No local floating-point or UI approximation may alter the result.

## Approval versus quorum

Quorum and approval answer different questions.

~~~text
quorum
    -> enough electorate participated?

approval
    -> enough electorate approved?
~~~

If quorum is non-null, quorum must succeed before approval can succeed.

A rejected or abstaining participant counts toward quorum but not approval.

A missing decision counts toward neither.

An evidence-only proof counts toward neither.

If approval is null, decision proofs are not required for authorization and any supplied non-null decision proof is invalid unless a future policy version explicitly permits advisory decisions.

This prevents unused votes from acquiring ambiguous semantics.

## Evidence requirement schema

The exact evidence-requirement map is:

~~~text
{
  "semantic_role": text,
  "min_count": uint,
  "max_count": uint / null,
  "media_types": [ * text ],
  "provenance": provenance
}
~~~

Requirements are sorted by UTF-8 byte ordering of `semantic_role`.

Roles are unique within each requirement array.

For authority evidence:

- `min_count` may be zero or greater;
- at least one requirement across the policy must have `min_count > 0` when `approval` is null.

For supplementary evidence:

~~~text
min_count = 0
~~~

Supplementary evidence can never be required to reconstruct or authorize the transition.

If `media_types` is empty, any nonempty media type is permitted.

Otherwise the evidence object's media type must occur in the sorted unique `media_types` array.

## Governance policy provenance

The top-level policy `provenance` describes the overall source lineage of the compiled governance policy.

More specific electorate, decision-rule, and evidence-requirement provenance descriptors explain where individual substantive parameters came from.

The generic verifier checks provenance references and exact source-set membership.

It does not pretend to independently perform unrestricted natural-language statutory or bylaw interpretation.

The canonical policy is the published machine-readable interpretation that can be inspected against its exact source bytes.

## Governance proof representation

Every v1 governance proof is a signed standalone authority object.

It is not a generic Civic history record because it must exist before the ceremony hash exists.

The exact proof payload format is:

~~~text
kane-civic-governance-proof
~~~

Version:

~~~text
1
~~~

The payload is deterministic CBOR.

The signed container is COSE_Sign1 using the accepted Civic cryptographic profile:

~~~text
COSE algorithm        ESP256 / -9
signature             P-256 / SHA-256
signature encoding    64-byte P1363 r||s
kid                   exact participant key_id
external AAD          zero-length bytes
~~~

The exact protected content type is:

~~~text
application/kane-civic-governance-proof+cbor
~~~

The exact stored-object media type is:

~~~text
application/kane-civic-governance-proof+cose
~~~

The exact object-index semantic role is:

~~~text
governance-proof
~~~

The proof identity used by the ceremony is:

~~~text
governance_proof_sha256 =
    SHA-256(exact complete COSE_Sign1 proof bytes)
~~~

A semantically equivalent proof payload with a different valid signature is a different proof object.

## Governance proof payload schema

The exact v1 payload contains:

~~~text
{
  "format": "kane-civic-governance-proof",
  "version": 1,
  "crypto_profile": "kane-civic-ecdsa-p256-sha256-v1",

  "subject_sha256": bytes(32),

  "governance_policy": {
    "policy_id": text,
    "policy_sha256": bytes(32)
  },

  "signer": {
    "participant_record_sha256": bytes(32),
    "participant_key_id": bytes(32)
  },

  "decision":
      "approve"
    / "reject"
    / "abstain"
    / null,

  "authority_evidence": [
    * evidence_descriptor
  ],

  "supplementary_evidence": [
    * evidence_descriptor
  ]
}
~~~

Unknown fields are invalid in v1.

Private key material is forbidden.

## Governance proof evidence descriptor

The exact evidence descriptor is:

~~~text
{
  "sha256": bytes(32),
  "byte_length": uint,
  "media_type": text,
  "semantic_role": text
}
~~~

Each evidence array is sorted bytewise ascending by `sha256` and duplicate-free.

A single evidence SHA-256 must not appear more than once in the same proof.

If the same evidence object appears in multiple governance proofs, its descriptor metadata must be identical everywhere.

## Proof subject binding

Every proof must satisfy:

~~~text
proof.subject_sha256
    == SHA-256(exact canonical governance-transition-subject bytes)
~~~

This binds the proof to:

- transition kind;
- HOA root;
- epoch number;
- predecessor identity when applicable;
- effective time;
- governing-profile identity;
- candidate participant identities and keys;
- proposed operator;
- proposed Signing Node key;
- exact governance policy.

Changing any of those values changes the subject hash and invalidates reuse of the proof for the changed transition.

The proof does not contain the ceremony hash.

## Proof policy binding

The proof payload must contain:

~~~text
governance_policy.policy_id
governance_policy.policy_sha256
~~~

exactly equal to the ceremony descriptor.

The exact policy bytes must verify to that hash.

A proof created under another policy revision cannot be silently reused.

## Proof signer resolution

The proof signer must be a member of the exact canonical policy electorate.

The signature key is resolved differently by transition kind.

### Bootstrap

For:

~~~text
transition_kind = "bootstrap"
~~~

the signer key is resolved from the ceremony candidate participant projection.

The signer:

~~~text
participant_record_sha256
participant_key_id
~~~

must exactly match one policy electorate member and one ceremony participant.

The public key used to verify the proof is the candidate participant public key committed by the ceremony.

This signature proves attribution by that candidate key.

It does not by itself admit the participant or authorize bootstrap.

### Successor

For:

~~~text
transition_kind = "successor"
~~~

the signer key is resolved from the **verified predecessor Epoch Manifest** participant descriptor.

The signer participant must be one exact predecessor electorate member.

The proof must use that participant's predecessor-epoch key:

~~~text
proof.signer.participant_key_id
    == predecessor participant.participant_key_id
~~~

The successor candidate participant key is not used to authorize the transition.

Therefore a newly added participant cannot authorize their own addition merely by signing with a newly generated successor key.

## Proof signature meaning

A valid proof signature establishes:

~~~text
this participant key signed
this exact governance-proof payload
for this exact transition subject
under this exact governance policy
~~~

It does not independently establish:

- legal truth;
- factual truth of referenced evidence;
- quorum;
- approval threshold;
- source-derived sufficiency;
- authority of a new Signing Node;
- validity of the Epoch Manifest.

Those are higher-level verifier results.

## Authority evidence

Every governance proof may reference authority evidence.

Authority evidence contributes to governance-policy evidence requirements.

Every authority-evidence descriptor must resolve to exact bytes through the candidate/accepted Epoch Manifest `object_index`.

The verifier requires equality of:

- SHA-256;
- byte length;
- media type;
- semantic role.

The exact bytes must be locally available from the authority-state bundle.

Missing authority evidence fails governance verification.

The generic verifier need not parse every arbitrary external evidence format.

Instead, it verifies exact bytes, declared role/media constraints, policy provenance, and any separately standardized evidence type that Civic explicitly knows how to verify.

This preserves:

~~~text
evidence identity
    !=
universal legal interpretation
~~~

## Supplementary evidence

Supplementary evidence may be referenced for diagnostics, explanation, corroboration, or later review.

It:

- must conform to policy-permitted supplementary roles;
- may be absent from a minimal authority-state replica;
- does not satisfy an authority-evidence minimum;
- cannot be required for governance authorization;
- must not become a hidden reconstruction dependency.

A policy requiring an object for authorization must classify it as authority evidence.

## Evidence aggregation

Governance evidence requirements are evaluated over the union of evidence descriptors from all verified proof objects.

Aggregation is by exact evidence SHA-256.

The same exact evidence object referenced by multiple proofs counts once.

If two proofs describe the same SHA-256 with conflicting byte length, media type, or semantic role, governance verification fails.

This prevents duplicated references from inflating a minimum evidence count.

## Evidence-role validation

For each aggregated authority-evidence object:

- its `semantic_role` must be declared by one policy authority-evidence requirement;
- its media type must satisfy that role's permitted media types.

For each requirement:

~~~text
unique matching object count >= min_count
~~~

and, when `max_count` is non-null:

~~~text
unique matching object count <= max_count
~~~

Undeclared authority-evidence roles fail verification.

Supplementary evidence is evaluated separately against supplementary requirements.

## Proof-set binding

The exact proof identities from the ceremony:

~~~text
ceremony.governance_proof_sha256
~~~

must satisfy all of:

- nonempty;
- sorted bytewise ascending;
- duplicate-free;
- every proof object resolves to exact bytes;
- SHA-256 of exact proof bytes equals the listed digest;
- object-index descriptor media type is the governance-proof media type;
- object-index semantic role is `governance-proof`;
- every proof payload binds the exact subject;
- every proof payload binds the exact governance policy;
- every signature verifies under the required electorate key basis.

No extra proof object may silently influence the result.

A stored proof not listed by the ceremony is irrelevant to authorization of that ceremony.

## Decision uniqueness

For one exact ceremony subject and policy:

~~~text
one electorate participant
    -> at most one non-null governance decision
~~~

If two valid proofs from the same participant contain non-null decisions, governance verification fails even if both decisions are identical.

This preserves one deterministic ballot/decision contribution per electorate member.

Multiple evidence-only proofs from the same participant remain permitted.

## Electorate reconstruction

Before evaluating quorum or approval, the verifier independently reconstructs the expected electorate from:

~~~text
policy.electorate.basis
policy.electorate.standing_class
ceremony effective_time
candidate or predecessor authority state
accepted participant-standing verifier
~~~

It then requires exact equality between:

~~~text
reconstructed eligible participant IDs
~~~

and:

~~~text
policy.electorate.members[].participant_record_sha256
~~~

For `weight_mode = equal`, every policy weight must be 1.

For `weight_mode = explicit_uint`, the exact policy weights are used.

The generic verifier does not invent or normalize different weights.

## Bootstrap electorate reconstruction

For bootstrap:

1. take the ceremony candidate participant set;
2. resolve each candidate participant's exact standing record from the candidate Epoch Manifest;
3. verify standing against the canonical governing profile;
4. evaluate currentness at `ceremony.effective_time_ms`;
5. select exactly those whose standing class equals the policy electorate standing class;
6. require that exact set to equal the policy member set.

A candidate proof signature can count only after that candidate participant's standing verifies.

This prevents a generated key from becoming an elector merely because it signed a proof.

## Successor electorate reconstruction

For a successor:

1. begin with the verified predecessor Epoch Manifest participant set;
2. resolve each predecessor participant's accepted standing record under the predecessor authority context;
3. evaluate that standing at the successor ceremony `effective_time_ms`;
4. select exactly those whose standing class equals the policy electorate standing class;
5. require that exact set to equal the policy member set.

The successor candidate participant set is not the source of the electorate.

This preserves the continuity rule:

~~~text
current accepted authority
    authorizes
proposed successor authority
~~~

rather than:

~~~text
proposed successor authority
    authorizes itself
~~~

## Quorum computation

Let:

~~~text
E = complete electorate member set
P = unique members with one non-null decision proof
A = members in P whose decision is "approve"
R = members in P whose decision is "reject"
B = members in P whose decision is "abstain"
~~~

Then:

~~~text
P = A union R union B
A, R, B are pairwise disjoint
~~~

Let:

~~~text
count(S)  = number of members in set S
weight(S) = sum of exact policy weights for members in S
~~~

If policy quorum is null, no separate quorum test is applied.

If non-null, evaluate it exactly using the threshold rules in this contract.

Failure of quorum fails authorization.

## Approval computation

If policy approval is non-null, evaluate it over the same exact sets.

Only:

~~~text
decision = "approve"
~~~

contributes to approving count/weight.

Reject and abstain do not approve.

If approval fails, authorization fails.

If approval is null, any non-null decision proof is invalid in v1 and authorization is determined only by required authority evidence plus all other policy conditions.

## Exact arithmetic

All counts and weights use unsigned integers.

Fraction comparisons use cross multiplication.

A verifier must not use:

- binary floating point;
- decimal rounding;
- percentages rounded for display;
- local UI approximations.

Overflow must be detected rather than wrapped.

Implementations may use arbitrary-precision integers internally.

## Operator constraint

After electorate reconstruction, if:

~~~text
policy.electorate.operator_must_be_elector = true
~~~

the ceremony operator must be a member of the exact reconstructed electorate.

If false, no additional electorate-membership rule is imposed here.

The operator must still satisfy all existing manifest, participant-standing, operator-selection, and source-derived constraints.

## Policy object retention and binding

The ceremony contains:

~~~text
governance_policy = {
  "policy_id": text,
  "policy_sha256": bytes(32)
}
~~~

The exact policy bytes must:

- hash to `policy_sha256`;
- decode as deterministic v1 policy CBOR;
- carry the same `policy_id`;
- carry the same source-set hash as the ceremony governing profile.

The Epoch Manifest `object_index` must contain exactly one descriptor for the policy:

~~~text
sha256 = policy_sha256
media_type = "application/kane-civic-governance-policy+cbor"
semantic_role = "governance-policy"
byte_length = len(exact policy bytes)
~~~

If inline bytes are present, they must equal the exact verified policy bytes.

The policy is authority-required reconstruction material.

## Governance proof object retention

Every proof hash in the ceremony must have exactly one Epoch Manifest object-index descriptor:

~~~text
sha256 = governance_proof_sha256
media_type = "application/kane-civic-governance-proof+cose"
semantic_role = "governance-proof"
byte_length = len(exact proof bytes)
~~~

Proof bytes are authority-required reconstruction material.

A URI, database row, UI export, or textual summary is not a substitute.

## Governance source binding

The policy's `source_set_sha256` must equal the governing profile source-set identity.

Every source ID referenced by any policy provenance descriptor must exist in the candidate/accepted Epoch Manifest `governing_sources`.

The exact governing source bytes required by those descriptors must be available as authority-required content under the existing source/object rules.

A successful governance-policy evaluation therefore remains traceable to:

~~~text
exact transition
+
exact policy
+
exact governing source set
+
exact proof objects
+
exact authority evidence
~~~

## Relationship to operator-selection record

The accepted operator-selection record may contain:

~~~text
selection_proof_sha256
~~~

as a subset of the ceremony governance-proof set.

After complete governance verification, every selection-proof hash must identify a verified proof from the same exact ceremony proof set.

The subset is explanatory/type-specific provenance.

It does not create an independent weaker threshold.

The governing transition is authorized or rejected by the canonical governance-policy verifier over the complete ceremony proof set.

Therefore:

~~~text
selection proof subset
    !=
separate governance universe
~~~

## Relationship to Signing Node authorization record

The accepted Signing Node authorization record requires:

~~~text
record.body.governance_proof_sha256
    == manifest.ceremony.governance_proof_sha256
~~~

Under this contract that means the Signing Node authorization record names the exact complete proof set that was evaluated for the ceremony.

The node signature remains proof of possession.

Governance authorization comes from the successful canonical governance-policy evaluation.

## Relationship to participant admission

For bootstrap, candidate participants may be members of the bootstrap electorate only after their standing verifies at the ceremony effective time.

For successor transitions, newly proposed successor participants do not join the governance electorate merely by appearing in the successor ceremony.

Their admission is one fact inside the exact transition subject approved under predecessor authority.

This prevents circular participant admission.

## Relationship to participant key rotation

For successor transitions, governance proofs are verified using predecessor participant keys.

The ceremony separately commits to successor participant keys.

Therefore the same participant may:

~~~text
authorize successor transition with predecessor key
        +
receive new successor key in the proposed ceremony
~~~

without the successor key authorizing itself.

This cleanly separates:

~~~text
authority to approve transition
    from
credential created by transition
~~~

## Evidence-only governance

A source-derived policy may define:

~~~text
approval = null
~~~

when participant decision attestations are not the governing requirement.

In that case:

- at least one authority-evidence requirement must have `min_count > 0`;
- every governance proof must have `decision = null`;
- proof signers still provide attribution for the exact evidence package;
- source-derived authority comes from satisfying the exact evidence requirements under the policy, not from the signer merely signing.

This supports procedures whose decisive authority is documentary or otherwise evidenced rather than ballot-based.

## Decision-plus-evidence governance

A policy may require both:

~~~text
approval threshold
+
authority evidence
~~~

Both must succeed.

A qualifying vote without required documentary evidence fails.

Required documentary evidence without the required vote fails.

This permits the canonical policy to express source-derived combinations without hiding the conjunction in code.

## What v1 deliberately does not express

Governance Policy v1 does not attempt to encode every conceivable parliamentary, corporate, statutory, judicial, or contractual procedure.

It does not natively model:

- ranked-choice voting;
- cumulative voting;
- proxy chains;
- secret-ballot anonymity;
- delegated voting graphs;
- conditional veto hierarchies;
- multi-chamber approval;
- temporal notice-window calculation;
- complex meeting-order rules;
- natural-language legal interpretation;
- arbitrary executable predicates.

If a real governing process requires semantics outside v1, the implementation must not approximate them silently.

The correct response is a new reviewed policy version or additional canonical evidence/verifier contract.

This is preferable to embedding an opaque general-purpose rule engine.

## Legal/source interpretation boundary

A successful v1 governance verification means:

~~~text
the exact retained evidence and signed participant proofs
satisfy the exact published canonical governance policy
bound to the exact governing-source set
for the exact transition subject
~~~

It does not mean:

~~~text
a court has adjudicated every disputed legal interpretation
~~~

The source-derived policy remains inspectable against source text.

Disputes or contradictory evidence remain Diagnostics inputs.

## Bootstrap verification integration

For Epoch 1, the bootstrap verifier must:

1. verify exact governance-policy bytes;
2. verify policy source-set and provenance references;
3. derive the exact governance transition subject from the ceremony;
4. verify each proof object and candidate-participant signature;
5. reconstruct the bootstrap electorate from candidate standing at the ceremony effective time;
6. require exact equality with policy electorate members;
7. verify all authority evidence;
8. evaluate quorum if required;
9. evaluate approval if required;
10. enforce operator electorate membership if configured;
11. return success only when every policy condition succeeds.

Only then may governance be treated as sufficient for the bootstrap bundle.

## Successor verification integration

For a successor epoch, the governance verifier additionally requires the verified predecessor authority context.

It must:

1. verify predecessor manifest identity and sequence relation;
2. verify exact governance-policy bytes;
3. derive the exact transition subject;
4. reconstruct the electorate from predecessor participants and standing at successor effective time;
5. verify governance proofs under predecessor participant keys;
6. verify all authority evidence;
7. evaluate quorum and approval;
8. verify operator electorate constraint if configured;
9. return success only when every policy condition succeeds.

The successor candidate state is the decision subject, not the source of voting authority.

## Conceptual verifier interface

The reference implementation should expose semantics equivalent to:

~~~text
verified_policy =
    verify_governance_policy(
        exact_policy_bytes,
        governing_sources
    )

subject =
    canonical_governance_transition_subject(
        verified_ceremony
    )

verified_governance =
    verify_governance_transition(
        policy = verified_policy,
        ceremony = verified_ceremony,
        governance_proof_bytes = exact listed proofs,
        candidate_manifest = candidate_or_accepted_manifest,
        predecessor_manifest = null_or_verified_predecessor,
        load_object = authority_object_loader
    )
~~~

The verifier result should expose at least:

- policy ID/hash;
- subject hash;
- transition kind;
- electorate participant IDs and weights;
- participating participant IDs;
- approving participant IDs;
- rejecting participant IDs;
- abstaining participant IDs;
- total electorate weight;
- participating weight;
- approving weight;
- quorum result;
- approval result;
- verified authority-evidence identities;
- governance-proof identities.

It must not expose a successful result if any required condition failed.

## Deterministic failure conditions

Governance verification fails if any applicable condition is false, including:

- policy bytes are non-deterministic or malformed;
- policy hash or policy ID mismatches ceremony;
- policy source-set hash mismatches governing profile;
- policy does not permit ceremony transition kind;
- provenance references an unknown source;
- electorate basis is invalid for transition kind;
- electorate standing class cannot be resolved;
- reconstructed electorate differs from policy member list;
- electorate member weight is invalid;
- equal-weight policy contains a weight other than 1;
- operator is required to be an elector but is not;
- proof set is empty;
- proof hash, length, media type, semantic role, or object-index binding fails;
- proof CBOR/COSE is malformed;
- proof subject hash mismatches;
- proof policy descriptor mismatches;
- proof signer is not in the electorate;
- proof signer key does not match the required bootstrap/successor authority basis;
- proof signature fails;
- one participant supplies multiple non-null decisions;
- non-null decision exists under an evidence-only policy;
- authority evidence is missing or corrupt;
- authority evidence has an undeclared role;
- authority-evidence count or media-type rule fails;
- supplementary evidence is used to satisfy an authority requirement;
- quorum fails;
- approval fails;
- integer arithmetic would overflow a bounded implementation without safe handling;
- predecessor context is absent or wrong for a successor transition.

No failure is repaired heuristically.

## Divergence semantics

Two validly signed governance proofs may disagree.

That disagreement is not corruption.

For example:

~~~text
participant A -> approve
participant B -> reject
~~~

Both proofs may be cryptographically valid.

The canonical policy determines whether the resulting set satisfies quorum and approval.

Likewise, competing candidate policies or ceremony subjects may exist.

Only the exact policy and proof set committed by the accepted ceremony/manifest lineage can authorize that lineage.

Other candidate material may be preserved as Diagnostics evidence.

## Privacy and disclosure boundary

Governance proof objects are authority material and must be replicable to current participants when required for complete authority-state reconstruction.

Therefore raw private evidence should not be embedded casually inside governance proof payloads.

The proof should normally carry exact evidence descriptors while the authority-required evidence object is retained under the applicable disclosure/storage rules.

If an evidence object's privacy requirements are incompatible with replication to every current participant, that object cannot silently be made authority-required under the one-participant reconstruction baseline.

A future privacy-preserving evidence mechanism would require an explicit new authority contract.

## No central governance service

Verification must be possible from retained authority-state content.

The policy and proof design must not require:

- an online Kane server;
- a proprietary portal;
- a cloud voting service;
- a remote signer;
- a central identity provider;
- live access to the original operator;
- continued availability of the original project.

Optional services may transport or mirror objects.

They do not become governance authority.

## Production boundary

This contract freezes authority semantics only.

It does not define:

- production random-number generation;
- private-key file format;
- signing process isolation;
- key backup;
- key rotation implementation;
- transaction staging;
- crash consistency;
- filesystem paths;
- systemd services;
- LXD layout;
- `annales` deployment.

Those belong to closure pieces 4 through 6 and the later Annales project.

## Closure status

After this document:

~~~text
1. Epoch-1 bootstrap contract
       architecture frozen

2. canonical ceremony-record contract
       architecture frozen

3. governance policy/proof/verifier contract
       architecture frozen by this document

4. production signing/key-lifecycle contract
       next

5. authority-state transaction/composition contract
       pending

6. Signing Node conformance/deployment boundary
       pending
~~~

The next implementation work inside Kane Fabric should encode and test these piece-3 canonical formats and semantic rules before production signing is designed.

## Decision summary

The v1 governance authorization path is:

~~~text
exact governing sources
        ↓
canonical source-derived governance policy
        ↓
canonical transition subject
        ↓
subject_sha256
        ↓
participant-signed governance proofs
        +
exact authority evidence
        ↓
deterministic electorate reconstruction
        ↓
deterministic quorum/approval/evidence evaluation
        ↓
verified governance transition
        ↓
canonical ceremony commits exact proof set
        ↓
Epoch Manifest commits ceremony + accepted authority records
~~~

The core continuity rule is:

~~~text
bootstrap:
    candidate participant standing
        -> candidate electorate authority basis

successor:
    predecessor accepted participant standing
        -> predecessor electorate authority basis
        -> proposed successor state
~~~

The core semantic rule is:

~~~text
valid signatures
    !=
governance authorization

governance authorization
    =
exact source-bound policy
+
exact transition subject
+
exact proof set
+
exact evidence
+
deterministic policy satisfaction
~~~

This closes the governance-proof sufficiency gap without creating a hidden universal voting rule or a self-authorizing Signing Node.
