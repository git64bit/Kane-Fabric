# Kane Fabric — Current Handoff

## Read this first

A new Assistant should read these in order before proposing implementation work:

1. `docs/CURRENT_STATE.json`
2. `docs/BROWSER_FIRST_ONLINE_FIRST_DIRECTIVE.md`
3. `administration/README.md`
4. `docs/WEB_APPLICATION_DESIGN.md`
5. `docs/ADMINISTRATIVE_EDGE_BOUNDARY.md`
6. `docs/MILESTONE_5_DESIGN.md`
7. `docs/CIVICVS_PROJECT_ENVIRONMENT.md`
8. `docs/CPE_HOST_CONTROL_PLANE_MODEL.md`

The normative detailed MS5 sequence remains in `docs/MILESTONE_5_DESIGN.md`.

## Current strategic direction

Kane Fabric remains **Browser-First**.

The active implementation order is now **Online-First**:

```text
full online Kane County browser/interface
        ↓
county categories + participant contracts
        ↓
bounded participant-publication composition
        ↓
freeze shared browser modules/contracts
        ↓
reduce the same application to local/offline operation
```

Browser-First means the browser is the durable human client and browser-visible contracts remain platform-neutral. It does **not** mean the disconnected/offline form must be implemented first.

The offline/local browser is a later reduction of the same application architecture, not a separate product, schema, or contract family.

The authoritative development-order document is `docs/BROWSER_FIRST_ONLINE_FIRST_DIRECTIVE.md`.

## Active workstream

The active priority workstream is:

**Administrative County / Web / Category / Contract Development**

The immediate implementation surface is the **full online Kane County browser/interface**.

The next work is to make the administrative model concrete in that interface:

- category/object model;
- association/participating-organization identity;
- unit or participant-object identity;
- bounded participant publication manifest/generation contract;
- references to accepted county/building identities;
- public/restricted/private visibility semantics;
- online composition of participant publications into the county map;
- source-neutral browser loaders/adapters;
- independent county-operator conformance rules.

The first concrete participant reference case is a condominium association with unit-level data.

Do not return to ESP32 programming merely because one of these administrative contracts is unresolved.

## Infrastructure versus SaaS boundary

Online-First must not become SaaS-First.

The online interface may provide useful network conveniences such as discovery, aggregation, richer search, current availability, administrative workflows, and authentication required to obtain restricted content.

Those services must not become:

- civic identity;
- the exclusive datastore for participant data;
- a proprietary account prerequisite for locally retained data;
- a requirement that an independent county operator inherit Kane County private operational state.

County, association, unit, category, publication-generation, geographic, and physical-edge identities remain separate.

Participant data must remain portable and independently retainable.

## Released foundation

Milestones 0 through 4 are released.

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

## MS5-006 physical edge status — accepted

The ESP32-S3 MS5-006 device-runtime gate is complete.

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

The ESP32 is therefore not the current development bottleneck.

## Physical-edge role

The ESP32-S3 is a **bounded participant edge**, not a miniature county server.

It may eventually hold a focused publication such as one condominium association and its unit-level material. It is not required to hold the complete Kane County substrate.

The edge does not own:

- county geographic authority;
- county web/map composition;
- category/schema authority;
- participant-contract authority;
- person/account identity;
- browser HTTPS termination.

Browser HTTPS terminates at Wiregate/admin infrastructure. The ESP32 reference edge serves bounded immutable artifacts by plain HTTP behind that boundary.

## Later MS5 work still pending

MS5 is not fully closed.

Later gates remain:

- MS5-007 real online browser/admin composition with a focused participant edge publication;
- MS5-008 management transport / WireGuard feasibility: retain, reject, or defer;
- MS5-009 firmware authenticity, update, rollback, and recovery;
- MS5-010 physical replacement/reprovisioning identity preservation;
- MS5-011 constrained-resource/concurrent-workload acceptance;
- MS5-012 release evidence and closeout.

These later edge/lifecycle gates do not block current administrative county/web/category/contract development.

## Firmware Authority status

The `firmware-authority` LXD container on `annales` is accepted but deliberately inert.

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
  current administrative/runtime development environment

fw / 10.110.0.4
  bare-metal Ubuntu
  ESP-IDF build / USB programming / physical ESP32 acceptance
  firmware work is currently paused

annales / 10.110.0.9
  Ubuntu LXD
  inert firmware-authority container
```

Do not transfer filesystem paths or control-plane commands between these environments.

CT102 does not receive an independent CPE/WireGuard identity merely because it is the current administrative development environment. Normal management is host-mediated through `srv-b` and `pct`.

## Current development environment transition

The previous work ended on `fw` only because that was the physical MS5-006 programming workstation.

Current development should move back to `srv-b` / CT102 for county, web, category, contract, database, and browser work.

GitHub `main` remains the software/documentation authority. Before new administrative implementation is accepted, CT102 must be synchronized to current `main` and its relevant repository/runtime checks rerun there.

The old CT102 acceptance checkpoint at `2b7c74e...` remains historical evidence; do not describe it as acceptance of later administrative commits until CT102 is explicitly rerun.

## Current online-browser target

The next implementation should start from the existing web application and accepted MS3/MS4 browser modules, not from a new framework or an offline-only page.

Reference target:

```text
accepted Kane County geography
        +
administrative categories/contracts
        +
bounded condominium publication
        =
full online county browser/interface
```

The online reference interface should be used to discover and stabilize the complete category/contract model.

Only after those contracts and reusable browser modules stabilize should the project produce the reduced offline/local form by substituting local sources and removing network-only conveniences.

## Independent operator criterion

Before it is realistic to ask an independent operator to join the Civic Infrastructure for another Illinois county, the administrative contracts must be portable enough that the operator does not need Kane County's:

- hostnames;
- filesystem paths;
- private keys;
- internal GeoPackage schema as an external API;
- account database;
- proprietary service state;
- ESP32 hardware identity.

The operator should be able to implement the published jurisdiction/category/participant/browser contracts using its own infrastructure and jurisdiction-specific sources.

## Next safe action

Do **not** continue firmware development on `fw`.

Move to the host-mediated CT102 administrative environment on `srv-b`, synchronize the CT102 checkout to current GitHub `main`, verify the administrative/browser repository state, and then begin the online county/category/participant contract work.

Leave the accepted ESP32-S3 runtime unchanged until a concrete administrative contract exposes a necessary edge change or a later MS5 lifecycle gate is deliberately resumed.
