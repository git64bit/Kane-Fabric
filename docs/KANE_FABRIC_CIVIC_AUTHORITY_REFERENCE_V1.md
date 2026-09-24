# Kane Fabric Civic Authority Reference v1

## Publication status

This document publishes the first closed Kane Fabric Civic authority reference.

~~~text
reference: Kane Fabric Civic Authority Reference
version: v1
accepted code head: 0234b8e09fc0ce092d6b4f47a579d4253a19b812
acceptance date: 2026-09-24
complete Civic gate: 171 / 171
focused final Signing Node gate: 10 / 10
~~~

The exact Git commit SHA above is the immutable implementation identity of v1.

No mutable branch name, hostname, deployment path, or local machine state replaces that identity.

This publication document may exist on a later documentation commit than the accepted code head. That does not enlarge or alter the v1 implementation surface.

## Acceptance evidence

CT102 accepted the exact code head:

~~~text
0234b8e09fc0ce092d6b4f47a579d4253a19b812
~~~

The final focused Signing Node conformance gate completed:

~~~text
10 tests run
10 passed
0 failed
0 skipped
~~~

The complete Civic gate completed:

~~~text
171 tests run
171 passed
0 failed
0 skipped
~~~

The accepted CT102 worktree was clean after both gates.

## Reference purpose

Kane Fabric Civic Authority Reference v1 is the platform-neutral authority and interoperability reference for an HOA-local Civic Signing Node.

It freezes:

- canonical authority semantics;
- deterministic public formats;
- source-bound governance behavior;
- verification behavior;
- production signing/key-lifecycle behavior;
- authority-state transaction semantics;
- Signing Node conformance and recovery behavior;
- conformance tests.

It does not deploy a real HOA production system.

## Six closure pieces

### 1. Epoch-1 / bootstrap contract

Normative architecture:

`docs/CIVIC_EPOCH1_BOOTSTRAP_CONTRACT.md`

Architecture head:

~~~text
89c8695686c73747664e741f375170c58533691b
~~~

Status:

~~~text
architecture frozen
~~~

This contract defines the exceptional first accepted HOA authority epoch without introducing a permanent bootstrap privilege or HOA master private key.

### 2. Canonical ceremony record

Normative architecture:

`docs/CIVIC_CEREMONY_RECORD_CONTRACT.md`

Accepted code/test head:

~~~text
8b3d06ac4f7cba0417dd7e4efdbae56dc102bab1
~~~

The ceremony is the canonical non-recursive transition record binding the exact candidate authority context and governance proof set.

### 3. Governance policy, proof, and transition verification

Normative architecture:

`docs/CIVIC_GOVERNANCE_POLICY_PROOF_CONTRACT.md`

Accepted complete transition head:

~~~text
0a79ca8cef3095c43dbf23eee0e3a54a68a6cfbf
~~~

The verifier reconstructs electorate/standing and evaluates exact source-bound policy, proof, evidence, quorum, and approval semantics without inventing a universal majority rule.

### 4. Production signing and key lifecycle

Normative architecture:

`docs/CIVIC_PRODUCTION_SIGNING_KEY_LIFECYCLE_CONTRACT.md`

Architecture head:

~~~text
6638b7262f58af1e099001241f12b15bba7c6fdf
~~~

Implementation head:

~~~text
5ed70c0c72c88e7a4122f2b2c7322964efb93afd
~~~

Accepted head:

~~~text
ce3fac5fa1ca5678feed73d1fe6acedd8a64e6d1
~~~

Reference implementation:

~~~text
civic/ecdsa.py
civic/production_signing.py
~~~

Key custody remains local operational state. Authority binding comes from verified Civic state. Key generation never activates authority.

### 5. Authority-state transaction and composition

Normative architecture:

`docs/CIVIC_AUTHORITY_STATE_TRANSACTION_COMPOSITION_CONTRACT.md`

Architecture head:

~~~text
dc4a41c3774f3247ba3e795d59c7f35efce4a7ba
~~~

Implementation head:

~~~text
0afaac6d0b1335332c5303f4b5f6268e171570df
~~~

Accepted head:

~~~text
bd0bf8dae7e3060bbfba9daaa8523a3be3f3261d
~~~

Reference implementation:

~~~text
civic/authority_transaction.py
~~~

Reference transaction rule:

~~~text
immutable candidate bytes
    -> complete persisted verification
    -> compare expected predecessor
    -> atomic selector commit
    -> current authority
~~~

### 6. Platform-neutral Signing Node conformance boundary

Normative architecture:

`docs/CIVIC_SIGNING_NODE_CONFORMANCE_DEPLOYMENT_BOUNDARY.md`

Architecture head:

~~~text
81cc6ee191f88a0b5c767cdbd7cc2bdb1468e0dc
~~~

Implementation head:

~~~text
ddfde75e87c875765b157a7f4bf4a9294da5e32a
~~~

