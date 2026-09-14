export class AppInteractionError extends Error {
  constructor(message) {
    super(message);
    this.name = "AppInteractionError";
  }
}

const MIN_SCALE = 1;
const MAX_SCALE = 8;

function fail(message) {
  throw new AppInteractionError(message);
}

function finite(value, label) {
  const number = Number(value);
  if (!Number.isFinite(number)) fail(`${label} must be finite`);
  return number;
}

function dimensions(width, height) {
  const w = finite(width, "viewport width");
  const h = finite(height, "viewport height");
  if (w <= 0 || h <= 0) fail("viewport dimensions must be positive");
  return [w, h];
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function clampNavigation(state, width, height) {
  const [w, h] = dimensions(width, height);
  const scale = clamp(finite(state.scale, "navigation scale"), MIN_SCALE, MAX_SCALE);
  const minX = w - w * scale;
  const minY = h - h * scale;
  return {
    scale,
    offset_x: clamp(finite(state.offset_x, "navigation offset_x"), minX, 0),
    offset_y: clamp(finite(state.offset_y, "navigation offset_y"), minY, 0),
  };
}

export function createNavigationState() {
  return { scale: 1, offset_x: 0, offset_y: 0 };
}

export function resetNavigation() {
  return createNavigationState();
}

export function panNavigation(state, deltaX, deltaY, width, height) {
  return clampNavigation(
    {
      scale: state.scale,
      offset_x: finite(state.offset_x, "navigation offset_x") + finite(deltaX, "pan delta_x"),
      offset_y: finite(state.offset_y, "navigation offset_y") + finite(deltaY, "pan delta_y"),
    },
    width,
    height,
  );
}

export function zoomNavigation(state, factor, anchorX, anchorY, width, height) {
  const current = clampNavigation(state, width, height);
  const zoomFactor = finite(factor, "zoom factor");
  if (zoomFactor <= 0) fail("zoom factor must be positive");
  const anchor_x = finite(anchorX, "zoom anchor_x");
  const anchor_y = finite(anchorY, "zoom anchor_y");
  const nextScale = clamp(current.scale * zoomFactor, MIN_SCALE, MAX_SCALE);
  const ratio = nextScale / current.scale;
  return clampNavigation(
    {
      scale: nextScale,
      offset_x: anchor_x - (anchor_x - current.offset_x) * ratio,
      offset_y: anchor_y - (anchor_y - current.offset_y) * ratio,
    },
    width,
    height,
  );
}

export function screenToMapPoint(state, screenX, screenY) {
  const scale = finite(state.scale, "navigation scale");
  if (scale <= 0) fail("navigation scale must be positive");
  return {
    x: (finite(screenX, "screen x") - finite(state.offset_x, "navigation offset_x")) / scale,
    y: (finite(screenY, "screen y") - finite(state.offset_y, "navigation offset_y")) / scale,
  };
}

export function createVisibilityState(subscriptionKeys) {
  if (!Array.isArray(subscriptionKeys)) fail("subscription keys must be an array");
  const keys = [];
  const seen = new Set();
  for (const value of subscriptionKeys) {
    const key = String(value);
    if (!key || seen.has(key)) fail("subscription keys must be non-empty and unique");
    seen.add(key);
    keys.push(key);
  }
  return {
    substrate: true,
    subscriptions: Object.fromEntries(keys.map((key) => [key, true])),
  };
}

export function setSubstrateVisible(state, visible) {
  return { ...state, substrate: Boolean(visible), subscriptions: { ...state.subscriptions } };
}

export function setSubscriptionVisible(state, key, visible) {
  if (!Object.prototype.hasOwnProperty.call(state.subscriptions, key)) {
    fail(`unknown subscription visibility key: ${key}`);
  }
  return {
    ...state,
    subscriptions: { ...state.subscriptions, [key]: Boolean(visible) },
  };
}

export function visibleOverlays(overlays, visibility) {
  if (!Array.isArray(overlays)) fail("overlays must be an array");
  return overlays.filter((overlay) => visibility.subscriptions?.[overlay.subscription_key] !== false);
}

export function hitTestOverlay(overlays, visibility, mapX, mapY) {
  const x = finite(mapX, "map x");
  const y = finite(mapY, "map y");
  const candidates = visibleOverlays(overlays, visibility).filter((overlay) =>
    x >= overlay.x && x <= overlay.x + overlay.width && y >= overlay.y && y <= overlay.y + overlay.height,
  );
  candidates.sort((first, second) => {
    const firstArea = first.width * first.height;
    const secondArea = second.width * second.height;
    if (firstArea !== secondArea) return firstArea - secondArea;
    if (first.subscription_index !== second.subscription_index) return second.subscription_index - first.subscription_index;
    return second.object_index - first.object_index;
  });
  return candidates[0] ?? null;
}

export function inspectionView(overlay) {
  if (overlay === null) return null;
  if (!overlay || typeof overlay !== "object" || Array.isArray(overlay)) fail("inspection overlay must be an object");
  return {
    subscription_key: String(overlay.subscription_key ?? ""),
    generation_key: String(overlay.generation_key ?? ""),
    object_key: String(overlay.object_key ?? ""),
    object_sha256: String(overlay.object_sha256 ?? ""),
    bounds: Array.isArray(overlay.bounds) ? [...overlay.bounds] : [],
    geographic_refs: Array.isArray(overlay.geographic_refs) ? overlay.geographic_refs.map((entry) => ({ ...entry })) : [],
    payload: overlay.payload ?? null,
  };
}

export function interactionAcceptancePayload(navigation, visibility, selectedOverlay) {
  const enabledSubscriptions = Object.entries(visibility.subscriptions ?? {})
    .filter(([, visible]) => visible)
    .map(([key]) => key)
    .sort();
  return {
    navigation: {
      scale: navigation.scale,
      offset_x: navigation.offset_x,
      offset_y: navigation.offset_y,
    },
    substrate_visible: visibility.substrate,
    visible_subscriptions: enabledSubscriptions,
    selected_object_key: selectedOverlay?.object_key ?? null,
    physical_platform_assumed: false,
  };
}

export const _test = { MIN_SCALE, MAX_SCALE };
