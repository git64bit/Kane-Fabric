import test from "node:test";
import assert from "node:assert/strict";
import { webcrypto } from "node:crypto";

import {
  ParticipantEdgePlacementError,
  buildParticipantEdgePlacement,
  validateParticipantEdgePlacement,
} from "../administration/contracts/participant-edge-placement-v1.mjs";

const GENERATION = {
  generation_sha256: "cb85e4e22999088ffbd0589d74995b1a37571b613ed1b013588db1e1254244a1",
  generation_key: "kfpg1-cb85e4e22999088ffbd0589d74995b1a",
};

test("participant edge placement deterministically binds one publication generation", async () => {
  const placement = await buildParticipantEdgePlacement(GENERATION, webcrypto);
  assert.deepEqual(placement, {
    format: "kane-fabric-participant-edge-placement",
    format_version: 1,
    publication_generation: GENERATION,
    logical_placement_sha256: "5194311669fa69c783e645bf72487c8249666a3f4c8dd6dd3ade72a54d51d3be",
  });
  assert.equal(await validateParticipantEdgePlacement(placement, webcrypto), placement);
});

test("participant logical placement identity is distinct from publication generation identity", async () => {
  const placement = await buildParticipantEdgePlacement(GENERATION, webcrypto);
  assert.notEqual(
    placement.logical_placement_sha256,
    placement.publication_generation.generation_sha256,
  );
});

test("participant edge placement contains no physical source or transport identity", async () => {
  const placement = await buildParticipantEdgePlacement(GENERATION, webcrypto);
  assert.deepEqual(
    Object.keys(placement).sort(),
    ["format", "format_version", "logical_placement_sha256", "publication_generation"].sort(),
  );
  for (const forbidden of ["device", "source", "hostname", "ip", "mac", "wireguard", "account"]) {
    assert.equal(forbidden in placement, false);
  }
});

test("generation key must agree with the full publication generation SHA-256", async () => {
  const bad = {
    ...GENERATION,
    generation_key: "kfpg1-" + "0".repeat(32),
  };
  await assert.rejects(
    () => buildParticipantEdgePlacement(bad, webcrypto),
    (error) =>
      error instanceof ParticipantEdgePlacementError &&
      error.path === "$.publication_generation.generation_key",
  );
});

test("mutated logical placement identity fails closed", async () => {
  const placement = await buildParticipantEdgePlacement(GENERATION, webcrypto);
  placement.logical_placement_sha256 = "0".repeat(64);
  await assert.rejects(
    () => validateParticipantEdgePlacement(placement, webcrypto),
    (error) =>
      error instanceof ParticipantEdgePlacementError &&
      error.path === "$.logical_placement_sha256",
  );
});
