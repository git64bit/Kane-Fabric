# County Node Reconstruction

## 1. Purpose

The first Kane Fabric deployment is also a reconstruction experiment.

The objective is not to copy a working Kane Condo machine. The objective is to prove that a clean county Fabric node can be rebuilt from declared inputs and can independently reproduce the required geographic pipeline.

This procedure is expected to become the basis for repeating Kane Fabric across many counties.

## 2. Declared starting state

A reconstruction begins with:

- a clean supported Debian CT;
- documented LXC requirements;
- required base packages;
- an accepted county seed or equivalent initial acquisition evidence;
- versioned source/county profiles;
- versioned Kane Fabric software;
- explicit external reconstruction/reference artifacts when validating historical reproducibility.

Hidden state on an old orchestrator is not an acceptable dependency.

## 3. Kane County reference reconstruction

The initial Kane County reconstruction uses:

- Debian 12 CT;
- `nesting=1,keyctl=1` for the current Proxmox/LXC environment;
- locale `en_US.UTF-8`;
- Python 3;
- SQLite runtime and CLI;
- Git;
- CA certificates;
- immutable donor seed `kane-county.gpkg`;
- Kane Condo tag `0.4` as the historical software/reference baseline;
- staged boundary, building, road, and coordinated water evidence;
- reconciliation and promotion artifacts;
- known-good promoted reference database.

The Kane Condo reference repository and data are reconstruction evidence. They are not automatically the future Kane Fabric implementation.

## 4. Reconstruction stages

### Stage A — Infrastructure baseline

Verify:

- supported Debian release;
- CT feature flags;
- networking;
- timezone;
- locale;
- storage;
- systemd health;
- package updates;
- Python;
- SQLite;
- Git;
- TLS CA bundle.

Every infrastructure defect found here must be documented because it is likely to recur on future county nodes.

### Stage B — Evidence installation

Install external reconstruction inputs into an isolated read-only evidence tree.

Never treat imported historical artifacts as active Kane Fabric state merely because they are known-good.

Verify all known byte lengths and SHA-256 identities before use.

### Stage C — Software reproducibility

Obtain the exact versioned software baseline from Git.

Run its full bounded test suite on the clean county node.

A repository that becomes dirty merely by running tests or validation is a reconstruction defect unless explicitly documented.

### Stage D — Read-only pipeline validation

Against an immutable known-good database:

- validate database structure;
- inspect database identity/state;
- validate source-profile registry;
- run lightweight live source-status checks;
- verify the database hash is unchanged before and after.

This proves the clean node can understand both accepted state and official upstream services without mutation.

### Stage E — Working database reconstruction

Create a new working database from declared seed/evidence rather than copying the final historical database into active state.

Replay the required migrations/imports and refresh sequence.

The exact sequence depends on the county and software generation, but Kane County must exercise at least:

- initial database creation/import;
- source-profile registration;
- candidate validation/registration;
- deterministic comparison;
- identity reconciliation where applicable;
- promotion preparation;
- promotion validation;
- atomic activation;
- rollback verification.

### Stage F — Semantic comparison

Compare reconstructed state against the known-good historical reference.

Byte identity is useful where deterministic and expected, but semantic identity is the primary requirement when timestamps, file layout, SQLite page placement, or new Fabric-specific schema legitimately differ.

Comparison should cover:

- accepted source releases;
- feature counts;
- source hashes/identities;
- geometry/content identities;
- project-owned geographic identities where retained;
- promotion history semantics;
- classification/subscription migration semantics where applicable.

### Stage G — Compilation and publication

Once authoritative database reconstruction is proven:

- compile the shared substrate;
- compile one or more subscriptions;
- produce deterministic manifests;
- verify browser consumption;
- publish to an edge-node implementation;
- verify operation while the county Fabric node is unavailable.

## 5. Transfer discipline

Cross-machine file transfer is not part of the architectural contract.

For the current environment, large reconstruction bundles are moved manually as tarballs using Webmin download/upload, then verified by SHA-256 before extraction.

The bootstrap process must not depend on SSH or `scp` availability.

## 6. Evidence versus active state

Keep these categories separate:

```text
seed/                    immutable accepted seed evidence
reconstruction-inputs/   imported historical evidence/reference artifacts
reconstruction-code/     exact historical software used to prove reproducibility
database/                active reconstructed Kane Fabric database
staging/                 active candidate/reconciliation/promotion workspace
rollback/                active rollback material
audit/                   active reconstruction and operation audit output
render/                   compiled substrate/subscription outputs
```

## 7. Repetition goal

The desired future county bootstrap should approach:

```text
clean Debian CT
    +
Kane Fabric software
    +
county/source profile
    +
accepted seed or initial harvest
    =
reconstructable county Fabric node
```

Kane County is the first proof of that equation.