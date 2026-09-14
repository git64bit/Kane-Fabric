import test from "node:test";
import assert from "node:assert/strict";

import {
  AppViewError,
  acceptancePayload,
  buildCompositionView,
  projectSubscriptionOverlays,
  renderBoundsForDescriptor,
} from "./app-view.js";

const RESULT = {
  composition: {
    jurisdiction: { name: "Kane County", fips_code: "17089" },
    substrate_content_sha256: "a".repeat(64),
    partitions: [{ name: "west", partition_key: "kfp1-0123456789abcdef0123456789abcdef" }],
  },
  descriptor: {
    partition_key: "kfp1-0123456789abcdef0123456789abcdef",
    label: "West proof partition",
    scope: {
      scope_class: "bounded-region",
      definition: { bounds: ["-88.6000000", "41.6000000", "-88.2950000", "42.2000000"] },
    },
  },
  renderer: { substrate_content_sha256: "a".repeat(64) },
  subscriptions: [
    {
      manifest: { subscription_key: "condo", generation_key: "kfsg1-11111111111111111111111111111111" },
      objects: [{ object_key: "condo-a", bounds: ["-88.4010000", "41.8790000", "-88.3990000", "41.8810000"] }],
    },
    {
      manifest: { subscription_key: "industry", generation_key: "kfsg1-22222222222222222222222222222222" },
      objects: [{ object_key: "industry-a", bounds: ["-88.4010000", "41.8790000", "-88.3990000", "41.8810000"] }],
    },
  ],
};

test("composition view exposes user-facing verified facts", () => {
  const view = buildCompositionView(RESULT);
  assert.equal(view.jurisdiction_name, "Kane County");
  assert.equal(view.jurisdiction_fips, "17089");
  assert.equal(view.partition_name, "west");
  assert.equal(view.subscription_count, 2);
  assert.equal(view.object_count, 2);
});

test("renderer/composition identity disagreement is rejected", () => {
  const bad = structuredClone(RESULT);
  bad.renderer.substrate_content_sha256 = "b".repeat(64);
  assert.throws(() => buildCompositionView(bad), AppViewError);
});

test("bounded partition exposes numeric render bounds", () => {
  assert.deepEqual(renderBoundsForDescriptor(RESULT.descriptor), [-88.6, 41.6, -88.295, 42.2]);
});

test("subscription overlays project into finite canvas geometry", () => {
  const overlays = projectSubscriptionOverlays(RESULT, 1024, 768);
  assert.equal(overlays.length, 2);
  for (const overlay of overlays) {
    for (const key of ["x", "y", "width", "height", "center_x", "center_y"]) {
      assert.equal(Number.isFinite(overlay[key]), true);
    }
    assert.ok(overlay.width > 0);
    assert.ok(overlay.height > 0);
  }
  assert.notEqual(overlays[0].width, overlays[1].width);
});

test("acceptance payload records visible composition without platform assumption", () => {
  const view = buildCompositionView(RESULT);
  const overlays = projectSubscriptionOverlays(RESULT, 1024, 768);
  const payload = acceptancePayload(view, overlays);
  assert.equal(payload.status, "web-002-verified");
  assert.equal(payload.object_count, 2);
  assert.equal(payload.overlay_count, 2);
  assert.equal(payload.physical_platform_assumed, false);
  assert.doesNotMatch(JSON.stringify(payload), /esp32|idf|hardware/i);
});
