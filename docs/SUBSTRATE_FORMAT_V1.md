# Kane Fabric Substrate Format v1

## Status

Milestone 3 durable wire-format contract.

This contract defines the first browser-consumable Kane Fabric shared substrate before road/water implementation is extracted from the historical Kane Condo renderer.

The v1 substrate contains only civic geographic context:

- jurisdiction boundary/context;
- roads;
- water.

Buildings, categories, classifications, qualifications, workflows, Mechanical Compiler state, and other application/subscription semantics are outside this format and do not inherit Kane Fabric's public-domain status merely because they are composed with it.

Kane County, Illinois is the reference deployment. It is not the namespace of the wire contract.

## Requirements

V1 must provide:

- deterministic bytes for identical accepted geographic state and format/profile versions;
- explicit jurisdiction identity;
- accepted-release provenance;
- validation before rendering or activation;
- bounded-memory browser and ESP32-S3 access;
- no server-side rendering requirement;
- no authoritative database mutation during compilation;
- no private registry or continuing permission requirement;
- clean separation between the public substrate and separately owned subscriptions.

## Package layout

A complete v1 substrate publication contains exactly:

```text
county-overview.json
roads-lod.kfs
water-lod.kfs
substrate-manifest.json
```

`kfs` means Kane Fabric substrate. It identifies the software/project format, not Kane County.

The complete directory is an activation unit. Components are generated and validated in staging before the activated package is replaced.

## Jurisdiction identity

Every component and manifest carries jurisdiction identity explicitly. The current authoritative Kane Fabric database uses:

```json
{
  "country_code":"US",
  "state_code":"IL",
  "fips_code":"17089",
  "county_key":"kane-county-il",
  "name":"Kane County"
}
```

For v1:

- `fips_code` is the durable U.S. county/county-equivalent code used across packages;
- `county_key` is a Fabric project identifier and is not a substitute for FIPS identity;
- `name` is descriptive display metadata, not a primary key;
- jurisdiction must never be inferred from filename, host, directory, Wi-Fi SSID, or physical edge device.

The design horizon includes U.S. county-equivalent jurisdictions even where the local name is not "county".

## Canonical JSON

All v1 JSON metadata and uncompressed chunk records use the proven deterministic convention:

```python
json.dumps(
    value,
    ensure_ascii=False,
    separators=(",", ":"),
    sort_keys=True,
    allow_nan=False,
).encode("utf-8")
```

Therefore canonical structures use UTF-8, no BOM, sorted object keys, no insignificant whitespace, and no NaN/Infinity. Content-addressed structures must not contain machine paths, hostnames, process IDs, random UUIDs, filesystem timestamps, or local-time values.

Validators reserialize parsed metadata and reject noncanonical bytes. Fixed byte/hash test vectors are part of the v1 compatibility suite.

## Flat-container framing

`roads-lod.kfs` and `water-lod.kfs` use:

```text
8 bytes   magic/version
8 bytes   unsigned big-endian index byte length
N bytes   canonical UTF-8 JSON index
...       contiguous zlib-compressed canonical JSON chunks
```

Magic values:

```text
roads   KFSR001\n
water   KFSW001\n
```

Each magic is exactly eight ASCII bytes. The fixed 16-byte prefix lets a constrained reader discover index length without loading or scanning the component.

Chunk offsets are relative to the first payload byte after the index. Payload chunks must be contiguous, non-overlapping, and fully indexed; trailing unindexed payload bytes are invalid.

## Compression

Every v1 chunk uses zlib-wrapped DEFLATE and the index records:

```json
"compression":"zlib-deflate"
```

The compiler begins with deterministic zlib level 9 because that behavior was proven by Kane Condo. A later codec requires a new format decision justified by measured browser/edge evidence.

## Chunk descriptor

Every chunk records at least:

```text
bounds
feature_count
offset
length
uncompressed_length
payload_sha256
records_sha256
```

`payload_sha256` hashes the compressed bytes exactly as stored. `records_sha256` hashes the canonical uncompressed JSON record bytes. Features are not split merely to satisfy a target chunk count, so chunk boundaries cannot create geographic seams.

## Component identities

The road component uses:

```text
format  kane-fabric-substrate-roads
version 1
magic   KFSR001\n
path    roads-lod.kfs
```

The water component uses:

```text
format  kane-fabric-substrate-water
version 1
magic   KFSW001\n
path    water-lod.kfs
```

The overview uses:

```text
format  kane-fabric-substrate-overview
version 1
path    county-overview.json
```

The manifest uses:

```text
format  kane-fabric-substrate-manifest
version 1
path    substrate-manifest.json
```

Role, relative path, format, and version are bound together and must not be swapped independently.

## Common `.kfs` index

Every flat component index contains at least:

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

It also carries the accepted source-release identities required to prove the authoritative geographic state from which it was compiled.

A structurally valid component is still rejected if its jurisdiction or release lineage disagrees with the enclosing manifest.

## County overview

`county-overview.json` remains small canonical JSON for immediate viewport fitting and coarse boundary drawing. It contains:

- jurisdiction identity;
- EPSG:4326 identity;
- exact accepted boundary bounds and deterministic center;
- accepted boundary release identity;
- simplified exterior rings;
- source/output vertex counts;
- explicit simplification-policy identity and applied tolerance.

Exact fit bounds come from accepted source geometry, never the simplified outline.

For Kane County v1 the proven starting simplification policy is Ramer-Douglas-Peucker with tolerance `max_extent / 2048`. The applied policy is explicit metadata, not a universal jurisdiction rule.