Final accepted head:

~~~text
0234b8e09fc0ce092d6b4f47a579d4253a19b812
~~~

Reference implementation:

~~~text
civic/signing_node.py
~~~

Focused conformance tests:

~~~text
civic/tests/test_signing_node.py
10 / 10 passed
~~~

Complete Civic gate:

~~~text
171 / 171 passed
~~~

## Normative v1 authority model

The v1 reference preserves these core invariants:

~~~text
one HOA
    -> one autonomous Civic authority domain

HOA Civic Identity
    -> authenticated authority lineage
       + replicated current authority state

Signing Node
    -> replaceable local authority appliance
       NOT permanent HOA identity

participant devices
    -> independent epoch-specific keys

1-of-N participant state
    -> continuity/recovery
       NOT unilateral governance

governance transition
    -> source-derived procedure
       + exact verified proof/evidence

key generation
    != authority activation

candidate bytes/signatures
    != accepted authority

current authority
    -> complete verified state
       + atomic accepted-state selection
~~~

There is no required permanent HOA master/recovery private key.

## Cryptographic profile

Reference profile:

~~~text
kane-civic-ecdsa-p256-sha256-v1
ECDSA P-256 / SHA-256
SEC1 uncompressed public key: 65 bytes
P1363 signature: 64 bytes
key ID: SHA-256(public key)
COSE algorithm: ESP256 / -9
~~~

The reference does not accept ES256 / -7 as the Civic v1 algorithm identifier.

## Public authority before private custody

A conforming Signing Node begins with verified public authority state.

~~~text
verify accepted state
    -> derive expected current Signing Node key
    -> inspect local provider custody
    -> require exact key/role/key-ID match
    -> READY_CURRENT
~~~

A local private key does not define authority merely because it exists.

## Recovery model

Participant-held replicas preserve continuity.

A recovered exact accepted replica may restore local knowledge of already accepted authority on an empty replacement node.

That does not authorize a new Signing Node key.

If the accepted current key is unavailable:

~~~text
accepted authority state survives
current signing disabled
replacement key remains candidate
governed successor required
~~~

Conflicting valid branches are Diagnostics evidence and are not resolved automatically by timestamp, hash ordering, copy count, or operator preference.

## Exact-byte replication

Participant authority-state export/import transfers exact bytes.

It does not re-compose or re-sign accepted objects.

Replica closure excludes private keys and deployment-local key references.

Transport is not authority.

## Source hierarchy

For HOA Diagnostics:

~~~text
Illinois statute
    -> valid condominium instruments
    -> Civic/HOA Diagnostics instrumentation
~~~

The Civic Infrastructure records, verifies, and explains authority/provenance.

It does not become the source of Illinois substantive law or invent substantive HOA governance when the governing source already prescribes it.

## Reference versus deployment

Kane Fabric provides:

~~~text
reference architecture
canonical protocols
authority semantics
verification implementation
conformance tests
interoperability reference
~~~

A production project provides:

~~~text
actual host/runtime
actual service placement
actual storage paths
actual network exposure
actual signer-provider configuration
actual private-key custody
backup/recovery procedures
monitoring and operator procedure
~~~

Those production choices are not part of the v1 Civic identity unless a canonical contract explicitly says otherwise.

## Production hold at publication

At v1 publication:

~~~text
production_signing_enabled = false
production_key_created = false
annales_mutated = false
~~~

The reference implementation is production-capable in behavior, but no real HOA production key or production authority state has been created by the Kane Fabric closure.

## Annales project boundary

Annales begins outside Kane Fabric as one concrete production implementation of this published reference.

The first declaration in that project should be:

~~~text
This Signing Node implements
Kane Fabric Civic Authority Reference v1
at commit 0234b8e09fc0ce092d6b4f47a579d4253a19b812
~~~

The Annales implementation may define:

- LXD/container names;
- systemd units;
- filesystem paths;
- Unix accounts;
- network addresses and firewall policy;
- signer-provider configuration;
- concrete key locations;
- backup locations;
- monitoring;
- deployment commands.

Those choices must not silently redesign Civic v1 authority semantics.

## Change control after v1

The exact accepted code head remains v1 even if GitHub `main` advances.

A later bug fix, semantic change, or conformance expansion is not silently part of v1.

If deployment reveals a material defect:

1. preserve it as Diagnostics evidence;
2. return to Kane Fabric;
3. make the smallest explicit reference correction;
4. run the required conformance/CT102 gates;
5. publish an explicit erratum or later reference version.

Annales must not privately redefine v1 to work around a reference-semantic problem.

## Handoff statement

For a new production-project Assistant:

> Implement a production Civic Signing Node conforming to Kane Fabric Civic Authority Reference v1. Do not redesign Civic authority semantics.

Reference identity:

~~~text
0234b8e09fc0ce092d6b4f47a579d4253a19b812
~~~
