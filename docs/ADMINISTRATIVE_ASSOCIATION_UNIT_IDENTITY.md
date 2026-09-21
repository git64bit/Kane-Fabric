# Administrative Association and Unit Identity

## Status

Architecture candidate for the next Kane Fabric administrative contract checkpoint.

This document defines the identity boundary required before a real condominium participant publication is composed into the county-facing browser. It does **not** yet define a publication manifest, persistence model, account system, or physical-edge identity.

The governing design authorities remain:

- `docs/ADMINISTRATIVE_DESCRIPTOR_ARCHITECTURE.md`
- `docs/ADMINISTRATIVE_EDGE_BOUNDARY.md`
- `docs/WEB_APPLICATION_DESIGN.md`
- `administration/README.md`

## Purpose

The accepted Administrative Web now models statewide Illinois condominium Infrastructure separately from association-instance values. The next contract must let a browser say, without ambiguity:

- which condominium association an instance or participant publication refers to;
- which recorded unit an object refers to;
- which accepted county/building geography is referenced;
- which descriptor/category contract gives the data meaning;
- which publication generation supplied a value;
- which source delivered the publication;
- and which of those identifiers are **not** interchangeable.

The identity model must not require Board approval, a property-manager account, a proprietary portal, a Secretary-of-State corporation record, a particular county operator, or an ESP32 device identity merely to recognize the condominium and its recorded units.

## Identity classes

Kane Fabric distinguishes at least these identity classes:

```text
county / geographic object identity
association logical identity
unit logical identity
category / schema identity
publication generation identity
source / transport identity
physical edge identity
human / account identity
```

They are intentionally separate.

A browser may display several of them together, but one must never silently substitute for another.

## Association identity anchor

For an Illinois condominium, the association logical identity is anchored to the **recorded condominium declaration that created the condominium property**, together with the public recording authority/reference needed to identify that original recorded instrument.

Conceptually:

```text
association identity anchor
  state / jurisdiction context
  + public recording authority reference
  + original declaration recording reference
```

This anchor is chosen because the condominium's recorded declaration exists independently of later Board composition, management contracts, portal vendors, corporate form, or physical publication infrastructure.

The following are attributes or evidence and **not** association identity by themselves:

- current association display name;
- Board membership;
- property-manager account or customer number;
- management-company identity;
- Secretary-of-State corporation identifier;
- tax account or bank account;
- website, hostname, email domain, or portal identifier;
- IP address;
- WireGuard identity;
- ESP32 MAC address, chip identity, serial number, TLS key, or management key;
- current publication URL;
- current publication generation hash.

An incorporated association may record corporate information as association-instance data, but incorporation is not universal to Illinois condominium associations and therefore cannot be the root identity requirement.

## Declaration amendments and lifecycle

An amendment to the declaration does not create a new association logical identity merely because the recorded instrument set changed. Amendments belong to the association/property record history under the same association anchor.

Likewise, a developer turnover, Board election, management-company replacement, insurance renewal, assessment change, or portal migration does not create a new association identity.

A statutory sale/removal/termination event may end or transform the lifecycle represented by the association identity, but it does not retroactively change the identity of the condominium publication history that existed before that event.

## Unit identity anchor

A unit logical identity is subordinate to exactly one association logical identity and is anchored to the unit's recorded declaration/plat identity.

Conceptually:

```text
unit identity anchor
  association logical identity
  + recorded unit designation / legal or plat reference
```

The following are unit attributes and **not** unit identity by themselves:

- current owner name;
- resident name;
- mailing address;
- tax bill recipient;
- assessment ledger account number;
- portal account;
- for-sale state;
- occupancy state;
- participant device;
- publication URL;
- current publication generation.

A sale of a unit changes ownership, not unit identity.

A participant may publish information about a unit without that publication becoming the legal identity of the unit or proof of ownership/residency.

## Geographic references

Association and unit identities do not replace accepted county geography.

A participant publication may reference one or more accepted county/building objects, but those geographic references remain independently versioned Fabric identities. A building reference therefore means "this participant object is associated with this accepted geographic object," not "the building object is the association identity."

Reference model:

```text
accepted county/building object
          ↑
          | geographic reference
association logical identity
          ↑
          | parent identity
unit logical identity
```

