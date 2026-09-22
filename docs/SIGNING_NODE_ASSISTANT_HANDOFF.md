# Signing Node — New Assistant Handoff

## Purpose

This document is the fast handoff for a new Assistant resuming the Kane Fabric / Civic Signing Node work.

It does not replace the project SSOT. It tells the successor **what must be read, how development is executed, how manual script/log relay works, what must not be rediscovered, and what the current implementation boundary is**.

GitHub `git64bit/Kane-Fabric` branch `main` remains software authority.

Do not use private chat history as a substitute for the repository.

---

## 1. Mandatory development method

The project development rule is:

~~~text
read live repository first
        ↓
understand current accepted architecture/state
        ↓
interrogate only the unresolved implementation question
        ↓
update repository design/state when a material design decision changes
        ↓
make the smallest coherent implementation change
        ↓
exercise the correct real environment
        ↓
return and inspect logs/evidence
        ↓
run only invalidated gates
        ↓
record one material checkpoint
~~~

Never begin by writing implementation code from remembered chat context.

Stable facts already recorded in GitHub are not discovery tasks.

If a live observation contradicts the SSOT, stop and investigate only that contradiction before continuing.

---

## 2. Files that MUST be read before development resumes

Read these from **current live `main`**, in this order.

### Session/process authority

1. `docs/DEVELOPMENT_PROCESS.md`
   - governing development workflow;
   - authority map;
   - execution domains;
   - repository workflow;
   - test-invalidation discipline;
   - file-transfer rules;
   - handoff/checkpoint rules.

2. `docs/HANDOFF.md`
   - durable project narrative;
   - accepted checkpoints;
   - non-obvious constraints;
   - current workstream;
   - recent architecture decisions.

3. `docs/CURRENT_STATE.json`
   - compact current/last-observed operational state;
   - target environment;
   - accepted implementation heads;
   - exact next safe action.

4. `docs/SESSION_START.md`
   - short session-resume path;
   - currently required read order;
   - stable infrastructure facts;
   - current priority.

### Cross-cutting Civic constraints

Before evaluating Signing Node providers or participant-device storage, also read:

- `docs/CIVIC_INFRASTRUCTURE_PRINCIPLES.md`;
- `docs/CIVIC_INFRASTRUCTURE_ANTI_CAPTURE.md`.

Current mandatory boundary:

- Civic Infrastructure implements functionality rather than requiring hardware-enforced key secrecy;
- ESP32-S3 is a reference participant/edge implementation, not the required Civic platform;
- no Kane Fabric deployment/acceptance may use ATECC608A-class Civic key custody or irreversible ESP security-eFuse Civic key custody;
- baseline Civic functionality must not depend on proprietary SaaS, Hardware-as-a-Service, a vendor cloud, or a required proprietary hardware signer;
- user-owned edges may store/serve openly readable user-owned public verification material such as CA public material, OpenPGP public keys, and SSH public keys;
- edge-assisted IPFS pinning of user-owned CIDs is a deferred wish-list item only.

### Current Civic Signing Node architecture

5. `docs/CIVIC_CRYPTOGRAPHIC_BASELINE.md`
   - accepted functionality-first Civic cryptographic profile v1;
   - ECDSA P-256/SHA-256;
   - uncompressed 65-byte public key;
   - 64-byte P1363 signature;
   - SHA-256 key identity;
   - evidence-driven rather than speculative hardening.

6. `docs/CIVIC_AUTHORITY_CONTINUITY_DECISION.md`
   - accepted HOA Civic Identity continuity model;
   - independent epoch-specific participant-device keys;
   - replicated authenticated authority state;
   - 1-of-N continuity but not 1-of-N governance;
   - no permanent HOA master/recovery private key.

6. `docs/CIVIC_AUTHORITY_EPOCH_CEREMONY.md`
   - authority epochs;
   - key-signing ceremony;
   - trust-set change -> new epoch/new current keys;
   - historical epoch preservation.

7. `docs/CIVIC_OWNER_OPERATED_SIGNING_NODE.md`
   - one operator-owned Civic Signing Node per participating HOA;
   - operator assumes local operating costs;
   - signing node is replaceable and is not the permanent HOA Civic Identity.

8. `docs/CIVIC_SIGNING_NODE_FUTURE_SERVICE_BOUNDARIES.md`
   - future Kane County CA/TLS service;
   - future Kane-local restricted email service;
   - future IPFS service;
   - all are deferred attachments and **not baseline Civic authority dependencies**.

