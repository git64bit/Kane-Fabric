import { loadPartitionComposition } from "../ms4/browser/kane-fabric-ms4.js";
import { configFromSearch } from "./app-config.js";
import {
  AdministrativeDescriptorError,
  descriptorSummary,
  renderAdministrativeDescriptor,
  sha256CanonicalJson,
} from "./admin-descriptor.js";
import {
  composeParticipantPublication,
  loadParticipantPublication,
} from "./participant-publication.js";

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

function waitForVerifiedGeographicComposition() {
  const page = document.documentElement;
  const evaluate = () => {
    if (page.dataset.verification === "verified") return "verified";
    if (page.dataset.state === "failed" || page.dataset.state === "unconfigured") return "blocked";
    return "waiting";
  };
  const current = evaluate();
  if (current === "verified") return Promise.resolve();
  if (current === "blocked") return Promise.reject(new Error("geographic composition is not verified"));

  return new Promise((resolve, reject) => {
    const observer = new MutationObserver(() => {
      const state = evaluate();
      if (state === "waiting") return;
      observer.disconnect();
      if (state === "verified") resolve();
      else reject(new Error("geographic composition did not verify"));
    });
    observer.observe(page, { attributes: true, attributeFilter: ["data-state", "data-verification"] });
  });
}

function subjectLabel(subject) {
  if (subject.kind === "association") return "Association publication";
  return `Unit publication · ${subject.unit_anchor.recorded_unit_designation}`;
}

async function renderParticipantPublication(panel, descriptorRegistry) {
  const page = document.documentElement;
  page.dataset.participantPublication = "not-configured";
  delete page.dataset.participantDescriptorCount;

  let config;
  try {
    config = configFromSearch(location.search, location.href);
  } catch (error) {
    panel.replaceChildren(paragraph("admin-load-error", `Participant source configuration rejected: ${String(error?.message || error)}`));
    page.dataset.participantPublication = "failed";
    return;
  }

  if (!config.participantSource) {
    panel.replaceChildren(paragraph("admin-app-help", "No participant publication is configured. Administrative descriptors remain available as the infrastructure baseline."));
    return;
  }
  if (!config.configured) {
    panel.replaceChildren(paragraph("admin-load-error", "Participant publication requires a configured and verified geographic composition."));
    page.dataset.participantPublication = "blocked";
    return;
  }

  page.dataset.participantPublication = "waiting";
  panel.replaceChildren(paragraph("admin-loading", "Waiting for verified geographic composition before loading participant data…"));

  try {
    await waitForVerifiedGeographicComposition();
    page.dataset.participantPublication = "loading";
    panel.replaceChildren(paragraph("admin-loading", "Loading and validating participant publication…"));

    const [compositionResult, publication] = await Promise.all([
      loadPartitionComposition(config.compositionBase, config.partition),
      loadParticipantPublication(config.participantSource),
    ]);
    const composed = composeParticipantPublication(publication, compositionResult, descriptorRegistry);

    const header = document.createElement("header");
    header.className = "admin-app-header";
    header.append(paragraph("admin-kicker", "Participant publication"));
    const heading = document.createElement("h2");
    heading.textContent = "Verified participant data";
    header.append(heading);
    header.append(paragraph("admin-app-help", "Participant data is composed only after the geographic view verifies, its geographic references match that verified composition, and its descriptor identities match the accepted administrative baseline."));
    panel.replaceChildren(header);

    composed.forEach(({ descriptor, instance }, index) => {
      const frame = document.createElement("section");
      frame.className = "admin-descriptor-frame participant-descriptor-frame";
      frame.dataset.participantDescriptorId = instance.descriptor_id;
      frame.dataset.participantSubject = instance.subject.kind;

      const provenance = document.createElement("div");
      provenance.className = "admin-descriptor-provenance";
      provenance.append(
        paragraph("admin-descriptor-source", subjectLabel(instance.subject)),
        paragraph("admin-descriptor-version", `${instance.descriptor_id} · descriptor v${instance.descriptor_version} · ${instance.geographic_refs.length} verified geographic reference${instance.geographic_refs.length === 1 ? "" : "s"}`),
      );
      frame.append(provenance);

      const host = document.createElement("div");
      frame.append(host);
      renderAdministrativeDescriptor(host, descriptor, {
        initialData: instance.data,
        idPrefix: `participant-${index}-${instance.descriptor_id.replace(/[^a-zA-Z0-9_-]+/g, "-")}`,
      });
      applyPresentationMetadata(host, descriptor);
      panel.append(frame);
    });

    page.dataset.participantPublication = "verified";
    page.dataset.participantDescriptorCount = String(composed.length);
  } catch (error) {
    panel.replaceChildren();
    const failure = document.createElement("section");
    failure.className = "admin-load-error";
    const heading = document.createElement("h2");
    heading.textContent = "Participant publication not composed";
    failure.append(heading, paragraph("", String(error?.message || error)));
    panel.append(failure);
    page.dataset.participantPublication = "failed";
    delete page.dataset.participantDescriptorCount;
  }
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

    const participantPanel = document.createElement("section");
    participantPanel.className = "admin-participant-panel";
    participantPanel.setAttribute("aria-label", "Participant publication composition");
    participantPanel.append(paragraph("admin-loading", "Preparing participant publication composition…"));
    root.append(participantPanel);

    const descriptorRegistry = new Map();
    for (const source of bootstrap.descriptor_sources) {
      if (source.enabled === false) continue;
      const url = new URL(source.url, BOOTSTRAP_URL);
      const descriptor = await fetchJson(url, source.label ?? source.url);
      const summary = descriptorSummary(descriptor);
      const hash = await sha256CanonicalJson(descriptor);
      descriptorRegistry.set(summary.descriptor_id, descriptor);

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

    await renderParticipantPublication(participantPanel, descriptorRegistry);
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
