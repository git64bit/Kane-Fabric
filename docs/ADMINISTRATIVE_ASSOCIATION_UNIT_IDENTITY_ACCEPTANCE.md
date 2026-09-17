# Administrative Association/Unit Identity Contract Acceptance

Date: 2026-09-17

## Accepted contract checkpoint

CT102 accepted the first source-neutral association/unit identity contract at:

```text
a1629361063f4dd2806bcddade05f7cb9b1548ed
```

Observed on `srv-b` / CT102 (`kane-fabric`) at `/tmp/kane-fabric-ms2`:

```text
web/run-tests.sh  70/70 PASS
worktree          clean
```

The accepted implementation delta from the architecture checkpoint `199e090583c265285bf8a2a69fb8da6f0a1845a2` is exactly:

```text
administration/contracts/association-unit-identity-v1.mjs
administration/contracts/association-unit-identity-v1.schema.json
web/run-tests.sh
web/test-admin-identity-contract.mjs
```

## Contract boundary

The v1 contract freezes only source-neutral recorded identity anchors.

Association anchor:

```text
jurisdiction
recording_authority_reference
original_declaration_recording_reference
```

Unit anchor:

```text
recorded_unit_designation
recorded_unit_reference
```

The contract deliberately does not contain or derive Board identity, owner/resident identity, account or portal identifiers, source URLs, transport identity, physical-edge/device identity, association logical IDs, unit logical IDs, publication-generation IDs, or hashes.

Validation fails closed for malformed jurisdiction codes, missing declaration references, incomplete unit anchors, duplicate exact unit anchors, and unknown fields.

## Real-record exercise status

The next required step is to exercise these raw anchor fields against a real recorded condominium example before canonicalization or derived logical identifiers are frozen.

Public Kane County tax/assessment material establishes a Kings Row condominium record family in West Dundee associated with Lot 34 of Old World Subdivision, parcel series `03-27-129-...`, and recorded unit designations such as `208-A`, `211-A`, and `312-A`. This is sufficient to establish that the contract's association/unit distinction maps to a real county record family, but it is not sufficient to instantiate the accepted association anchor because the original condominium declaration recording reference has not yet been established from the Recorder's land-record index.

No placeholder declaration number, parcel number, street address, management identifier, or inferred document number may substitute for the required original declaration recording reference.

## Acceptance consequence

The contract implementation is accepted. Canonicalization and derived logical identifiers remain intentionally deferred until the Recorder evidence supplies the original declaration recording reference and at least one unit's recorded legal/plat reference in the form actually used by the public land record.
