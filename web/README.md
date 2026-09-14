# Kane Fabric Web Application

This directory is the human-facing Kane Fabric browser application workstream defined by `docs/WEB_APPLICATION_DESIGN.md`.

It is distinct from the historical browser proof harnesses under `substrate/browser/` and `ms4/browser/`. Those modules remain the accepted verification/rendering foundation and are reused by the application rather than copied or reimplemented.

## Current boundary

The application consumes Fabric through ordinary browser URLs and browser APIs. It does not infer whether the artifact source is an ESP32-S3, another microcontroller, an SBC, or a software server.

Development source configuration uses query parameters:

```text
substrate=<directory URL>
composition=<directory URL>
partition=<partition name>
label=<optional human-readable source label>
```

`ms4=` remains a temporary alias for `composition=` so existing MS4 proof layouts can be consumed without inventing a second wire format.

## WEB-001

WEB-001 established:

- a responsive map/application shell;
- platform-neutral artifact-source configuration;
- explicit loading, verified, unconfigured, and failure states;
- verified substrate identity display;
- verified subscription generation display;
- no npm or third-party browser dependency graph.

WEB-001 was accepted on CT102 at `98873196438f87f946796d9b4ffd2ff2a5a135e4` with 8 passing Web tests.

## WEB-002

WEB-002 turns the verified composition into a visible user-facing vertical slice while preserving the accepted MS3/MS4 browser modules.

The application now exposes:

- verified Kane jurisdiction and partition identity;
- the accepted substrate content identity;
- verified subscription generation identities;
- composed subscription object counts;
- visible Canvas overlays for the verified subscription objects;
- a hidden machine-readable status payload for real-browser acceptance evidence.

Subscription overlays are application presentation only. They do not alter MS3 substrate rendering, MS4 subscription identity, or accepted geographic authority.

`validate-browser-dump.py` validates a real-browser DOM dump against the accepted Kane County MS3 substrate identity and accepted MS4 composition identity. It also requires the two proof subscriptions and visible overlay/object counts while asserting that the application made no physical-platform assumption.

## Tests

Run repository/unit tests with:

```bash
bash web/run-tests.sh
```

WEB-002 additionally requires a normal-browser gate against the accepted Kane County MS3/MS4 artifacts before the application slice is recorded as accepted. Repository tests alone do not make that claim.
