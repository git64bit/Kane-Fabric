# ESP32-S3 Reference Components

This directory contains the default physical-edge implementation used by Milestone 5.

It is a reference implementation, not a platform definition. Fabric logical identity and the Web Application protocol remain platform-neutral.

## MS5-006 components

- `kane_fabric_http`: pure C strict byte-range and artifact-path validation.
- `kane_fabric_artifact_server`: VFS-backed bounded artifact serving for an ESP-IDF HTTP/HTTPS server supplied by the caller.
- `kane_fabric_storage`: read-only raw FAT partition mounting for host-generated immutable artifact images.
- `host_test`: host compiler tests for the pure HTTP/range core.
- `main`: build-probe application used to ensure the components link under the pinned ESP-IDF toolchain.

The build probe intentionally does not start Wi-Fi, mount a particular physical partition, or start a plaintext HTTP server. Those would prematurely choose deployment details or violate the accepted secure-origin boundary.

For the implementation contract, read `docs/MS5_006_STORAGE_HTTP_IMPLEMENTATION.md`.

## Pinned build target

The accepted MS5 toolchain selection is ESP-IDF v6.0.3 targeting `esp32s3`.

A later MS5-006 gate compiles this project with that exact toolchain. Real browser consumption of the resulting physical edge belongs to the following Milestone 5 work item.
