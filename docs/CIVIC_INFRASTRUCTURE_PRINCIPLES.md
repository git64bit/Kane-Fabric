# Civic Infrastructure Principles

## Purpose

Kane Fabric is intended to be public infrastructure in the strongest practical sense: infrastructure that the public may possess, understand, reproduce, adapt, operate, redistribute, and build upon without requiring continuing permission from this project.

This is not incidental licensing language. It is a project objective and an architectural constraint.

## Civic infrastructure scope

The civic-infrastructure layer is broader than the county database alone.

It includes the Kane Fabric implementation required to maintain and distribute accepted public geographic state, including:

- the county geographic database core and its source/provenance/update machinery;
- deterministic comparison, reconciliation, promotion, rollback, and reconstruction mechanisms;
- shared substrate compilation and public package/manifest formats;
- the browser-side code required to validate, decompress, and render the shared substrate;
- the replaceable edge-serving reference implementation, initially an ESP32-S3-class device;
- Kane Fabric firmware and HTTP-serving code for that reference edge implementation, built using ESP-IDF;
- public synchronization, verification, activation, and recovery contracts required to replace an edge node without changing geographic authority.

ESP-IDF and other third-party dependencies retain their own legal terms. Use of a third-party framework does not change the public-domain intent of Kane Fabric's own code.

The edge node is part of the civic infrastructure because it distributes public geographic state without becoming its authority. It must not become a proprietary or institutional gate through which a browser needs permission to obtain the public substrate.

## Public-domain software

Kane Fabric is released under the repository `LICENSE`, which uses The Unlicense/public-domain dedication.

The intent is deliberate:

- anyone may copy, modify, publish, use, compile, sell, or distribute the Kane Fabric software;
- commercial and non-commercial use are equally permitted by the project;
- adaptation and independent continuation are expected and welcomed;
- a useful civic-infrastructure deployment must not depend on continuing permission, membership, payment, or approval from the original project.

If a jurisdiction does not give full effect to a public-domain dedication, the permissions and disclaimer in the repository `LICENSE` remain the project's governing legal statement.

This document explains project intent. It does not replace or narrow the `LICENSE`.

## Application and subscription boundary

The public-domain status of the civic-infrastructure layer does not automatically apply to every application, subscription, classification, qualification, workflow, or business dataset built on top of it.

Kane Fabric deliberately separates public geographic infrastructure from application-owned semantics.

Examples of application-level state include:

- building categories and domain classifications;
- participant and organization information;
- qualifications and capability records;
- workflow and operational state;
- business rules and business data;
- Mechanical Compiler application/federation state;
- other subscription-specific metadata that is not itself part of the shared civic substrate.

Those layers may have their own ownership, access, licensing, privacy, governance, or commercial terms. They do not become public-domain merely because they reference Kane Fabric geographic identities, use Kane Fabric packages, or are delivered through the same physical edge device.

Conversely, an application must not silently claim ownership of the underlying Kane Fabric civic substrate merely because it adds proprietary or restricted state on top of it.

The architectural boundary is therefore intentional:

```text
public geographic authority + shared substrate + public edge/browser delivery
                            = Kane Fabric civic infrastructure

application categories + qualifications + workflows + domain/business state
                            = separately owned application/subscription layer
```

The two may compose in one browser session without merging their ownership or licensing status.

## No ideological or institutional condition of use

Kane Fabric must not make political, religious, commercial, governmental, philosophical, or intellectual-ideological affiliation a condition of using the civic infrastructure.

The project does not require users to adopt a doctrine, join an institution, accept a political position, participate in a particular governance structure, or obtain permission from a preferred class of operator.

This principle is about non-encumbrance by Kane Fabric itself. It does not purport to override applicable law, the rights of third parties, or lawful terms attached to external data, applications, subscriptions, or services.

## Commerce and government

Public infrastructure is not made less public because it is used by a business, a government, a nonprofit organization, or an individual.

Kane Fabric therefore must not introduce field-of-use restrictions that prohibit ordinary commerce or government adoption. A downstream user may charge for hardware, hosting, integration, support, analysis, or another service without owing the Kane Fabric project a royalty or seeking project permission.

The same freedom permits a public agency, private organization, community group, researcher, or individual to operate an independent deployment.

This freedom applies to Kane Fabric. It does not prohibit an independent application built on top of Kane Fabric from having its own lawful commercial or licensing model.

## Independence from the original project

A durable public infrastructure project must tolerate institutional failure, disagreement, abandonment, and forks.

Accordingly:

- the original repository is not intended to be a permanent gatekeeper;
- reconstructability and declared inputs must remain preferable to hidden operator state;
- published formats and identities should not require a private registry controlled by the original author;
- independently operated Fabric nodes must be architecturally possible;
- independently built ESP32-S3/ESP-IDF edge nodes must be able to serve conforming public Fabric artifacts;
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

The public-domain intent of Kane Fabric does not automatically change the legal status of third-party software, data, fonts, imagery, services, frameworks, or other inputs.

When adding a dependency or incorporated asset, prefer choices that preserve the project's ability to be freely possessed, adapted, redistributed, and operated. Do not silently introduce field-of-use, political, religious, commercial, institutional, or other restrictions that would contradict these principles.

Where a third-party dependency has its own terms, those terms must remain distinguishable from Kane Fabric's own public-domain dedication. ESP-IDF is therefore a toolchain/framework dependency of the initial edge implementation, not the source of Kane Fabric's public-domain status.

A dependency should be added because a concrete technical requirement justifies it, not merely because it is common or convenient.

## Geographic data is a separate rights boundary

Kane Fabric software and the geographic data it processes are not the same legal object.

Official-source data remains subject to the status, provenance, and lawful terms of its source. A Fabric package must not imply that upstream data became public-domain merely because public-domain Kane Fabric software processed it.

Source identity and provenance therefore remain important not only for reconstruction and update detection, but also for keeping external data lineage visible.

## Contributions

Contributions incorporated into Kane Fabric should be made with the understanding that the Kane Fabric repository is public-domain software under the existing `LICENSE`.

The project should not accumulate substantial Kane Fabric code whose redistribution status is unclear or whose contributor terms silently reintroduce restrictions inconsistent with this repository.

This principle should remain lightweight. It exists to preserve freedom of use, not to build an institutional permission system around contribution.

## Engineering rule

When two technically reasonable civic-infrastructure designs are otherwise comparable, prefer the design that leaves a future operator with fewer dependencies on the original project, fewer permission boundaries, fewer proprietary assumptions, and a clearer path to reconstruction and independent operation.

When designing an application or subscription above that infrastructure, preserve the boundary rather than assuming that the application's state must inherit the civic infrastructure's public-domain status.

Public-infrastructure integrity is a continuing design criterion, not a one-time licensing decision.
