#!/usr/bin/env node
import { webcrypto } from "node:crypto";
import { composePartitions, renderPartitionComposition } from "./kane-fabric-ms4.js";
import { renderSubstrate } from "../../substrate/browser/kane-fabric-renderer.js";

class RecordingContext2D {
  constructor() { this.counts = new Map(); }
  hit(name) { this.counts.set(name, (this.counts.get(name) || 0) + 1); }
  beginPath() { this.hit("beginPath"); }
  clearRect() { this.hit("clearRect"); }
  closePath() { this.hit("closePath"); }
  fill() { this.hit("fill"); }
  fillRect() { this.hit("fillRect"); }
  lineTo() { this.hit("lineTo"); }
  moveTo() { this.hit("moveTo"); }
  restore() { this.hit("restore"); }
  save() { this.hit("save"); }
  stroke() { this.hit("stroke"); }
}
class RecordingCanvas {
  constructor(width, height) { this.width = width; this.height = height; this.context = new RecordingContext2D(); }
  getContext(kind) { return kind === "2d" ? this.context : null; }
}

const substrateBase = process.argv[2];
const compositionBase = process.argv[3];
if (!substrateBase || !compositionBase) {
  console.error("usage: node ms4/browser/probe.mjs SUBSTRATE_BASE_URL MS4_COMPOSITION_BASE_URL");
  process.exit(2);
}
const runtime = { crypto: webcrypto };
const canvas = new RecordingCanvas(1024, 768);
const west = await renderPartitionComposition(
  canvas,
  substrateBase,
  compositionBase,
  "west",
  { runtime, renderImpl: renderSubstrate },
);
const composed = await composePartitions(compositionBase, ["west", "east"], { runtime });
if (west.subscriptions.length !== 2) throw new Error("west partition did not compose two subscriptions");
if (composed.object_appearances !== 4 || composed.unique_objects.length !== 2) throw new Error("cross-partition deduplication failed");
if ((canvas.context.counts.get("stroke") || 0) < 1) throw new Error("substrate renderer did not draw geometry");
console.log(JSON.stringify({
  status: "ms4-node-composition-passed",
  substrate_content_sha256: west.renderer.substrate_content_sha256,
  partition_keys: composed.partitions.map((item) => item.descriptor.partition_key),
  subscription_generations: west.subscriptions.map((item) => ({ subscription_key: item.manifest.subscription_key, generation_key: item.manifest.generation_key })),
  object_appearances: composed.object_appearances,
  unique_objects: composed.unique_objects.length,
  canvas_operations: Object.fromEntries([...canvas.context.counts.entries()].sort()),
}));
