import { renderPartitionComposition } from "../ms4/browser/kane-fabric-ms4.js";
import { renderSubstrate } from "../substrate/browser/kane-fabric-renderer.js";
import { AppConfigError, configFromSearch, sourceSummary } from "./app-config.js";

const elements = {
  root: document.documentElement,
  canvas: document.getElementById("map"),
  state: document.getElementById("state"),
  sourceLabel: document.getElementById("source-label"),
  sourceDetail: document.getElementById("source-detail"),
  identity: document.getElementById("substrate-identity"),
  partition: document.getElementById("partition"),
  subscriptions: document.getElementById("subscriptions"),
  setup: document.getElementById("setup"),
  error: document.getElementById("error"),
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
  for (const subscription of subscriptions) {
    const item = document.createElement("li");
    const manifest = subscription?.manifest ?? {};
    const key = text(manifest.subscription_key, "subscription");
    const generation = text(manifest.generation_key, "generation unavailable");
    const strong = document.createElement("strong");
    strong.textContent = key;
    const code = document.createElement("code");
    code.textContent = generation;
    item.append(strong, document.createTextNode(" "), code);
    elements.subscriptions.append(item);
  }
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

    const substrateIdentity = result?.renderer?.substrate_content_sha256;
    if (!substrateIdentity) throw new Error("verified render did not report substrate content identity");

    elements.identity.textContent = substrateIdentity;
    renderSubscriptions(result.subscriptions);
    elements.error.hidden = true;
    setState("verified", "Verified Fabric data");
  } catch (error) {
    elements.error.hidden = false;
    elements.error.textContent = String(error?.stack || error);
    renderSubscriptions([]);
    setState("failed", "Artifact verification or rendering failed");
  }
}

start();
