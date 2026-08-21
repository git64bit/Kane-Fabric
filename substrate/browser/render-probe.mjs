#!/usr/bin/env node

import { webcrypto } from "node:crypto";

import { renderSubstrate } from "./kane-fabric-renderer.js";

class RecordingContext2D {
  constructor() {
    this.counts = new Map();
  }

  _hit(name) {
    this.counts.set(name, (this.counts.get(name) || 0) + 1);
  }

  beginPath() { this._hit("beginPath"); }
  clearRect() { this._hit("clearRect"); }
  closePath() { this._hit("closePath"); }
  fill() { this._hit("fill"); }
  fillRect() { this._hit("fillRect"); }
  lineTo() { this._hit("lineTo"); }
  moveTo() { this._hit("moveTo"); }
  restore() { this._hit("restore"); }
  save() { this._hit("save"); }
  stroke() { this._hit("stroke"); }
}

class RecordingCanvas {
  constructor(width, height) {
    this.width = width;
    this.height = height;
    this.context = new RecordingContext2D();
  }

  getContext(kind) {
    return kind === "2d" ? this.context : null;
  }
}

const baseUrl = process.argv[2];
const expectedContent = process.argv[3] || null;
if (!baseUrl) {
  console.error("usage: node render-probe.mjs BASE_URL [EXPECTED_SUBSTRATE_CONTENT_SHA256]");
  process.exit(2);
}

const runtime = { crypto: webcrypto };
const canvas = new RecordingCanvas(1024, 768);
const stats = await renderSubstrate(canvas, baseUrl, {
  roadLevel: "orientation",
  runtime,
  waterLevel: "overview",
});

if (expectedContent !== null && stats.substrate_content_sha256 !== expectedContent) {
  throw new Error(
    `substrate content identity is ${stats.substrate_content_sha256}; expected ${expectedContent}`,
  );
}
if (stats.subscription_data_used !== false) {
  throw new Error("renderer reported subscription data usage");
}
if (stats.boundary_ring_count < 1 || stats.roads.feature_count < 1 || stats.water.feature_count < 1) {
  throw new Error("renderer did not consume boundary/road/water geometry");
}
if ((canvas.context.counts.get("stroke") || 0) < 3) {
  throw new Error("renderer did not issue expected canvas stroke operations");
}
if ((canvas.context.counts.get("lineTo") || 0) < 1) {
  throw new Error("renderer did not trace geometry");
}

console.log(JSON.stringify({
  canvas: {
    height: canvas.height,
    operations: Object.fromEntries([...canvas.context.counts.entries()].sort()),
    width: canvas.width,
  },
  renderer: stats,
  status: "render-command-contract-passed",
}));
