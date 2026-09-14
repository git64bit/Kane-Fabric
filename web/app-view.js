import { createViewportProjection } from "../substrate/browser/kane-fabric-renderer.js";

export class AppViewError extends Error {
  constructor(message) {
    super(message);
    this.name = "AppViewError";
  }
}

function fail(message) {
  throw new AppViewError(message);
}

function objectValue(value, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) fail(`${label} must be an object`);
  return value;
}

function finiteBounds(value, label) {
  if (!Array.isArray(value) || value.length !== 4) fail(`${label} must contain four coordinates`);
  const bounds = value.map((item, index) => {
    const number = Number(item);
    if (!Number.isFinite(number)) fail(`${label}[${index}] must be finite`);
    return number;
  });
  if (bounds[0] >= bounds[2] || bounds[1] >= bounds[3]) fail(`${label} must have positive width and height`);
  return bounds;
}

export function renderBoundsForDescriptor(descriptor) {
  objectValue(descriptor, "partition descriptor");
  const scope = objectValue(descriptor.scope, "partition scope");
  if (scope.scope_class === "bounded-region" || scope.scope_class === "administrative") {
    return finiteBounds(objectValue(scope.definition, "scope definition").bounds, "partition bounds");
  }
  fail(`WEB-002 overlay requires a bounded or administrative partition, got ${String(scope.scope_class)}`);
}

export function buildCompositionView(result) {
  objectValue(result, "composition result");
  const composition = objectValue(result.composition, "composition manifest");
  const descriptor = objectValue(result.descriptor, "partition descriptor");
  const renderer = objectValue(result.renderer, "renderer result");
  const jurisdiction = objectValue(composition.jurisdiction, "jurisdiction");
  if (renderer.substrate_content_sha256 !== composition.substrate_content_sha256) {
    fail("renderer substrate identity differs from composition identity");
  }
  if (!Array.isArray(result.subscriptions)) fail("subscriptions must be an array");

  const subscriptions = result.subscriptions.map((entry) => {
    const manifest = objectValue(entry?.manifest, "subscription manifest");
    if (!Array.isArray(entry.objects)) fail("subscription objects must be an array");
    return {
      subscription_key: String(manifest.subscription_key ?? ""),
      generation_key: String(manifest.generation_key ?? ""),
      object_count: entry.objects.length,
    };
  });

  return {
    jurisdiction_name: String(jurisdiction.name ?? ""),
    jurisdiction_fips: String(jurisdiction.fips_code ?? ""),
    composition_sha256: String(composition.composition_sha256 ?? ""),
    partition_name: String(composition.partitions?.find((entry) => entry?.partition_key === descriptor.partition_key)?.name ?? ""),
    partition_key: String(descriptor.partition_key ?? ""),
    partition_label: descriptor.label === null || descriptor.label === undefined ? "" : String(descriptor.label),
    substrate_content_sha256: String(composition.substrate_content_sha256 ?? ""),
    subscription_count: subscriptions.length,
    object_count: subscriptions.reduce((total, entry) => total + entry.object_count, 0),
    subscriptions,
  };
}

export function projectSubscriptionOverlays(result, width, height, padding = 24) {
  objectValue(result, "composition result");
  if (!Number.isInteger(width) || width <= 0 || !Number.isInteger(height) || height <= 0) {
    fail("canvas dimensions must be positive integers");
  }
  const projection = createViewportProjection(renderBoundsForDescriptor(result.descriptor), width, height, padding);
  if (!Array.isArray(result.subscriptions)) fail("subscriptions must be an array");

  const overlays = [];
  result.subscriptions.forEach((entry, subscriptionIndex) => {
    const manifest = objectValue(entry?.manifest, "subscription manifest");
    if (!Array.isArray(entry.objects)) fail("subscription objects must be an array");
    entry.objects.forEach((object, objectIndex) => {
      objectValue(object, "subscription object");
      const bounds = finiteBounds(object.bounds, "subscription object bounds");
      const [left, bottom] = projection.project([bounds[0], bounds[1]]);
      const [right, top] = projection.project([bounds[2], bounds[3]]);
      const expansion = 3 + subscriptionIndex * 4;
      overlays.push({
        subscription_key: String(manifest.subscription_key ?? ""),
        generation_key: String(manifest.generation_key ?? ""),
        object_key: String(object.object_key ?? ""),
        object_sha256: String(object.object_sha256 ?? ""),
        bounds,
        geographic_refs: Array.isArray(object.geographic_refs) ? object.geographic_refs.map((entry) => ({ ...entry })) : [],
        payload: object.payload ?? null,
        subscription_index: subscriptionIndex,
        object_index: objectIndex,
        x: Math.min(left, right) - expansion,
        y: Math.min(top, bottom) - expansion,
        width: Math.abs(right - left) + expansion * 2,
        height: Math.abs(bottom - top) + expansion * 2,
        center_x: (left + right) / 2,
        center_y: (top + bottom) / 2,
      });
    });
  });
  return overlays;
}

export function acceptancePayload(view, overlays) {
  objectValue(view, "composition view");
  if (!Array.isArray(overlays)) fail("overlays must be an array");
  return {
    status: "web-002-verified",
    jurisdiction: view.jurisdiction_name,
    jurisdiction_fips: view.jurisdiction_fips,
    substrate_content_sha256: view.substrate_content_sha256,
    composition_sha256: view.composition_sha256,
    partition_name: view.partition_name,
    partition_key: view.partition_key,
    subscription_generations: view.subscriptions.map((entry) => ({
      subscription_key: entry.subscription_key,
      generation_key: entry.generation_key,
      object_count: entry.object_count,
    })),
    object_count: view.object_count,
    overlay_count: overlays.length,
    physical_platform_assumed: false,
  };
}
