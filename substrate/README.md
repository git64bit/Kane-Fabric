# Kane Fabric Substrate

This directory contains the Milestone 3 shared geographic substrate implementation.

The substrate is civic infrastructure. It contains jurisdiction boundary/context, roads, and water in deterministic browser-consumable form. It does not own application/subscription semantics such as building categories, qualifications, workflows, Mechanical Compiler state, or other domain/business data.

## Durable contract

The v1 wire contract is defined in:

```text
docs/SUBSTRATE_FORMAT_V1.md
```

The shared contract primitives are implemented in:

```text
substrate/tools/kane_fabric_substrate.py
```

Run the bounded substrate tests with:

```sh
bash substrate/run-tests.sh
```

The first real compiler output is:

```sh
bash substrate/kane-fabric-overview.sh build DATABASE county-overview.json
```

The generator opens the authoritative database read-only and emits canonical deterministic JSON.

## Naming rule

`kane-fabric-*` identifies the software/project format. It must not imply Kane County as the jurisdiction.

Kane County remains the reference deployment. Jurisdiction identity is explicit in every durable component and manifest. County/source-specific LOD rules belong in county-aware generators and metadata rather than being silently encoded as universal Fabric semantics.

## Edge constraint

The initial reference edge is ESP32-S3-class hardware running Kane Fabric firmware built with ESP-IDF and serving immutable Fabric artifacts over HTTP.

Milestone 3 does not complete that firmware, but package design must support bounded reads, byte-range/seek access, deterministic integrity verification, and browser-side decompression without requiring whole-county component residency in edge RAM.
