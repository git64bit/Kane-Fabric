// Kane Fabric Milestone 4 browser composition loader.
// Browser-compatible: Web APIs only, no third-party runtime dependency.

export class Ms4CompositionError extends Error {
  constructor(message) {
    super(message);
    this.name = "Ms4CompositionError";
  }
}

const FORMAT = "kane-fabric-ms4-composition-manifest";
const VERSION = 1;
const PARTITION_KEY_RE = /^kfp1-[0-9a-f]{32}$/;
const GENERATION_KEY_RE = /^kfsg1-[0-9a-f]{32}$/;
const SHA_RE = /^[0-9a-f]{64}$/;
const SLUG_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const COORDINATE_RE = /^-?(?:0|[1-9][0-9]*)\.[0-9]{7}$/;

function fail(message) {
  throw new Ms4CompositionError(message);
}

function exactKeys(value, expected, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) fail(`${label} must be an object`);
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  if (actual.length !== wanted.length || actual.some((key, index) => key !== wanted[index])) {
    fail(`${label} keys are invalid`);
  }
}

function codePointCompare(first, second) {
  const a = Array.from(first, (value) => value.codePointAt(0));
  const b = Array.from(second, (value) => value.codePointAt(0));
  for (let index = 0; index < Math.min(a.length, b.length); index += 1) {
    if (a[index] !== b[index]) return a[index] - b[index];
  }
  return a.length - b.length;
}

function stableJson(value) {
  if (value === null || typeof value === "boolean" || typeof value === "string") return JSON.stringify(value);
  if (typeof value === "number") {
    if (!Number.isFinite(value)) fail("MS4 JSON contains a non-finite number");
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) return `[${value.map(stableJson).join(",")}]`;
  if (typeof value === "object") {
    const entries = Object.keys(value)
      .sort(codePointCompare)
      .map((key) => `${JSON.stringify(key)}:${stableJson(value[key])}`);
    return `{${entries.join(",")}}`;
  }
  fail(`MS4 JSON contains unsupported value ${typeof value}`);
}

function canonicalBytes(value) {
  return new TextEncoder().encode(stableJson(value));
}

function assertCapability(runtime = globalThis) {
  if (typeof runtime?.crypto?.subtle?.digest === "function") return runtime.crypto.subtle;
  if (runtime?.isSecureContext === false) {
    fail(
      "Kane Fabric MS4 composition verification requires Web Crypto SHA-256. " +
        "This browser context is not secure. Use a secure HTTPS origin or a " +
        "browser-recognized trustworthy local development origin.",
    );
  }
  fail(
    "Kane Fabric MS4 composition verification requires Web Crypto SHA-256, but " +
      "crypto.subtle.digest is unavailable in this runtime.",
  );
}

async function sha256Hex(bytes, runtime = globalThis) {
  const subtle = assertCapability(runtime);
  const input = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  const digest = new Uint8Array(await subtle.digest("SHA-256", input));
  return Array.from(digest, (value) => value.toString(16).padStart(2, "0")).join("");
}

function directoryUrl(baseUrl) {
  const text = String(baseUrl);
  return new URL(text.endsWith("/") ? text : `${text}/`, globalThis.location?.href);
}

async function fetchBytes(url, { fetchImpl = fetch, runtime = globalThis, expectedSha256 = null } = {}) {
  assertCapability(runtime);
  const response = await fetchImpl(url);
  if (!response.ok) fail(`GET ${url} failed with HTTP ${response.status}`);
  const bytes = new Uint8Array(await response.arrayBuffer());
  if (expectedSha256 !== null) {
    if (!SHA_RE.test(expectedSha256)) fail(`invalid expected SHA-256 for ${url}`);
    if ((await sha256Hex(bytes, runtime)) !== expectedSha256) fail(`MS4 publication byte SHA-256 mismatch for ${url}`);
  }
  return bytes;
}

function decodeJson(bytes, label) {
  try {
    const value = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
    if (!value || typeof value !== "object" || Array.isArray(value)) fail(`${label} must be an object`);
    return value;
  } catch (error) {
    if (error instanceof Ms4CompositionError) throw error;
    fail(`${label} is invalid JSON/UTF-8: ${error.message}`);
  }
}

async function verifyBodyHash(document, hashField, runtime, label) {
  const expected = document[hashField];
  if (typeof expected !== "string" || !SHA_RE.test(expected)) fail(`${label} ${hashField} is invalid`);
  const body = { ...document };
  delete body[hashField];
  const actual = await sha256Hex(canonicalBytes(body), runtime);
  if (actual !== expected) fail(`${label} ${hashField} does not match its canonical body`);
}

