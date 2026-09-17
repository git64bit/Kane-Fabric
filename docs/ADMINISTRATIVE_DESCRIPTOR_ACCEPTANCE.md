# Administrative Descriptor Browser Acceptance

Date: 2026-09-17

## Accepted implementation

The first descriptor-driven Kane Fabric Administrative Web slice is accepted at implementation source:

```text
7b8b116d5b43660d4260a21f0dc7ea85ec6bc753
```

That source includes:

- the generic administrative descriptor engine in `web/admin-descriptor.js`;
- the descriptor bootstrap in `web/admin-app.json` and `web/admin-app.js`;
- descriptor schema `administration/descriptors/descriptor-v1.schema.json`;
- Illinois condominium insurance reference descriptor `administration/descriptors/illinois/condominium/insurance.v1.json`;
- descriptor-driven layout, help, authority references, controls, collections, and canonical JSON SHA-256 presentation;
- the Node repository gate compatibility shim used only by tests.

The generic engine is intentionally jurisdiction-neutral. Illinois, condominium, insurance, county, and parish semantics belong in descriptors and profiles rather than in renderer code.

## CT102 repository acceptance

Environment:

```text
host control plane     srv-b / Proxmox / pct
container              CT102 / kane-fabric
checkout               /tmp/kane-fabric-ms2
branch                 main
accepted source HEAD   7b8b116d5b43660d4260a21f0dc7ea85ec6bc753
worktree               clean
```

Repository/browser unit suite:

```text
bash web/run-tests.sh

35 tests
35 pass
0 fail
0 skipped
```

The suite includes the new administrative descriptor tests and the previously accepted browser tests.

## Real-browser evidence

A local HTTP server was started inside CT102 and the application was loaded by the installed headless Chromium binary:

```text
BROWSER=/bin/chromium
```

The browser fetched:

```text
/web/
/web/admin-app.json
/administration/descriptors/illinois/condominium/insurance.v1.json
```

The resulting DOM dump was checked after JavaScript execution. Observed results:

```text
administrative_header=PASS
descriptor_title=PASS
descriptor_loaded_without_error=PASS
descriptor_sha256=PASS
association_policy_collection=PASS
add_policy_action=PASS
statewide_framework=PASS
form_input_rendered=PASS
form_select_rendered=PASS
form_textarea_rendered=PASS

admin_browser_checks=10/10
admin_browser_render=PASS
DOM bytes: 16254
```

This proves that the real browser successfully performed the descriptor path:

```text
HTTP fetch
  -> administrative bootstrap JSON
  -> Illinois descriptor JSON
  -> descriptor validation
  -> canonical descriptor SHA-256
  -> generic descriptor renderer
  -> generated DOM controls and layout
```

## Repository-owned repeat gate

After the observed acceptance, the successful browser procedure was converted into repository-owned tooling:

```text
web/run-admin-browser-acceptance.sh
web/validate-admin-browser-dump.py
```

The validator computes the expected canonical SHA-256 independently from the reference descriptor and requires the rendered DOM to contain that exact identity. It also checks the descriptor summary, collection action, statewide framework, and representative input/select/textarea controls.

The tooling-only commits after `7b8b116` do not alter the accepted browser implementation and therefore do not invalidate the observed implementation acceptance. They provide a repeatable gate for subsequent descriptor work.

## Acceptance scope

Accepted:

- JSON is capable of supplying the current Administrative Web semantics and presentation for this slice;
- the browser engine can remain generic while descriptor data supplies Illinois-specific meaning;
- control type, labels, help, authority references, placement, dimensions represented by the current vocabulary, options, conditional presentation, and repeating collections can be descriptor-driven;
- semantic bindings remain distinct from presentation placement;
- descriptors can be versioned and represented by a canonical SHA-256 identity;
- the first Illinois condominium insurance descriptor renders in real Chromium.

Not accepted or claimed by this checkpoint:

- final visual design or usability;
- complete Illinois condominium ontology;
- completeness of the insurance descriptor beyond the deliberately bounded first slice;
- persistent storage or server-side mutation;
- authentication, authorization, encrypted private delivery, or abuse resistance;
- offline/local reduction;
- participant-publication or edge-device contract;
- ESP32-S3 application shape;
- any requirement that is not established as Illinois-wide Civic Infrastructure or explicitly represented as association-instance data.

## Development consequence

The Administrative Web is now the active design instrument for determining the Civic Infrastructure boundary.

Development should proceed by expanding statewide Illinois condominium Infrastructure through descriptor data and generic descriptor capabilities. The edge-device shape remains deliberately deferred until the Administrative Web makes the Infrastructure-versus-participant boundary concrete enough to derive a bounded participant-publication role.
