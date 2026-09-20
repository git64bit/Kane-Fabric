# Kane Fabric — Current Handoff

## Read this first

A new Assistant should read these in order before proposing implementation work:

1. `docs/CURRENT_STATE.json`
2. `docs/BROWSER_FIRST_ONLINE_FIRST_DIRECTIVE.md`
3. `docs/ADMINISTRATIVE_DESCRIPTOR_ARCHITECTURE.md`
4. `docs/ADMINISTRATIVE_DESCRIPTOR_ACCEPTANCE.md`
5. `administration/README.md`
6. `docs/WEB_APPLICATION_DESIGN.md`
7. `docs/ADMINISTRATIVE_EDGE_BOUNDARY.md`
8. `docs/MILESTONE_5_DESIGN.md`
9. `docs/CIVICVS_PROJECT_ENVIRONMENT.md`
10. `docs/CPE_HOST_CONTROL_PLANE_MODEL.md`

The normative detailed MS5 sequence remains in `docs/MILESTONE_5_DESIGN.md`, but the active application-design workstream is now descriptor-driven Civic Infrastructure.

## MS5-007 physical participant integration — accepted 2026-09-20

MS5-007 is complete. The accepted live gate proved the full bounded path:

```text
normal trusted Chromium
        |
        | HTTPS / secure context / WebCrypto SHA-256
        v
CT103 kane-wiregate / https://kane-wiregate.dev.infra
        |
        | temporary verified laboratory adapter
        | plain HTTP TCP/80
        v
physical ESP32-S3 bounded participant publication
```

Accepted physical participant evidence:

```text
expected MAC                    b8:f8:62:e2:d5:2c
last observed transient locator 10.0.0.185
participant.json bytes          1357
participant.json SHA-256        03f74e9e48254cc9d3fd4af22b840ce5d3857c028d8acd9cc8eca63003ab883c
CT101 edge access               BLOCKED
browser secure context          PASS
browser WebCrypto SHA-256       PASS
```

Accepted recovery/postconditions:

```text
Wiregate vhost SHA-256          df116928cbd02441d90751d6289a776e48874a9c81adc3695f21789c584b466c
persistent rules.v4 SHA-256     521d6834dc2fe6b9f4c84207af3819981a3a88163e489773e412d2f971a9c4a6
host baseline                   81 passed / 0 failed / 4 informational
/edge/participant.json          404 after cleanup
temporary filter rule           absent
temporary NAT rule              absent
WireGuard prerequisite          absent
```

The ESP LAN address is operational locator state only. It must be rediscovered and verified when needed; it is never Fabric identity and must not become a DHCP reservation, firmware static address, inbound port-forward requirement, or persistent per-device operator rule.

## Current strategic direction

Kane Fabric remains **Browser-First** and implementation remains **Online-First**.

The full-featured Administrative Web is now the project’s design instrument for discovering and stabilizing Civic Infrastructure. The current sequence is:

```text
accepted Kane County geography
        ↓
full-featured descriptor-driven Administrative Web
        ↓
statewide Illinois condominium Infrastructure model
        ↓
separate Infrastructure from association-instance and participant data
        ↓
derive participant-publication contract
        ↓
derive bounded edge-device role
        ↓
resume ESP32 specialization only if that role requires it
```

The edge contract no longer defines the Administrative Web. The Administrative Web defines enough of the common Infrastructure model that a later bounded edge contract can be derived from it.

Browser-First means the browser is the durable human client and browser-visible contracts remain platform-neutral. Online-First means the complete useful application is developed before its reduced local/offline form. The offline/local browser remains a later reduction of the same application, not a separate product or schema.

## Civic Infrastructure admission rule

The current content jurisdiction is deliberately narrow:

```text
United States
└── Illinois
    └── condominium infrastructure
```

The Administrative Web should model what is common across Illinois condominium associations and externally grounded in statewide law, regulation, registration, insurance, taxes, licensing, contracts, required records, or other statewide obligations.

If a requirement is county-specific, municipal, merely customary, uncertain, or not demonstrably statewide, defer it rather than promoting it into common Infrastructure.

Other states are not current content targets. The descriptor engine itself must remain jurisdiction-neutral so a future operator can supply different descriptor content for another state or a different local-government structure such as a parish.

## Infrastructure versus association-instance data

The Administrative Web must distinguish:

```text
Infrastructure definition
  statewide meaning / authority / requirement / record category

Association instance
  actual insurer / policy / contract / date / registration / document / value

Participant data
  later homeowner/resident assertions and publications
```

Public/private/restricted classification is separate from this authority distinction.

A statewide Infrastructure definition may require an association-specific value without making that value itself statewide authority.

## Descriptor-driven application rule

