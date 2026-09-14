import { renderPartitionComposition } from "../ms4/browser/kane-fabric-ms4.js";
import { renderSubstrate } from "../substrate/browser/kane-fabric-renderer.js";
import { AppConfigError, configFromSearch, sourceSummary } from "./app-config.js";
import { acceptancePayload, buildCompositionView, projectSubscriptionOverlays } from "./app-view.js";
import {
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

const OVERLAY_STYLES = [
  { stroke: "#a33f3f", fill: "rgba(163,63,63,.12)" },
  { stroke: "#315f9b", fill: "rgba(49,95,155,.12)" },
  { stroke: "#6b5a24", fill: "rgba(107,90,36,.12)" },
  { stroke: "#4c6f50", fill: "rgba(76,111,80,.12)" },
];

const elements = {
  root: document.documentElement,
  canvas: document.getElementById("map"),
  state: document.getElementById("state"),
  sourceLabel: document.getElementById("source-label"),
  sourceDetail: document.getElementById("source-detail"),
  jurisdiction: document.getElementById("jurisdiction"),
  identity: document.getElementById("substrate-identity"),
  partition: document.getElementById("partition"),
  objectCount: document.getElementById("object-count"),
  subscriptions: document.getElementById("subscriptions"),
  layers: document.getElementById("layers"),
  inspector: document.getElementById("inspector"),
  navigationStatus: document.getElementById("navigation-status"),
  zoomIn: document.getElementById("zoom-in"),
  zoomOut: document.getElementById("zoom-out"),
  resetView: document.getElementById("reset-view"),
  setup: document.getElementById("setup"),
  error: document.getElementById("error"),
  machineStatus: document.getElementById("machine-status"),
};

const session = {
  result: null,
  view: null,
  overlays: [],
  baseCanvas: null,
  composedCanvas: null,
  navigation: createNavigationState(),
  visibility: null,
  selected: null,
  drag: null,
};

function setState(state, text) {
  elements.root.dataset.state = state;
  elements.state.dataset.state = state;
  elements.state.textContent = text;
}

function text(value, fallback = "—") {
  if (value === null || value === undefined || String(value).trim() === "") return fallback;
  return String(value);
}

function drawSubscriptionOverlays(context, overlays) {
  overlays.forEach((overlay) => {
    const style = OVERLAY_STYLES[overlay.subscription_index % OVERLAY_STYLES.length];
    context.save();
    context.fillStyle = style.fill;
    context.strokeStyle = style.stroke;
    context.lineWidth = 2;
    context.setLineDash(overlay.subscription_index % 2 === 0 ? [] : [6, 4]);
    context.fillRect(overlay.x, overlay.y, overlay.width, overlay.height);
    context.strokeRect(overlay.x, overlay.y, overlay.width, overlay.height);
    context.beginPath();
    context.arc(overlay.center_x, overlay.center_y, 3.5 + overlay.subscription_index * 1.5, 0, Math.PI * 2);
    context.fillStyle = style.stroke;
    context.fill();
    context.restore();
  });
}

function redrawMap() {
  if (!session.baseCanvas || !session.composedCanvas || !session.visibility) return;
  const composed = session.composedCanvas.getContext("2d");
  const display = elements.canvas.getContext("2d");
  if (!composed || !display) throw new Error("Canvas 2D context is unavailable");

  composed.clearRect(0, 0, session.composedCanvas.width, session.composedCanvas.height);
  composed.fillStyle = "#fff";
  composed.fillRect(0, 0, session.composedCanvas.width, session.composedCanvas.height);
  if (session.visibility.substrate) composed.drawImage(session.baseCanvas, 0, 0);
  drawSubscriptionOverlays(composed, visibleOverlays(session.overlays, session.visibility));

  display.save();
  display.setTransform(1, 0, 0, 1, 0, 0);
  display.clearRect(0, 0, elements.canvas.width, elements.canvas.height);
  display.fillStyle = "#fff";
  display.fillRect(0, 0, elements.canvas.width, elements.canvas.height);
  display.setTransform(
    session.navigation.scale,
    0,
    0,
    session.navigation.scale,
    session.navigation.offset_x,
    session.navigation.offset_y,
  );
  display.drawImage(session.composedCanvas, 0, 0);
  display.restore();

  elements.navigationStatus.textContent = `${session.navigation.scale.toFixed(2)}×`;
  publishMachineStatus();
}

function renderSubscriptions(subscriptions) {
  elements.subscriptions.replaceChildren();
  subscriptions.forEach((subscription, index) => {
    const item = document.createElement("li");
    const heading = document.createElement("div");
    heading.className = "subscription-heading";
    const swatch = document.createElement("span");
    swatch.className = "swatch";
    swatch.style.setProperty("--swatch", OVERLAY_STYLES[index % OVERLAY_STYLES.length].stroke);
    const strong = document.createElement("strong");
    strong.textContent = text(subscription.subscription_key, "subscription");
    heading.append(swatch, strong);

    const meta = document.createElement("div");
    meta.className = "subscription-meta";
    const code = document.createElement("code");
    code.textContent = text(subscription.generation_key, "generation unavailable");
    const count = document.createElement("span");
    count.textContent = `${subscription.object_count} composed object${subscription.object_count === 1 ? "" : "s"}`;
    meta.append(code, count);
    item.append(heading, meta);
    elements.subscriptions.append(item);
  });
}

function checkboxRow(labelText, checked, onChange, swatch = null) {
  const label = document.createElement("label");
  label.className = "layer-row";
  const input = document.createElement("input");
  input.type = "checkbox";
  input.checked = checked;
  input.addEventListener("change", () => onChange(input.checked));
  if (swatch) {
    const marker = document.createElement("span");
    marker.className = "swatch";
    marker.style.setProperty("--swatch", swatch);
    label.append(input, marker, document.createTextNode(labelText));
  } else {
    label.append(input, document.createTextNode(labelText));
  }
  return label;
}

function renderLayerControls(view) {
  elements.layers.replaceChildren();
  elements.layers.append(
    checkboxRow("Accepted substrate", true, (checked) => {
      session.visibility = setSubstrateVisible(session.visibility, checked);
      redrawMap();
    }),
  );
  view.subscriptions.forEach((subscription, index) => {
    elements.layers.append(
      checkboxRow(subscription.subscription_key, true, (checked) => {
        session.visibility = setSubscriptionVisible(session.visibility, subscription.subscription_key, checked);
        if (session.selected?.subscription_key === subscription.subscription_key && !checked) {
          session.selected = null;
          renderInspector(null);
        }
        redrawMap();
      }, OVERLAY_STYLES[index % OVERLAY_STYLES.length].stroke),
    );
  });
}

function renderInspector(overlay) {
  elements.inspector.replaceChildren();
  const inspected = inspectionView(overlay);
  if (!inspected) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "Select a visible subscription object on the map.";
    elements.inspector.append(empty);
    return;
  }

  const title = document.createElement("strong");
  title.textContent = inspected.object_key;
  const subscription = document.createElement("p");
  subscription.textContent = `Subscription: ${inspected.subscription_key}`;
  const generation = document.createElement("code");
  generation.textContent = inspected.generation_key;
  const identity = document.createElement("code");
  identity.textContent = inspected.object_sha256;
  const bounds = document.createElement("p");
  bounds.textContent = `Bounds: ${inspected.bounds.join(", ")}`;
  const payload = document.createElement("pre");
  payload.className = "inspector-payload";
  payload.textContent = JSON.stringify(inspected.payload, null, 2);

  elements.inspector.append(title, subscription, generation, identity, bounds, payload);
}

