// Kane Fabric v1 browser substrate loader.
//
// This module deliberately separates metadata discovery from payload reads:
// manifest/overview use ordinary GETs, while .kfs components use exact HTTP
// byte ranges for the fixed prefix, canonical index, and selected chunks.

export const VERSION = 1;
export const SRS_ID = 4326;
export const MANIFEST_PATH = "substrate-manifest.json";

const COMPONENTS = {
  roads: {
    path: "roads-lod.kfs",
    format: "kane-fabric-substrate-roads",
    magic: "KFSR001\n",
  },
  water: {
    path: "water-lod.kfs",
    format: "kane-fabric-substrate-water",
    magic: "KFSW001\n",
  },
};

const MANIFEST_FORMAT = "kane-fabric-substrate-manifest";
const OVERVIEW_FORMAT = "kane-fabric-substrate-overview";
const ROLE_ORDER = ["county_overview", "roads", "water"];

export class SubstrateError extends Error {
  constructor(message) {
    super(message);
    this.name = "SubstrateError";
  }
}

function requireObject(value, label) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new SubstrateError(`${label} must be an object`);
  }
  return value;
}

function requireInteger(value, label, minimum = 0) {
  if (!Number.isInteger(value) || value < minimum) {
    throw new SubstrateError(`${label} must be an integer >= ${minimum}`);
  }
  return value;
}

function requireSha256(value, label) {
  if (typeof value !== "string" || !/^[0-9a-f]{64}$/.test(value)) {
    throw new SubstrateError(`${label} must be a lowercase SHA-256 hex digest`);
  }
  return value;
}

