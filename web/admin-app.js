import {
  AdministrativeDescriptorError,
  descriptorSummary,
  renderAdministrativeDescriptor,
  sha256CanonicalJson,
} from "./admin-descriptor.js";

const root = document.getElementById("admin-app");
const BOOTSTRAP_URL = new URL("./admin-app.json", import.meta.url);

function paragraph(className, text) {
  const node = document.createElement("p");
  node.className = className;
  node.textContent = text;
  return node;
}

async function fetchJson(url, label) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`${label} returned HTTP ${response.status}`);
  return response.json();
}

function validateBootstrap(config) {
  if (!config || config.format !== "kane-fabric-administrative-bootstrap" || config.version !== 1) {
    throw new Error("unsupported administrative bootstrap format");
  }
  if (!Array.isArray(config.descriptor_sources) || config.descriptor_sources.length === 0) {
    throw new Error("administrative bootstrap has no descriptor sources");
  }
  return config;
}

function descriptorControls(descriptor) {
  const controls = [];
  const visit = (items) => {
    items.forEach((control) => {
      controls.push(control);
      if (Array.isArray(control.item_controls)) visit(control.item_controls);
    });
  };
  descriptor.pages.forEach((page) => page.sections.forEach((section) => visit(section.controls)));
  return controls;
}

function applyPresentationMetadata(host, descriptor) {
  descriptorControls(descriptor).forEach((control) => {
    if (!control.unit && !control.format) return;
    host.querySelectorAll("[data-control-id]").forEach((node) => {
      if (node.dataset.controlId !== control.id) return;
      if (control.unit) node.dataset.unit = control.unit;
      if (control.format) node.dataset.format = control.format;
      if (!control.unit || node.querySelector(".admin-unit")) return;
      const unit = document.createElement("small");
      unit.className = "admin-unit";
      unit.textContent = control.unit;
      const field = node.querySelector("input, select, textarea");
      if (field) field.insertAdjacentElement("afterend", unit);
      else node.append(unit);
    });
  });
}

async function startAdministrativeApplication() {
  if (!root) return;
  root.replaceChildren(paragraph("admin-loading", "Loading Administrative Civic Infrastructure…"));

  try {
    const bootstrap = validateBootstrap(await fetchJson(BOOTSTRAP_URL, "administrative bootstrap"));
    root.replaceChildren();

    const header = document.createElement("header");
    header.className = "admin-app-header";
    header.append(paragraph("admin-kicker", bootstrap.kicker ?? "Civic Infrastructure"));
    const heading = document.createElement("h2");
    heading.textContent = bootstrap.title;
    header.append(heading);
    if (bootstrap.help) header.append(paragraph("admin-app-help", bootstrap.help));
    root.append(header);

    for (const source of bootstrap.descriptor_sources) {
      if (source.enabled === false) continue;
      const url = new URL(source.url, BOOTSTRAP_URL);
      const descriptor = await fetchJson(url, source.label ?? source.url);
      const summary = descriptorSummary(descriptor);
      const hash = await sha256CanonicalJson(descriptor);

      const frame = document.createElement("section");
      frame.className = "admin-descriptor-frame";
      const provenance = document.createElement("div");
      provenance.className = "admin-descriptor-provenance";
      provenance.append(
        paragraph("admin-descriptor-source", source.label ?? summary.descriptor_id),
        paragraph("admin-descriptor-version", `Descriptor v${summary.descriptor_version} · ${summary.sections} sections · ${summary.controls} controls`),
      );
      const hashNode = document.createElement("code");
      hashNode.textContent = `SHA-256 ${hash}`;
      provenance.append(hashNode);
      frame.append(provenance);

      const host = document.createElement("div");
      frame.append(host);
      renderAdministrativeDescriptor(host, descriptor);
      applyPresentationMetadata(host, descriptor);
      root.append(frame);
    }
  } catch (error) {
    root.replaceChildren();
    const panel = document.createElement("section");
    panel.className = "admin-load-error";
    const heading = document.createElement("h2");
    heading.textContent = "Administrative descriptor not loaded";
    const detail = paragraph("", error instanceof AdministrativeDescriptorError ? error.message : String(error?.stack || error));
    panel.append(heading, detail);
    root.append(panel);
  }
}

startAdministrativeApplication();