function publishMachineStatus() {
  if (!session.view || !session.visibility) return;
  const payload = {
    ...acceptancePayload(session.view, session.overlays),
    ...interactionAcceptancePayload(session.navigation, session.visibility, session.selected),
    status: "web-003-interactive",
  };
  elements.machineStatus.textContent = JSON.stringify(payload);
  elements.root.dataset.substrateIdentity = payload.substrate_content_sha256;
  elements.root.dataset.partitionName = payload.partition_name;
  elements.root.dataset.objectCount = String(payload.object_count);
  elements.root.dataset.overlayCount = String(payload.overlay_count);
  elements.root.dataset.zoom = String(payload.navigation.scale);
}

function canvasPoint(event) {
  const rect = elements.canvas.getBoundingClientRect();
  return {
    x: (event.clientX - rect.left) * (elements.canvas.width / rect.width),
    y: (event.clientY - rect.top) * (elements.canvas.height / rect.height),
  };
}

function inspectAt(point) {
  const mapPoint = screenToMapPoint(session.navigation, point.x, point.y);
  session.selected = hitTestOverlay(session.overlays, session.visibility, mapPoint.x, mapPoint.y);
  renderInspector(session.selected);
  publishMachineStatus();
}

function installInteractionHandlers() {
  elements.zoomIn.addEventListener("click", () => {
    session.navigation = zoomNavigation(session.navigation, 1.5, elements.canvas.width / 2, elements.canvas.height / 2, elements.canvas.width, elements.canvas.height);
    redrawMap();
  });
  elements.zoomOut.addEventListener("click", () => {
    session.navigation = zoomNavigation(session.navigation, 1 / 1.5, elements.canvas.width / 2, elements.canvas.height / 2, elements.canvas.width, elements.canvas.height);
    redrawMap();
  });
  elements.resetView.addEventListener("click", () => {
    session.navigation = resetNavigation();
    redrawMap();
  });

  elements.canvas.addEventListener("wheel", (event) => {
    event.preventDefault();
    const point = canvasPoint(event);
    session.navigation = zoomNavigation(session.navigation, event.deltaY < 0 ? 1.25 : 0.8, point.x, point.y, elements.canvas.width, elements.canvas.height);
    redrawMap();
  }, { passive: false });

  elements.canvas.addEventListener("pointerdown", (event) => {
    const point = canvasPoint(event);
    session.drag = { pointerId: event.pointerId, point, moved: false };
    elements.canvas.setPointerCapture?.(event.pointerId);
  });
  elements.canvas.addEventListener("pointermove", (event) => {
    if (!session.drag || session.drag.pointerId !== event.pointerId) return;
    const point = canvasPoint(event);
    const dx = point.x - session.drag.point.x;
    const dy = point.y - session.drag.point.y;
    if (Math.abs(dx) + Math.abs(dy) > 1) session.drag.moved = true;
    session.navigation = panNavigation(session.navigation, dx, dy, elements.canvas.width, elements.canvas.height);
    session.drag.point = point;
    redrawMap();
  });
  elements.canvas.addEventListener("pointerup", (event) => {
    if (!session.drag || session.drag.pointerId !== event.pointerId) return;
    const point = canvasPoint(event);
    const moved = session.drag.moved;
    session.drag = null;
    if (!moved) inspectAt(point);
  });

  elements.canvas.addEventListener("keydown", (event) => {
    const step = 48;
    if (event.key === "+" || event.key === "=") {
      event.preventDefault();
      elements.zoomIn.click();
    } else if (event.key === "-" || event.key === "_") {
      event.preventDefault();
      elements.zoomOut.click();
    } else if (event.key === "0") {
      event.preventDefault();
      elements.resetView.click();
    } else if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) {
      event.preventDefault();
      const dx = event.key === "ArrowLeft" ? step : event.key === "ArrowRight" ? -step : 0;
      const dy = event.key === "ArrowUp" ? step : event.key === "ArrowDown" ? -step : 0;
      session.navigation = panNavigation(session.navigation, dx, dy, elements.canvas.width, elements.canvas.height);
      redrawMap();
    }
  });
}