The browser does not hard-code Illinois condominium forms.

Everything reasonably representable as descriptor data should be in versioned JSON, including:

- page and section structure;
- field/control identity;
- type and validation;
- labels and help text;
- statutory/legal authority references;
- select options;
- repeating collections;
- row/column placement and spans;
- sizes represented by the descriptor vocabulary;
- conditional presentation;
- semantic bindings;
- descriptor identity/version.

The JavaScript renderer provides generic capabilities. It must not know what Illinois, a condominium, insurance, a county, or a parish means.

Semantic identity must remain independent of screen placement. Moving a control must not change the underlying civic-data identity.

Descriptors are versioned and canonicalizable/hashable. The browser presents the canonical SHA-256 identity of a loaded descriptor.

Authoritative architecture document:

```text
docs/ADMINISTRATIVE_DESCRIPTOR_ARCHITECTURE.md
```

## First accepted descriptor slice

The first real descriptor slice is Illinois condominium insurance.

Reference descriptor:

```text
administration/descriptors/illinois/condominium/insurance.v1.json
```

Descriptor schema:

```text
administration/descriptors/descriptor-v1.schema.json
```

It demonstrates:

- statewide Infrastructure notices and authority references;
- association-instance policy records;
- a repeating current-policy collection;
- text/date/select/textarea controls;
- help text and layout supplied from JSON;
- a distinction between statewide legal structure and association-specific unit-owner insurance requirements.

This is a proof of the descriptor architecture, not a claim that the insurance model is complete.

## Administrative descriptor acceptance — accepted

The first descriptor-driven implementation is accepted in CT102 at:

```text
7b8b116d5b43660d4260a21f0dc7ea85ec6bc753
```

Repository/browser unit suite:

```text
bash web/run-tests.sh
35 passed
0 failed
0 skipped
```

Real Chromium render evidence:

```text
BROWSER=/bin/chromium
10/10 Administrative Descriptor DOM checks passed
admin_browser_render=PASS
DOM bytes: 16254
```

Acceptance record:

```text
docs/ADMINISTRATIVE_DESCRIPTOR_ACCEPTANCE.md
```

Repository-owned repeat gate added after the observed acceptance:

```text
bash web/run-admin-browser-acceptance.sh
```

The tooling/documentation commits after `7b8b116` do not modify the accepted application implementation.

## Acceptance scope

The descriptor checkpoint accepts that:

- the JSON bootstrap and descriptor load in real Chromium;
- the generic renderer can construct the current Administrative Web slice from JSON;
- descriptor identity can be represented by canonical SHA-256;
- generic input/select/textarea/collection capabilities work for this slice;
- the engine remains separate from Illinois condominium domain vocabulary.

It does **not** accept or claim:

- final visual design or usability;
- persistent storage;
- authentication/authorization;
- encrypted private delivery;
- abuse resistance;
- offline/local behavior;
- complete Illinois condominium legal/administrative coverage;
- a participant-publication contract;
- an ESP32 application shape.

## Released geographic foundation

Milestones 0 through 4 remain released.

Accepted MS3 substrate content identity:

```text
fe417a02222669d9b81c72dc717ab0178b54b1c13cd0d3e8510c6b4f25224bcc
```

Accepted MS4 implementation:

```text
9f6013d1b8b44998047f71e2b3f3e9c55c9ed298
```

Accepted MS4 composition identity:

```text
a58c8398248cee05b7baad9ae289fe0581bdb3624ce1aff3aa8a49721f92ee53
```

The authoritative county database remains:

```text
/var/lib/kane-fabric/database/kane-county-fabric.gpkg
SHA-256 31e362b696a37f1b9c45ae355c5669511a3128c17a651108a62e20d1cedebd67
```

## MS5-006 physical edge status — accepted and paused

The ESP32-S3 MS5-006 device-runtime gate remains complete.

Accepted firmware source:

```text
7aa3c836bae470704d051a36a6261a1140e9d3d0
```

Physical acceptance record:

```text
docs/CPE_ESP32_MS5_006_DEVICE_RUNTIME_ACCEPTANCE.md
```

Accepted physical behavior includes:

```text
pinned ESP-IDF/toolchain build                  PASS
ESP32-S3 flash/boot/build identity              PASS
16 MB reference flash geometry                 PASS
Wi-Fi provisioning -> deployment station       PASS
read-only Fabric partition mount                PASS
active-inventory verification before serving   PASS
plain HTTP full GET                             PASS
exact closed byte range                         PASS
invalid/open/suffix/multiple/OOB range reject  PASS
path traversal reject                           PASS
deliberately corrupt active storage fail-close PASS
known-good storage restore                      PASS
post-restore HTTP/hash verification             PASS
```

