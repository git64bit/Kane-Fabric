# Kane Fabric Web Application

This directory is the human-facing Kane Fabric browser application workstream defined by `docs/WEB_APPLICATION_DESIGN.md`.

It is distinct from the historical browser proof harnesses under `substrate/browser/` and `ms4/browser/`. Those modules remain the accepted verification/rendering foundation and are reused by the application rather than copied or reimplemented.

## WEB-001

The first application slice provides:

- a responsive map/application shell;
- platform-neutral artifact-source configuration;
- explicit loading, verified, unconfigured, and failure states;
- verified substrate identity display;
- subscription generation display;
- no npm or third-party browser dependency graph.

The application currently accepts development source configuration through query parameters:

```text
substrate=<directory URL>
composition=<directory URL>
partition=<partition reference>
label=<optional human-readable source label>
```

`ms4=` is accepted as a temporary alias for `composition=` so the application can consume existing MS4 proof layouts during transition.

The application deliberately does not infer whether the artifact source is an ESP32-S3, another microcontroller, an SBC, or a software server.

## Tests

Run:

```bash
bash web/run-tests.sh
```

These tests validate source-configuration normalization and the platform-neutral boundary. A real Kane County application acceptance claim requires a later CT102 real-browser gate against accepted MS3/MS4 artifacts.
