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

Official Kane County tax/assessment material establishes a Kings Row condominium record family in West Dundee associated with Lot 34 of Old World Subdivision and parcel series `03-27-129-...`. The County Clerk's 2023 judgment book identifies parcel `03-27-129-016` as `KINGS ROW CONDO - UNIT 208-A`. That establishes a real association/unit record family and a public unit designation, but it does not by itself establish the Recorder's original declaration instrument or the unit's Recorder legal/plat reference.

The Kane County Recorder states that documents recorded from 1977 to date are available through its computer/imaging system, while older land instruments are indexed in Original Tract, Grantor/Grantee, or Mortgagor/Mortgagee books and microfilm. The identity contract therefore must not assume that every valid declaration reference has a modern computerized document-number syntax.

The regression suite preserves this boundary with a synthetic tract-book/page-style declaration reference. The test establishes format compatibility only; it is not a claimed Kings Row recording reference.

Public source references used for this evidence pass:

```text
https://www.kanecountyrecorder.net/about/
https://clerk.kanecountyil.gov/TaxExtension/Documents/Tax/Judgment%20Books/2023%20Judgment%20Book.pdf
```

The original Kings Row condominium declaration recording reference remains unresolved. No placeholder declaration number, parcel number, street address, management identifier, inferred modern document number, or tax description may substitute for it.

## Acceptance consequence

The contract implementation at `a1629361063f4dd2806bcddade05f7cb9b1548ed` remains accepted. The post-acceptance evidence regression at `9ec26bb40a1af5912d60d49ac8be6a64c8ccc90f` must pass CT102 before it is recorded as an accepted hardening checkpoint.

Canonicalization and derived logical identifiers remain intentionally deferred until Recorder evidence supplies the original declaration recording reference and at least one unit's recorded legal/plat reference in the form actually used by the public land record.
