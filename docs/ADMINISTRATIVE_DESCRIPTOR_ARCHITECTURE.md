# Administrative Descriptor Architecture

## Status

Active design authority for the descriptor-driven Kane Fabric Administrative Web.

The Administrative Web is presently the design instrument used to discover and formalize Civic Infrastructure. The physical participant edge is deliberately downstream of this work. MS5-006 proved an ESP32-S3 bounded artifact appliance, but the final participant-publication and edge shape are not assumed while the Administrative Web is being established.

## Core rule

The browser engine supplies **generic capabilities**. Administrative meaning and presentation are **descriptor data**.

The renderer must not contain Illinois-, county-, condominium-, insurance-, contract-, assessment-, board-, or unit-specific form logic. A descriptor may contain those concepts; the engine only knows generic concepts such as pages, sections, controls, collections, bindings, validation, layout, help, authority references, and actions.

Accordingly, controls are not hand-authored in HTML. The host page provides a generic application shell and rendering mount. Field labels, help, options, ordering, placement, dimensions, and declarative behavior live in JSON whenever they can be represented as data.

## Layering

The architecture intentionally separates four layers:

```text
Kane Fabric descriptor language
        ↓
jurisdiction profile (Illinois today)
        ↓
domain profile (Illinois condominium infrastructure)
        ↓
association instance data
```

The descriptor language must not define `county`, `parish`, `condominium`, or any other jurisdiction/domain term as a renderer primitive. Those are profile content. This allows another jurisdiction to reuse the descriptor engine even when its political subdivisions or legal institutions differ.

Kane Fabric is deliberately scoped to Illinois during the current Infrastructure build. Other states are not used to weaken or generalize Illinois requirements prematurely. Jurisdiction neutrality belongs in the descriptor language and renderer; the current civic content remains Illinois-specific.

## Infrastructure admission rule

For the Illinois condominium profile, shared Civic Infrastructure contains facts, obligations, record classes, and administrative concepts that are statewide or otherwise demonstrably common to Illinois condominiums.

If an apparent requirement is county-specific, municipal, association-customary, disputed, or not yet established as statewide, it is deferred rather than silently promoted into Infrastructure.

Association-specific values instantiate the statewide model but do not become statewide rules merely because Kane Fabric records them.

Examples:

```text
Statewide Infrastructure
  Illinois Condominium Property Act insurance framework
  requirement to retain current association insurance policies

Association instance data
  insurer name
  policy number
  effective/expiration dates
  whether an association exercised a statutory option through declaration/bylaws/rule
```

## Authority, authenticity, and security

These are separate concerns.

**Authority** defines what Kane Fabric is entitled to state as shared Infrastructure and what source establishes that authority.

**Authenticity** permits a participant or operator to verify that a descriptor, publication, or generation is the exact object it claims to be. Administrative descriptors are therefore versioned, deterministically canonicalizable, and hashable.

**Security** addresses adversarial behavior, unauthorized disclosure, impersonation, denial of service, and related threats. Security work remains necessary, but it must not prematurely narrow the Civic Infrastructure model. Current development assumes cooperative participants while preserving explicit authority and provenance.

## Semantics versus presentation

A semantic binding and its screen placement are independent.

For example:

```text
association.insurance.policies[].expiration_date
        ├── semantic binding
        ├── data role
        ├── authority/provenance
        └── presentation row/column/span
```

Moving a field from one row or column to another must not change the identity or meaning of the stored value.

Category identity is likewise distinct from descriptor/schema identity. `insurance.association` can remain a civic category while `us.il.condominium.insurance` and its version identify the descriptor contract used to represent it.

## Descriptor v1

The v1 descriptor format is:

```text
kane-fabric-administrative-descriptor / format_version 1
```

The published structural schema is:

```text
administration/descriptors/descriptor-v1.schema.json
```

The browser additionally performs fail-closed runtime validation without introducing a third-party JavaScript schema dependency.

Descriptor v1 supports:

- descriptor identity and version;
- jurisdiction/domain scope metadata;
- separate civic category declarations;
- authority/provenance declarations;
- pages and sections;
- declarative grid layout;
- text, number, date, select, textarea, checkbox, notice, and repeating collection controls;
- semantic data bindings;
- labels, help, placeholders, options, and action labels;
- required/read-only/disabled metadata;
- bounded numeric attributes;
- simple declarative conditional visibility;
- authority references at section and control level;
- explicit data-role labeling such as `infrastructure` versus `association_instance`.

No executable JavaScript is permitted in descriptors. More expressive declarative rules may be added only when the application demonstrates a concrete need.

## Browser bootstrap

`web/admin-app.json` identifies the descriptor sources to render. The browser code does not hard-code the Illinois insurance descriptor path or its fields. Adding another administrative domain should normally mean adding another descriptor source rather than another hand-authored form.

The browser computes and displays a SHA-256 identity over canonical JSON for each loaded descriptor. This is an authenticity primitive, not a signing or authorization mechanism.

## First vertical slice: insurance

The first reference descriptor is:

```text
administration/descriptors/illinois/condominium/insurance.v1.json
```

Insurance was selected because it exercises both sides of the Infrastructure boundary:

- statewide Illinois requirements and record classes;
- association-specific policy instances;
- an Illinois statutory option that can become an association-specific requirement;
- repeating records;
- legal authority references;
- multiple control types and grid placement.

The reference descriptor is deliberately an initial slice, not a claim that every insurance, tax, licensing, registration, contract, governance, or records requirement has already been enumerated.

## Edge relationship

The Administrative Web comes first.

The development order is now:

```text
accepted Illinois/Kane geographic substrate
        ↓
full-featured descriptor-driven Administrative Web
        ↓
formalize statewide Infrastructure domains and association instantiation
        ↓
identify participant/user data that is not Infrastructure
        ↓
derive participant-publication contracts
        ↓
select/design the appropriate edge role
```

Do not shape administrative descriptors around ESP32 limitations. The accepted ESP32-S3 implementation remains evidence that a bounded immutable artifact appliance is feasible; it is not the definition of the eventual participant edge.
