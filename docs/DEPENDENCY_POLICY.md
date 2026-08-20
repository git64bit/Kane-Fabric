# Kane Fabric Dependency and Vendoring Policy

## Hard licensing rule

Kane Fabric-authored code remains under the repository's existing Unlicense/public-domain dedication.

The root `LICENSE` is a hard project invariant. A dependency is not acceptable if using, modifying, linking, embedding, distributing, or vendoring it would require Kane Fabric-authored code to adopt another license.

Vendored third-party material retains its own license, copyright, attribution, and notice requirements. Those terms apply to that third-party material; they do not replace the Unlicense for Kane Fabric-authored code.

The repository may therefore contain multiple licensing scopes after vendoring:

- root `LICENSE`: Kane Fabric-authored code;
- `vendor/...`: the original license(s) of the vendored component;
- generated `THIRD_PARTY_NOTICES` material: attribution/notice obligations for vendored components.

Do not rewrite or broaden the root `LICENSE` to absorb third-party terms.

## No upstream compatibility dependency at release

By final release, every third-party implementation that Kane Fabric ships, embeds, links, imports as a project runtime, or requires as a project-controlled build/test tool must be pinned and vendored.

A final Kane Fabric build/test/deployment must not require a package manager to resolve a moving dependency graph from the network. In particular, project-controlled dependencies must not depend on live `pip`, `npm`, Cargo, Git, or similar resolution.

Each vendored component must record at least:

- exact version/tag/commit;
- immutable source SHA-256;
- original source URI;
- license/SPDX identity;
- complete required license and notice files;
- whether the component is runtime, build, test, firmware SDK/toolchain, or documentation/reference material;
- Kane Fabric reason for retaining it.

Vendored source is an immutable input. Updating it is an explicit Kane Fabric change with a compatibility and license review; an upstream release does not automatically update Kane Fabric.

## Platform boundary

Vendoring cannot meaningfully include every external layer of a computing system. Kane Fabric therefore distinguishes **third-party project implementations** from **target-platform contracts**.

Target-platform contracts are interfaces supplied by the execution environment rather than code incorporated into Kane Fabric. Current examples are:

- ordinary Linux/POSIX process, file, socket, and filesystem behavior on the declared server platform;
- standard browser APIs used by the public substrate reader (`fetch`, HTTP byte ranges, WebCrypto SHA-256, `DecompressionStream("deflate")`, DOM/canvas APIs when rendering is added);
- TCP/IP and HTTP protocol behavior;
- authoritative public source endpoints used to harvest county geography.

Kane Fabric must define and test the portions of these interfaces it requires. It must fail closed when an authoritative source contract changes. It does not assume an upstream service or browser will preserve undocumented behavior.

If Kane Fabric begins packaging a platform implementation itself, that implementation crosses the boundary and becomes a vendored third-party component.

## Current implementation dependency direction

### CPython

Current database, source-harvesting, compiler, validation, and test code is Python and deliberately uses the Python standard library rather than PyPI packages. CPython is nevertheless a third-party runtime. If the final Kane Fabric distribution retains Python as a project-controlled runtime, an exact CPython distribution must be pinned and vendored with its license set.

### SQLite

Kane Fabric's authoritative GeoPackage implementation uses Python's `sqlite3` interface directly. SQLite is therefore a native dependency behind the current runtime. The final runtime must use a pinned SQLite implementation rather than accepting an arbitrary future system SQLite ABI/behavior when reproducibility matters.

### zlib

The `.kfs` v1 contract deliberately freezes zlib-wrapped DEFLATE. The compiler currently reaches zlib through Python's standard library; the browser reaches the same wire contract through the browser platform's `DecompressionStream("deflate")`. A project-controlled compiler runtime must pin/vendor the zlib implementation it uses to produce release bytes.

### TLS/OpenSSL

Official-source harvesting uses Python `urllib` over HTTPS. The current Python runtime's TLS implementation is therefore part of the executable dependency chain even though Kane Fabric does not import a third-party HTTP package. If the final harvester ships a project-controlled Python runtime, its TLS implementation must also be pinned/vendored. OpenSSL 3.x is acceptable in principle under Apache-2.0, subject to the exact selected release and notices.

### Browser substrate reader

The browser reader has no npm dependencies. `substrate/browser/package.json` exists only to select ES module semantics. Browser Web APIs are target-platform contracts, not vendored JavaScript libraries.

Node.js, when used to execute the browser-contract probe, is development/test tooling only. It is not part of the substrate publication and is not required by an edge node or end-user browser. If Node remains part of the final Kane Fabric acceptance workflow, the exact Node distribution and its bundled third-party notices must be vendored. No npm dependency graph is approved.

### ESP-IDF

ESP-IDF is a future project-controlled firmware SDK/toolchain, not merely a platform API. Before Kane Fabric firmware is released, the exact ESP-IDF release used to build it must be pinned and vendored, including the license inventory for the firmware components actually included. ESP-IDF core is Apache-2.0 but the distribution contains third-party components under multiple licenses; the exact selected release must be reviewed rather than summarized as one license.

### GeoPackage 1.4.0

GeoPackage is a frozen external standard, not a runtime library. Kane Fabric currently implements the required GeoPackage structures itself using SQLite and standard-library geometry/WKB code. The contract is frozen to OGC GeoPackage 1.4.0 (`OGC 12-128r19`). If a copy of the OGC document is vendored for offline reference, it must remain under the OGC document terms and retain its required notices; its document license does not change Kane Fabric code licensing.

## External geographic sources

County/agency source services cannot be vendored as software dependencies. Kane Fabric instead vendors/fixes the **source profile and validation contract** and records accepted harvested data/provenance. Live source drift never silently changes accepted authority. A changed upstream API or schema is a failed source-contract check requiring an explicit Kane Fabric update.

## Admission rule for new dependencies

Before introducing any new third-party implementation:

1. identify why a Kane Fabric implementation or existing approved dependency is insufficient;
2. identify the exact license and redistribution/notice obligations;
3. reject it if those obligations require changing the license of Kane Fabric-authored code;
4. decide whether it is a project implementation or only a target-platform contract;
5. if it is a project implementation, add it to the machine-readable third-party inventory before use;
6. define how its exact release will be vendored and verified offline;
7. add compatibility tests at the interface Kane Fabric actually uses.

Convenience alone is not sufficient reason to add a dependency.
