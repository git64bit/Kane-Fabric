# Multi-County Design Horizon

## Purpose

Kane County, Illinois is the reference deployment for Kane Fabric. It is not intended to become the conceptual namespace of the software.

Milestones 1 through 3 proved that Kane County's authoritative geographic pipeline can be reconstructed, operated through Kane Fabric-owned contracts, compiled into a deterministic public substrate, and consumed selectively by a browser. Those proofs remain permanent project requirements, but reconstruction and county-wide substrate compilation are no longer the principal development objective.

The forward design objective is broader:

> New Kane Fabric contracts, namespaces, package identities, geographic partition identities, subscription identities, database identifiers, and reusable implementation should not unnecessarily bind the architecture to Kane County when the underlying concept is applicable to another U.S. county or county-equivalent jurisdiction.

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

## Generic concepts versus jurisdiction facts

The governing rule is:

> Generic where the concept is generic; jurisdiction-specific where the fact is jurisdiction-specific.

Reusable concepts should use reusable names. Examples include:

- jurisdiction identity;
- dataset identity;
- source identity;
- release identity;
- candidate identity;
- substrate identity;
- partition identity;
- partition scope class;
- subscription identity;
- generation identity;
- object hash;
- package/partition/subscription manifest;
- accepted and candidate state;
- provenance;
- promotion and rollback.

Jurisdiction-specific facts should remain in county/source profiles, county configuration, accepted evidence, or clearly jurisdiction-specific entry points. Examples include:

- Kane County source URLs;
- Kane County source-layer names;
- Kane-specific field mappings;
- source quirks and accepted inventories;
- accepted Kane release identities;
- Kane administrative-boundary source choices;
- Kane County filesystem deployment paths where intentionally deployment-specific.

## Namespace discipline

Every new durable identifier or namespace should be reviewed for accidental Kane coupling.

A reusable protocol field should prefer concepts such as:

```text
jurisdiction_id
dataset_id
source_id
release_id
substrate_id
partition_id
scope_class
subscription_id
generation_id
object_sha256
```

rather than embedding `kane` in a field or token whose semantics are generic.

This rule does not require renaming existing Kane-specific commands, files, test fixtures, or source profiles that accurately describe Kane County. Existing names may remain when they are deployment entry points or historical release evidence.

The important boundary is the durable contract. New browser/package/database/partition/subscription contracts should not require Kane County to be implicit.

## Jurisdiction identity

Human-readable names are attributes, not sufficient durable identities.

A future multi-jurisdiction deployment must be able to distinguish jurisdictions whose naming conventions differ and must tolerate display-name changes without changing every downstream identity.

For U.S. deployments, authoritative geographic codes such as Census/FIPS-derived identifiers are useful durable jurisdiction identities where applicable.

The internal model must not assume every county-equivalent jurisdiction uses the English word `county`. The design horizon includes parishes, boroughs/census areas, independent cities, and other U.S. county-equivalent structures where they satisfy the same geographic role.

## Geographic partition implications

Milestone 4 adds logical geographic partition identity. That contract must be generic even though Kane County supplies the first operational examples.

The generic partition model is based on **scope classes**, not on the assumption that every jurisdiction has the same municipal/township structure.

Initial classes include:

- whole jurisdiction;
- named administrative subdivision;
- explicit bounded region;
- deterministic composite scope.

Kane may expose convenient named administrative subtypes such as municipality/incorporated place and township. Another jurisdiction may use different local-government concepts or may lack an equivalent township structure.

Therefore:

- `municipality` and `township` are useful declared scope types where applicable, not universal national assumptions;
- an administrative partition must record the explicit boundary/source lineage that defines it;
- a generic bounded-region partition remains available when administrative geography is unsuitable;
- partition identity must remain independent of physical edge devices;
- a feature crossing partitions retains one geographic identity;
- partitioning must not create separate authoritative databases merely because the scopes are geographically smaller.

A second jurisdiction should be able to supply its own accepted administrative-boundary contracts without changing the generic partition identity model.