## Road LOD

Generic v1 level keys are:

```text
orientation
context
detail
```

The Kane road source does not retain authoritative functional road classification, so Kane v1 reuses the proven deterministic source policy:

- `orientation`: longest features sufficient for 35% of coordinate-length score;
- `context`: longest features sufficient for 75%;
- `detail`: all accepted road features with exact accepted coordinates.

This is Kane source policy. Another jurisdiction with authoritative road class may choose membership using that source semantics while still producing the same generic component contract.

## Water LOD

Generic v1 level keys are:

```text
overview
context
detail
```

Kane v1 reuses the coordinated Fox River/creek policy:

- `overview`: all accepted Fox River features, no creeks;
- `context`: all Fox River features plus longest creeks sufficient for 60% of creek coordinate-length score;
- `detail`: every accepted Fox River and creek feature with exact accepted coordinates.

This is Kane source policy, not a universal hydrologic classification.

## Ordering and chunk policy

V1 may use deterministic 16-bit Morton ordering followed by stable source identity as a tie breaker. Morton order is an invisible storage-locality mechanism, never a user-facing grid, cell, sector, or geographic identity.

Kane implementation begins with a maximum of 256 whole features per detailed chunk because historical real-data benchmarks support it. The applied policy is recorded in metadata and is not a universal county constant.

## Manifest and content identity

`substrate-manifest.json` inventories exactly these component roles, in order:

```text
county_overview
roads
water
```

Each component descriptor carries:

```text
role
path
format
version
byte_length
sha256
```

The manifest also records jurisdiction identity, authoritative database audit identity, required accepted releases, and:

```text
substrate_content_sha256
```

The content hash is computed from canonical jurisdiction identity, accepted-release inventory, and ordered component descriptors. Build/publication time is excluded from this identity.

Each accepted release descriptor contains at least:

```text
dataset_key
release_key
content_sha256
feature_count
```

Compilation fails if a required dataset has zero or multiple accepted releases, or if accepted-release metadata disagrees with stored feature inventory. A candidate never enters the substrate merely because it is newer.

## ESP32-S3 / ESP-IDF constraint

ESP32-S3 edge serving is part of the architecture now even though firmware implementation is scheduled later.

V1 is designed so an ESP32-S3 does not need whole-county component residency in RAM. The intended access pattern is:

```text
GET manifest / overview
        ↓
read fixed 16-byte `.kfs` prefix
        ↓
read canonical index
        ↓
select needed chunks
        ↓
read selected compressed byte ranges
        ↓
browser validates + decompresses + renders
```

Milestone 5 will freeze and prove the Kane Fabric ESP-IDF HTTP contract. Milestone 3 must keep the bytes compatible with a small URI handler that can read request headers, set response headers, seek persistent storage, and stream bounded buffers.

The anticipated server behavior supports ordinary single byte-range requests with `206 Partial Content`, `Content-Range`, `Content-Length`, and `Accept-Ranges: bytes`. HTTP range behavior is not part of `.kfs` content identity.

The ESP32-S3 is the initial minimum reference edge, not the permanent definition of an edge node.

## Browser decompression

V1 retains zlib-wrapped DEFLATE so a modern browser can use the standards-based Compression Streams API with `DecompressionStream("deflate")`; no bundled decompression library is required by the browser contract.

The browser still validates compressed and decompressed SHA-256 identities at the required boundary.

## Validation failures

A v1 validator rejects at least:

- wrong magic or unsupported format/version;
- malformed or noncanonical UTF-8 JSON;
- truncated prefix, index, or payload;
- invalid/overlapping/noncontiguous offsets;
- trailing unindexed payload bytes;
- invalid zlib data;
- compressed or uncompressed length disagreement;
- payload or record hash mismatch;
- malformed bounds;
- jurisdiction mismatch;
- accepted-release mismatch;
- component byte-length/hash mismatch;
- missing, duplicate, or swapped required components;
- components generated from a different accepted authoritative state.

## Build and activation

A complete compiler run:

1. opens one authoritative Fabric GeoPackage read-only;
2. validates required accepted substrate releases;
3. generates all components in staging;
4. validates every component;
5. generates and validates the manifest;
6. performs required reproducibility comparison;
7. atomically activates the complete directory;
8. restores the prior complete directory if activation fails.

Substrate compilation never mutates authoritative database state.

## Rights boundary

The v1 substrate, compiler, browser substrate code, and Kane Fabric ESP32-S3 edge firmware belong to the Kane Fabric civic-infrastructure layer.

A subscription may be stored on the same edge and composed in the same browser without acquiring or transferring rights. Public Kane Fabric does not force categories, qualifications, workflows, Mechanical Compiler state, or other separately owned application data into the public domain. Conversely, a restricted or proprietary subscription does not acquire ownership of the public substrate.

## Compatibility rule

V1 readers reject unknown major format versions rather than guessing. Framing, compression, offset, hash, or required-semantic changes require a new version.

## Release gate

Milestone 3 cannot release until tests prove:

- fixed canonical JSON/hash vectors;
- deterministic component bytes;
- framing/offset/hash validation and corruption rejection;
- explicit jurisdiction and release mismatch rejection;
- repeated Kane County builds are byte-identical;
- browser selective loading and zlib decompression;
- browser rendering of boundary, roads, and water without a subscription;
- bounded-memory serving compatibility with the ESP32-S3 reference architecture.
