# Milestone 3 Design — Shared Substrate

## Status

Design baseline for Milestone 3.

Milestone 3 produces the first deterministic browser-consumable Kane Fabric shared substrate for:

- jurisdiction boundary/context;
- roads;
- water.

Buildings and application classifications are intentionally excluded. They belong to later subscription work, not the shared substrate.

## Governing objectives

Milestone 3 is the first new durable-format work after the Milestone 2 geographic-core release. It therefore applies two forward project requirements directly:

1. Kane Fabric remains independently usable public civic infrastructure as defined in `docs/CIVIC_INFRASTRUCTURE_PRINCIPLES.md`.
2. New durable package, manifest, database, and protocol identities must not unnecessarily assume Kane County as defined in `docs/MULTI_COUNTY_DESIGN.md`.

Kane County remains the only required operational implementation for this milestone.

## Historical evidence to reuse

Kane Condo `0.4` is a historical regression/design oracle, not a runtime dependency.

Its render work already established several geographic mechanisms worth preserving where they remain applicable:

- a single flat-file component container using an indexed sequence of compressed deterministic chunks;
- deterministic overview and LOD generation;
- canonical JSON metadata;
- per-chunk lengths, bounds, and SHA-256 verification;
- deterministic spatial ordering as an internal storage detail rather than a user-visible grid;
- whole-component validation before use;
- a package manifest tying derived components to one accepted authoritative database state;
- package content identity independent of creation time;
- staged complete-package validation before atomic directory replacement.

Milestone 3 should extract these geographic/package properties rather than copy Condo application semantics.

## Package boundary

The initial Fabric substrate package is a directory containing exactly the shared geographic components plus one manifest:

```text
county-overview.json
roads-lod.<flat-container-extension>
water-lod.<flat-container-extension>
substrate-manifest.json
```

The exact flat-container extension and magic bytes are part of implementation Batch 001 and must identify Kane Fabric rather than Kane Condo.

The package directory is a publication unit. A new package is built and validated in staging before it replaces an activated package. Components are not incrementally copied into an active package.

Later edge-serving work may expose the same immutable component bytes through content-addressed object paths. Milestone 3 does not require an edge-node layout yet.

## Jurisdiction identity

A substrate manifest must identify its jurisdiction explicitly. A browser or cache must not infer Kane County from a filename, server, directory, or package location.

The Kane Fabric database already records:

- `county_key`;
- human-readable name;
- two-letter state code;
- country code;
- five-digit FIPS code.

For U.S. county and county-equivalent packages, the five-digit FIPS code is the primary durable jurisdiction code currently available in the Fabric core. The manifest should carry the full jurisdiction record rather than relying on the display name alone.

Initial manifest shape:

```json
{
  "jurisdiction": {
    "country_code": "US",
    "state_code": "IL",
    "fips_code": "17089",
    "county_key": "kane-county",
    "name": "Kane County"
  }
}
```

`name` and `county_key` are descriptive/project identifiers. `fips_code` is the durable U.S. geographic code for cross-package identity.

This milestone does not introduce a national registry service.

## Accepted-state contract

A substrate is compiled only from accepted geographic state.

The manifest records the exactly one accepted release used for each substrate dataset:

- boundary;
- roads;
- water source(s).

For each accepted release, record at least:

- dataset key;
- release key;
- source content SHA-256;
- feature count.

Compilation must fail if a required dataset has zero accepted releases or multiple accepted releases, or if accepted-release metadata disagrees with stored feature inventory.

A candidate release must never enter a published substrate merely because it is newer.

## Component format

Road and water components use the proven flat-container model:

1. fixed ASCII magic/version identifier;
2. unsigned 64-bit big-endian canonical-index byte length;
3. canonical UTF-8 JSON index;
4. contiguous compressed canonical-record chunks.

The index contains no machine-specific path and no creation timestamp.

Each chunk records at least:

- level;
- bounds;
- record count;
- payload offset;
- compressed byte length;
- uncompressed byte length;
- compressed payload SHA-256;
- canonical-record SHA-256.

Offsets are relative to the payload area. Chunks are contiguous and must not overlap or leave unexplained gaps.

Compression begins with zlib because it was already proven by the donor implementation and requires no new Kane Fabric platform dependency. A later format version may add another codec only when measured browser/edge requirements justify it.

## Canonical serialization

Determinism is part of package identity.

Canonical JSON used for indexes, manifests, and chunk records must have a single byte representation for the same logical value. Generators must not embed:

- absolute paths;
- hostnames;
- process identifiers;
- unordered map output;
- local timezone values;
- filesystem timestamps;
- nondeterministic UUIDs.

Repeated compilation from the same accepted geographic state and the same format/profile version must produce byte-identical component payloads.

## County overview

`county-overview.json` is a small canonical payload for immediate browser framing and coarse boundary drawing.

It contains:

- Fabric format key/version;
- jurisdiction identity;
- accepted boundary release identity;
- EPSG:4326 bounds;
- center;
- deterministic simplified exterior boundary geometry;
- source/output vertex counts;
- simplification rule identity and tolerance.

The historical Kane rule of simplifying exterior rings at `max_extent / 2048` is a proven Kane County starting policy, not a universal truth for every future jurisdiction. Milestone 3 may retain it for Kane County while making the applied policy explicit in the payload.

Exact bounds come from accepted source geometry, not from the simplified overview outline.

## Road LOD

The accepted Kane road source does not preserve road name, route number, ownership, functional class, or pavement class. Kane Fabric must not invent those semantics.

