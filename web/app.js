import { renderPartitionComposition } from "../ms4/browser/kane-fabric-ms4.js";
import { renderSubstrate } from "../substrate/browser/kane-fabric-renderer.js";
import { AppConfigError, configFromSearch, sourceSummary } from "./app-config.js";
import { acceptancePayload, buildCompositionView, projectSubscriptionOverlays } from "./app-view.js";

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
  setup: document.getElementById("setup"),
  error: document.getElementById("error"),
  machineStatus: document.getElementById("machine-status"),
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

function renderSubscriptions(subscriptions) {
  elements.subscriptions.replaceChildren();
  if (!Array.isArray(subscriptions) || subscriptions.length === 0) {
    const item = document.createElement("li");
    item.textContent = "No subscriptions loaded for this partition.";
    elements.subscriptions.append(item);
    return;
  }
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

function drawSubscriptionOverlays(overlays) {
  const context = elements.canvas.getContext("2d");
  if (!context) throw new Error("Canvas 2D context is unavailable for subscription overlays");
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

function showSetup(config) {
  elements.setup.hidden = false;
  elements.setup.querySelector("code").textContent =
    `?substrate=${encodeURIComponent("https://artifact-source.example/substrate/")}` +
    `&composition=${encodeURIComponent("https://artifact-source.example/ms4/")}` +
    `&partition=${encodeURIComponent("partition-ref")}`;
  elements.partition.textContent = config.partition ?? "—";
  setState("unconfigured", "Source configuration required");
}

function publishMachineStatus(payload) {
  elements.machineStatus.textContent = JSON.stringify(payload);
  elements.root.dataset.substrateIdentity = payload.substrate_content_sha256;
  elements.root.dataset.partitionName = payload.partition_name;
  elements.root.dataset.objectCount = String(payload.object_count);
  elements.root.dataset.overlayCount = String(payload.overlay_count);
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
    if (overlays.length !== view.object_count) {
      throw new Error("subscription overlay count differs from verified composed object count");
    }
    drawSubscriptionOverlays(overlays);

    elements.jurisdiction.textContent = `${text(view.jurisdiction_name)}${view.jurisdiction_fips ? ` (${view.jurisdiction_fips})` : ""}`;
    elements.identity.textContent = view.substrate_content_sha256;
    elements.partition.textContent = view.partition_name ? `${view.partition_name} — ${view.partition_key}` : view.partition_key;
    elements.objectCount.textContent = String(view.object_count);
    renderSubscriptions(view.subscriptions);
    elements.error.hidden = true;
    publishMachineStatus(acceptancePayload(view, overlays));
    setState("verified", "Verified Fabric composition");
  } catch (error) {
    elements.error.hidden = false;
    elements.error.textContent = String(error?.stack || error);
    renderSubscriptions([]);
    setState("failed", "Artifact verification or rendering failed");
  }
}

start();
