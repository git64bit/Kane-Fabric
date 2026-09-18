const SUPPORTED_PROTOCOLS = new Set(["http:", "https:"]);

export class AppConfigError extends Error {
  constructor(message) {
    super(message);
    this.name = "AppConfigError";
  }
}

function normalizeUrl(value, baseHref, label, { directory = false } = {}) {
  if (value === null || value === undefined || String(value).trim() === "") return null;
  let url;
  try {
    url = new URL(String(value).trim(), baseHref);
  } catch (error) {
    throw new AppConfigError(`${label} is not a valid URL: ${error.message}`);
  }
  if (!SUPPORTED_PROTOCOLS.has(url.protocol)) {
    throw new AppConfigError(`${label} must resolve to http: or https:`);
  }
  if (url.username || url.password) {
    throw new AppConfigError(`${label} must not contain embedded credentials`);
  }
  url.hash = "";
  if (directory && !url.pathname.endsWith("/")) url.pathname += "/";
  return url.href;
}

function normalizeDirectoryUrl(value, baseHref, label) {
  return normalizeUrl(value, baseHref, label, { directory: true });
}

function normalizeDocumentUrl(value, baseHref, label) {
  return normalizeUrl(value, baseHref, label);
}

function normalizePartition(value) {
  const text = String(value ?? "").trim();
  if (!text) return null;
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(text)) {
    throw new AppConfigError("partition contains unsupported characters");
  }
  return text;
}

function normalizeLabel(value) {
  const text = String(value ?? "").trim();
  if (!text) return null;
  if (text.length > 160) throw new AppConfigError("source label is too long");
  return text;
}

export function configFromSearch(search, baseHref) {
  const params = new URLSearchParams(search);
  const substrateBase = normalizeDirectoryUrl(params.get("substrate"), baseHref, "substrate source");
  const compositionBase = normalizeDirectoryUrl(params.get("composition") ?? params.get("ms4"), baseHref, "composition source");
  const partition = normalizePartition(params.get("partition"));
  const participantSource = normalizeDocumentUrl(params.get("participant"), baseHref, "participant publication source");
  const sourceLabel = normalizeLabel(params.get("label"));

  const missing = [];
  if (substrateBase === null) missing.push("substrate");
  if (compositionBase === null) missing.push("composition");
  if (partition === null) missing.push("partition");

  return {
    configured: missing.length === 0,
    missing,
    substrateBase,
    compositionBase,
    partition,
    participantSource,
    sourceLabel,
  };
}

export function sourceSummary(config) {
  if (!config.configured) {
    return {
      label: "Artifact source not configured",
      detail: `Missing: ${config.missing.join(", ")}`,
    };
  }
  return {
    label: config.sourceLabel || "Configured Fabric artifact source",
    detail: `partition ${config.partition}${config.participantSource ? " · participant publication configured" : ""}`,
  };
}
