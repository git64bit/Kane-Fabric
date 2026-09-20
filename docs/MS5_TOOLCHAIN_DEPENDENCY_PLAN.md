# MS5-005 — ESP-IDF and Toolchain Selection Plan

## Status

This document records the Milestone 5 reference firmware SDK/toolchain selection.
It is subordinate to `docs/MILESTONE_5_DESIGN.md`, which remains the sole
normative authority for the MS5 work sequence.

The machine-readable selection is:

```text
ms5/toolchain-selection.json
```

The same retained dependencies are registered in:

```text
third_party/manifest.json
```

## Reference target and build host

Reference firmware target:

```text
ESP32-S3 / esp32s3
```

Reference build-host profile:

```text
Linux x86_64 / linux-amd64
```

CT102 is the current acceptance environment. The live host architecture is
verified during MS5-005 acceptance rather than inferred from repository state.

## ESP-IDF selection

Kane Fabric selects **ESP-IDF v6.0.3** for the reference firmware baseline.

Immutable identity:

```text
release:        v6.0.3
commit:         76f5dedd9950a3012fee8fb7d5586df21fc67802
release asset:  esp-idf-v6.0.3.zip
SHA-256:        748b12484402d8a1cb58ba68b7545d2a1f96d36820ab0145e0332c8348ba5ab7
tools.json blob 2cf625c4bdd3b8b9baa6c1566ff94c802ddbe0fd
```

The release archive is Espressif's submodule-inclusive asset. The ordinary
GitHub source archive is not an adequate replacement because ESP-IDF uses Git
submodules.

v6.0.3 is intentionally selected instead of following a moving release branch
or automatically adopting the newest minor release. It is a bugfix release on
the established v6.0 line and supplies the ESP32-S3 facilities needed by the
reference design. Any future upgrade is an explicit Kane Fabric dependency
change with compatibility and license review.

## ESP32-S3 compiler selection

ESP-IDF v6.0.3 `tools/tools.json` selects the following Xtensa compiler for the
ESP32-S3 Linux-amd64 build profile:

```text
name:           xtensa-esp-elf
version:        15.2.0_20251204
archive:        xtensa-esp-elf-15.2.0_20251204-x86_64-linux-gnu.tar.xz
SHA-256:        3d50f5cd5f173acfd524e07c1cd69bc99585731a415ca2e5bce879997fe602b8
```

The compiler/toolchain license is recorded as
`GPL-3.0-with-GCC-exception`. It is a firmware build tool and does not replace
the Kane Fabric root Unlicense.

## License boundary

ESP-IDF's repository root license is Apache-2.0. The exact ESP-IDF distribution
also contains third-party components under their own licenses. Selection of the
SDK therefore does not mean the whole archive is summarized legally as a
single Apache-2.0 work.

Before firmware release, the vendored SDK/toolchain set must preserve all
component license, copyright, attribution, and notice material required by the
exact selected distributions. Kane Fabric-authored firmware remains under the
repository root Unlicense; third-party terms remain scoped to their respective
third-party material.

The selected compiler is a separate build-tool dependency and is inventoried
separately for the same reason.

## Offline reproduction contract

MS5 does not permit the final firmware build to depend on live dependency
resolution.

Before firmware release, the project must have an offline-reproducible build
input set containing at least:

- the exact submodule-complete ESP-IDF v6.0.3 release archive;
- the exact Linux-amd64 Xtensa compiler archive selected above;
- every additional ESP-IDF host tool artifact actually required by the build;
- an exact lock/mirror of the Python build environment actually required by
  this ESP-IDF release;
- all required license and notice files;
- machine-readable hashes and provenance in Git.

Large immutable SDK/tool archives remain outside Git, consistent with the Kane
Fabric operational-artifact policy. Git stores the identities, hashes,
selection rules, and acceptance metadata needed to verify those archives.

`development/check-dependency-policy.py --release` is expected to remain
fail-closed until final vendoring is complete. MS5-005 selects the immutable
inputs and reproduction policy; it does not falsely mark unvendored inputs as
release-ready.

## WireGuard boundary

**No WireGuard implementation is retained by MS5-005.**

Earlier ESP32 WireGuard compilation is feasibility evidence only. MS5-008 must
perform the real runtime/resource/coexistence proof. The active MS5-008
evaluation identity is recorded separately in:

```text
ms5/management-transport-candidate.json
docs/MS5_008_MANAGEMENT_TRANSPORT_EVALUATION.md
```

That record pins an evaluation candidate and its resolved cryptographic
dependency so physical evidence is reproducible. It does **not** add either
component to `third_party/manifest.json` or make WireGuard a v1 requirement.

Only a candidate that passes the runtime/resource/coexistence proof and receives
an explicit `retain` decision may be selected, added to
`third_party/manifest.json`, license-reviewed, pinned for release, and included
in the offline reproduction set.

This prevents a compile-only observation, a moving package-manager resolution,
or a newly published upstream package from becoming a Kane Fabric dependency by
implication.

## Acceptance

MS5-005 repository acceptance requires:

- the MS5 work-sequence authority guard remains valid;
- `development/check-dependency-policy.py` passes in development mode;
- CT102 identifies as Linux x86_64 for the selected reference build profile;
- Python compileall succeeds for `ms5`;
- all MS5 contract tests pass, including the toolchain-selection tests;
- the checkout remains clean.

This acceptance freezes the selection **plan and identities**. It does not claim
that ESP32-S3 firmware has yet been built, flashed, or accepted; those are later
MS5 work items.