## Source diversity

Nationwide design must not assume every jurisdiction publishes equivalent data through the same vendor, schema, endpoint type, object identifier, update schedule, or quality policy.

The reusable Fabric core should know what a dataset contract requires. A jurisdiction/source profile should know how that jurisdiction satisfies the contract.

For example, the generic system may know that a road dataset has:

- source identity;
- acquisition evidence;
- accepted and candidate releases;
- deterministic comparison rules;
- declared source-specific exceptions where required;
- provenance.

The Kane County road profile separately knows the Kane-specific endpoint, fields, object-ID behavior, and accepted harvest inventory.

The accepted Kane road release/harvest contains 27,675 objects. A later live upstream inventory exposed 27,676 IDs and correctly triggered `new_source_detected`. Do not encode the disproven earlier explanation that one accepted road was deliberately omitted for missing geometry as a generic or Kane-specific contract fact.

This separation is essential. A second jurisdiction should primarily require new profile/configuration work where its source can satisfy an existing contract, rather than edits throughout the geographic core.

## Package, partition, and manifest implications

Milestone 3 froze durable substrate package and manifest identities. Milestone 4 adds partition and subscription identities above that baseline.

Those contracts must carry enough explicit jurisdiction identity that a browser, cache, edge node, or later multi-county operator does not need an out-of-band assumption about which county/jurisdiction produced the data.

At minimum, external designs should keep these concepts distinguishable:

```text
jurisdiction
logical dataset
accepted source/release lineage
substrate generation/content identity
partition definition/generation
subscription generation
immutable object/component identity
physical placement/availability
```

Content hashes identify content. Human-readable labels should not be overloaded as global primary keys.

A partition should reference the canonical substrate rather than silently generating a different geography contract for each municipality or township.

## Database implications

New database tokens and schema concepts should avoid unnecessary Kane-specific naming when the stored concept is geographically generic.

However, the project should not churn the proven geographic core solely for cosmetic genericity. Renaming or migration is justified when an existing Kane-specific name would cross a new generic boundary, create ambiguity, or prevent another jurisdiction from being represented correctly.

Behavior preservation remains more important than stylistic renaming.

## Code comments and review

Where the distinction is not obvious, new code should state whether behavior is:

- generic Kane Fabric behavior;
- U.S.-jurisdiction policy;
- jurisdiction/source-specific policy;
- administrative-partition policy;
- deployment-specific infrastructure policy.

Comments should explain the ownership/boundary distinction, not speculate about unimplemented counties.

Code review for new durable contracts should ask:

1. Is this concept actually specific to Kane County?
2. If not, have we encoded `kane` or a Kane-only assumption unnecessarily?
3. Is jurisdiction identity explicit where it needs to survive packaging, caching, partitioning, or distribution?
4. Is a source-specific rule being mistaken for a generic geographic rule?
5. Is a Kane-specific administrative term being treated as universal when a generic scope class would be more accurate?
6. Can Kane remain the sole implementation without creating fake generalization machinery?

## Relationship to reconstructability

Reconstructability remains mandatory.

The project has already proven the foundational Kane County reconstruction chain and extracted the geographic core. Future work must preserve that ability and must not introduce hidden state that makes a Fabric deployment dependent on copying an existing machine.

The emphasis changes from proving reconstruction as the primary project objective to using the proven reconstructable architecture as the foundation for portable public infrastructure.

## Relationship to civic infrastructure

Multi-county portability and public-infrastructure independence reinforce each other.

A county or county-equivalent jurisdiction should not require permission from the original Kane deployment to become a Fabric deployment. A future operator should be able to obtain the public software, provide the jurisdiction/source contracts and accepted evidence required by the system, and operate independently.

The governing public-infrastructure principles are documented in `docs/CIVIC_INFRASTRUCTURE_PRINCIPLES.md`.

## Current rule

Kane County is the reference implementation.

Do not build the nation now.

Do not design new durable contracts as though Kane County is the nation.