function validateJurisdiction(value) {
  exactKeys(value, ["country_code", "state_code", "fips_code", "county_key", "name"], "jurisdiction");
  if (!/^[A-Z]{2}$/.test(value.country_code) || !/^[A-Z]{2}$/.test(value.state_code)) fail("jurisdiction country/state code is invalid");
  if (value.country_code === "US" && !/^[0-9]{5}$/.test(value.fips_code)) fail("U.S. jurisdiction FIPS is invalid");
  if (!SLUG_RE.test(value.county_key) || typeof value.name !== "string" || value.name.trim() === "") fail("jurisdiction identity is invalid");
  return value;
}

function normalizedBounds(value, label) {
  if (!Array.isArray(value) || value.length !== 4) fail(`${label} must contain four coordinates`);
  value.forEach((item, index) => {
    if (typeof item !== "string" || !COORDINATE_RE.test(item)) fail(`${label}[${index}] is not normalized fixed-decimal text`);
    const number = Number(item);
    const limit = index === 1 || index === 3 ? 90 : 180;
    if (!Number.isFinite(number) || number < -limit || number > limit || Object.is(number, -0)) fail(`${label}[${index}] is invalid`);
  });
  const numeric = value.map(Number);
  if (numeric[0] >= numeric[2] || numeric[1] >= numeric[3]) fail(`${label} must have positive width and height`);
  return value;
}

function normalizeScope(scope) {
  exactKeys(scope, ["scope_class", "definition"], "scope");
  const definition = scope.definition;
  if (scope.scope_class === "whole-jurisdiction") {
    exactKeys(definition, ["jurisdiction"], "whole-jurisdiction definition");
    if (definition.jurisdiction !== true) fail("whole-jurisdiction definition is invalid");
    return scope;
  }
  if (scope.scope_class === "bounded-region") {
    exactKeys(definition, ["bounds", "srs_id"], "bounded-region definition");
    if (definition.srs_id !== 4326) fail("bounded-region SRS is invalid");
    normalizedBounds(definition.bounds, "bounded-region bounds");
    return scope;
  }
  if (scope.scope_class === "administrative") {
    exactKeys(definition, ["administrative_kind", "name", "bounds", "boundary", "srs_id"], "administrative definition");
    if (!["municipality", "township-or-equivalent"].includes(definition.administrative_kind) || definition.srs_id !== 4326) fail("administrative scope semantics are invalid");
    if (typeof definition.name !== "string" || definition.name.trim() === "") fail("administrative name is invalid");
    normalizedBounds(definition.bounds, "administrative bounds");
    exactKeys(definition.boundary, ["dataset_key", "release_key", "content_sha256", "feature_id", "geometry_sha256"], "administrative boundary");
    if (!SHA_RE.test(definition.boundary.content_sha256) || !SHA_RE.test(definition.boundary.geometry_sha256)) fail("administrative boundary SHA-256 is invalid");
    return scope;
  }
  if (scope.scope_class === "composite") {
    exactKeys(definition, ["members", "operation", "srs_id"], "composite definition");
    if (definition.operation !== "union" || definition.srs_id !== 4326 || !Array.isArray(definition.members) || definition.members.length < 2) fail("composite scope semantics are invalid");
    let previous = null;
    for (const member of definition.members) {
      exactKeys(member, ["partition_key", "scope"], "composite member");
      if (!PARTITION_KEY_RE.test(member.partition_key)) fail("composite member partition key is invalid");
      if (previous !== null && codePointCompare(previous, member.partition_key) >= 0) fail("composite members are not unique and sorted");
      previous = member.partition_key;
      normalizeScope(member.scope);
    }
    return scope;
  }
  fail(`scope_class ${scope.scope_class} is unsupported by v1`);
}

async function partitionIdentitySha(jurisdiction, scope, runtime) {
  const identity = {
    format: "kane-fabric-partition-definition",
    version: 1,
    jurisdiction,
    scope,
  };
  return sha256Hex(canonicalBytes(identity), runtime);
}

async function verifyScopeMemberKeys(jurisdiction, scope, runtime) {
  if (scope.scope_class !== "composite") return;
  for (const member of scope.definition.members) {
    const sha = await partitionIdentitySha(jurisdiction, member.scope, runtime);
    if (member.partition_key !== `kfp1-${sha.slice(0, 32)}`) fail("composite member key does not match embedded scope identity");
    await verifyScopeMemberKeys(jurisdiction, member.scope, runtime);
  }
}