function showSetup(config) {
  elements.setup.hidden = false;
  elements.setup.querySelector("code").textContent =
    `?substrate=${encodeURIComponent("https://artifact-source.example/substrate/")}` +
    `&composition=${encodeURIComponent("https://artifact-source.example/ms4/")}` +
    `&partition=${encodeURIComponent("partition-ref")}`;
  elements.partition.textContent = config.partition ?? "—";
  setState("unconfigured", "Source configuration required");
}

async function start() {
  let config;
  try {
    config = configFromSearch(location.search, location.href);
  } catch (error) {
    const message = error instanceof AppConfigError ? error.message : String(error?.stack || error);
    elements.error.hidden = false;
    elements.error.textContent = message;
    setState("failed", "Configuration rejected");
    return;
  }

  const summary = sourceSummary(config);
  elements.sourceLabel.textContent = summary.label;
  elements.sourceDetail.textContent = summary.detail;

  if (!config.configured) {
    showSetup(config);
    return;
  }

  elements.partition.textContent = config.partition;
  setState("loading", "Loading and verifying Fabric artifacts…");

  try {
    const result = await renderPartitionComposition(
      elements.canvas,
      config.substrateBase,
      config.compositionBase,
      config.partition,
      { renderImpl: renderSubstrate },
    );

    const view = buildCompositionView(result);
    const overlays = projectSubscriptionOverlays(result, elements.canvas.width, elements.canvas.height);
    if (overlays.length !== view.object_count) throw new Error("subscription overlay count differs from verified composed object count");

    const baseCanvas = document.createElement("canvas");
    baseCanvas.width = elements.canvas.width;
    baseCanvas.height = elements.canvas.height;
    baseCanvas.getContext("2d").drawImage(elements.canvas, 0, 0);
    const composedCanvas = document.createElement("canvas");
    composedCanvas.width = elements.canvas.width;
    composedCanvas.height = elements.canvas.height;

    session.result = result;
    session.view = view;
    session.overlays = overlays;
    session.baseCanvas = baseCanvas;
    session.composedCanvas = composedCanvas;
    session.navigation = createNavigationState();
    session.visibility = createVisibilityState(view.subscriptions.map((entry) => entry.subscription_key));

    elements.jurisdiction.textContent = `${text(view.jurisdiction_name)}${view.jurisdiction_fips ? ` (${view.jurisdiction_fips})` : ""}`;
    elements.identity.textContent = view.substrate_content_sha256;
    elements.partition.textContent = view.partition_name ? `${view.partition_name} — ${view.partition_key}` : view.partition_key;
    elements.objectCount.textContent = String(view.object_count);
    renderSubscriptions(view.subscriptions);
    renderLayerControls(view);
    renderInspector(null);
    elements.error.hidden = true;
    redrawMap();
    setState("verified", "Verified interactive Fabric composition");
  } catch (error) {
    elements.error.hidden = false;
    elements.error.textContent = String(error?.stack || error);
    setState("failed", "Artifact verification or rendering failed");
  }
}

installInteractionHandlers();
start();