function canonicalString(value) {
  if (value === null) return "null";
  if (typeof value === "string") return JSON.stringify(value);
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      throw new SubstrateError("Canonical JSON cannot contain non-finite numbers");
    }
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map(canonicalString).join(",")}]`;
  }
  if (typeof value === "object") {
    const keys = Object.keys(value).sort();
    return `{${keys
      .map((key) => `${JSON.stringify(key)}:${canonicalString(value[key])}`)
      .join(",")}}`;
  }
  throw new SubstrateError(`Canonical JSON cannot contain ${typeof value}`);
}

export function canonicalJsonBytes(value) {
  return new TextEncoder().encode(canonicalString(value));
}

function equalBytes(first, second) {
  if (first.byteLength !== second.byteLength) return false;
  for (let index = 0; index < first.byteLength; index += 1) {
    if (first[index] !== second[index]) return false;
  }
  return true;
}

export async function sha256Hex(bytes) {
  const input = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", input));
  return Array.from(digest, (value) => value.toString(16).padStart(2, "0")).join("");
}

function parseCanonicalJson(bytes, label) {
  let text;
  try {
    text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch (error) {
    throw new SubstrateError(`${label} is not valid UTF-8: ${error.message}`);
  }
  let value;
  try {
    value = JSON.parse(text);
  } catch (error) {
    throw new SubstrateError(`${label} is not valid JSON: ${error.message}`);
  }
  if (!equalBytes(bytes, canonicalJsonBytes(value))) {
    throw new SubstrateError(`${label} is not canonical JSON`);
  }
  return value;
}

function baseDirectoryUrl(baseUrl) {
  const text = String(baseUrl);
  return new URL(text.endsWith("/") ? text : `${text}/`);
}

function componentUrl(baseUrl, path) {
  return new URL(path, baseDirectoryUrl(baseUrl));
}

async function fetchWhole(url, fetchImpl) {
  const response = await fetchImpl(url);
  if (!response.ok) {
    throw new SubstrateError(`GET ${url} failed with HTTP ${response.status}`);
  }
  return new Uint8Array(await response.arrayBuffer());
}

function parseContentRange(value) {
  const match = /^bytes (\d+)-(\d+)\/(\d+)$/.exec(value || "");
  if (!match) {
    throw new SubstrateError("Range response has invalid Content-Range");
  }
  return {
    start: Number(match[1]),
    end: Number(match[2]),
    total: Number(match[3]),
  };
}

export async function fetchExactRange(
  url,
  start,
  end,
  { expectedTotal = null, fetchImpl = fetch } = {},
) {
  requireInteger(start, "range start");
  requireInteger(end, "range end");
  if (end < start) throw new SubstrateError("range end precedes range start");

  const response = await fetchImpl(url, {
    headers: { Range: `bytes=${start}-${end}` },
  });
  if (response.status !== 206) {
    throw new SubstrateError(`Range GET ${url} returned HTTP ${response.status}; expected 206`);
  }
  const contentRange = parseContentRange(response.headers.get("Content-Range"));
  if (contentRange.start !== start || contentRange.end !== end) {
    throw new SubstrateError("Range response does not match requested byte interval");
  }
  if (expectedTotal !== null && contentRange.total !== expectedTotal) {
    throw new SubstrateError(
      `Range response total is ${contentRange.total}; expected ${expectedTotal}`,
    );
  }
  const expectedLength = end - start + 1;
  const declaredLength = response.headers.get("Content-Length");
  if (declaredLength !== null && Number(declaredLength) !== expectedLength) {
    throw new SubstrateError("Range response Content-Length is inconsistent");
  }
  const bytes = new Uint8Array(await response.arrayBuffer());
  if (bytes.byteLength !== expectedLength) {
    throw new SubstrateError("Range response body length is inconsistent");
  }
  return { bytes, total: contentRange.total };
}

function validateJurisdiction(value) {
  const item = requireObject(value, "jurisdiction");
  for (const key of ["country_code", "state_code", "fips_code", "county_key", "name"]) {
    if (typeof item[key] !== "string" || item[key].length === 0) {
      throw new SubstrateError(`jurisdiction ${key} is invalid`);
    }
  }
  return item;
}

function sameJson(first, second) {
  return canonicalString(first) === canonicalString(second);
}

function validateRelease(value) {
  const item = requireObject(value, "accepted release");
  if (typeof item.dataset_key !== "string" || !item.dataset_key) {
    throw new SubstrateError("accepted release dataset_key is invalid");
  }
  if (typeof item.release_key !== "string" || !item.release_key) {
    throw new SubstrateError("accepted release release_key is invalid");
  }
  requireSha256(item.content_sha256, "accepted release content_sha256");
  requireInteger(item.feature_count, "accepted release feature_count");
  return item;
}

function releaseByDataset(manifest, datasetKey) {
  const matches = manifest.accepted_releases.filter(
    (item) => item.dataset_key === datasetKey,
  );
  if (matches.length !== 1) {
    throw new SubstrateError(
      `manifest accepted release count for ${datasetKey} is ${matches.length}; expected 1`,
    );
  }
  return matches[0];
}

function descriptorByRole(manifest, role) {
  const matches = manifest.components.filter((item) => item.role === role);
  if (matches.length !== 1) {
    throw new SubstrateError(`manifest component count for ${role} is ${matches.length}; expected 1`);
  }
  return matches[0];
}

function validateManifest(document) {
  const manifest = requireObject(document, "substrate manifest");
  if (manifest.format !== MANIFEST_FORMAT || manifest.version !== VERSION) {
    throw new SubstrateError("substrate manifest format/version is unsupported");
  }
  if (manifest.srs_id !== SRS_ID) {
    throw new SubstrateError("substrate manifest SRS is unsupported");
  }
  validateJurisdiction(manifest.jurisdiction);
  requireSha256(manifest.substrate_content_sha256, "substrate_content_sha256");
  if (!Array.isArray(manifest.accepted_releases)) {
    throw new SubstrateError("substrate manifest accepted_releases must be an array");
  }
  manifest.accepted_releases.forEach(validateRelease);
  if (!Array.isArray(manifest.components)) {
    throw new SubstrateError("substrate manifest components must be an array");
  }
  const roles = manifest.components.map((item) => item.role);
  if (!sameJson(roles, ROLE_ORDER)) {
    throw new SubstrateError("substrate manifest component role order is invalid");
  }
  for (const descriptor of manifest.components) {
    requireObject(descriptor, "component descriptor");
    requireInteger(descriptor.byte_length, "component byte_length", 1);
    requireSha256(descriptor.sha256, "component sha256");
    if (descriptor.version !== VERSION) {
      throw new SubstrateError("component version is unsupported");
    }
  }
  return manifest;
}

export async function loadManifest(baseUrl, { fetchImpl = fetch } = {}) {
  const url = componentUrl(baseUrl, MANIFEST_PATH);
  const bytes = await fetchWhole(url, fetchImpl);
  const document = parseCanonicalJson(bytes, "substrate manifest");
  return { bytes, document: validateManifest(document), url };
}

export async function loadOverview(baseUrl, manifest, { fetchImpl = fetch } = {}) {
  const descriptor = descriptorByRole(manifest, "county_overview");
  const url = componentUrl(baseUrl, descriptor.path);
  const bytes = await fetchWhole(url, fetchImpl);
  if (bytes.byteLength !== descriptor.byte_length) {
    throw new SubstrateError("county overview byte length disagrees with manifest");
  }
  if ((await sha256Hex(bytes)) !== descriptor.sha256) {
    throw new SubstrateError("county overview SHA-256 disagrees with manifest");
  }
  const document = requireObject(
    parseCanonicalJson(bytes, "county overview"),
    "county overview",
  );
  if (document.format !== OVERVIEW_FORMAT || document.version !== VERSION) {
    throw new SubstrateError("county overview format/version is unsupported");
  }
  if (document.srs_id !== SRS_ID) {
    throw new SubstrateError("county overview SRS is unsupported");
  }
  if (!sameJson(document.jurisdiction, manifest.jurisdiction)) {
    throw new SubstrateError("county overview jurisdiction disagrees with manifest");
  }
  const source = validateRelease(document.source);
  if (!sameJson(source, releaseByDataset(manifest, "county-boundary"))) {
    throw new SubstrateError("county overview release lineage disagrees with manifest");
  }
  return { bytes, document, url };
}

function validateBounds(value, label) {
  if (!Array.isArray(value) || value.length !== 4) {
    throw new SubstrateError(`${label} bounds must contain four numbers`);
  }
  if (!value.every((item) => typeof item === "number" && Number.isFinite(item))) {
    throw new SubstrateError(`${label} bounds contain a non-finite number`);
  }
  if (value[0] > value[2] || value[1] > value[3]) {
    throw new SubstrateError(`${label} bounds are invalid`);
  }
  return value;
}

function validateFlatIndex(index, manifest, role, descriptor) {
  const spec = COMPONENTS[role];
  const document = requireObject(index, `${role} index`);
  if (document.format !== spec.format || document.version !== VERSION) {
    throw new SubstrateError(`${role} index format/version is unsupported`);
  }
  if (document.srs_id !== SRS_ID || document.compression !== "zlib-deflate") {
    throw new SubstrateError(`${role} index SRS/compression is unsupported`);
  }
  if (!sameJson(document.jurisdiction, manifest.jurisdiction)) {
    throw new SubstrateError(`${role} jurisdiction disagrees with manifest`);
  }

  if (role === "roads") {
    const source = validateRelease(document.source);
    if (!sameJson(source, releaseByDataset(manifest, "roads"))) {
      throw new SubstrateError("road release lineage disagrees with manifest");
    }
  } else {
    if (!Array.isArray(document.sources) || document.sources.length !== 2) {
      throw new SubstrateError("water index must contain exactly two accepted sources");
    }
    const sources = document.sources.map(validateRelease);
    const expected = [
      releaseByDataset(manifest, "water-creeks"),
      releaseByDataset(manifest, "water-fox-river"),
    ];
    if (!sameJson(sources, expected)) {
      throw new SubstrateError("water release lineage disagrees with manifest");
    }
  }

  if (!Array.isArray(document.levels) || document.levels.length === 0) {
    throw new SubstrateError(`${role} index has no levels`);
  }

  let expectedOffset = 0;
  for (const level of document.levels) {
    requireObject(level, `${role} level`);
    if (typeof level.key !== "string" || !level.key) {
      throw new SubstrateError(`${role} level key is invalid`);
    }
    if (!Array.isArray(level.chunks) || level.chunks.length === 0) {
      throw new SubstrateError(`${role} level ${level.key} has no chunks`);
    }
    let observedFeatures = 0;
    for (const chunk of level.chunks) {
      requireObject(chunk, `${role} chunk`);
      validateBounds(chunk.bounds, `${role} chunk`);
      requireInteger(chunk.feature_count, `${role} chunk feature_count`, 1);
      requireInteger(chunk.offset, `${role} chunk offset`);
      requireInteger(chunk.length, `${role} chunk length`, 1);
      requireInteger(chunk.uncompressed_length, `${role} chunk uncompressed_length`, 1);
      requireSha256(chunk.payload_sha256, `${role} chunk payload_sha256`);
      requireSha256(chunk.records_sha256, `${role} chunk records_sha256`);
      if (chunk.offset !== expectedOffset) {
        throw new SubstrateError(`${role} chunk payload offsets are not contiguous`);
      }
      expectedOffset += chunk.length;
      observedFeatures += chunk.feature_count;
    }
    if (observedFeatures !== level.feature_count) {
      throw new SubstrateError(`${role} level ${level.key} feature_count is inconsistent`);
    }
  }
  if (descriptor.byte_length <= 16 + expectedOffset) {
    // An index must exist between the fixed prefix and the payload area.
    throw new SubstrateError(`${role} component byte length is inconsistent`);
  }
  return { document, payloadLength: expectedOffset };
}

function magicText(bytes) {
  return new TextDecoder("ascii", { fatal: true }).decode(bytes);
}

export async function openFlatComponent(
  baseUrl,
  manifest,
  role,
  { fetchImpl = fetch } = {},
) {
  const spec = COMPONENTS[role];
  if (!spec) throw new SubstrateError(`unsupported flat component role: ${role}`);
  const descriptor = descriptorByRole(manifest, role);
  if (descriptor.path !== spec.path || descriptor.format !== spec.format) {
    throw new SubstrateError(`${role} manifest descriptor does not match v1 role contract`);
  }
  const url = componentUrl(baseUrl, descriptor.path);

  const prefixResult = await fetchExactRange(url, 0, 15, {
    expectedTotal: descriptor.byte_length,
    fetchImpl,
  });
  const prefix = prefixResult.bytes;
  if (magicText(prefix.slice(0, 8)) !== spec.magic) {
    throw new SubstrateError(`${role} component magic/version is invalid`);
  }
  const view = new DataView(prefix.buffer, prefix.byteOffset, prefix.byteLength);
  const indexLengthBig = view.getBigUint64(8, false);
  if (indexLengthBig > BigInt(Number.MAX_SAFE_INTEGER)) {
    throw new SubstrateError(`${role} index length exceeds browser-safe integer range`);
  }
  const indexLength = Number(indexLengthBig);
  if (indexLength <= 0 || 16 + indexLength >= descriptor.byte_length) {
    throw new SubstrateError(`${role} index length is invalid`);
  }

  const indexResult = await fetchExactRange(url, 16, 15 + indexLength, {
    expectedTotal: descriptor.byte_length,
    fetchImpl,
  });
  const index = parseCanonicalJson(indexResult.bytes, `${role} index`);
  const validated = validateFlatIndex(index, manifest, role, descriptor);
  const payloadStart = 16 + indexLength;
  if (payloadStart + validated.payloadLength !== descriptor.byte_length) {
    throw new SubstrateError(`${role} indexed payload does not cover the component exactly`);
  }

  return {
    descriptor,
    index: validated.document,
    payloadStart,
    role,
    url,
  };
}

function intersects(first, second) {
  return !(
    first[2] < second[0] ||
    first[0] > second[2] ||
    first[3] < second[1] ||
    first[1] > second[3]
  );
}

export function chunksForLevel(component, levelKey, bounds = null) {
  const level = component.index.levels.find((item) => item.key === levelKey);
  if (!level) {
    throw new SubstrateError(`${component.role} component has no ${levelKey} level`);
  }
  if (bounds === null) return level.chunks;
  validateBounds(bounds, "viewport");
  return level.chunks.filter((chunk) => intersects(chunk.bounds, bounds));
}

async function decompressDeflate(bytes) {
  if (typeof DecompressionStream !== "function") {
    throw new SubstrateError("Browser does not provide DecompressionStream");
  }
  const stream = new Blob([bytes])
    .stream()
    .pipeThrough(new DecompressionStream("deflate"));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

export async function readChunk(component, chunk, { fetchImpl = fetch } = {}) {
  const start = component.payloadStart + chunk.offset;
  const end = start + chunk.length - 1;
  const result = await fetchExactRange(component.url, start, end, {
    expectedTotal: component.descriptor.byte_length,
    fetchImpl,
  });
  if ((await sha256Hex(result.bytes)) !== chunk.payload_sha256) {
    throw new SubstrateError(`${component.role} compressed chunk SHA-256 mismatch`);
  }
  const recordsBytes = await decompressDeflate(result.bytes);
  if (recordsBytes.byteLength !== chunk.uncompressed_length) {
    throw new SubstrateError(`${component.role} uncompressed chunk length mismatch`);
  }
  if ((await sha256Hex(recordsBytes)) !== chunk.records_sha256) {
    throw new SubstrateError(`${component.role} uncompressed chunk SHA-256 mismatch`);
  }
  const document = requireObject(
    parseCanonicalJson(recordsBytes, `${component.role} chunk records`),
    `${component.role} chunk records`,
  );
  if (!Array.isArray(document.features) || document.features.length !== chunk.feature_count) {
    throw new SubstrateError(`${component.role} chunk feature_count is inconsistent`);
  }
  return document.features;
}

export async function* streamLevelChunks(
  component,
  levelKey,
  { bounds = null, fetchImpl = fetch } = {},
) {
  const chunks = chunksForLevel(component, levelKey, bounds);
  for (const chunk of chunks) {
    const features = await readChunk(component, chunk, { fetchImpl });
    yield { chunk, features };
  }
}

export async function loadSubstrateMetadata(baseUrl, { fetchImpl = fetch } = {}) {
  const manifestResult = await loadManifest(baseUrl, { fetchImpl });
  const overviewResult = await loadOverview(baseUrl, manifestResult.document, {
    fetchImpl,
  });
  return {
    baseUrl: baseDirectoryUrl(baseUrl),
    manifest: manifestResult.document,
    overview: overviewResult.document,
  };
}