async function verifyPartitionIdentity(descriptor, runtime) {
  exactKeys(descriptor, ["format", "version", "jurisdiction", "scope", "definition_sha256", "partition_key", "label"], "partition descriptor");
  if (descriptor.format !== "kane-fabric-partition" || descriptor.version !== 1) fail("partition format/version is unsupported");
  validateJurisdiction(descriptor.jurisdiction);
  normalizeScope(descriptor.scope);
  await verifyScopeMemberKeys(descriptor.jurisdiction, descriptor.scope, runtime);
  const sha = await partitionIdentitySha(descriptor.jurisdiction, descriptor.scope, runtime);
  if (descriptor.definition_sha256 !== sha || descriptor.partition_key !== `kfp1-${sha.slice(0, 32)}`) fail("partition deterministic identity is invalid");
  if (descriptor.label !== null && (typeof descriptor.label !== "string" || descriptor.label.trim() === "")) fail("partition label is invalid");
}

function boundsIntersect(first, second) {
  const a = first.map(Number);
  const b = second.map(Number);
  return !(a[2] < b[0] || a[0] > b[2] || a[3] < b[1] || a[1] > b[3]);
}

function scopeIncludesBounds(scope, candidateBounds) {
  normalizeScope(scope);
  if (scope.scope_class === "whole-jurisdiction") return true;
  if (scope.scope_class === "bounded-region" || scope.scope_class === "administrative") return boundsIntersect(scope.definition.bounds, candidateBounds);
  return scope.definition.members.some((member) => scopeIncludesBounds(member.scope, candidateBounds));
}

function renderBoundsForScope(scope) {
  if (scope.scope_class === "whole-jurisdiction") return null;
  if (scope.scope_class === "bounded-region" || scope.scope_class === "administrative") return scope.definition.bounds.map(Number);
  fail("composite union rendering must be performed through its member partitions, not a gap-filling envelope");
}

async function loadVerifiedJson(base, path, expectedSha256, options, label) {
  const bytes = await fetchBytes(new URL(path, base), { ...options, expectedSha256 });
  return decodeJson(bytes, label);
}

function validateOwner(owner) {
  exactKeys(owner, ["application_key", "name"], "subscription owner");
  if (!SLUG_RE.test(owner.application_key) || typeof owner.name !== "string" || owner.name.trim() === "") fail("subscription owner is invalid");
}

function validateRights(rights) {
  exactKeys(rights, ["license", "owner"], "subscription rights");
  if (typeof rights.license !== "string" || rights.license.trim() === "" || typeof rights.owner !== "string" || rights.owner.trim() === "") fail("subscription rights are invalid");
}

async function validateSubscriptionManifest(manifest, composition, descriptor, runtime) {
  exactKeys(manifest, ["format", "version", "subscription_key", "owner", "jurisdiction", "substrate_content_sha256", "coverage_partition_keys", "rights", "component", "dependencies", "generation_sha256", "generation_key"], "subscription manifest");
  if (manifest.format !== "kane-fabric-subscription-manifest" || manifest.version !== 1 || !SLUG_RE.test(manifest.subscription_key)) fail("subscription manifest format/version/key is invalid");
  validateOwner(manifest.owner);
  validateJurisdiction(manifest.jurisdiction);
  validateRights(manifest.rights);
  if (stableJson(manifest.jurisdiction) !== stableJson(composition.jurisdiction)) fail("subscription jurisdiction differs from composition jurisdiction");
  if (manifest.substrate_content_sha256 !== composition.substrate_content_sha256) fail("subscription substrate identity differs from composition substrate identity");
  if (!Array.isArray(manifest.coverage_partition_keys) || manifest.coverage_partition_keys.length === 0) fail("subscription coverage is invalid");
  const sortedCoverage = [...new Set(manifest.coverage_partition_keys)].sort(codePointCompare);
  if (stableJson(sortedCoverage) !== stableJson(manifest.coverage_partition_keys) || sortedCoverage.some((key) => !PARTITION_KEY_RE.test(key))) fail("subscription coverage identities are invalid or not normalized");
  const known = new Set(composition.partitions.map((entry) => entry.partition_key));
  if (sortedCoverage.some((key) => !known.has(key))) fail("subscription coverage references an unknown composition partition");
  if (!manifest.coverage_partition_keys.includes(descriptor.partition_key)) return false;
  exactKeys(manifest.component, ["path", "byte_length", "sha256", "object_count"], "subscription component");
  if (manifest.component.path !== "objects.json" || !Number.isInteger(manifest.component.byte_length) || manifest.component.byte_length < 0 || !SHA_RE.test(manifest.component.sha256) || !Number.isInteger(manifest.component.object_count) || manifest.component.object_count < 0) fail("subscription component descriptor is invalid");
  if (!Array.isArray(manifest.dependencies) || manifest.dependencies.length !== 0) fail("v1 subscription dependencies must be empty");
  const body = { ...manifest };
  delete body.generation_sha256;
  delete body.generation_key;
  const sha = await sha256Hex(canonicalBytes(body), runtime);
  if (manifest.generation_sha256 !== sha || manifest.generation_key !== `kfsg1-${sha.slice(0, 32)}` || !GENERATION_KEY_RE.test(manifest.generation_key)) fail("subscription generation identity is invalid");
  return true;
}

