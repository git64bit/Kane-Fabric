# Kane Fabric Substrate Format v1

## Status

Milestone 3 format contract.

This document freezes the first browser-consumable shared-substrate wire format before the implementation is extracted from the historical Kane Condo renderer.

The v1 substrate contains only public geographic context:

- jurisdiction boundary/context;
- roads;
- water.

Buildings, classifications, qualifications, workflows, Mechanical Compiler state, and other application/subscription semantics are not part of this substrate format.

## Design requirements

The format must satisfy all of the following:

- deterministic bytes for identical accepted geographic state and format/profile versions;
- explicit jurisdiction identity rather than an implicit Kane County assumption;
- validation before rendering or activation;
- bounded-memory browser access;
- practical serving from an ESP32-S3 running Kane Fabric firmware on ESP-IDF;
- no server-side rendering requirement;
- no authoritative database mutation during compilation;
- no dependency on the original Kane Fabric operator or a private registry;
- clean separation between public civic-infrastructure artifacts and separately owned application/subscription artifacts.

Kane County, Illinois is the v1 reference implementation. It is not the namespace of the wire contract.

## Package layout

A complete v1 substrate publication contains exactly:

```text
county-overview.json
roads-lod.kfs
water-lod.kfs
substrate-manifest.json
```

`kfs` means Kane Fabric substrate. It identifies the software/project format, not Kane County.

The package directory is an activation unit. A publisher must stage and validate the complete package before replacing the currently activated directory.

A later edge-serving layout may expose the same immutable files through content-addressed object paths without changing their bytes or logical identities.

## Jurisdiction identity

Every component and the package manifest must carry the jurisdiction identity explicitly.

For the current U.S. implementation the required jurisdiction object is:

```json
{
  "country_code": "US",
  "state_code": "IL",
  "fips_code": "17089",
  "county_key": "kane-county",
  "name": "Kane County"
}
```

For v1:

- `country_code` is the two-letter uppercase country code stored by the Fabric database;
- `state_code` is the two-letter uppercase state/territory code stored by the Fabric database;
- `fips_code` is the five-digit U.S. county/county-equivalent FIPS code and is the durable cross-package jurisdiction code;
- `county_key` is a Fabric project identifier and is not a substitute for FIPS identity;
- `name` is descriptive display metadata and is never a durable primary key.

A browser, cache, edge node, or application must not infer jurisdiction from a filename, host name, path, Wi-Fi SSID, or physical device.

## Canonical JSON

All v1 JSON metadata and chunk record payloads use the canonical byte convention inherited from the proven Kane Condo implementation:

```python
json.dumps(
    value,
    ensure_ascii=False,
    separators=(",", ":"),
    sort_keys=True,
    allow_nan=False,
).encode("utf-8")
```

Consequences:

- UTF-8 only;
- no BOM;
- object keys sorted lexicographically by the generator;
- no insignificant whitespace;
- no NaN or Infinity values;
- no machine-specific paths, hostnames, process IDs, random UUIDs, filesystem timestamps, or local-time values in content-addressed structures.

Validators reconstruct this canonical representation after parsing and reject metadata whose bytes are not canonical.

The v1 compatibility suite will provide fixed byte/hash test vectors before Milestone 3 release. Those vectors, rather than implementation language, are the final interoperability authority for canonical serialization.

## Flat-container framing

`roads-lod.kfs` and `water-lod.kfs` use the same generic framing:

```text
8 bytes   magic/version
8 bytes   unsigned big-endian index byte length
N bytes   canonical UTF-8 JSON index
...       contiguous zlib-compressed canonical JSON chunks
```

The v1 magic values are:

```text
roads   KFSR001\n
water   KFSW001\n
```

Each magic value is exactly eight ASCII bytes.

The eight-byte index length is retained from the proven donor format so readers can discover the complete index with bounded initial I/O and without scanning the component.

Chunk offsets recorded in the index are relative to the first byte of the payload area immediately following the index.

Payload chunks are contiguous. There may be no overlap, unexplained gap, or trailing unindexed payload data.

## Compression

Every v1 chunk uses zlib-wrapped DEFLATE.

The index records:

```json
"compression":"zlib-deflate"
```

The compiler currently uses deterministic zlib compression at level 9.

The wire contract is the resulting compressed bytes and their SHA-256 identities, not a requirement that a browser or future implementation use the same compression library internally.

A later format version may introduce another codec only after measured browser and edge-device evidence justifies the additional complexity.

## Chunk descriptor

Every compressed chunk descriptor contains at least:

