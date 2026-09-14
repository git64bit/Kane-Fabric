# MS5-006 — ESP32-S3 Immutable Artifact Storage and HTTP Byte-Range Implementation

## Scope

This document records the implementation boundary for the normative `MS5-006` work item in `docs/MILESTONE_5_DESIGN.md`. It does not redefine the Milestone 5 sequence.

WEB-005 closed the browser application workstream for this stage and froze the browser-facing serving contract sufficiently to resume the physical-edge reference implementation. The transport topology has since been corrected so browser HTTPS terminates at the Wiregate hub while the ESP32-S3 serves ordinary HTTP behind it.

The accepted browser requires an artifact source path that can:

- serve released immutable MS3/MS4 files through ordinary GET;
- serve `.kfs` data through exact single closed byte ranges;
- return exact `206 Partial Content`, `Content-Range`, `Content-Length`, and `Accept-Ranges` semantics;
- reject unsupported range forms rather than silently returning an unintended whole file;
- expose the CORS headers needed when application and artifact origins differ;
- stream bounded file regions without loading a whole `.kfs` file into RAM;
- remain a distribution appliance rather than geographic authority.

## Storage implementation

The reference component uses an ESP-IDF raw FAT partition mounted with `esp_vfs_fat_spiflash_mount_ro()`.

The partition is generated/populated off-device from a verified artifact tree. Runtime code:

- never formats the partition;
- mounts it read-only;
- exposes standard VFS/POSIX reads to the artifact server;
- does not encode partition offset, partition size, flash-chip size, hostname, Wiregate TLS identity, or hardware identity into Fabric content identity.

Exact physical partition sizing remains a deployment/build property because the default ESP32-S3 reference must not redefine the platform-neutral browser or Fabric identity contract. A deployment must provide a `fabric`-class partition large enough for the immutable image it chooses to activate.

`ms5/tools/kane_fabric_edge_image.py` stages a source tree only after the existing MS5 storage inventory validates and every source artifact matches its declared byte length and SHA-256. It then verifies the staged copy again. The resulting directory is suitable input to ESP-IDF's `fatfs_create_rawflash_image()` host build facility.

The physical FAT image itself is not Fabric logical identity. The storage inventory and the released artifact identities remain the logical binding.

## HTTP implementation

`ms5/esp32_reference/components/kane_fabric_artifact_server` registers a GET handler on an ESP-IDF HTTP server supplied by the caller.

The component deliberately does not start networking. In the Kane Fabric reference topology it is attached to a **plain HTTP** server on the ESP32-S3. Browser HTTPS and certificate trust terminate at the Wiregate hub under the corrected MS5-004 contract. Direct HTTP probes against the ESP32 remain valid device diagnostics, but direct browser HTTP is not the reference secure-origin path.

The handler:

- confines requests to normalized relative artifact paths;
- rejects traversal, percent-encoded path rewriting, query-bearing artifact paths, repeated empty path segments, and backslash path forms;
- accepts no range or exactly `Range: bytes=<start>-<end>`;
- rejects suffix, open-ended, multiple, malformed, reversed, overflowed, and out-of-bounds ranges with `416 Range Not Satisfiable`;
- emits `Content-Range: bytes */<size>` for `416`;
- uses bounded 4096-byte file buffers;
- uses ESP-IDF `httpd_send()` to construct a response with explicit `Content-Length`, avoiding chunked transfer encoding for byte-range responses;
- emits `Access-Control-Allow-Origin: *`;
- exposes `Accept-Ranges`, `Content-Length`, and `Content-Range` to cross-origin browser code;
- advertises immutable caching semantics for the released artifact bytes.

The pure closed-range and URI-validation core is isolated in `kane_fabric_http` and is host-compiled under repository tests with warnings treated as errors.

## Dependency boundary

No new third-party runtime dependency is introduced.

The implementation uses only facilities already present in the pinned ESP-IDF selection:

- `esp_http_server`;
- `fatfs`;
- VFS/POSIX file access.

ESP-IDF v6.0.3 documents `esp_vfs_fat_spiflash_mount_ro()` for raw read-only FAT partitions, host generation through `fatfs_create_rawflash_image()`, request-header access through `httpd_req_get_hdr_value_*()`, and raw response construction through `httpd_send()`.

## Acceptance stages

Repository acceptance proves:

- existing MS5 authority/dependency checks remain valid;
- all existing MS5 tests remain accepted;
- the pure C HTTP/range core compiles where a host C compiler is available;
- the immutable-image staging tests pass;
- the ESP32 component source retains the fixed serving invariants.

This is not yet the final MS5-006 acceptance.

Final MS5-006 acceptance additionally requires:

- compilation with the pinned ESP-IDF v6.0.3 / ESP32-S3 toolchain;
- a real reference device/storage image;
- ordinary GET and exact byte-range probes against that device;
- evidence that the served bytes match the accepted artifacts;
- no geographic/database mutation or promotion.

Real-browser consumption through the Wiregate hub from the physical ESP32-S3 HTTP edge remains the next normative item after MS5-006. That browser proof must not make WireGuard a prerequisite; management/WireGuard remains MS5-008.
