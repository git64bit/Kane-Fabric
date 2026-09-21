# MS5-009 Firmware Authority Interrogation

## Status

This is a design-interrogation record for MS5-009. Repository reconciliation found that firmware-authenticity implementation advanced past the signer-selection stage defined by the pre-existing Firmware Authority plan.

No implementation change is authorized by this document. Release signing remains disabled; no release-signing private key is created/imported; no signer/provider is selected; no signer tooling or hardware attachment is implied. The existing ECDSA/P-256 authorization implementation is provisional until the authority design is accepted.

## Repository authority interrogated

The reconciliation read live GitHub main, including ROADMAP, MILESTONE_5_DESIGN, MS5_FIRMWARE_AUTHORITY_NODE, MS5_009_FIRMWARE_LIFECYCLE, MS5_009_FIRMWARE_UPDATE_DESCRIPTOR, CPE_FIRMWARE_AUTHORITY_ACCEPTANCE, CPE_ANNALES_LXD_BASELINE, CIVICVS_PROJECT_ENVIRONMENT, CPE_HOST_CONTROL_PLANE_MODEL, DEVELOPMENT_PROCESS, PROJECT_CHARTER, CIVIC_INFRASTRUCTURE_PRINCIPLES, CIVIC_INFRASTRUCTURE_ANTI_CAPTURE, CURRENT_STATE, HANDOFF, SESSION_START, the MS5 README, firmware-authority scaffold/state, key-provider code, firmware-authority/authorization/update-descriptor code, and the lifecycle/authorization machine contracts.

The original Firmware Authority scaffold at e42ec17f0ccd6de39c2b5b6987063a424a22a649 was also inspected.

## Findings

### 1. Signer selection was intended to precede cryptographic envelope freeze

The original staged plan requires: role/manifest contract; inert container; unsigned verification; then signer/provider selection together with public-key representation, algorithm, key-id and authorization-envelope freeze; only then operational activation.

The original firmware-authority README explicitly said the authorization envelope was not frozen because the provider had not been selected.

### 2. Current implementation is ahead of that gate

The repository currently implements ECDSA P-256/SHA-256, 64-byte P1363 signatures, 65-byte uncompressed SEC1 public keys, SHA-256 key IDs, and a fixed 152-byte authorization payload. The provider nevertheless remains selection-pending.

These are implementation candidates, not accepted authority architecture. Repository tests prove internal consistency, not signer/provider design acceptance.

### 3. Accepted OTA mechanics remain valid independently

Accepted: additive OTA layout, rollback-capable bootloader, pinned build, healthy trial confirmation, deliberate failed-trial rollback, Fabric preservation, functional Wi-Fi provisioning preservation, sequence/rollback-floor mechanics, and transport-independent update mechanics.

Physical final state remains factory=production, ota_0=production confirmed-valid, ota_1=erased, otadata=ota_0 valid.

### 4. annales preflight established absence, not selection

The read-only preflight proved zero hardware signer candidates, no release-signing private key, signing disabled, no container signer passthrough, and no PIV/PKCS#11 tooling. It did not select or imply any token, HSM, TPM, smartcard, network signer, or provider class.

### 5. Outside the container does not define physical placement

The requirement is that ordinary container-filesystem compromise cannot disclose a reusable release-signing private key. The repo has not decided whether signing is host-attached, separately hosted, network-reachable, removable/offline, or exposed through another bounded interface.

### 6. Operator presence is required but not operationally defined

The repo gives PIN and/or physical touch only as examples. It does not define what the operator independently verifies, whether presence is required for every release, whether multiple operators are required, what ceremony evidence is retained, or how a compromised authority host is prevented from obtaining approval for the wrong object.

### 7. Key origin, loss, recovery and transition remain unresolved

Generate-inside-provider versus import, private-key backup policy, spare/recovery signer strategy, lost-versus-compromised response, successor-key authorization, old-key revocation/retirement and transition behavior are not frozen.

### 8. Device trust-anchor provisioning is not frozen

The edge must contain public verification material only, but the repo has not frozen where the initial trust anchor lives, how replacement devices receive it, how successor keys become trusted, whether multiple keys may coexist during transition, or how recovery handles divergence.

### 9. Authority artifact transfer is explicitly unresolved

DEVELOPMENT_PROCESS already requires any durable MS5-009 transfer path on annales to be frozen and documented at that gate. No such path exists yet for candidate firmware, provenance, manifest, signing request, authorization, public verification material and evidence.

The invariant remains: build authority != signing authority != distribution authority.

### 10. Independent operation constrains provider selection

Kane Fabric must remain reconstructable and independently operable. Provider selection must consider availability to another operator/county, documented interfaces, dependency/license impact, provider failure/replacement and avoidance of provider-specific Fabric identity.

## Accepted versus provisional state

Accepted: canonical release-manifest structure; Firmware Authority role separation; inert annales container; hardware-backed custody requirement; operator-presence requirement; OTA/rollback mechanics; physical healthy-trial and failed-trial proofs; Fabric/provisioning preservation boundary.

Provisional/not accepted: signer/provider class; signer placement; key origin/provisioning; signature algorithm; signature/public-key encoding; authorization payload format; device trust-anchor placement; key transition/revocation; authority transfer path; signing ceremony; authority recovery with signer loss.

The current P-256 implementation may survive unchanged, be adapted, or be replaced. No conclusion is implied.

## Required interrogation before further authenticity code

1. Threat/operating model: failures and compromises, purpose of operator presence, expected release frequency, required signer availability.
2. Custody/recovery model: key origin, backup policy, lost signer, suspected compromise, recovery.
3. Provider/placement model: viable provider classes, physical placement, acceptable authority-to-signer interface.
4. Release ceremony: exact object approved, independently visible information, audit evidence, operator count.
5. Device trust anchor/key transition: initial provisioning, successor authorization, revocation, replacement-edge reconstruction.
6. Artifact transfer/distribution: build/provenance input path, signed output path, durable SSOT dependencies.
7. Only then compare provider/algorithm compatibility and select provider, algorithm, key representation and envelope together.

## Implementation hold

No further firmware-authenticity code should be written until this interrogation produces an accepted repository design checkpoint. Existing authenticity code remains as a candidate so prior work is not destroyed. After design acceptance, reconcile implementation to the design, then resume tests/build/physical signing acceptance.
