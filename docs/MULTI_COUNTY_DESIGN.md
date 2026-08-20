# Multi-County Design Horizon

## Purpose

Kane County, Illinois is the reference deployment for Kane Fabric. It is not intended to become the conceptual namespace of the software.

Milestones 1 and 2 proved that Kane County's authoritative geographic pipeline can be reconstructed from declared inputs and operated through Kane Fabric-owned geographic contracts. That proof remains a permanent project requirement, but reconstruction is no longer the principal development objective.

The forward design objective is broader:

> New Kane Fabric contracts, namespaces, package identities, database identifiers, and reusable implementation should not unnecessarily bind the architecture to Kane County when the underlying concept is applicable to another U.S. county or county-equivalent jurisdiction.

This is a design horizon, not a commitment to implement every U.S. county now.

## Scope

The project is not starting a nationwide deployment program as part of the current milestone.

This document does not require:

- second-county implementation work;
- placeholder counties;
- speculative adapters;
- synthetic county fixtures solely to demonstrate genericity;
- a national registry service;
- redesign of proven Kane-specific code merely to remove the word `kane`;
- support for every variation in U.S. local-government geography before a concrete need exists.

Kane County remains the only required operational reference deployment until a later milestone or explicit requirement says otherwise.

## Generic concepts versus county facts

The governing rule is:

> Generic where the concept is generic; jurisdiction-specific where the fact is jurisdiction-specific.

Reusable concepts should use reusable names. Examples include:

- jurisdiction identity;
- dataset identity;
- source identity;
- release identity;
- candidate identity;
- substrate identity;
- subscription identity;
- generation identity;
- object hash;
- package manifest;
- accepted and candidate state;
- provenance;
- promotion and rollback.

County-specific facts should remain in county/source profiles, county configuration, county evidence, or clearly county-specific entry points. Examples include:

- Kane County source URLs;
- Kane County source-layer names;
- Kane-specific field mappings;
- source quirks and declared exclusions;
- accepted Kane release identities;
- Kane County filesystem deployment paths where those paths are intentionally deployment-specific.

## Namespace discipline

From Milestone 3 forward, every new durable identifier or namespace should be reviewed for accidental Kane coupling.

A reusable protocol field should prefer concepts such as:

```text
jurisdiction_id
dataset_id
source_id
release_id
substrate_id
subscription_id
generation_id
object_sha256
```

rather than embedding `kane` in a field or token whose semantics are actually generic.

This rule does not require renaming existing Kane-specific commands, files, test fixtures, or source profiles that accurately describe Kane County. Existing names may remain when they are deployment entry points or historical release evidence.

The important boundary is the durable contract. New browser/package/database contracts should not require Kane County to be implicit.

## Jurisdiction identity

Human-readable names are attributes, not sufficient durable identities.

A future multi-jurisdiction deployment must be able to distinguish jurisdictions whose naming conventions differ and must tolerate display-name changes without changing every downstream identity.

For U.S. deployments, authoritative geographic codes such as Census/FIPS-derived identifiers are likely candidates for durable jurisdiction identity where appropriate. This document does not freeze a specific wire format before Milestone 3 defines the relevant package contract.

The internal model should not assume that every county-equivalent jurisdiction uses the English word `county`. The design horizon includes U.S. county-equivalent jurisdictions such as parishes, boroughs/census areas, and independent cities where they satisfy the same geographic role.

## Source diversity

Nationwide design must not assume that every jurisdiction publishes equivalent data through the same vendor, schema, endpoint type, object identifier, update schedule, or quality policy.

The reusable Fabric core should know what a dataset contract requires. A county/source profile should know how a particular jurisdiction satisfies that contract.

For example, the generic system may know that a road dataset has:

- a source identity;
- acquisition evidence;
- accepted and candidate releases;
- deterministic comparison rules;
- declared exclusions where required;
- provenance.

The Kane County road profile may separately know the Kane-specific endpoint, fields, object-ID behavior, and missing-geometry exclusion.

This separation is essential. A second jurisdiction should primarily require new profile/configuration work where its source can satisfy an existing contract, rather than edits throughout the geographic core.

## Package and manifest implications

Milestone 3 begins defining durable substrate package and manifest identities. Those contracts must carry enough explicit jurisdiction identity that a browser, cache, edge node, or later multi-county operator does not need an out-of-band assumption that the package belongs to Kane County.

At minimum, package design should keep these concepts distinguishable:

```text
jurisdiction
logical dataset
accepted source/release lineage
compiled generation
immutable object identity
```

Content hashes should identify content. Human-readable labels should not be overloaded as global primary keys.

## Database implications

New database tokens and schema concepts should avoid unnecessary Kane-specific naming when the stored concept is geographically generic.

However, the project should not churn the proven Milestone 2 geographic core solely for cosmetic genericity. Renaming or migration is justified when an existing Kane-specific name would cross a new generic boundary, create ambiguity, or prevent a second jurisdiction from being represented correctly.

Behavior preservation remains more important than stylistic renaming.

## Code comments and review

Where the distinction is not obvious, new code should state whether a behavior is:

- generic Kane Fabric behavior;
- U.S.-jurisdiction policy;
- Kane County source policy;
- deployment-specific infrastructure policy.

Comments should explain the ownership boundary, not speculate about unimplemented counties.

Code review for new durable contracts should ask:

1. Is this concept actually specific to Kane County?
2. If not, have we encoded `kane` or a Kane-only assumption unnecessarily?
3. Is jurisdiction identity explicit where it needs to survive packaging, caching, or distribution?
4. Is a source-specific rule being mistaken for a generic geographic rule?
5. Can Kane remain the sole implementation without creating fake generalization machinery?

## Relationship to reconstructability

Reconstructability remains mandatory.

The project has already proven the foundational Kane County reconstruction chain and extracted the geographic core. Future work must preserve that ability and must not introduce hidden state that makes a Fabric deployment dependent on copying an existing machine.

The emphasis changes from proving reconstruction as the primary project objective to using the proven reconstructable architecture as the foundation for portable public infrastructure.

## Relationship to civic infrastructure

Multi-county portability and public-infrastructure independence reinforce each other.

A county should not require permission from the original Kane deployment to become a Fabric deployment. A future operator should be able to obtain the public software, provide the jurisdiction/source contracts and accepted evidence required by the system, and operate independently.

The governing public-infrastructure principles are documented in `docs/CIVIC_INFRASTRUCTURE_PRINCIPLES.md`.

## Current rule

Kane County is the reference implementation.

Do not build the nation now.

Do not design new durable contracts as though Kane County is the nation.
