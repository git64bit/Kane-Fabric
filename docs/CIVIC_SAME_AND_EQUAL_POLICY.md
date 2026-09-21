# Civic Same-and-Equal Equivalence Policy

## Status

Architecture primitive. Documentation only.

This document defines how `Same and Equal` is evaluated from Civic Relationship Tuples under a published Affordance Authority Contract.

It is not a universal identity rule, legal adjudication rule, database query implementation, access-control engine, or cryptographic format.

## Purpose

`Same and Equal` means that two issued civic relationships belong to the same published equivalence class for a specific civic purpose.

It does **not** mean:

- the two people are identical;
- they have every civic right/status in common;
- they live at the same address;
- they own the same property;
- they are equal under every possible policy;
- one institution has certified their global legal status.

The relation is always scoped by a named equivalence policy.

## Inputs

An evaluation consumes:

~~~text
Ra  = Civic Relationship Tuple for participant A
Rb  = Civic Relationship Tuple for participant B
E   = published Same-and-Equal policy
t   = evaluation time/context where required
~~~

The two tuples must be interpreted under resolvable Affordance Authority Contract identities.

## Policy form

The first logical policy form is:

~~~text
E = (
  policy_identity,
  purpose,
  applicability,
  relation_rule,
  domain_rule,
  role_rule,
  state_rule,
  target_rule,
  qualification_rule,
  validity_rule,
  contract_compatibility_rule,
  equivalence_key_rule
)
~~~

Exact serialization is deferred.

## 1. policy_identity

The rule must have a stable version/content identity.

An evaluation is meaningless if the verifier cannot determine which exact equality rule was applied.

## 2. purpose

`purpose` states what civic comparison the rule is making.

Examples:

- current condominium unit-owner standing within one association;
- current HOA-member standing within one association and role class;
- current county-resident standing within one county;
- property-taxpayer standing for one parcel class;
- another published diagnostic comparison.

The same two participants may be Same and Equal for one purpose and not for another.

## 3. applicability

`applicability` defines which tuples the policy is capable of comparing.

A tuple outside the policy's declared relation/family/domain class is not automatically unequal; it may simply be **not comparable** under that policy.

## 4. relation_rule

The relation rule identifies which relation identifiers must match or how explicitly compatible relations are normalized for this comparison.

No cross-relation equivalence is implied unless published.

## 5. domain_rule

The domain rule identifies which domain dimensions define the comparison class.

For an HOA policy, the specific association identity is normally material.

Therefore two current unit owners in different HOAs are not Same and Equal under a policy whose class key includes association identity.

## 6. role_rule

The role rule identifies which role/subtype dimensions must match.

A current unit owner and a service provider may both have an HOA-related affected status but are not Same and Equal under a unit-owner policy.

## 7. state_rule

The state rule identifies which temporal states are members of the class.

A current HOA member and a former HOA member are not Same and Equal under a policy that distinguishes current from former standing.

## 8. target_rule

The target rule determines whether target identity is:

- required to match;
- intentionally ignored;
- normalized to a broader target class;
- used only as an input to derive domain.

This field is essential.

Two unit owners in the same HOA normally own different units. A current-unit-owner equality policy may therefore ignore unit target identity while still requiring the same association domain.

For another policy, such as affectedness tied to one specific parcel, target identity may be required.

## 9. qualification_rule

The policy states whether qualification method/evidence class must match.

Possible approaches include:

- any qualification accepted under the same relation policy is equivalent;
- only specified evidence classes are equivalent;
- different evidence paths are comparable but produce `INDETERMINATE` pending review;
- qualification method is irrelevant after a relation has been validly issued.

The authority contract must choose deliberately; the implementation must not invent the answer.

## 10. validity_rule

The rule defines the evaluation-time requirement.

For current-state policies, both tuples normally must be current at the evaluation time.

Historical Same-and-Equal analysis may use a historical evaluation time rather than present state.

## 11. contract_compatibility_rule

Two tuples may have been issued under different contract versions.

The equivalence policy must say whether:

- only the exact same contract version is comparable;
- a declared compatibility class of contract versions is comparable;
- a translation/migration rule exists;
- otherwise the result is indeterminate or not comparable.

No silent cross-version normalization is allowed.

## 12. equivalence_key_rule

Within its applicable class, policy `E` derives a canonical comparison key:

~~~text
K_E(R, t) = canonical selected dimensions of R under E at time t
~~~

Then:

