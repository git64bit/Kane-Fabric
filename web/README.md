# Kane Fabric Web Application

This directory is the human-facing Kane Fabric browser application workstream defined by `docs/WEB_APPLICATION_DESIGN.md`.

It is distinct from the historical browser proof harnesses under `substrate/browser/` and `ms4/browser/`. Those modules remain the accepted verification/rendering foundation and are reused by the application rather than copied or reimplemented.

## Accepted foundation

WEB-001 established the dependency-free application shell and platform-neutral artifact-source configuration.

WEB-002 established a real user-facing vertical slice that consumes accepted MS3/MS4 artifacts, displays verified identities/generations, and visibly composes subscription objects over the accepted substrate. Its real-browser acceptance used independent ordinary HTTP origins for application code, substrate bytes, and composition bytes; no physical edge platform was assumed.

## WEB-003

WEB-003 adds application-side interaction without changing Fabric artifact identity or the browser-to-edge wire contract:

- pan, zoom, keyboard navigation, and reset of the verified map presentation;
- independent visibility controls for the accepted substrate and each verified subscription;
- deterministic hit testing of visible subscription overlays;
- inspection of verified subscription object key, generation, object SHA-256, bounds, geographic references, and application-owned payload;
- no third-party JavaScript/CSS dependency graph and no device-specific API.

Navigation operates on the already verified rendered composition. Visibility and inspection never alter accepted geography or artifact identities.

## Development source configuration

The application accepts source configuration through query parameters:

```text
substrate=<directory URL>
composition=<directory URL>
partition=<partition reference>
label=<optional human-readable source label>
```

`ms4=` remains a temporary alias for `composition=` so the application can consume existing MS4 proof layouts during transition.

The application deliberately does not infer whether the artifact source is an ESP32-S3, another microcontroller, an SBC, or a software server.

## Tests

Run:

```bash
bash web/run-tests.sh
```

The unit tests cover source normalization, verified composition presentation, projection, navigation bounds, visibility state, overlay hit testing, inspection data, and the platform-neutral interaction boundary.

Real browser acceptance belongs on CT102 using accepted Kane County artifacts. The accepted WEB-002 evidence remains valid for its implementation head and is not rerun merely because WEB-003 interaction code is developed.
