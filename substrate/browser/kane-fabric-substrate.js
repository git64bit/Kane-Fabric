// Kane Fabric v1 browser substrate loader.
//
// Small JSON files use ordinary GET. Flat .kfs components use exact byte-range
// requests for the fixed prefix, canonical index, and selected compressed
// chunks. The loader never needs whole .kfs residency in memory.

export const VERSION = 1;
export const SRS_ID = 4326;
export const MANIFEST_PATH = "substrate-manifest.json";

const ROLE_ORDER = ["county_overview", "roads", "water"];
const ROLE_CONTRACT = {
  county_overview: {
    path: "county-overview.json",
    format: "kane-fabric-substrate-overview",
  },
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

function codePointCompare(first, second) {
  const a = Array.from(first, (value) => value.codePointAt(0));
  const b = Array.from(second, (value) => value.codePointAt(0));
  const count = Math.min(a.length, b.length);
  for (let index = 0; index < count; index += 1) {
    if (a[index] !== b[index]) return a[index] - b[index];
  }
  return a.length - b.length;
}

class CanonicalJsonParser {
  constructor(text, label) {
    this.text = text;
    this.label = label;
    this.position = 0;
  }

  fail(message) {
    throw new SubstrateError(`${this.label} is not canonical JSON: ${message}`);
  }

  parse() {
    const canonical = this.value();
    if (this.position !== this.text.length) this.fail("trailing bytes");
    if (canonical !== this.text) this.fail("noncanonical structure or key ordering");
  }

  value() {
    const char = this.text[this.position];
    if (char === "{") return this.object();
    if (char === "[") return this.array();
    if (char === '"') return this.string().raw;
    if (char === "t" && this.text.startsWith("true", this.position)) {
      this.position += 4;
      return "true";
    }
    if (char === "f" && this.text.startsWith("false", this.position)) {
      this.position += 5;
      return "false";
    }
    if (char === "n" && this.text.startsWith("null", this.position)) {
      this.position += 4;
      return "null";
    }
    return this.number();
  }

  string() {
    const start = this.position;
    this.position += 1;
    let escaped = false;
    while (this.position < this.text.length) {
      const char = this.text[this.position];
      this.position += 1;
      if (escaped) {
        escaped = false;
        continue;
      }
      if (char === "\\") {
        escaped = true;
        continue;
      }
      if (char === '"') {
        const raw = this.text.slice(start, this.position);
        let value;
        try {
          value = JSON.parse(raw);
        } catch (error) {
          this.fail(`invalid string token: ${error.message}`);
        }
        if (JSON.stringify(value) !== raw) {
          this.fail("noncanonical string escape");
        }
        return { raw, value };
      }
      if (char.charCodeAt(0) < 0x20) this.fail("unescaped control character");
    }
    this.fail("unterminated string");
  }

  number() {
    const rest = this.text.slice(this.position);
    const match = /^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/.exec(rest);
    if (!match) this.fail(`unexpected token at byte ${this.position}`);
    const raw = match[0];
    this.position += raw.length;
    const value = Number(raw);
    if (!Number.isFinite(value)) this.fail("non-finite number");
    return raw;
  }

  array() {
    this.position += 1;
    const values = [];
    if (this.text[this.position] === "]") {
      this.position += 1;
      return "[]";
    }
    while (true) {
      values.push(this.value());
      const char = this.text[this.position];
      if (char === "]") {
        this.position += 1;
        return `[${values.join(",")}]`;
      }
      if (char !== ",") this.fail("array separator is invalid");
      this.position += 1;
    }
  }

  object() {
    this.position += 1;
    const entries = [];
    const seen = new Set();
    if (this.text[this.position] === "}") {
      this.position += 1;
      return "{}";
    }
    while (true) {
      if (this.text[this.position] !== '"') this.fail("object key is not a string");
      const key = this.string();
      if (seen.has(key.value)) this.fail("duplicate object key");
      seen.add(key.value);
      if (this.text[this.position] !== ":") this.fail("object key/value separator is invalid");
      this.position += 1;
      entries.push({ key: key.value, keyRaw: key.raw, value: this.value() });
      const char = this.text[this.position];
      if (char === "}") {
        this.position += 1;
        const ordered = [...entries].sort((a, b) => codePointCompare(a.key, b.key));
        return `{${ordered.map((entry) => `${entry.keyRaw}:${entry.value}`).join(",")}}`;
      }
      if (char !== ",") this.fail("object separator is invalid");
      this.position += 1;
    }
  }
}

function decodeCanonicalJson(bytes, label) {
  let text;
  try {
    text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch (error) {
    throw new SubstrateError(`${label} is not valid UTF-8: ${error.message}`);
  }
  new CanonicalJsonParser(text, label).parse();
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new SubstrateError(`${label} is not valid JSON: ${error.message}`);
  }
}

function stableSemanticString(value) {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(stableSemanticString).join(",")}]`;
  return `{${Object.keys(value)
    .sort(codePointCompare)
    .map((key) => `${JSON.stringify(key)}:${stableSemanticString(value[key])}`)
    .join(",")}}`;
}

function sameSemanticJson(first, second) {
  return stableSemanticString(first) === stableSemanticString(second);
}

export async function sha256Hex(bytes) {
  const input = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  if (!globalThis.crypto?.subtle) {
    throw new SubstrateError("Web Crypto SHA-256 is unavailable");
  }
  const digest = new Uint8Array(await globalThis.crypto.subtle.digest("SHA-256", input));
  return Array.from(digest, (value) => value.toString(16).padStart(2, "0")).join("");
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
  if (!match) throw new SubstrateError("Range response has invalid Content-Range");
  return { start: Number(match[1]), end: Number(match[2]), total: Number(match[3]) };
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
  const response = await fetchImpl(url, { headers: { Range: `bytes=${start}-${end}` } });
  if (response.status !== 206) {
    throw new SubstrateError(`Range GET ${url} returned HTTP ${response.status}; expected 206`);
  }
  const range = parseContentRange(response.headers.get("Content-Range"));
  if (range.start !== start || range.end !== end) {
    throw new SubstrateError("Range response does not match requested byte interval");
  }
  if (expectedTotal !== null && range.total !== expectedTotal) {
    throw new SubstrateError(`Range response total is ${range.total}; expected ${expectedTotal}`);
  }
  const expectedLength = end - start + 1;
  const headerLength = response.headers.get("Content-Length");
  if (headerLength !== null && Number(headerLength) !== expectedLength) {
    throw new SubstrateError("Range response Content-Length is inconsistent");
  }
  const bytes = new Uint8Array(await response.arrayBuffer());
  if (bytes.byteLength !== expectedLength) {
    throw new SubstrateError("Range response body length is inconsistent");
  }
  return { bytes, total: range.total };
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

function releaseIdentity(value) {
  const item = requireObject(value, "accepted release");
  if (typeof item.dataset_key !== "string" || !item.dataset_key) {
    throw new SubstrateError("accepted release dataset_key is invalid");
  }
  if (typeof item.release_key !== "string" || !item.release_key) {
    throw new SubstrateError("accepted release release_key is invalid");
  }
  requireSha256(item.content_sha256, "accepted release content_sha256");
  requireInteger(item.feature_count, "accepted release feature_count");
  return {
    content_sha256: item.content_sha256,
    dataset_key: item.dataset_key,
    feature_count: item.feature_count,
    release_key: item.release_key,
  };
}

function releaseByDataset(manifest, datasetKey) {
  const matches = manifest.accepted_releases.filter((item) => item.dataset_key === datasetKey);
  if (matches.length !== 1) {
    throw new SubstrateError(`manifest accepted release count for ${datasetKey} is ${matches.length}; expected 1`);
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
  if (manifest.format !== MANIFEST_FORMAT || manifest.version !== VERSION || manifest.srs_id !== SRS_ID) {
    throw new SubstrateError("substrate manifest format/version/SRS is unsupported");
  }
  validateJurisdiction(manifest.jurisdiction);
  requireSha256(manifest.substrate_content_sha256, "substrate_content_sha256");
  if (!Array.isArray(manifest.accepted_releases)) {
    throw new SubstrateError("substrate manifest accepted_releases must be an array");
  }
  manifest.accepted_releases = manifest.accepted_releases.map(releaseIdentity);
  if (!Array.isArray(manifest.components)) {
    throw new SubstrateError("substrate manifest components must be an array");
  }
  const roles = manifest.components.map((item) => item.role);
  if (!sameSemanticJson(roles, ROLE_ORDER)) {
    throw new SubstrateError("substrate manifest component role order is invalid");
  }
  for (const descriptor of manifest.components) {
    requireObject(descriptor, "component descriptor");
    const contract = ROLE_CONTRACT[descriptor.role];
    if (!contract || descriptor.path !== contract.path || descriptor.format !== contract.format) {
      throw new SubstrateError(`component descriptor for ${descriptor.role} violates v1 role contract`);
    }
    if (descriptor.version !== VERSION) throw new SubstrateError("component version is unsupported");
    requireInteger(descriptor.byte_length, "component byte_length", 1);
    requireSha256(descriptor.sha256, "component sha256");
  }
  return manifest;
}

export async function loadManifest(baseUrl, { fetchImpl = fetch } = {}) {
  const url = componentUrl(baseUrl, MANIFEST_PATH);
  const bytes = await fetchWhole(url, fetchImpl);
  return { bytes, document: validateManifest(decodeCanonicalJson(bytes, "substrate manifest")), url };
}

export async function loadOverview(baseUrl, manifest, { fetchImpl = fetch } = {}) {
  const descriptor = descriptorByRole(manifest, "county_overview");
  const url = componentUrl(baseUrl, descriptor.path);
  const bytes = await fetchWhole(url, fetchImpl);
  if (bytes.byteLength !== descriptor.byte_length || (await sha256Hex(bytes)) !== descriptor.sha256) {
    throw new SubstrateError("county overview bytes disagree with manifest");
  }
  const document = requireObject(decodeCanonicalJson(bytes, "county overview"), "county overview");
  if (document.format !== ROLE_CONTRACT.county_overview.format || document.version !== VERSION || document.srs_id !== SRS_ID) {
    throw new SubstrateError("county overview format/version/SRS is unsupported");
  }
  if (!sameSemanticJson(document.jurisdiction, manifest.jurisdiction)) {
    throw new SubstrateError("county overview jurisdiction disagrees with manifest");
  }
  const sourceRelease = releaseIdentity(document.source);
  if (!sameSemanticJson(sourceRelease, releaseByDataset(manifest, "county-boundary"))) {
    throw new SubstrateError("county overview release lineage disagrees with manifest");
  }
  return { bytes, document, url };
}

function validateBounds(value, label) {
  if (!Array.isArray(value) || value.length !== 4 || !value.every((item) => typeof item === "number" && Number.isFinite(item))) {
    throw new SubstrateError(`${label} bounds must contain four finite numbers`);
  }
  if (value[0] > value[2] || value[1] > value[3]) throw new SubstrateError(`${label} bounds are invalid`);
  return value;
}

function validateFlatIndex(index, manifest, role) {
  const contract = ROLE_CONTRACT[role];
  const document = requireObject(index, `${role} index`);
  if (document.format !== contract.format || document.version !== VERSION || document.srs_id !== SRS_ID || document.compression !== "zlib-deflate") {
    throw new SubstrateError(`${role} index format/version/SRS/compression is unsupported`);
  }
  if (!sameSemanticJson(document.jurisdiction, manifest.jurisdiction)) {
    throw new SubstrateError(`${role} jurisdiction disagrees with manifest`);
  }
  if (role === "roads") {
    if (!sameSemanticJson(releaseIdentity(document.source), releaseByDataset(manifest, "roads"))) {
      throw new SubstrateError("road release lineage disagrees with manifest");
    }
  } else {
    if (!Array.isArray(document.sources) || document.sources.length !== 2) {
      throw new SubstrateError("water index must contain exactly two accepted sources");
    }
    const actual = document.sources.map(releaseIdentity);
    const expected = [releaseByDataset(manifest, "water-creeks"), releaseByDataset(manifest, "water-fox-river")];
    if (!sameSemanticJson(actual, expected)) throw new SubstrateError("water release lineage disagrees with manifest");
  }
  if (!Array.isArray(document.levels) || document.levels.length === 0) {
    throw new SubstrateError(`${role} index has no levels`);
  }
  let expectedOffset = 0;
  for (const level of document.levels) {
    requireObject(level, `${role} level`);
    if (typeof level.key !== "string" || !level.key || !Array.isArray(level.chunks) || level.chunks.length === 0) {
      throw new SubstrateError(`${role} level metadata is invalid`);
    }
    let featureCount = 0;
    for (const chunk of level.chunks) {
      requireObject(chunk, `${role} chunk`);
      validateBounds(chunk.bounds, `${role} chunk`);
      requireInteger(chunk.feature_count, `${role} chunk feature_count`, 1);
      requireInteger(chunk.offset, `${role} chunk offset`);
      requireInteger(chunk.length, `${role} chunk length`, 1);
      requireInteger(chunk.uncompressed_length, `${role} chunk uncompressed_length`, 1);
      requireSha256(chunk.payload_sha256, `${role} chunk payload_sha256`);
      requireSha256(chunk.records_sha256, `${role} chunk records_sha256`);
      if (chunk.offset !== expectedOffset) throw new SubstrateError(`${role} chunk payload offsets are not contiguous`);
      expectedOffset += chunk.length;
      featureCount += chunk.feature_count;
    }
    if (featureCount !== level.feature_count) {
      throw new SubstrateError(`${role} level ${level.key} feature_count is inconsistent`);
    }
  }
  return { document, payloadLength: expectedOffset };
}

export async function openFlatComponent(baseUrl, manifest, role, { fetchImpl = fetch } = {}) {
  const contract = ROLE_CONTRACT[role];
  if (!contract?.magic) throw new SubstrateError(`unsupported flat component role: ${role}`);
  const descriptor = descriptorByRole(manifest, role);
  const url = componentUrl(baseUrl, descriptor.path);
  const prefix = (await fetchExactRange(url, 0, 15, { expectedTotal: descriptor.byte_length, fetchImpl })).bytes;
  const magic = new TextDecoder("ascii", { fatal: true }).decode(prefix.slice(0, 8));
  if (magic !== contract.magic) throw new SubstrateError(`${role} component magic/version is invalid`);
  const view = new DataView(prefix.buffer, prefix.byteOffset, prefix.byteLength);
  const lengthBig = view.getBigUint64(8, false);
  if (lengthBig > BigInt(Number.MAX_SAFE_INTEGER)) throw new SubstrateError(`${role} index is too large`);
  const indexLength = Number(lengthBig);
  if (indexLength <= 0 || 16 + indexLength >= descriptor.byte_length) {
    throw new SubstrateError(`${role} index length is invalid`);
  }
  const indexBytes = (await fetchExactRange(url, 16, 15 + indexLength, { expectedTotal: descriptor.byte_length, fetchImpl })).bytes;
  const validated = validateFlatIndex(decodeCanonicalJson(indexBytes, `${role} index`), manifest, role);
  const payloadStart = 16 + indexLength;
  if (payloadStart + validated.payloadLength !== descriptor.byte_length) {
    throw new SubstrateError(`${role} indexed payload does not cover the component exactly`);
  }
  return { descriptor, index: validated.document, payloadStart, role, url };
}

function intersects(first, second) {
  return !(first[2] < second[0] || first[0] > second[2] || first[3] < second[1] || first[1] > second[3]);
}

export function chunksForLevel(component, levelKey, bounds = null) {
  const level = component.index.levels.find((item) => item.key === levelKey);
  if (!level) throw new SubstrateError(`${component.role} component has no ${levelKey} level`);
  if (bounds === null) return level.chunks;
  validateBounds(bounds, "viewport");
  return level.chunks.filter((chunk) => intersects(chunk.bounds, bounds));
}

async function decompressDeflate(bytes) {
  if (typeof globalThis.DecompressionStream !== "function") {
    throw new SubstrateError("DecompressionStream is unavailable");
  }
  const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("deflate"));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

export async function readChunk(component, chunk, { fetchImpl = fetch } = {}) {
  const start = component.payloadStart + chunk.offset;
  const end = start + chunk.length - 1;
  const compressed = (await fetchExactRange(component.url, start, end, {
    expectedTotal: component.descriptor.byte_length,
    fetchImpl,
  })).bytes;
  if ((await sha256Hex(compressed)) !== chunk.payload_sha256) {
    throw new SubstrateError(`${component.role} compressed chunk SHA-256 mismatch`);
  }
  const recordsBytes = await decompressDeflate(compressed);
  if (recordsBytes.byteLength !== chunk.uncompressed_length || (await sha256Hex(recordsBytes)) !== chunk.records_sha256) {
    throw new SubstrateError(`${component.role} uncompressed chunk identity mismatch`);
  }
  const document = requireObject(decodeCanonicalJson(recordsBytes, `${component.role} chunk records`), `${component.role} chunk records`);
  if (!Array.isArray(document.features) || document.features.length !== chunk.feature_count) {
    throw new SubstrateError(`${component.role} chunk feature_count is inconsistent`);
  }
  return document.features;
}

export async function* streamLevelChunks(component, levelKey, { bounds = null, fetchImpl = fetch } = {}) {
  for (const chunk of chunksForLevel(component, levelKey, bounds)) {
    yield { chunk, features: await readChunk(component, chunk, { fetchImpl }) };
  }
}

export async function loadSubstrateMetadata(baseUrl, { fetchImpl = fetch } = {}) {
  const manifest = await loadManifest(baseUrl, { fetchImpl });
  const overview = await loadOverview(baseUrl, manifest.document, { fetchImpl });
  return {
    baseUrl: baseDirectoryUrl(baseUrl),
    manifest: manifest.document,
    overview: overview.document,
  };
}
