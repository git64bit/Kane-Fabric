#!/usr/bin/env node
import test from "node:test";
import assert from "node:assert/strict";
import { webcrypto } from "node:crypto";

import {
  composePartitions,
  loadPartitionComposition,
  _test,
} from "./kane-fabric-ms4.js";

const runtime = { crypto: webcrypto };
const BASE = "https://example.test/ms4/";
const JURISDICTION = {
  country_code: "US",
  state_code: "IL",
  fips_code: "17089",
  county_key: "kane-county-il",
  name: "Kane County",
};

async function shaBytes(bytes) {
  return _test.sha256Hex(bytes, runtime);
}
async function shaDoc(value) {
  return shaBytes(_test.canonicalBytes(value));
}
async function partition(bounds, label) {
  const scope = {
    scope_class: "bounded-region",
    definition: { bounds, srs_id: 4326 },
  };
  const identity = {
    format: "kane-fabric-partition-definition",
    version: 1,
    jurisdiction: JURISDICTION,
    scope,
  };
  const definition_sha256 = await shaDoc(identity);
  return {
    format: "kane-fabric-partition",
    version: 1,
    jurisdiction: JURISDICTION,
    scope,
    definition_sha256,
    partition_key: `kfp1-${definition_sha256.slice(0, 32)}`,
    label,
  };
}

async function subscription(key, partitions, objectKey) {
  const objectBody = {
    object_key: objectKey,
    bounds: ["-88.3020000", "41.8000000", "-88.2980000", "41.8040000"],
    geographic_refs: [{
      kind: "building",
      dataset_key: "buildings",
      release_key: "release-a",
      source_content_sha256: "a".repeat(64),
      object_key: "kcb-proof",
    }],
    payload: { proof: key },
  };
  const object = { ...objectBody, object_sha256: await shaDoc(objectBody) };
  const objectsDoc = {
    format: "kane-fabric-subscription-objects",
    version: 1,
    subscription_key: key,
    objects: [object],
  };
  const objectsBytes = _test.canonicalBytes(objectsDoc);
  const component = {
    path: "objects.json",
    byte_length: objectsBytes.length,
    sha256: await shaBytes(objectsBytes),
    object_count: 1,
  };
  const body = {
    format: "kane-fabric-subscription-manifest",
    version: 1,
    subscription_key: key,
    owner: { application_key: `${key}-proof`, name: `${key} proof` },
    jurisdiction: JURISDICTION,
    substrate_content_sha256: "f".repeat(64),
    coverage_partition_keys: partitions.map((item) => item.partition_key).sort(),
    rights: { license: "proof-only", owner: `${key} proof` },
    component,
    dependencies: [],
  };
  const generation_sha256 = await shaDoc(body);
  const manifest = {
    ...body,
    generation_sha256,
    generation_key: `kfsg1-${generation_sha256.slice(0, 32)}`,
  };
  return { manifest, objectsDoc };
}

