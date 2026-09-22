# Civic Infrastructure Anti-Capture Contract

## Status

Cross-cutting Kane Fabric architecture invariant.

This contract applies to physical edges, gateways, provisioning, applications, later county-access work, and businesses built on top of the infrastructure. A milestone may add capabilities, but it must not silently convert Kane Fabric into a captive SaaS control plane.

## Purpose

Kane Fabric is civic infrastructure. Its function is to make durable civic interfaces, identities, provenance, transport, verification, and access available without requiring users or businesses to become tenants of a central operator.

The infrastructure must make capture difficult by construction rather than relying on an operator promise not to capture users later.

The governing principle is:

```text
infrastructure provides access, not ownership
infrastructure provides interoperability, not dependency
infrastructure provides verification, not surveillance
infrastructure enables services, but does not require service tenancy
```

## Anti-capture invariants

Base Kane Fabric operation must not require:

- a mandatory central user account;
- a recurring subscription to keep locally issued infrastructure useful;
- operator custody of user-created or application-created data;
- mandatory activity reporting, tracking, or behavioral telemetry;
- a proprietary cloud service in the normal local serving path;
- an operator-controlled portal as the only way to configure, inspect, export, or replace a device;
- physical-device identity to become person identity, business identity, or Fabric logical identity;
- continued availability of the original issuer after an appliance has been issued and accepted.

A deployment or independent business may offer optional hosted services above Kane Fabric. Those services must remain distinguishable from the infrastructure itself and must not become prerequisites for the underlying civic interfaces.

## County-data boundary

A County Database is not Kane Fabric infrastructure merely because Kane Fabric accesses it.

The County Database remains an external authoritative source operated under its own legal, technical, and institutional authority. Kane Fabric infrastructure may provide reliable and reproducible access to that source, preserve source/witness lineage, distribute immutable derived artifacts, and expose stable interfaces for consumers.

The separation is:

```text
County Database
    = external authoritative source

Kane Fabric
    = reliable access + identity + provenance + transport
      + verification + replaceable distribution

Applications and businesses
    = independent consumers/producers above those interfaces
```

Kane Fabric must not acquire county authority by caching, transforming, serving, or witnessing county-derived bytes.

## Business neutrality

Building a business on top of Kane Fabric should be structurally comparable to operating a business in a physical building connected to public infrastructure.

The infrastructure may provide common capabilities, but it does not thereby acquire the tenant's customers, records, commercial identity, or business process. An application provider should be able to compete, migrate, cease operation, or be replaced without invalidating the underlying civic infrastructure.

Open interfaces, replaceable implementations, exportability, and logical identity separation are therefore economic as well as technical requirements.

## Issuance, not fleet tenancy

The reference physical-edge model is individual issuance, not mandatory fleet tenancy.

A dedicated issuance/provisioning node may prepare one appliance at a time for different civic or maker roles, for example a homeowner-network appliance or a maker/3D-printing network appliance. The issuance node may build or select an approved firmware image, install replaceable device-local credentials, prepare storage, record acceptance evidence, and perform recovery or reissuance.

After issuance, normal local operation must not depend on continuous contact with that node.

```text
Kane Fabric contracts
        ↓
local issuance/provisioning node
        ↓
one accepted physical appliance
        ↓
independent local operation
```

The issuance node is not a SaaS account authority and does not become the owner of the appliance's application data.

Individual civic issuance is further defined in `docs/CIVIC_ISSUANCE_AUTHORITY.md`. The issuance/provisioning node may apply published civic-standing rules and place a signed Civic Issuance Record on an appliance, but the physical device does not become the person's identity and the issuer does not acquire ownership of the person's local data.

## Provisioning clients

Provisioning is a local protocol boundary, not a permanent portal product.

A web page, Android application, Chromium/PWA application, Apple application, desktop utility, or later compatible client may perform the same bounded provisioning transaction. No particular UI implementation becomes part of Fabric logical identity.

For the ESP32-S3 reference edge, a temporary local setup access point and web form may be used when deployment-network credentials are absent. That setup interface is distinct from the normal browser-serving path:

```text
unprovisioned appliance
        ↓
temporary local setup interface
        ↓
write deployment-local configuration
        ↓
setup interface ends / device reboots
        ↓
normal local appliance operation
```

The temporary setup interface does not make the ESP32-S3 the persistent browser gateway. Normal Fabric browser HTTPS remains a separate gateway role.

## Data and identity separation

The following relationships must remain false:

```text
physical device identity = user identity
provisioning account      = required civic identity
operator database         = required application database
network address           = Fabric logical identity
subscription status       = right to access local civic artifacts
```

Application-specific membership, private user records, commercial data, and participation semantics belong to the application or organization that actually uses them unless a future public contract explicitly defines otherwise.

## Failure and replacement test

A design is consistent with this contract when the following questions can be answered without relying on the original operator:

1. Can an accepted appliance continue its local role if the issuer is offline?
2. Can the physical device be replaced without changing Fabric logical identities?
3. Can a compatible provisioning client replace the original provisioning UI?
4. Can locally held data be exported or migrated without an operator account?
5. Can a different business build against the same civic interfaces without permission from a privileged platform operator?
6. Can an external authoritative source remain authoritative without being absorbed into Kane Fabric ownership?

If a proposed capability makes the answer to one of these questions dependent on a central operator, that dependency must be justified as an optional service above the infrastructure boundary rather than silently incorporated into the infrastructure itself.


## Participant-operated validation

The anti-capture model now explicitly includes participant-operated SASE validation. Any active participant may become an operator/validator under the applicable published profile; operator is a bounded procedural role, not a permanent administrative identity.

The institution being diagnosed must not automatically control its diagnostic infrastructure. In particular, HOA Board/property-management control of the association does not imply exclusive control of HOA Diagnostics, and school administration does not imply exclusive control of school-related Civic Infrastructure.

Operator actions remain subject to participant peer scrutiny ("scrubbing"), which may confirm facts or expose contradictions/capture. See `docs/CIVIC_OPERATOR_PEER_SCRUTINY.md`.


## HOA-local signing-node autonomy

Mandatory shared civic-signing tenancy across HOAs is prohibited by the anti-capture model.

Each participating HOA must be capable of owning/operating its own Civic Signing Node and bearing its own operating costs. One HOA's node, operator, outage, dispute, compromise, or recovery must not become another HOA's authority boundary.

Common software and common statutory references are compatible with independent local signing roots.

See `docs/CIVIC_OWNER_OPERATED_SIGNING_NODE.md`.


## Optional shared-service boundary

Future shared Kane Fabric services such as a Kane County CA, Kane-local mail infrastructure, or IPFS may support multiple HOA-local roots without merging them.

Shared transport, endpoint authentication, communication, or storage must remain replaceable and must not become the Civic authority source for any participating HOA.

See `docs/CIVIC_SIGNING_NODE_FUTURE_SERVICE_BOUNDARIES.md`.
