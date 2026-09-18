import test from "node:test";
import assert from "node:assert/strict";

import { AppConfigError, configFromSearch, sourceSummary } from "./app-config.js";

const BASE = "https://fabric.example/web/index.html";

test("unconfigured application reports required source fields", () => {
  const config = configFromSearch("", BASE);
  assert.equal(config.configured, false);
  assert.deepEqual(config.missing, ["substrate", "composition", "partition"]);
  assert.equal(config.participantSource, null);
});

test("relative artifact sources resolve against the application origin", () => {
  const config = configFromSearch("?substrate=../data/substrate&composition=../data/ms4&partition=west", BASE);
  assert.equal(config.configured, true);
  assert.equal(config.substrateBase, "https://fabric.example/data/substrate/");
  assert.equal(config.compositionBase, "https://fabric.example/data/ms4/");
  assert.equal(config.partition, "west");
});

test("legacy ms4 query name is accepted as development configuration", () => {
  const config = configFromSearch("?substrate=/s/&ms4=/m/&partition=east", BASE);
  assert.equal(config.compositionBase, "https://fabric.example/m/");
  assert.equal(config.partition, "east");
});

test("absolute source URLs remain platform neutral", () => {
  const config = configFromSearch(
    "?substrate=https%3A%2F%2Fedge.example%2Fs&composition=https%3A%2F%2Fedge.example%2Fm&partition=kfp1-demo&label=Kitchen%20edge",
    BASE,
  );
  assert.equal(config.substrateBase, "https://edge.example/s/");
  assert.equal(config.compositionBase, "https://edge.example/m/");
  assert.equal(config.sourceLabel, "Kitchen edge");
});

test("participant publication is optional and resolves as a document URL", () => {
  const config = configFromSearch(
    "?substrate=/s/&composition=/m/&partition=west&participant=../participant.json",
    BASE,
  );
  assert.equal(config.configured, true);
  assert.equal(config.participantSource, "https://fabric.example/participant.json");
  assert.match(sourceSummary(config).detail, /participant publication configured/);
});

test("participant publication is not required for county composition", () => {
  const config = configFromSearch("?substrate=/s/&composition=/m/&partition=west", BASE);
  assert.equal(config.configured, true);
  assert.equal(config.participantSource, null);
});

test("participant source rejects non-http protocols and embedded credentials", () => {
  assert.throws(
    () => configFromSearch("?substrate=/s/&composition=/m/&partition=west&participant=file:///tmp/p.json", BASE),
    AppConfigError,
  );
  assert.throws(
    () => configFromSearch("?substrate=/s/&composition=/m/&partition=west&participant=https://u:p@example.test/p.json", BASE),
    AppConfigError,
  );
});

test("non-http artifact protocols are rejected", () => {
  assert.throws(
    () => configFromSearch("?substrate=file:///tmp/s&composition=/m/&partition=west", BASE),
    AppConfigError,
  );
});

test("embedded URL credentials are rejected", () => {
  assert.throws(
    () => configFromSearch("?substrate=https://user:pass@example.test/s&composition=/m/&partition=west", BASE),
    AppConfigError,
  );
});

test("partition reference is bounded and normalized", () => {
  assert.throws(
    () => configFromSearch("?substrate=/s/&composition=/m/&partition=bad%20partition", BASE),
    AppConfigError,
  );
});

test("source summary does not infer physical platform", () => {
  const config = configFromSearch("?substrate=/s/&composition=/m/&partition=west", BASE);
  const summary = sourceSummary(config);
  assert.equal(summary.label, "Configured Fabric artifact source");
  assert.equal(summary.detail, "partition west");
  assert.doesNotMatch(JSON.stringify(summary), /esp32|idf|hardware/i);
});