async function fixture({ industryCoverage = "both" } = {}) {
  const west = await partition(["-88.6000000", "41.6000000", "-88.2950000", "42.2000000"], "west");
  const east = await partition(["-88.3050000", "41.6000000", "-88.0000000", "42.2000000"], "east");
  const partitions = { west, east };
  const selections = {};
  for (const [name, descriptor] of Object.entries(partitions)) {
    const body = {
      format: "kane-fabric-substrate-partition-selection",
      version: 1,
      jurisdiction: JURISDICTION,
      partition_key: descriptor.partition_key,
      partition_definition_sha256: descriptor.definition_sha256,
      partition_scope: descriptor.scope,
      substrate_content_sha256: "f".repeat(64),
      components: [],
    };
    selections[name] = { ...body, selection_sha256: await shaDoc(body) };
  }
  const condo = await subscription("condo", [west, east], "condo-object");
  const industryPartitions = industryCoverage === "both" ? [west, east] : [west];
  const industry = await subscription("industry", industryPartitions, "industry-object");
  const docs = new Map();

  async function add(path, value) {
    const bytes = _test.canonicalBytes(value);
    docs.set(new URL(path, BASE).href, bytes);
    return await shaBytes(bytes);
  }

  const partitionEntries = [];
  for (const name of ["west", "east"]) {
    const descriptorSha = await add(`partitions/${name}.json`, partitions[name]);
    const selectionSha = await add(`selections/${name}.json`, selections[name]);
    partitionEntries.push({
      name,
      partition_key: partitions[name].partition_key,
      descriptor_path: `partitions/${name}.json`,
      descriptor_sha256: descriptorSha,
      selection_path: `selections/${name}.json`,
      selection_sha256: selectionSha,
    });
  }
  const subscriptionEntries = [];
  for (const [key, value] of [["condo", condo], ["industry", industry]]) {
    const manifestSha = await add(`subscriptions/${key}/subscription-manifest.json`, value.manifest);
    const objectsSha = await add(`subscriptions/${key}/objects.json`, value.objectsDoc);
    subscriptionEntries.push({
      subscription_key: key,
      generation_key: value.manifest.generation_key,
      manifest_path: `subscriptions/${key}/subscription-manifest.json`,
      manifest_sha256: manifestSha,
      objects_path: `subscriptions/${key}/objects.json`,
      objects_sha256: objectsSha,
    });
  }
  const body = {
    format: "kane-fabric-ms4-composition-manifest",
    version: 1,
    jurisdiction: JURISDICTION,
    substrate_content_sha256: "f".repeat(64),
    source_database_sha256: "d".repeat(64),
    proof_building: { building_key: "kcb-proof" },
    partitions: partitionEntries,
    subscriptions: subscriptionEntries,
    edge_placement_logical_sha256: "e".repeat(64),
  };
  const composition = { ...body, composition_sha256: await shaDoc(body) };
  await add("composition-manifest.json", composition);

  const fetchImpl = async (url) => {
    const key = String(url);
    const bytes = docs.get(key);
    if (!bytes) return new Response("not found", { status: 404 });
    return new Response(bytes, { status: 200 });
  };
  return { fetchImpl, partitions };
}

test("loads two verified subscriptions for an explicitly covered partition", async () => {
  const { fetchImpl } = await fixture();
  const loaded = await loadPartitionComposition(BASE, "west", { fetchImpl, runtime });
  assert.equal(loaded.subscriptions.length, 2);
  assert.deepEqual(loaded.subscriptions.map((item) => item.manifest.subscription_key), ["condo", "industry"]);
  assert.equal(loaded.subscriptions[0].objects.length, 1);
});

test("cross-partition composition deduplicates replicated logical objects", async () => {
  const { fetchImpl } = await fixture();
  const composed = await composePartitions(BASE, ["west", "east"], { fetchImpl, runtime });
  assert.equal(composed.object_appearances, 4);
  assert.equal(composed.unique_objects.length, 2);
});

test("composition rejects a subscription not declaring selected partition coverage", async () => {
  const { fetchImpl } = await fixture({ industryCoverage: "west" });
  await assert.rejects(
    loadPartitionComposition(BASE, "east", { fetchImpl, runtime }),
    /does not declare selected partition coverage/,
  );
});

test("composite union inclusion excludes a disjoint-member gap", () => {
  const scope = {
    scope_class: "composite",
    definition: {
      operation: "union",
      srs_id: 4326,
      members: [
        { partition_key: `kfp1-${"1".repeat(32)}`, scope: { scope_class: "bounded-region", definition: { bounds: ["-88.6000000", "41.6000000", "-88.5000000", "41.7000000"], srs_id: 4326 } } },
        { partition_key: `kfp1-${"2".repeat(32)}`, scope: { scope_class: "bounded-region", definition: { bounds: ["-88.2000000", "41.6000000", "-88.1000000", "41.7000000"], srs_id: 4326 } } },
      ],
    },
  };
  assert.equal(_test.scopeIncludesBounds(scope, ["-88.5800000", "41.6200000", "-88.5600000", "41.6400000"]), true);
  assert.equal(_test.scopeIncludesBounds(scope, ["-88.4000000", "41.6200000", "-88.3500000", "41.6400000"]), false);
});

test("missing WebCrypto fails before the first publication fetch", async () => {
  let fetchCount = 0;
  const fetchImpl = async () => { fetchCount += 1; return new Response("{}"); };
  await assert.rejects(
    loadPartitionComposition(BASE, "west", { fetchImpl, runtime: { isSecureContext: false } }),
    /requires Web Crypto SHA-256.*not secure/s,
  );
  assert.equal(fetchCount, 0);
});
