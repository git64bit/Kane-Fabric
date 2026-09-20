import test from "node:test";
import assert from "node:assert/strict";
import { createHash, webcrypto } from "node:crypto";
import { readFile } from "node:fs/promises";

import {
  ParticipantEdgePlacementError,
  buildParticipantEdgePlacement,
  validateParticipantEdgePlacement,
} from "../administration/contracts/participant-edge-placement-v1.mjs";
import { participantPublicationGenerationIdentity } from "../administration/contracts/participant-publication-generation-v1.mjs";

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


test("reference participant edge image binds accepted geography, generation, placement, and bytes", async () => {
  const publicationPath = new URL(
    "../ms5/esp32_reference/participant_image/participant.json",
    import.meta.url,
  );
  const inventoryPath = new URL(
    "../ms5/esp32_reference/participant_image/.kane-fabric-storage-inventory.json",
    import.meta.url,
  );
  const publicationBytes = await readFile(publicationPath);
  const publication = JSON.parse(publicationBytes.toString("utf8"));
  const inventory = JSON.parse(await readFile(inventoryPath, "utf8"));

  const generation = await participantPublicationGenerationIdentity(publication, webcrypto);
  assert.deepEqual(generation, {
    generation_sha256: "37e6f0ffa5f3eba5f5564ff56631c82a24c0f82da07730c1053d0dd937e00f7b",
    generation_key: "kfpg1-37e6f0ffa5f3eba5f5564ff56631c82a",
  });

  const placement = await buildParticipantEdgePlacement(generation, webcrypto);
  assert.equal(
    placement.logical_placement_sha256,
    "02c9230496b677f12e49af696afbc5fb06116fe10c3d9818ec85e6f2445ac7a3",
  );
  assert.equal(inventory.logical_placement_sha256, placement.logical_placement_sha256);

  assert.deepEqual(publication.descriptor_instances[0].geographic_refs, [{
    dataset_key: "buildings",
    kind: "building",
    object_key: "kcb-aee53d8f13ccc7eebbf23d2a4c42d7d1d939f9b4b057584966642827bace7fb1",
    release_key: "kane-buildings-20250730-086f09eba5ad",
    source_content_sha256: "086f09eba5ad5b21eea1b6c9a8158eaf8c509a258c53509d115eaf1d19a7f799",
  }]);

  assert.equal(inventory.artifacts.length, 1);
  assert.deepEqual(inventory.artifacts[0], {
    artifact_key: "participant-publication",
    path: "participant.json",
    byte_length: publicationBytes.length,
    sha256: createHash("sha256").update(publicationBytes).digest("hex"),
  });
});