9. `docs/CIVIC_OPERATOR_PEER_SCRUTINY.md`
   - operator role;
   - participant-operated validation;
   - scrubbing;
   - anti-capture;
   - source-derived operator selection.

10. `docs/CIVIC_ISSUANCE_RECORD.md`
    - complete-snapshot issuance semantics;
    - participant/appliance separation;
    - history, supersession, correction, provenance;
    - authority-epoch context.

11. `docs/CIVIC_PARTICIPATION_RENEWAL.md`
    - voluntary SASE participation;
    - operator-attested participation versus participant-maintained claims;
    - SASE cadence is profile/governance policy, not cryptographic continuity.

### Governing-source model

12. `docs/HOA_GOVERNING_SOURCE_INHERITANCE.md`
    - HOA Diagnostics does not invent substantive HOA governance;
    - Illinois statute -> declaration/bylaws/instruments -> Civic instrumentation;
    - education is a first-class function.

13. `docs/ILLINOIS_STATUTORY_PROCEDURE_BASELINE.md`
    - first Illinois Condominium Property Act source map;
    - meetings, notices, records, technological means, fiduciary/inspection duties.

14. `docs/CIVIC_SAME_AND_EQUAL_POLICY.md`
    - Same and Equal is scoped, relational, temporal, and policy-bound;
    - relevant electorate/comparison semantics.

15. `docs/CIVIC_AFFORDANCE_AUTHORITY_CONTRACT.md`
    - vocabulary/policy authority;
    - deny-by-default derivation;
    - qualification/initiation/validity/surface semantics.

### Before any host, firmware, ESP32, or signer action

16. `docs/CIVICVS_PROJECT_ENVIRONMENT.md`
    - physical host identities;
    - control-plane boundaries;
    - exact `fw` project home;
    - exact USB PROGRAM/TERMINAL roles;
    - `annales` LXD boundary;
    - CT102 paths;
    - prohibited cross-host assumptions.

17. `docs/MS5_009_AUTHORITY_INTERROGATION.md`
    - signer/provider decisions not yet accepted;
    - provisional authenticity implementation;
    - authority questions that remain implementation-level.

18. `docs/MS5_009_FIRMWARE_LIFECYCLE.md`
    - accepted OTA/update/rollback mechanics;
    - firmware lifecycle boundary.

19. `docs/MS5_FIRMWARE_AUTHORITY_NODE.md`
    - Firmware Release Authority role;
    - keep distinct from HOA-local Civic Signing Node authority.

Read `docs/MILESTONE_5_DESIGN.md` and `ms5/README.md` before modifying Milestone 5 implementation or tests.

---

## 3. Repository map

### `docs/` — architecture and SSOT

This is where the current design authority, environment contracts, handoffs, acceptance records, and current-state documents live.

Do not implement against a remembered chat decision that is absent from `docs/`. Reconcile the repository first.

### `development/` — development guards and state tools

Contains repository/process utilities such as:

- `kane-fabric-dev-state.sh`;
- work-sequence authority checks;
- dependency-policy checks;
- development/reconciliation helpers.

These tools protect the development process. They do not replace milestone-specific acceptance.

### `ms5/` — current physical-edge / lifecycle implementation

Contains:

- `esp32_reference/`;
- firmware-lifecycle and authorization contracts;
- Firmware Authority implementation/scaffold;
- MS5 tests;
- acceptance/preflight scripts;
- management-transport decision records.

Before changing this area, read the corresponding `docs/MS5_*.md` authority document.

### `administration/` — administrative/HOA diagnostic contract work

Contains the descriptor-driven administrative model and current online administrative workstream.

It is the application/diagnostic layer, not the cryptographic Civic authority root.

### `web/` — browser implementation and acceptance

Contains the browser application and browser acceptance tooling.

Browser work has its own gates and must be accepted in the documented CT102/browser environment when browser-visible behavior changes.

### `substrate/` — shared browser/substrate components

Shared reusable substrate/browser contracts live here.

Do not fork semantics between online and offline forms.

### `database/` — source-controlled database definitions/assets

Do not confuse repository database material with the accepted operational database under:

~~~text
/var/lib/kane-fabric
~~~

inside CT102.

Operational data/evidence is not automatically source-controlled.

### `ms4/` and `third_party/`

`ms4/` preserves earlier milestone implementation/contracts.

`third_party/` contains external dependency material/pins.

Do not modify either casually while working on the Signing Node.

---

## 4. Physical/execution domains

Never transfer commands or paths between hosts by analogy.

### `srv-b`