async function validateObjectsDocument(document, manifest, runtime) {
  exactKeys(document, ["format", "version", "subscription_key", "objects"], "subscription objects document");
  if (document.format !== "kane-fabric-subscription-objects" || document.version !== 1 || document.subscription_key !== manifest.subscription_key || !Array.isArray(document.objects)) fail("subscription objects document is invalid");
  const bytes = canonicalBytes(document);
  if (bytes.length !== manifest.component.byte_length || (await sha256Hex(bytes, runtime)) !== manifest.component.sha256 || document.objects.length !== manifest.component.object_count) fail("subscription object component identity is invalid");
  const seen = new Set();
  for (const object of document.objects) {
    exactKeys(object, ["object_key", "bounds", "geographic_refs", "payload", "object_sha256"], "subscription object");
    if (typeof object.object_key !== "string" || object.object_key.trim() === "" || seen.has(object.object_key)) fail("subscription object_key is invalid or duplicate");
    seen.add(object.object_key);
    normalizedBounds(object.bounds, "subscription object bounds");
    if (!Array.isArray(object.geographic_refs)) fail("subscription geographic_refs are invalid");
    for (const ref of object.geographic_refs) {
      exactKeys(ref, ["kind", "dataset_key", "release_key", "source_content_sha256", "object_key"], "Fabric geographic reference");
      if (!SLUG_RE.test(ref.kind) || !SLUG_RE.test(ref.dataset_key) || typeof ref.release_key !== "string" || ref.release_key.trim() === "" || !SHA_RE.test(ref.source_content_sha256) || typeof ref.object_key !== "string" || ref.object_key.trim() === "") fail("Fabric geographic reference is invalid");
    }
    const body = { object_key: object.object_key, bounds: object.bounds, geographic_refs: object.geographic_refs, payload: object.payload };
    if (!SHA_RE.test(object.object_sha256) || (await sha256Hex(canonicalBytes(body), runtime)) !== object.object_sha256) fail("subscription object identity is invalid");
  }
}