```json
{
  "bounds":[-88.0,41.0,-87.0,42.0],
  "feature_count":1,
  "length":1234,
  "offset":0,
  "payload_sha256":"<64 lowercase hex>",
  "records_sha256":"<64 lowercase hex>",
  "uncompressed_length":5678
}
```

The exact geographic bounds vary by layer and level.

Definitions:

- `offset`: byte offset relative to the payload area;
- `length`: compressed byte length;
- `uncompressed_length`: canonical JSON record byte length after decompression;
- `payload_sha256`: SHA-256 of the compressed bytes exactly as stored;
- `records_sha256`: SHA-256 of the canonical uncompressed record bytes;
- `feature_count`: number of whole geographic feature records contained by the chunk;
- `bounds`: EPSG:4326 bounds of the records represented by the chunk.

Features are not split merely to meet a target chunk count. Chunk boundaries must not create geographic seams.

## Component index common fields

Every `.kfs` component index contains these common fields:

```json
{
  "compression":"zlib-deflate",
  "format":"kane-fabric-substrate-roads",
  "jurisdiction":{},
  "levels":[],
  "srs_id":4326,
  "version":1
}
```

The road format key is:

```text
kane-fabric-substrate-roads
```

The water format key is:

```text
kane-fabric-substrate-water
```

The component index also records all accepted source-release identities needed to prove which authoritative geographic state produced the component.

A component whose jurisdiction or source-release identity does not agree with its enclosing manifest must be rejected even if its internal hashes are otherwise correct.

## County overview

`county-overview.json` is canonical UTF-8 JSON rather than a `.kfs` container because it is intentionally small and must be available immediately for browser viewport framing.

Its format key is:

```text
kane-fabric-substrate-overview
```

and its version is `1`.

It contains at least:

- jurisdiction identity;
- EPSG:4326 SRS identity;
- exact accepted boundary bounds;
- deterministic center;
- accepted boundary release identity;
- deterministic simplified exterior boundary rings;
- source and output vertex counts;
- simplification-policy identity and applied tolerance.

Exact package bounds come from accepted source geometry, not the simplified overview geometry.

## Road levels

The generic v1 road level keys are:

```text
orientation
context
detail
```

The level names describe browser/display purpose, not an assumed road classification scheme.

For Kane County v1, membership follows the previously proven Kane source policy because the accepted source does not retain an official functional road class:

- `orientation`: longest features sufficient to cover 35% of deterministic coordinate-length score;
- `context`: longest features sufficient to cover 75%;
- `detail`: every accepted road feature.

The Kane policy is recorded explicitly in component metadata. It is not the definition of road importance for another jurisdiction.

The level sets are monotonic and the detail level retains exact accepted source coordinates.

## Water levels

The generic v1 water level keys are:

```text
overview
context
detail
```

For Kane County v1, membership follows the previously proven coordinated Fox River/creek policy:

- `overview`: all accepted Fox River features and no creeks;
- `context`: all accepted Fox River features plus enough longest creeks to cover 60% of deterministic creek coordinate-length score;
- `detail`: every accepted Fox River and creek feature.

This is Kane County source policy and is recorded as such. It is not a generic hydrologic classification claim.

## Chunk ordering

Within a level, v1 may use deterministic 16-bit Morton ordering based on feature center/bounds followed by stable source-feature identity as a tie breaker.

Morton order is an internal storage-locality mechanism only. It must not become a user-facing geographic identity, grid, sector, cell, or administrative partition.

The initial Kane implementation begins with a maximum of 256 whole features per detailed chunk because that value has existing real-data benchmark evidence. The applied chunking policy is recorded in the component index and is not a universal county constant.

## Substrate manifest

`substrate-manifest.json` is canonical UTF-8 JSON with:

```text
format   kane-fabric-substrate-manifest
version  1
```

It contains at least:

- jurisdiction identity;
- authoritative Fabric database audit identity;
- exactly one accepted release identity for each required substrate dataset;
- component descriptors;
- deterministic substrate content identity;
- optional isolated build/publication time metadata.

The required component roles, in order, are:

```text
county_overview
roads
water
```

Each descriptor contains:

```text
role
path
format
version
byte_length
sha256
```

Absolute paths are prohibited.

## Accepted-release inventory

Each required accepted source release recorded by the manifest contains at least:

```text
dataset_key
release_key
content_sha256
feature_count
```

Compilation fails if a required dataset has zero accepted releases, multiple accepted releases, or stored feature inventory inconsistent with accepted release metadata.

Candidate state never enters a published substrate merely because it is newer.

## Substrate content identity

The manifest carries:

```text
substrate_content_sha256
```

This is the SHA-256 of canonical content-identity metadata containing:

1. jurisdiction identity;
2. ordered accepted-release inventory;
3. ordered component descriptors.