This permits county geography to be updated or re-released without making an ESP32, portal record, or mutable street-address string the root condominium identity.

## Descriptor and category identity

The accepted administrative descriptor identities such as:

```text
us.il.condominium.insurance
us.il.condominium.records
us.il.condominium.finance
...
```

identify contracts/semantics, not associations or units.

An association instance may contain values governed by many descriptor identities. A unit publication may likewise use one or more category/schema contracts. Descriptor/category identity must therefore remain orthogonal to association/unit identity.

## Publication generation identity

A participant publication is versioned by a generation/content identity separate from the association or unit it describes.

Conceptually:

```text
association identity     stable logical subject
unit identity            stable logical subject
publication generation   immutable/versioned statement about subject(s)
```

Publishing a new generation must not create a new association or unit identity.

The publication-generation contract may later use deterministic canonical JSON and cryptographic hashes, consistent with existing Kane Fabric artifact identity practice. The exact v1 canonical object and hash input are deliberately **not frozen in this document**; they will be specified only after the identity-anchor fields are exercised with a real recorded condominium reference.

## Source and physical-edge independence

Source acquisition is separate from content identity.

The same publication generation may be obtained through:

- the online administrative origin;
- Wiregate;
- an ESP32-S3 reference edge;
- another MCU/SBC/software edge;
- a development server;
- local/offline storage.

Changing source adapter, URL, IP address, hostname, device, or transport must not change:

- association identity;
- unit identity;
- category/schema identity;
- publication generation identity.

The physical edge is replaceable custody infrastructure, not civic identity.

## Human identity and authority boundary

Association/unit recognition does not establish who is authorized to speak for the association, who owns a unit, who resides in a unit, or whether a publication is official Board speech.

Those are separate authority/authentication questions.

`docs/CIVIC_ISSUANCE_AUTHORITY.md` now defines the architectural place for one such authority: a Civic Issuance Authority may attest a participant's current standing and granted affordances under published rules. Such an attestation does not redefine association identity, unit identity, or physical-device identity, and it must not be treated as the recorded property identity itself.

This separation is required so that:

- the Fabric can recognize that a recorded condominium and unit exist without Board cooperation;
- a unit owner or resident can publish bounded participant information without impersonating the association;
- an association-controlled publication can later establish its own authority evidence without redefining the association's logical identity;
- the browser can distinguish "publication about this association/unit" from "official statement by this association."

## Board-bypass consequence

Board participation is not a prerequisite for the identity graph.

A recorded condominium may be represented in the administrative layer from public recording evidence. Participant publications may reference that association and recorded unit identities even when the Board or property manager supplies no data.

This does **not** authorize a participant to alter association-instance facts, claim ownership, or speak for the Board. It only prevents Board or portal control from becoming the technical prerequisite for recognizing the underlying recorded civic object.

## Missing or disputed evidence

The browser must be able to represent missing, unresolved, or disputed association-instance evidence without inventing a different identity system.

A missing management contract, unavailable bylaws, disputed assessment ledger, unknown corporate status, or absent Board-supplied record does not by itself erase the recorded condominium or unit identity anchor.

Later contracts may carry evidence/provenance status for specific claims. They must not silently convert absence of evidence into a new association or unit identifier.

## V1 implementation boundary

The next implementation step after this architecture checkpoint is accepted is deliberately narrow:

1. define a source-neutral JSON contract for the association identity anchor and unit identity anchors;
2. define deterministic canonicalization and derived logical identifiers only after testing the fields against a real recorded condominium example;
3. add repository validation tests;
4. add browser parsing/inspection only after the contract is stable;
5. keep publication-generation, visibility/classification, and participant payload schemas as subsequent bounded contracts.

Do **not** combine the first identity schema with:

- account/login design;
- Board authorization;
- participant visibility rules;
- persistence/server mutation;
- edge provisioning;
- ESP32-specific fields;
- county-private database paths;
- proprietary portal identifiers.

## Acceptance criterion

This architecture checkpoint is accepted when the repository records this identity separation and CT102 confirms that the change is documentation-only relative to the last accepted executable Administrative Web state.

Acceptance of this document does not yet claim that an association/unit JSON identity contract is implemented.