For Kane County, the historical deterministic LOD policy remains a valid starting policy:

- `orientation`: longest features sufficient to cover 35% of accepted coordinate-length score;
- `context`: longest features sufficient to cover 75%;
- `detail`: all accepted road features.

Geometry simplification:

- `orientation`: `road_extent / 2048`;
- `context`: `road_extent / 8192`;
- `detail`: exact accepted coordinates.

Membership is monotonic: orientation is a subset of context, which is a subset of detail.

This selection method is Kane-source policy arising from missing road classification semantics. It must not be encoded as the definition of what a road LOD means for all jurisdictions. A future source with authoritative functional class may use that source semantics while producing the same generic package contract.

## Water LOD

Kane County currently has coordinated accepted Fox River and creek datasets whose retained attributes do not provide a generic hydrologic importance hierarchy.

For Kane County, the historical deterministic policy remains a valid starting policy:

- `overview`: all accepted Fox River features, no creeks;
- `context`: all Fox River features plus longest creek features sufficient to cover 60% of accepted creek coordinate-length score;
- `detail`: all accepted Fox River and creek features.

Geometry simplification:

- `overview`: `water_extent / 2048`;
- `context`: `water_extent / 8192`;
- `detail`: exact accepted coordinates.

Fox River remains present at every level.

As with roads, this is Kane County source policy, not a universal hydrologic classification contract.

## Chunking and spatial order

The historical real-data benchmark found 256-record chunks useful for detailed viewport and hit-test access, while larger chunks reduced index overhead and improved broad reads.

Milestone 3 should begin with a maximum of 256 whole features per detailed chunk because that value is supported by existing evidence. It is not a permanent cross-jurisdiction constant.

Records may use deterministic Morton ordering based on feature bounds/centers to improve locality. Morton order is an internal storage detail only. Kane Fabric must not resurrect County Field Map sectors, cells, grids, or VOID-mask semantics as user-facing identity.

Features are never split merely to fit a chunk. Complete source geometry remains complete within its level representation so chunk boundaries cannot introduce visible geographic seams.

## Manifest and identities

`substrate-manifest.json` inventories exactly the components in the package and ties them to one accepted authoritative geographic state.

Each component descriptor records:

- role;
- conventional relative filename;
- component format/version;
- byte length;
- SHA-256.

The manifest also records:

- Fabric substrate manifest format/version;
- jurisdiction identity;
- authoritative database identity needed for audit/reproduction;
- accepted source-release inventory;
- component descriptors;
- deterministic substrate content SHA-256;
- optional `created_at` publication/build metadata isolated from content identity.

`substrate_content_sha256` is computed from canonical jurisdiction identity, accepted-release inventory, and component descriptors. It excludes `created_at`.

The resulting content hash is the durable compiled-generation identity. Human-readable directory names may contain convenience labels, but they are not the authority for content identity.

## Validation

A validator must reject at least:

- wrong magic or unsupported component version;
- malformed or noncanonical index/manifest JSON;
- truncated index or payload;
- overlapping or noncontiguous chunk offsets;
- invalid compressed data;
- compressed/uncompressed length disagreement;
- chunk hash disagreement;
- component byte-length or SHA-256 disagreement;
- jurisdiction mismatch between component and manifest;
- accepted-release mismatch;
- required component missing or duplicated;
- component generated from another accepted database state.

Browser-side validation may be narrower than compiler-side semantic validation, but it must at least be able to verify package structure and component/content identity before rendering untrusted bytes.

## Reproducible build and activation

A complete build:

1. reads one authoritative Fabric GeoPackage;
2. verifies required accepted substrate releases;
3. generates all components into a temporary sibling staging directory;
4. validates every component;
5. generates the manifest from the staged bytes;
6. validates the complete package;
7. promotes the complete directory atomically;
8. retains/restores the previous complete package if activation fails.

The build must not mutate authoritative database state.

Repeated builds from identical accepted state and format/profile versions must produce byte-identical geometry components and identical manifest content after excluding only explicitly isolated build-time metadata.

## Browser proof

Milestone 3 is not complete merely because Python can generate valid files.

The browser proof must demonstrate, without application subscription data:

- loading the overview;
- validating component/package identities needed by the browser;
- decompressing road and water chunks;
- selecting LOD content appropriate to the demonstrated view;
- drawing county boundary/context, roads, and water;
- panning and zooming Kane County independently of Condo or another subscription.

The browser must not need the authoritative GeoPackage or county refresh machinery.

## Explicit exclusions

Milestone 3 does not include:

- building geometry as shared substrate;
- Condo classification data;
- Mechanical Compiler data;
- subscription contracts;
- ESP32 edge serving;
- multi-node distribution;
- national deployment automation;
- a second-county implementation;
- a private registry or permission service;
- a return to County Field Map grids, cells, sectors, or VOID masks.

## Implementation order

1. freeze Fabric component/manifest format identifiers and canonical serialization rules;
2. implement county overview generation/validation from Fabric-owned tables;
3. implement Kane road LOD generation/validation behind the generic substrate component contract;
4. implement coordinated Kane water LOD generation/validation behind the generic contract;
5. implement complete substrate manifest validation and content identity;
6. implement reproducible staged build and atomic activation;
7. replay against the accepted Kane County database on CT102;
8. implement the minimal browser loader/validator/renderer;
9. prove browser navigation of the shared substrate;
10. record Milestone 3 release evidence.

Behavior-preserving extraction from the historical renderer is preferred over unnecessary redesign, but no Condo-specific application ownership or Kane-only implicit package identity may cross into the new durable Fabric contract.
