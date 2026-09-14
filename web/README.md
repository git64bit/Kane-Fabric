# Kane Fabric Web Application

This directory is the human-facing Kane Fabric browser application workstream defined by `docs/WEB_APPLICATION_DESIGN.md`.

It is distinct from the historical proof harnesses under `substrate/browser/` and `ms4/browser/`. Those accepted verification/rendering modules remain the foundation and are reused rather than copied or weakened.

## Accepted foundation

WEB-001 established the dependency-free application shell and platform-neutral artifact-source configuration.

WEB-002 established the verified user-facing composition vertical slice against accepted MS3/MS4 artifacts in real Chromium.

WEB-003 established browser-side navigation, independent substrate/subscription visibility, and inspection of verified subscription objects without changing Fabric identity or the browser-to-edge wire contract.

## WEB-004

WEB-004 makes verification, failure, connectivity, and recovery state explicit to the user.

The application now:

- distinguishes loading/checking from verified presentation;
- marks a failed load as **not verified** and clears prior interactive presentation before a retry attempt;
- distinguishes browser offline state, network/source unavailability, and artifact verification failure;
- never treats a network failure as successful verification;
- exposes a user-controlled retry action rather than hidden automatic fallback;
- preserves an already verified in-memory presentation if connectivity is lost afterward, while explicitly reporting that no new artifact fetch is being claimed;
- keeps failure/recovery machine status platform neutral;
- introduces no service worker, browser framework, device-specific API, application identity, or geographic promotion behavior.

Verification failures from the accepted MS3/MS4 loaders remain authoritative. WEB-004 only classifies and presents those failures; it does not reimplement their cryptographic or structural checks.

## Development source configuration

The application accepts source configuration through query parameters:

```text
substrate=<directory URL>
composition=<directory URL>
partition=<partition reference>
label=<optional human-readable source label>
```

`ms4=` remains a temporary alias for `composition=` for compatibility with existing proof layouts.

The application deliberately does not infer whether the artifact source is an ESP32-S3, another microcontroller, an SBC, or a software server.

## Tests

Run:

```bash
bash web/run-tests.sh
```

Unit tests cover source normalization, verified composition presentation, projection, navigation, visibility, inspection, failure classification, verification-state presentation, fail-closed recovery status, and platform neutrality.

Real browser acceptance belongs on CT102 using accepted Kane County artifacts. Historical WEB-002 and WEB-003 acceptance remain valid at their implementation heads and are not rerun merely because WEB-004 adds status/recovery presentation.
