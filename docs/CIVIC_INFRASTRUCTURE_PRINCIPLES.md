# Civic Infrastructure Principles

## Purpose

Kane Fabric is intended to be public infrastructure in the strongest practical sense: infrastructure that the public may possess, understand, reproduce, adapt, operate, redistribute, and build upon without requiring continuing permission from this project.

This is not incidental licensing language. It is a project objective and an architectural constraint.

## Public-domain software

Kane Fabric is released under the repository `LICENSE`, which uses The Unlicense/public-domain dedication.

The intent is deliberate:

- anyone may copy, modify, publish, use, compile, sell, or distribute the software;
- commercial and non-commercial use are equally permitted by the project;
- adaptation and independent continuation are expected and welcomed;
- a useful deployment must not depend on continuing permission, membership, payment, or approval from the original project.

If a jurisdiction does not give full effect to a public-domain dedication, the permissions and disclaimer in the repository `LICENSE` remain the project's governing legal statement.

This document explains project intent. It does not replace or narrow the `LICENSE`.

## No ideological or institutional condition of use

Kane Fabric must not make political, religious, commercial, governmental, philosophical, or intellectual-ideological affiliation a condition of using the software.

The project does not require users to adopt a doctrine, join an institution, accept a political position, participate in a particular governance structure, or obtain permission from a preferred class of operator.

This principle is about non-encumbrance by Kane Fabric itself. It does not purport to override applicable law, the rights of third parties, or lawful terms attached to external data and services.

## Commerce and government

Public infrastructure is not made less public because it is used by a business, a government, a nonprofit organization, or an individual.

Kane Fabric therefore must not introduce field-of-use restrictions that prohibit ordinary commerce or government adoption. A downstream user may charge for hardware, hosting, integration, support, analysis, or another service without owing the Kane Fabric project a royalty or seeking project permission.

The same freedom permits a public agency, private organization, community group, researcher, or individual to operate an independent deployment.

## Independence from the original project

A durable public infrastructure project must tolerate institutional failure, disagreement, abandonment, and forks.

Accordingly:

- the original repository is not intended to be a permanent gatekeeper;
- reconstructability and declared inputs must remain preferable to hidden operator state;
- published formats and identities should not require a private registry controlled by the original author;
- independently operated Fabric nodes must be architecturally possible;
- forks and incompatible experiments are not, by themselves, violations of project intent.

Interoperability is valuable, but it must be earned through clear public contracts rather than control over participation.

## Liability and responsibility

The repository `LICENSE` provides the software "AS IS", without warranty, and contains the project's liability disclaimer.

Kane Fabric must not create documentation or interfaces that imply a warranty which the project does not provide. In particular:

- an accepted geographic release is a Kane Fabric operational state, not a legal guarantee that an upstream source is complete or correct;
- validation, deterministic comparison, provenance, promotion, and rollback improve technical reliability but do not create a warranty;
- downstream operators remain responsible for their deployments, modifications, operational decisions, and uses;
- applications consuming Kane Fabric remain responsible for their own application semantics and decisions.

No disclaimer can prevent a claim from being asserted. The project objective is to keep responsibility, provenance, and absence of warranty explicit rather than ambiguous.

## Third-party dependencies

The public-domain intent of Kane Fabric does not automatically change the legal status of third-party software, data, fonts, imagery, services, or other inputs.

When adding a dependency or incorporated asset, prefer choices that preserve the project's ability to be freely possessed, adapted, redistributed, and operated. Do not silently introduce field-of-use, political, religious, commercial, institutional, or other restrictions that would contradict these principles.

Where a third-party dependency has its own terms, those terms must remain distinguishable from Kane Fabric's own public-domain dedication.

A dependency should be added because a concrete technical requirement justifies it, not merely because it is common or convenient.

## Geographic data is a separate rights boundary

Kane Fabric software and the geographic data it processes are not the same legal object.

Official-source data remains subject to the status, provenance, and lawful terms of its source. A Fabric package must not imply that upstream data became public-domain merely because public-domain Kane Fabric software processed it.

Source identity and provenance therefore remain important not only for reconstruction and update detection, but also for keeping external data lineage visible.

## Contributions

Contributions incorporated into Kane Fabric should be made with the understanding that the repository is public-domain software under the existing `LICENSE`.

The project should not accumulate substantial code whose redistribution status is unclear or whose contributor terms silently reintroduce restrictions inconsistent with this repository.

This principle should remain lightweight. It exists to preserve freedom of use, not to build an institutional permission system around contribution.

## Engineering rule

When two technically reasonable designs are otherwise comparable, prefer the design that leaves a future operator with fewer dependencies on the original project, fewer permission boundaries, fewer proprietary assumptions, and a clearer path to reconstruction and independent operation.

Public-infrastructure integrity is a continuing design criterion, not a one-time licensing decision.
