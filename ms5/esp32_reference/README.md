# ESP32-S3 Reference Components

This directory contains the default physical-edge implementation used by
Milestone 5.

It is a reference implementation, not a platform definition. Fabric logical
identity and the Web Application protocol remain platform-neutral.

## First-release role

The ESP32-S3 is intentionally included in the first Kane Fabric release so the
project has a real firmware component, pinned firmware toolchain, physical
storage model, provisioning/replacement workflow, and later update/recovery
path from the beginning.

Its initial responsibility is deliberately small:

- immutable artifact storage;
- bounded plain-HTTP artifact serving;
- exact closed byte-range behavior;
- physical firmware build/provisioning/replacement.

Browser TLS is **not** an ESP32-S3 responsibility.

Reference path:

```text
browser -- HTTPS --> Wiregate hub -- HTTP --> ESP32-S3
```

The Wiregate hub owns browser HTTPS termination and certificate trust. The
ESP32-S3 reference firmware holds no browser TLS private key.

## MS5-006 components

- `kane_fabric_http`: pure C strict byte-range and artifact-path validation.
- `kane_fabric_artifact_server`: VFS-backed bounded artifact serving for an
  ESP-IDF HTTP server supplied by the caller.
- `kane_fabric_storage`: read-only raw FAT partition mounting for host-generated
  immutable artifact images.
- `host_test`: host compiler tests for the pure HTTP/range core.
- `main`: build-probe application used to ensure the components link under the
  pinned ESP-IDF toolchain.

The build probe intentionally does not start networking or mount a particular
physical partition. Runtime integration later attaches the artifact component
to a plain HTTP server. HTTPS remains at the Wiregate hub.

For the implementation contract, read
`docs/MS5_006_STORAGE_HTTP_IMPLEMENTATION.md`.

## Pinned build target

The accepted MS5 toolchain selection is ESP-IDF v6.0.3 targeting `esp32s3`.

A later MS5-006 gate compiles this project with that exact toolchain. Real
browser consumption through the Wiregate hub belongs to the following
Milestone 5 work item.