- Proxmox host;
- CPE address: `10.110.0.12`;
- owns CT lifecycle;
- normal CT102 control plane is `pct`.

### CT102 `kane-fabric`

- service address: `10.20.0.12`;
- recorded checkout: `/tmp/kane-fabric-ms2`;
- operational root: `/var/lib/kane-fabric`;
- repository/database/browser/admin acceptance environment.

### `fw`

- bare-metal Ubuntu;
- CPE address: `10.110.0.4`;
- project account: `cpe-build`;
- project home: `/home/cpe-build`;
- durable Kane Fabric hardware evidence root: `/home/cpe-build/evidence/Kane-Fabric`;
- direct ESP32 build/program/terminal environment.

Use the fixed USB roles from `docs/CIVICVS_PROJECT_ENVIRONMENT.md`. Never switch PROGRAM and TERMINAL.

### `annales`

- Ubuntu/LXD host;
- CPE address: `10.110.0.9`;
- hosts the inert `firmware-authority` LXD container;
- not Proxmox;
- do not use `pct`;
- do not assume CT102 or `fw` filesystem paths exist here.

The Firmware Authority remains signing-disabled until deliberately activated by an accepted gate.

---

## 5. Development by uploaded scripts and returned logs

When the Assistant has no authorized direct execution channel to the required host, use the bounded manual relay workflow.

The user is the physical relay, not the analyst.

### Step A — Assistant prepares one bounded script

Prefer a script over a long sequence of ad-hoc commands when the operation:

- has multiple dependent commands;
- changes state;
- needs reproducible preflight/postflight checks;
- must capture complete output;
- would be error-prone to paste manually.

The script must target **one exact execution domain**.

It should:

- identify the target host/context before mutation;
- use exact recorded paths;
- fail closed on unexpected preconditions;
- avoid secret/private-key output;
- make the smallest coherent change;
- capture the observations needed to judge success;
- write a log/evidence file to a durable path appropriate to that host;
- print the final log/evidence path and relevant hashes/status.

Do not write a script that assumes a path from another host.

### Step B — Assistant provides the script for upload

The Assistant supplies the script as a downloadable file or, when it is durable project source, commits it to GitHub and identifies the exact repository path/commit.

The user uploads the script to the **specified target host**.

For the established `srv-b`/CT102 environment, Webmin is the accepted file-transfer path. The repository process explicitly uses:

~~~text
create tarball
-> Webmin download/upload
-> verify SHA-256
-> extract/use
~~~

for larger cross-machine artifacts.

Do not default to SCP/SSH file transfer unless project policy is deliberately changed.

For a small bounded execution script, direct Webmin upload is acceptable when that is the chosen manual relay.

### Step C — User executes only the specified script/command

The user runs the exact bounded command given for the target host.

Do not ask the user to improvise follow-up commands.

For state-changing work, one bounded script/command group is executed, then its evidence is reviewed before another mutation is proposed.

### Step D — Script creates a durable log/evidence file

The script should capture enough information for the Assistant to determine:

- precondition state;
- command/action performed;
- stdout/stderr or structured results;
- exit status;
- relevant file hashes;
- postcondition state;
- whether rollback/cleanup occurred where applicable.

Do not rely only on a terminal screenshot or copied excerpt when a complete log can be produced.

### Step E — User downloads the log

Using the appropriate host-management interface—normally Webmin where already established—the user downloads the generated log/evidence file.

The user then uploads that file back into the ChatGPT conversation.

If several evidence files are produced, package them into a tarball only when useful; preserve the original filenames and include a SHA-256 inventory where practical.

### Step F — Assistant reads the returned log before continuing

The Assistant must inspect the returned evidence and decide whether the bounded action:

- passed;
- failed;
- partially completed;
- contradicted the SSOT;
- requires rollback/recovery;
- invalidated an earlier acceptance gate.

Do **not** issue the next state-changing script before examining the returned log.

### Step G — Record a material checkpoint

When the evidence materially changes accepted state, update:

- `docs/CURRENT_STATE.json`;
- `docs/HANDOFF.md`;
- `docs/SESSION_START.md`;
- the relevant architecture/environment/milestone document.

Do not create documentation commits for every trivial observation.

---

## 6. Manual relay safety rules

The following are mandatory:

~~~text
one bounded change at a time
one exact target host at a time
one returned evidence set before the next mutation
~~~

Never:

