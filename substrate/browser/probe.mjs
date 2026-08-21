#!/usr/bin/env node

import {
  chunksForLevel,
  loadSubstrateMetadata,
  openFlatComponent,
  readChunk,
} from "./kane-fabric-substrate.js";

function fail(message) {
  throw new Error(message);
}

const baseUrl = process.argv[2];
const expectedContent = process.argv[3] || null;
if (!baseUrl) {
  console.error("usage: node probe.mjs BASE_URL [EXPECTED_SUBSTRATE_CONTENT_SHA256]");
  process.exit(2);
}

if (typeof fetch !== "function") fail("global fetch is unavailable");
if (typeof DecompressionStream !== "function") fail("DecompressionStream is unavailable");

const metadata = await loadSubstrateMetadata(baseUrl);
if (
  expectedContent !== null &&
  metadata.manifest.substrate_content_sha256 !== expectedContent
) {
  fail(
    `substrate content identity is ${metadata.manifest.substrate_content_sha256}; expected ${expectedContent}`,
  );
}

const roads = await openFlatComponent(baseUrl, metadata.manifest, "roads");
const water = await openFlatComponent(baseUrl, metadata.manifest, "water");

const roadChunks = chunksForLevel(roads, "orientation");
const waterChunks = chunksForLevel(water, "overview");
if (roadChunks.length === 0 || waterChunks.length === 0) fail("expected selectable chunks");

const roadChunk = roadChunks[0];
const waterChunk = waterChunks[0];
const roadFeatures = await readChunk(roads, roadChunk);
const waterFeatures = await readChunk(water, waterChunk);

const roadRequested = roads.payloadStart + roadChunk.length;
const waterRequested = water.payloadStart + waterChunk.length;
if (roadRequested >= roads.descriptor.byte_length) {
  fail("road probe did not remain selective");
}
if (waterRequested >= water.descriptor.byte_length) {
  fail("water probe did not remain selective");
}

const result = {
  browser_contract: {
    decompression_stream: "deflate",
    range_status_required: 206,
    sha256: "WebCrypto",
  },
  jurisdiction: metadata.manifest.jurisdiction,
  overview: {
    byte_length: metadata.manifest.components[0].byte_length,
    ring_count: metadata.overview.outline.ring_count,
  },
  roads: {
    component_byte_length: roads.descriptor.byte_length,
    index_byte_length: roads.payloadStart - 16,
    first_orientation_chunk_byte_length: roadChunk.length,
    first_orientation_chunk_feature_count: roadFeatures.length,
    selective_bytes_requested: roadRequested,
  },
  substrate_content_sha256: metadata.manifest.substrate_content_sha256,
  water: {
    component_byte_length: water.descriptor.byte_length,
    index_byte_length: water.payloadStart - 16,
    first_overview_chunk_byte_length: waterChunk.length,
    first_overview_chunk_feature_count: waterFeatures.length,
    selective_bytes_requested: waterRequested,
  },
};

console.log(JSON.stringify(result));