Build/publication timestamps are excluded from this hash.

Therefore identical accepted geographic state compiled under the same v1 format/profile rules produces the same substrate content identity regardless of build time or machine.

## ESP32-S3 / ESP-IDF serving constraint

The v1 files are designed so the ESP32-S3 never needs to load an entire county component into RAM merely to serve it.

The intended browser access pattern for `.kfs` files is:

```text
GET manifest / overview
        ↓
read fixed 16-byte component prefix
        ↓
read canonical index
        ↓
select required chunks
        ↓
read only selected compressed byte ranges
        ↓
browser validates + decompresses + renders
```

Milestone 5 will freeze the HTTP edge contract, but Milestone 3 requires the format to remain compatible with a small ESP-IDF URI handler that can:

- read request headers;
- serve a whole immutable file when requested;
- serve a single explicit byte range from persistent storage;
- set ordinary HTTP response headers;
- stream bounded buffers rather than allocate the requested object in full.

The anticipated range response uses normal HTTP semantics (`206 Partial Content`, `Content-Range`, `Content-Length`, and `Accept-Ranges: bytes`). Range-serving behavior is an edge-server contract, not part of the `.kfs` byte identity.

A future edge implementation may use different hardware or server software while serving the same immutable v1 files.

## Browser decompression constraint

V1 deliberately retains zlib-wrapped DEFLATE because the browser can decompress this format using the standards-based Compression Streams API (`DecompressionStream("deflate")`) without bundling a third-party decompression library.

Browser code must still validate the recorded compressed payload SHA-256 and the decompressed canonical-record SHA-256 at the appropriate validation boundary.

## Size discipline

Milestone 3 must measure actual Kane County component/index/chunk sizes and browser access behavior before declaring final edge acceptance.

V1 implementations must use bounded reads and must fail clearly rather than silently truncating offsets or lengths on a constrained platform.

No county-wide component may depend on whole-file RAM residency.

If a future jurisdiction produces a component too large for practical seek/range serving on the reference edge, the correct response is an explicit later sharding/versioning design, not hidden truncation or an implicit requirement for desktop-class hardware.

## Validation failures

A v1 validator rejects at least:

- wrong magic or unsupported format/version;
- malformed UTF-8 or malformed JSON;
- noncanonical JSON metadata;
- truncated prefix, index, or payload;
- invalid index length;
- duplicate or unknown required level identities where the component contract forbids them;
- noncontiguous, overlapping, or out-of-bounds payload offsets;
- trailing unindexed payload bytes;
- invalid zlib payload;
- compressed or uncompressed length disagreement;
- compressed-payload SHA-256 disagreement;
- canonical-record SHA-256 disagreement;
- malformed geographic bounds;
- jurisdiction mismatch;
- accepted-release mismatch;
- component descriptor byte-length or SHA-256 mismatch;
- missing, duplicated, or swapped required package components;
- component bytes generated from another accepted authoritative state.

## Activation rule

Compilation is staged outside the active publication directory.

The compiler:

1. validates required accepted geographic state;
2. generates all three components into staging;
3. validates each component;
4. generates the manifest from staged bytes;
5. validates the complete package;
6. compares reproducibility when required by the milestone gate;
7. atomically activates the complete directory;
8. restores the previous complete package if activation fails.

The compiler never mutates authoritative database state as a side effect of substrate generation.

## Rights and ownership boundary

This format is part of the Kane Fabric civic-infrastructure layer and is intended to remain usable independently of any application subscription.

A later subscription may reference the substrate and may be served by the same physical ESP32-S3, but co-location does not transfer ownership or licensing between layers.

Public Kane Fabric substrate and edge firmware do not force building categories, qualifications, workflows, Mechanical Compiler state, or other separately owned application semantics into the public domain.

Likewise, a restricted or proprietary subscription does not acquire ownership of the underlying public Kane Fabric substrate.

## Compatibility rule

V1 readers must reject unknown major format versions rather than guessing.

A future extension may add optional metadata only when old v1 readers can safely ignore it without changing the meaning or identity of required fields. Any framing, compression, offset, hash, or required-semantic change requires a new format version.

## Implementation gate

No Milestone 3 generator should be considered released until tests prove:

- deterministic v1 bytes from fixed fixtures;
- fixed canonical JSON/hash vectors;
- correct framing and offset validation;
- corruption/truncation rejection;
- explicit jurisdiction mismatch rejection;
- accepted-release mismatch rejection;
- repeated Kane County builds produce identical component bytes;
- the browser can selectively obtain and decompress required chunks;
- the format can be served with bounded memory from the ESP32-S3 reference architecture.