- claim a remote command ran when it did not;
- treat Assistant sandbox output as host acceptance;
- paste or request private signing keys;
- print WireGuard private/preshared keys;
- use an unknown remote path;
- silently discard unexpected Git changes;
- rerun expensive accepted tests just because the Assistant is new;
- alter `wg-pk`, Firmware Authority activation, or signer attachment without the relevant accepted gate;
- burn/provision ESP security eFuses or attach/provision an ATECC608A-class secure element for Civic key custody;
- switch the fixed ESP32 PROGRAM and TERMINAL USB roles.

If a script encounters an unexpected condition, it should stop and report it rather than “repair” unrelated state.

---

## 7. Repository publication versus execution evidence

Keep these separate.

### Repository source

GitHub `main` owns:

- source code;
- contracts;
- tests;
- deterministic manifests;
- documentation;
- reusable development/acceptance scripts.

### Execution evidence

Real-host evidence owns:

- build logs;
- device logs;
- one-off preflight/postflight output;
- flash dumps/backups;
- runtime captures;
- generated acceptance artifacts;
- operational database evidence.

Do not commit sensitive or large operational evidence merely because it exists.

Record the durable evidence path, hashes, and acceptance result in repository documentation when appropriate.

---

## 8. Current accepted Signing Node baseline

The current design phase is sufficiently closed to begin implementation interrogation.

Accepted invariants:

~~~text
one participating HOA
    -> one autonomous HOA Civic authority domain

one HOA
    -> one operator-owned/operator-funded Civic Signing Node

HOA Civic Identity
    -> replicated authenticated authority state
       on current Same-and-Equal participant ESP32-S3 devices

participant devices
    -> independent epoch-specific keys

1-of-N
    -> continuity/recovery of authority state

governance transition
    -> source-derived Same-and-Equal procedure

trust-set change
    -> new ceremony
       new authority epoch
       new current keys

operator signing node
    -> replaceable current authority appliance
       NOT permanent HOA identity
~~~

There is no required permanent HOA master/recovery private key.

The Common Firmware Release Authority remains logically distinct from HOA-local Civic authority.

The Civic baseline is platform-neutral. References to ESP32-S3 describe the current reference implementation only. Hardware-backed non-exportability is not an authority invariant, ATECC608A-class Civic key custody is prohibited, and security-eFuse Civic key custody is prohibited.


---

## 9. Governing-source rule

For HOA Diagnostics:

~~~text
Illinois statute
    ↓
valid declaration / bylaws / condominium instruments
    ↓
HOA Diagnostics education + observation
    ↓
Kane Fabric instrumentation / attestation / provenance
~~~

The Civic Infrastructure must not invent substantive HOA governance when the governing source already prescribes it.

The Signing Node does not become the source of Illinois law.

It binds local Civic acts to the applicable governing source and preserves provenance.

---

## 10. Deferred future services

Do not make the first Signing Node implementation depend on:

- Kane County CA/TLS service;
- Kane-local restricted email service;
- IPFS.

Their future roles are documented in:

`docs/CIVIC_SIGNING_NODE_FUTURE_SERVICE_BOUNDARIES.md`

They may later provide endpoint authentication, communication/evidence transport, and content-addressed storage.

They do not independently establish Civic authority.

---

## 11. Current implementation boundary

The next phase is **implementation interrogation**, not broad architecture redesign.

The implementation must now determine concrete choices for:

- implementation/provider for the accepted Civic cryptographic profile (`kane-civic-ecdsa-p256-sha256-v1`);
- operator-node key custody;
- Epoch Manifest representation;
- participant-device key/state storage (ESP32-S3 is the reference implementation, not the required platform);
- replicated authority-state storage;
- verification behavior;
- operator-node replacement/recovery mechanics;
- baseline signing-node hardware/software boundary.

Before selecting any implementation, compare it against the accepted invariants in:

`docs/CIVIC_AUTHORITY_CONTINUITY_DECISION.md`

Do not add CA, email, or IPFS dependencies to the baseline.

Do not activate the existing Firmware Authority merely because Signing Node implementation has begun.

Do not reopen the Civic v1 algorithm/key-representation choice without Diagnostics evidence that invalidates it. The next unresolved representation question is the Epoch Manifest canonical byte format.

---

## 12. First action for the new Assistant

Do not write code immediately.

First:

1. read the mandatory documents above from live `main`;
2. confirm the current `docs/CURRENT_STATE.json` next safe action;
3. inspect the relevant existing `ms5/` implementation and tests;
4. identify the smallest concrete implementation question;
5. present at least two viable alternatives where a material design/implementation choice remains;
6. update repository design only if a real architecture decision changes;
7. then implement one bounded slice.

A successor should be able to resume from the repository without private conversation history and without rediscovering stable infrastructure.
