import test from "node:test";
import assert from "node:assert/strict";

import {
  AppInteractionError,
  createNavigationState,
  createVisibilityState,
  hitTestOverlay,
  inspectionView,
  interactionAcceptancePayload,
  panNavigation,
  resetNavigation,
  screenToMapPoint,
  setSubscriptionVisible,
  setSubstrateVisible,
  visibleOverlays,
  zoomNavigation,
} from "./app-interaction.js";

const overlays = [
  {
    subscription_key: "condo",
    generation_key: "kfsg1-condo",
    object_key: "condo-object",
    object_sha256: "a".repeat(64),
    bounds: [-88.4, 41.8, -88.3, 41.9],
    geographic_refs: [{ kind: "building", object_key: "building-1" }],
    payload: { proof_kind: "condo" },
    subscription_index: 0,
    object_index: 0,
    x: 100,
    y: 100,
    width: 40,
    height: 40,
  },
  {
    subscription_key: "industry",
    generation_key: "kfsg1-industry",
    object_key: "industry-object",
    object_sha256: "b".repeat(64),
    bounds: [-88.4, 41.8, -88.3, 41.9],
    geographic_refs: [],
    payload: { proof_kind: "industry" },
    subscription_index: 1,
    object_index: 0,
    x: 90,
    y: 90,
    width: 80,
    height: 80,
  },
];

test("navigation starts at full partition extent", () => {
  assert.deepEqual(createNavigationState(), { scale: 1, offset_x: 0, offset_y: 0 });
  assert.deepEqual(resetNavigation(), createNavigationState());
});

test("zoom anchors the selected screen point and remains bounded", () => {
  const state = zoomNavigation(createNavigationState(), 2, 500, 300, 1000, 600);
  assert.equal(state.scale, 2);
  assert.equal(state.offset_x, -500);
  assert.equal(state.offset_y, -300);
  assert.deepEqual(screenToMapPoint(state, 500, 300), { x: 500, y: 300 });

  const maximum = zoomNavigation(state, 100, 500, 300, 1000, 600);
  assert.equal(maximum.scale, 8);
});

test("pan is clamped so transformed map remains in the viewport", () => {
  const zoomed = zoomNavigation(createNavigationState(), 2, 0, 0, 1000, 600);
  assert.deepEqual(panNavigation(zoomed, 5000, 5000, 1000, 600), { scale: 2, offset_x: 0, offset_y: 0 });
  assert.deepEqual(panNavigation(zoomed, -5000, -5000, 1000, 600), { scale: 2, offset_x: -1000, offset_y: -600 });
});

test("visibility state independently controls substrate and subscriptions", () => {
  let state = createVisibilityState(["condo", "industry"]);
  assert.equal(state.substrate, true);
  assert.deepEqual(state.subscriptions, { condo: true, industry: true });
  state = setSubstrateVisible(state, false);
  state = setSubscriptionVisible(state, "industry", false);
  assert.equal(state.substrate, false);
  assert.deepEqual(state.subscriptions, { condo: true, industry: false });
  assert.deepEqual(visibleOverlays(overlays, state).map((entry) => entry.object_key), ["condo-object"]);
});

test("unknown subscription visibility keys fail closed", () => {
  const state = createVisibilityState(["condo"]);
  assert.throws(() => setSubscriptionVisible(state, "industry", false), AppInteractionError);
});

test("overlay hit testing prefers the smallest visible containing object", () => {
  let visibility = createVisibilityState(["condo", "industry"]);
  assert.equal(hitTestOverlay(overlays, visibility, 110, 110)?.object_key, "condo-object");
  visibility = setSubscriptionVisible(visibility, "condo", false);
  assert.equal(hitTestOverlay(overlays, visibility, 110, 110)?.object_key, "industry-object");
  visibility = setSubscriptionVisible(visibility, "industry", false);
  assert.equal(hitTestOverlay(overlays, visibility, 110, 110), null);
});

test("inspection view exposes verified object identity without inventing application semantics", () => {
  const inspected = inspectionView(overlays[0]);
  assert.equal(inspected.object_key, "condo-object");
  assert.equal(inspected.object_sha256, "a".repeat(64));
  assert.deepEqual(inspected.bounds, overlays[0].bounds);
  assert.deepEqual(inspected.payload, { proof_kind: "condo" });
});

test("interaction acceptance payload remains platform neutral", () => {
  const navigation = zoomNavigation(createNavigationState(), 2, 100, 100, 1000, 600);
  let visibility = createVisibilityState(["condo", "industry"]);
  visibility = setSubscriptionVisible(visibility, "industry", false);
  const payload = interactionAcceptancePayload(navigation, visibility, overlays[0]);
  assert.equal(payload.physical_platform_assumed, false);
  assert.deepEqual(payload.visible_subscriptions, ["condo"]);
  assert.equal(payload.selected_object_key, "condo-object");
  assert.doesNotMatch(JSON.stringify(payload), /esp32|idf|hardware/i);
});
