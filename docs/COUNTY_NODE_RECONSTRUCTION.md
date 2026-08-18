# County Node Reconstruction

## 1. Purpose

The first Kane Fabric deployment is also a reconstruction experiment.

The objective is not to copy a working Kane Condo machine. The objective is to prove that a clean county Fabric node can be rebuilt from declared inputs and can independently reproduce the required geographic pipeline.

This procedure is expected to become the basis for repeating Kane Fabric across many counties.

## 2. Declared starting state

A reconstruction begins with:

- a conformant supported Debian CT;
- an executable host/deployment conformance gate where the deployment environment defines one;
- documented Fabric-specific runtime requirements;
- required base packages;
- an accepted county seed or equivalent initial acquisition evidence;
- versioned source/county profiles;
- versioned Kane Fabric software;
- explicit external reconstruction/reference artifacts when validating historical reproducibility.

Hidden state on an old orchestrator is not an acceptable dependency.

Host conformance and Kane Fabric application requirements are separate layers. A Fabric repository must not redefine a shared host standard merely because it happens to run on that host.

## 3. Kane County reference reconstruction

The initial Kane County reconstruction uses CT102 on `srv-b`.

For this deployment, shared CT properties are governed by the host-level `ct-baseline.sh` check. CT102 was recorded conformant with CT100 and CT101 on 2026-08-18.

Kane-specific reconstruction requirements include:

- Debian 12 as required by the current host baseline;
- `nesting=1` as required by the host baseline;
- `keyctl=1` currently present on CT102 but not a Kane Fabric platform requirement unless a workload such as Docker requires it;
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

### Stage A — Infrastructure and host conformance

First prove that the CT conforms to the deployment host's executable standard.

On `srv-b`, run the host-level `ct-baseline.sh` gate. It covers the shared properties that must remain uniform across CT100, CT101 and CT102, including container mode, network placement/isolation, Debian release, locale, timezone, required host-standard tools/admin access, mail prohibition, and systemd health.

The governing rule is:

> A property not checked by the host baseline is not part of the shared host standard.

Then verify Kane Fabric-specific requirements not owned by that baseline:

- `/var/lib/kane-fabric` storage and layout;
- package updates required by the current work;
- Python;
- SQLite;
- Git;
- reconstruction evidence locations;
- Fabric-specific test gates.

Every infrastructure defect found here must be classified correctly:

- shared host defect -> host conformance standard/failure log;
- Kane Fabric-specific defect -> Kane Fabric reconstruction record.

This prevents another county or project from rediscovering host properties independently.

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

## 5. Conformance lifecycle

On hosts that provide an executable baseline, conformance is not a one-time provisioning event.

For `srv-b`, rerun the host baseline:

- before work when host/container state may have changed;
- after relevant CT or firewall changes;
- after host reboot;
- before backup work;
- as part of restore verification.

Conformance is a precondition for backup. Restoration must re-establish conformance before an application-level restore is accepted.

## 6. Transfer discipline

Cross-machine file transfer is not part of the architectural contract.

For the current environment, large reconstruction bundles are moved manually as tarballs using Webmin download/upload, then verified by SHA-256 before extraction.

The bootstrap process must not depend on SSH or `scp` availability between machines.

## 7. Evidence versus active state

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

## 8. Repetition goal

The desired future county bootstrap should approach:

```text
conformant supported CT
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

The deployment host may vary from county to county. Therefore the Fabric contract requires a conformant supported environment, while the exact executable host-standard implementation remains deployment-owned.