export async function loadPartitionComposition(compositionBaseUrl, partitionName, { fetchImpl = fetch, runtime = globalThis } = {}) {
  assertCapability(runtime);
  const base = directoryUrl(compositionBaseUrl);
  const composition = decodeJson(await fetchBytes(new URL("composition-manifest.json", base), { fetchImpl, runtime }), "MS4 composition manifest");
  exactKeys(composition, ["format", "version", "jurisdiction", "substrate_content_sha256", "source_database_sha256", "proof_building", "partitions", "subscriptions", "edge_placement_logical_sha256", "composition_sha256"], "MS4 composition manifest");
  if (composition.format !== FORMAT || composition.version !== VERSION) fail("MS4 composition manifest format/version is unsupported");
  validateJurisdiction(composition.jurisdiction);
  if (!SHA_RE.test(composition.substrate_content_sha256) || !SHA_RE.test(composition.source_database_sha256) || !SHA_RE.test(composition.edge_placement_logical_sha256)) fail("MS4 composition identity field is invalid");
  if (!Array.isArray(composition.partitions) || composition.partitions.length < 1 || !Array.isArray(composition.subscriptions) || composition.subscriptions.length < 2) fail("MS4 composition inventory is invalid");
  await verifyBodyHash(composition, "composition_sha256", runtime, "MS4 composition manifest");
  const entry = composition.partitions.find((item) => item?.name === partitionName);
  if (!entry) fail(`unknown MS4 partition name: ${partitionName}`);
  exactKeys(entry, ["name", "partition_key", "descriptor_path", "descriptor_sha256", "selection_path", "selection_sha256"], "composition partition entry");
  const descriptor = await loadVerifiedJson(base, entry.descriptor_path, entry.descriptor_sha256, { fetchImpl, runtime }, "partition descriptor");
  await verifyPartitionIdentity(descriptor, runtime);
  if (descriptor.partition_key !== entry.partition_key || stableJson(descriptor.jurisdiction) !== stableJson(composition.jurisdiction)) fail("partition entry identity disagrees with composition");
  const selection = await loadVerifiedJson(base, entry.selection_path, entry.selection_sha256, { fetchImpl, runtime }, "selection manifest");
  exactKeys(selection, ["format", "version", "jurisdiction", "partition_key", "partition_definition_sha256", "partition_scope", "substrate_content_sha256", "components", "selection_sha256"], "selection manifest");
  if (selection.format !== "kane-fabric-substrate-partition-selection" || selection.version !== 1 || selection.partition_key !== descriptor.partition_key || selection.partition_definition_sha256 !== descriptor.definition_sha256 || stableJson(selection.partition_scope) !== stableJson(descriptor.scope) || selection.substrate_content_sha256 !== composition.substrate_content_sha256) fail("selection manifest disagrees with composition partition/substrate identity");
  await verifyBodyHash(selection, "selection_sha256", runtime, "selection manifest");

  const subscriptions = [];
  for (const subEntry of composition.subscriptions) {
    exactKeys(subEntry, ["subscription_key", "generation_key", "manifest_path", "manifest_sha256", "objects_path", "objects_sha256"], "composition subscription entry");
    if (!GENERATION_KEY_RE.test(subEntry.generation_key)) fail("composition subscription generation key is invalid");
    const manifest = await loadVerifiedJson(base, subEntry.manifest_path, subEntry.manifest_sha256, { fetchImpl, runtime }, "subscription manifest");
    if (manifest.subscription_key !== subEntry.subscription_key || manifest.generation_key !== subEntry.generation_key) fail("subscription entry disagrees with manifest identity");
    const covered = await validateSubscriptionManifest(manifest, composition, descriptor, runtime);
    if (!covered) fail(`subscription ${manifest.subscription_key} does not declare selected partition coverage`);
    if (subEntry.objects_sha256 !== manifest.component.sha256) fail("subscription objects identity disagrees with manifest");
    const objectsDoc = await loadVerifiedJson(base, subEntry.objects_path, subEntry.objects_sha256, { fetchImpl, runtime }, "subscription objects");
    await validateObjectsDocument(objectsDoc, manifest, runtime);
    const objects = objectsDoc.objects.filter((object) => scopeIncludesBounds(descriptor.scope, object.bounds));
    subscriptions.push({ manifest, objects });
  }
  return { composition, descriptor, selection, subscriptions };
}

export async function composePartitions(compositionBaseUrl, partitionNames, options = {}) {
  const partitions = [];
  const unique = new Map();
  let objectAppearances = 0;
  for (const name of partitionNames) {
    const loaded = await loadPartitionComposition(compositionBaseUrl, name, options);
    partitions.push(loaded);
    for (const subscription of loaded.subscriptions) {
      for (const object of subscription.objects) {
        objectAppearances += 1;
        const identity = `${subscription.manifest.subscription_key}:${object.object_sha256}`;
        const encoded = stableJson(object);
        const existing = unique.get(identity);
        if (existing && existing.encoded !== encoded) fail("cross-partition object identity has conflicting bytes");
        unique.set(identity, { subscription_key: subscription.manifest.subscription_key, object, encoded });
      }
    }
  }
  return {
    partitions,
    object_appearances: objectAppearances,
    unique_objects: Array.from(unique.values(), ({ subscription_key, object }) => ({ subscription_key, object })),
  };
}

export async function renderPartitionComposition(canvas, substrateBaseUrl, compositionBaseUrl, partitionName, { fetchImpl = fetch, runtime = globalThis, renderImpl } = {}) {
  if (typeof renderImpl !== "function") fail("renderImpl must be the Kane Fabric substrate renderer");
  const loaded = await loadPartitionComposition(compositionBaseUrl, partitionName, { fetchImpl, runtime });
  const bounds = renderBoundsForScope(loaded.descriptor.scope);
  const renderer = await renderImpl(canvas, substrateBaseUrl, { bounds, fetchImpl, runtime });
  if (renderer.substrate_content_sha256 !== loaded.composition.substrate_content_sha256) fail("renderer substrate identity disagrees with MS4 composition identity");
  return { ...loaded, renderer };
}

export const _test = { canonicalBytes, sha256Hex, normalizeScope, scopeIncludesBounds, verifyPartitionIdentity };
