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

## MS5-008 candidate repository contract — accepted 2026-09-20

CT102 accepted the pinned management-transport candidate/evaluation contract at:

```text
5a35b607ef16b5c94bd732e7f2eb73fbffc17ad0
```

Evidence:

```text
focused candidate tests      12/12 PASS
complete MS5 repository      86 PASS / 1 skipped
dependency policy            PASS
MS5 work-sequence authority  PASS
WireGuard retained           NO
decision state               defer
CT102 worktree               clean
```

This accepts only the evaluation inputs and evidence contract. No physical
firmware, WireGuard hub, peer credential, or tunnel was changed.

## MS5-008 fw transport preflight — accepted 2026-09-20

The read-only `fw` WireGuard preflight accepted the existing CPE transport:

```text
host                      fw
interface                 wg0
fw public key             k24Ry8paxtcKkwPdxTcICjeiJWS7TEhrQQ0ztEWyT2A=
hub public key            1+Wb++fjXNbY0joOvj4AZvJgF6b125YOPSFsmNqVo3I=
hub endpoint              198.58.111.109:51820
allowed IPs               10.110.0.0/22
persistent keepalive      25 seconds
hub reference address     10.110.0.1
hub ping                  PASS
```

No private-key file or preshared key was read or printed. WireGuard,
repository, and firmware state were unchanged.

## MS5-008 wg-pk allocation preflight — accepted 2026-09-20

The corrected read-only hub inventory accepted:

```text
host                         wg-pk
interface                    wg0
hub address                  10.110.0.1/22
hub public key               1+Wb++fjXNbY0joOvj4AZvJgF6b125YOPSFsmNqVo3I=
listen port                  51820
existing peers               19
temporary evaluation address 10.110.3.254/32
collision check              FREE
```

No peer was created. No WireGuard or routing state changed. No private or
preshared key was read or printed.

## MS5-008 temporary ESP32 evaluation keypair — accepted 2026-09-20

The evaluation-only WireGuard identity was generated locally on `fw`:

```text
private key path   /home/cpe-build/evidence/Kane-Fabric/ms5-008/esp32-evaluation-wireguard.private
private key mode   0600
private key owner  cpe-build:cpe-build
private key SHA256 a48666ae7f91e5eb6ab9d5dd435175601e142786a6d25fd172c2dcccdded095f
public key         UlpYmFs2nt4XKHM+zs71Mxt/9/H2vr6SGUxLpnwJemA=
```

The private-key contents were not printed. No hub peer, firmware build, flash,
or tunnel was created.

## MS5-008 runtime-only hub peer — accepted 2026-09-20

The temporary evaluation peer was accepted in `wg-pk` runtime state:

```text
public key                  UlpYmFs2nt4XKHM+zs71Mxt/9/H2vr6SGUxLpnwJemA=
AllowedIPs                  10.110.3.254/32
endpoint                    none
hub-side keepalive          off
latest handshake            0
transfer                    0 / 0
persistent wg0.conf SHA256  dc3331149f854e0fd6a069fdd4505aa259069f768c0ec88be5a473824e9b2429
persistent config changed   NO
IPv4 routes changed         NO
```

The peer was intentionally not persisted. This is a **last-observed accepted
runtime state**, not a claim that the peer is still live after later work.

## MS5-008 first physical runtime attempt — investigated 2026-09-20

The corrected `fw` evaluation reached a materially new boundary:

```text
fw repository head              3aeebe0b33570859277aae11aa1b3e147267db79
ESP-IDF                         6.0.3 / 76f5dedd9950...
WireGuard                       cddaa4eab4e633847bf846723ac0449a34c3d2f7
libsodium wrapper               40c22448d6e8f42be56c45f739b52a5c8d21c8ca
libsodium upstream              d24faf56214469b354b01c8ba36257e04737101e
libsodium patch series          PASS
evaluation build                PASS
evaluation application bytes    918240
evaluation application SHA256   691d72e834b0bd3e7f75b9d75b0ad758a2927e136a8bb2159ec10467c44fb892
pre-test application SHA256     6e3c2bbcfb77107898bd96210f85bd49d93621ea057739e86c2914a56f554c96
Wi-Fi/DHCP                      PASS / 10.0.0.185
participant image verification  PASS
HTTP artifact server ready      PASS
WireGuard peer-up               NOT REACHED
runtime failure                 LoadProhibited / EXCVADDR 0x00000000
exact application restore       PASS / SHA256 identical to pre-test
```

The outer script failed because peer-up evidence was absent. The runtime log
shows the more precise cause: the ESP32 panicked immediately after the
MS5-008 evaluation task printed its WireGuard configuration, before any
successful WireGuard startup/peer-up evidence.

The physical board was restored byte-identical to its pre-test application.
The Fabric partition was not rewritten.

Detailed record:

```text
docs/MS5_008_RUNTIME_INVESTIGATION.md
```

WireGuard remains candidate-only and the MS5-008 decision remains `defer`.

## Next safe action

Stay on **`fw`** and diagnose the panic before another state-changing test.

1. use the preserved evaluation ELF/map, if present, to symbolize the captured
   backtrace;
2. if the temporary workspace is gone, reproduce the exact pinned build only,
   without flashing;
3. identify the exact crashing function and source line;
4. only then decide the smallest integration correction or whether the
   candidate should be rejected/deferred.

Do not modify `wg-pk`, do not create another peer, and do not flash the
ESP32 again merely to rediscover the same panic.
