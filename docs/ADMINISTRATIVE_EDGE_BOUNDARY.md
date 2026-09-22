# Administrative Infrastructure / Physical Edge Boundary

## Status

Active architecture boundary for Kane Fabric administrative development and physical edge participation.

This document clarifies a distinction that became concrete during the MS5 ESP32-S3 physical proof: the ESP32-S3 is an **edge device**, while county geography, the county web map, category definitions, publication contracts, and independent-operator interoperability are **administrative infrastructure**.

The physical edge is intentionally bounded. It is not a miniature county server and is not required to carry the complete county substrate.

## Administrative infrastructure

Administrative infrastructure defines and operates the shared civic context in which independently controlled edges participate.

It owns or defines:

- accepted county geography and its provenance/release state;
- the county-wide web/map presentation;
- category and object-class definitions used by participating domains;
- publication, reference, visibility, and interoperability contracts;
- the rules by which participant publications attach to accepted geographic identities;
- validation of the shared contract without acquiring ownership of participant-local data merely because it is presented online;
- operator-facing procedures needed for an independent operator to implement the same infrastructure for another county.

The administrative layer may integrate many independently controlled publications into one county view. That composition does not make the county web service the exclusive custodian of the participant data.

## Physical edge

A physical edge is a low-cost, replaceable local custodian and serving point for a **bounded participant publication**.

The ESP32-S3 is the current reference implementation of that role, not the required Civic edge platform. The physical-edge contract must remain implementable on another user-owned platform without importing ESP32-specific identity, eFuse state, or secure-element assumptions.

The participant edge is a user-owned custody point: user-owned data remains on user-owned storage unless the participant deliberately publishes or replicates it under another explicit contract.


A condominium deployment is the reference example. One association edge may hold the association and unit information that the participating association or unit owners intentionally publish through the Fabric contracts. A 35-unit condominium therefore does not need a complete Kane County road/water/substrate package on its ESP32-S3 merely to participate in the county map.

The edge may:

- hold immutable generations of its bounded participant publication;
- hold and serve user-owned, publicly readable public verification/key artifacts such as CA public material, OpenPGP public keys, and SSH public keys;
- retain references to accepted county/building/partition identities instead of duplicating county-wide substrate bytes;
- verify an inventory before activation/serving;
- serve activated artifacts locally by the accepted bounded HTTP contract;
- retain the last valid local publication through upstream/management loss;
- be replaced or reprovisioned without changing the logical participant publication or the geographic identities it references.

The edge does not own:

- county-wide geographic authority;
- county-wide substrate replication as a prerequisite for participation;
- the county web map;
- category or publication-contract administration;
- browser account/person identity;
- county candidate promotion or release signing.

## Contribution model

The intended relationship is:

```text
accepted county geography
+ administrative categories/contracts
+ county web/map
             ^
             | integrate bounded publication
             |
      participant edge publication
             ^
             |
          ESP32-S3
```

For a condominium example:

```text
Kane County base map
        +
Kings Row association publication
        +
unit publications / unit state
        =
composed county-facing view
```

Some participant fields may be public, such as an intentionally published `for-sale` state. Other fields may be restricted or private. The contract must express the visibility/classification semantics, but the ESP32-S3 v1 firmware does not become a human account or person-identity service. Authentication/authorization and browser presentation belong above the physical edge boundary.

A later Civic Issuance Record may carry authoritative standing/affordance assertions for the participant appliance. That record remains data issued under published civic contracts; it does not make the firmware the semantic authority for `Current Resident`, `Affected Status`, `HOA Homeowner`, `Property Taxpayer`, or another civic affordance. See `docs/CIVIC_ISSUANCE_AUTHORITY.md`.

## Infrastructure, not SaaS

The administrative service is infrastructure only if an independently controlled participant remains able to retain and move its own publication without dependence on one operator's private database, account system, or subscription service.

Accordingly:

- publication formats and identities must be explicit and replaceable;
- participant data must not exist only inside one hosted service;
- local useful operation must survive loss of upstream management connectivity;
- joining the online county view must not transfer geographic authority to the edge or exclusive data custody to the county web operator;
- physical ESP32 identity, IP address, hostname, TLS identity, or management key must never become the logical identity of the participant publication;
- another county operator must be able to implement the administrative contracts without adopting Kane County hostnames, databases, device identities, or private operational internals.

## Independent county operator target

The next administrative development must make the following statement realistic rather than aspirational:

> An independent operator can stand up Civic Infrastructure for another Illinois county by implementing the published county, category, web, and participant-publication contracts, without cloning Kane County's private operational state and without requiring Kane County to host that operator's users or data.

That requires administrative work before further edge specialization:

- define the county-facing object/category model;
- define how participant publications reference county geography;
- define public/restricted/private publication semantics without coupling them to ESP32 firmware;
- define the web/map composition contract;
- define the operator-facing conformance boundary;
- prove the same bounded participant publication can be integrated into the county view while remaining locally controlled.

## MS5 relationship

MS5-006 physically proved the reference ESP32-S3 artifact appliance. That proof remains accepted.

MS5-007 now uses the administrative work above to prove browser integration of a **focused participant edge publication** through Wiregate with the county/web view. It does not require the ESP32-S3 to store or serve the complete accepted county substrate.

Later MS5 firmware lifecycle work remains required for closeout—management-transport evaluation, firmware update/recovery, replacement/reprovisioning, and constrained-resource acceptance—but those tasks do not block administrative county/web/category/contract development.