~~~text
SAME_AND_EQUAL
    when both tuples are applicable, sufficiently known, valid for t,
    and K_E(Ra,t) == K_E(Rb,t)
~~~

This key-based model makes Same and Equal an actual equivalence-class concept rather than an arbitrary pairwise opinion.

## Evaluation results

Evaluation returns one of four diagnostic results:

### SAME_AND_EQUAL

Both tuples are applicable and sufficiently known, and their canonical equivalence keys match.

### NOT_SAME_AND_EQUAL

Both tuples are applicable and sufficiently known, but one or more policy-selected dimensions differ.

Examples:

- same unit-owner relation, different HOA domain;
- same HOA domain, current versus former state;
- same HOA relationship, unit-owner role versus service-provider role where role is material.

### NOT_COMPARABLE

At least one tuple is outside the declared scope of the policy.

Example:

Comparing a `COURT_LINKED_PARTY` tuple to a `CONDO_UNIT_OWNER` tuple under a current-unit-owner policy.

This is different from saying the people are unequal.

### INDETERMINATE

The policy applies in principle, but required information cannot be resolved confidently.

Examples:

- missing domain identity;
- unresolved policy version;
- ambiguous role;
- unknown current/former state;
- insufficient qualification context where the policy requires it.

Indeterminate must not be silently converted to NOT_SAME_AND_EQUAL.

## Equivalence properties

For tuples that are applicable, sufficiently known, and evaluated under the same policy and evaluation context, `Same and Equal` is intended to define an equivalence class.

Therefore the key rule should preserve:

- reflexivity: a valid tuple is Same and Equal to itself;
- symmetry: if A is Same and Equal to B, B is Same and Equal to A;
- transitivity: if A and B share the same class key, and B and C share the same class key, then A and C share it as well.

Policies that cannot preserve these properties should be described as a different diagnostic comparison, not as a Same-and-Equal policy.

## Example: current condominium owners in one HOA

Policy purpose:

`CURRENT_CONDO_UNIT_OWNER_WITHIN_ASSOCIATION`

Illustrative selected dimensions:

~~~text
relation  = CONDO_UNIT_OWNER
domain    = specific association identity
role      = unit_owner
state     = current
target    = ignored for equality
policy    = compatible contract class
~~~

Participant A:

~~~text
target = Unit 211
domain = Association X
state  = current
~~~

Participant B:

~~~text
target = Unit 311
domain = Association X
state  = current
~~~

Result:

`SAME_AND_EQUAL`

The differing unit targets do not matter for this policy.

## Example: same role, different HOA

Participant C:

~~~text
target = Unit 8
domain = Association Y
state  = current
~~~

Compared with A under the same policy:

`NOT_SAME_AND_EQUAL`

because association domain is part of the equivalence key.

## Example: current versus former

Participant D:

~~~text
relation = HOA_MEMBER
domain   = Association X
role     = unit_owner
state    = former
~~~

A current-member policy that includes state in the key returns:

`NOT_SAME_AND_EQUAL`

## Example: unrelated civic relationships

Comparing A's `CONDO_UNIT_OWNER` tuple to another person's `PUBLIC_RECORDS_REQUESTER` tuple under the condominium-owner policy returns:

`NOT_COMPARABLE`

## Same-and-Equal does not automatically grant an action

An equivalence result is a civic relationship fact derived under a policy.

A diagnostic surface may use that result as one qualification input, but the surface's published binding decides whether the participant may Read, Write, Speak, Submit Evidence, Publish, or perform another action.

Therefore:

~~~text
Same and Equal != universal authorization
~~~

## Cross-root comparison

Because multiple county/root profiles may exist, cross-root Same-and-Equal requires explicit contract compatibility.

Recognition by one root is not automatically recognition by another.

A verifier should be able to state:

~~~text
which two tuple identities were compared
which contract identities interpreted them
which equivalence policy was used
which evaluation time/context was used
which result was produced
~~~

That record itself can later become diagnostic evidence.

## Future Witness Attestation

A future witness record may identify the relationship tuple and Same-and-Equal class relevant to the witness context at the time the appliance assembled the record.

This can help answer questions such as whether multiple device-owning participants were acting from equivalent civic standing within the same bounded institution.

Witness Attestation remains future scope; no attestation behavior is frozen here.

## Next boundary

The next architecture object is the canonical Civic Issuance Record that wraps one or more relationship tuples with issuer, policy, appliance, sequence, supersession, and signature provenance.

No implementation code should precede that record design.