The MS5 repository suite was rerun on `fw` after the administrative/edge boundary correction:

```text
Ran 72 tests
OK
```

The physical runtime is therefore available as a proven bounded artifact-serving reference platform, but the project deliberately does **not** yet know what final participant application shape belongs on it.

Do not infer the future edge schema from the existing firmware. Resume ESP32 application specialization only after the Administrative Web exposes a concrete bounded participant role or a later MS5 lifecycle gate intentionally resumes firmware work.

## Board-independent participation principle

The Civic Infrastructure must not require a condominium board to authorize homeowner participation.

Kane Fabric may know that an accepted building is a condominium and may know statewide Infrastructure facts about condominium associations. Later participant publications may be contributed by independently participating residents without those participants being treated as the corporate association or Board.

The Administrative Web must therefore avoid making Board approval a prerequisite for technical participation or civic-data visibility.

## Physical-edge provisioning direction — deferred design input

A future edge may be provisioned to a participant who demonstrates access to mail delivery at a claimed location through the SASE process. That fact should be treated narrowly as provisioning evidence, not as proof of ownership, legal residence, Board membership, or corporate authority.

Same-association peer discovery may eventually be useful, but no discovery protocol or ESP32 data model should be frozen until the Administrative Web establishes the participant-publication boundary.

## Infrastructure versus SaaS boundary

Online-First must not become SaaS-First.

The online interface may eventually provide network conveniences such as discovery, aggregation, richer search, current availability, administrative workflows, and authentication required for restricted content.

Those services must not become:

- civic identity;
- exclusive participant-data custody;
- a proprietary account prerequisite for locally retained data;
- a requirement that another operator inherit Kane County private operational state.

The descriptor language and browser engine must be reusable independently of Kane County's internal deployment.

## Firmware Authority status

The `firmware-authority` LXD container on `annales` remains accepted but deliberately inert.

```text
host                        annales / 10.110.0.9
container                   firmware-authority
network                     lxdbr0 / NAT
independent CPE identity    none
WireGuard                   absent
GPU                         none
USB signer                  none
persistent private key      none
signing                     DISABLED
activation boundary         MS5-009
```

Do not activate signing, attach a signer, add an independent WireGuard peer, or create a persistent private signing key before MS5-009 explicitly authorizes it.

## CPE execution domains

```text
srv-b / 10.110.0.12
  Proxmox host / pct control plane
  CT102 kane-fabric on private 10.20.0.12/24
  active administrative/runtime development environment

fw / 10.110.0.4
  bare-metal Ubuntu
  ESP-IDF build / USB programming / physical ESP32 acceptance
  firmware application work paused

annales / 10.110.0.9
  Ubuntu LXD
  inert firmware-authority container
```

Do not transfer filesystem paths or control-plane commands between these environments.

CT102 does not receive an independent CPE/WireGuard identity merely because it is the active administrative development environment. Normal management is host-mediated through `srv-b` and `pct`.

## Later MS5 work still pending

MS5 is not fully closed. MS5-007 is accepted; the next normative item is MS5-008.

Remaining gates:

- MS5-008 candidate outbound management transport / WireGuard runtime-resource feasibility across ordinary participant NAT; retain, reject, or defer;
- MS5-009 firmware authenticity, update, rollback, and recovery;
- MS5-010 physical replacement/reprovisioning identity preservation;
- MS5-011 constrained-resource/concurrent-workload acceptance;
- MS5-012 release evidence and closeout.

Management transport is distinct from the already accepted browser/Wiregate/HTTP path. No result from MS5-008 may retroactively make WireGuard a browser prerequisite or Fabric logical identity.

## Independent operator criterion

The generic descriptor engine must not contain Kane County or Illinois domain assumptions.

For the current Illinois implementation, descriptor content should be portable to another Illinois county without changing the statewide condominium semantics. A future state implementation should be able to supply a different profile without rewriting generic rendering capabilities.

An independent operator must not need Kane County's:

- hostnames;
- filesystem paths;
- private keys;
- internal GeoPackage schema as an external API;
- proprietary account database;
- service state;
- ESP32 hardware identity.

## Next safe action

Begin **MS5-008** with one repository-only primitive: freeze the exact candidate management-transport implementation and the evaluation contract that will govern later build/runtime testing.

Do not yet:

- add WireGuard to `third_party/manifest.json` as a retained dependency;
- modify the accepted ESP32 runtime;
- flash the board;
- create persistent management credentials;
- stand up or persist a WireGuard hub/peer;
- alter participant-router configuration;
- treat a tunnel address, public key, endpoint, MAC address, hostname, or LAN locator as Fabric logical identity.

Only after the candidate/evaluation contract is accepted should the project construct the first physical outbound-handshake gate on `fw`.
