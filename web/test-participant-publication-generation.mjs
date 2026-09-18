import test from "node:test";
import assert from "node:assert/strict";
import { webcrypto } from "node:crypto";
import { readFile } from "node:fs/promises";

import {
  ParticipantPublicationGenerationError,
  canonicalParticipantPublicationJson,
  participantPublicationGenerationIdentity,
} from "../administration/contracts/participant-publication-generation-v1.mjs";

async function fixture() {
  return JSON.parse(
    await readFile(
      new URL("../administration/fixtures/participant-publication-v1.synthetic.json", import.meta.url),
      "utf8",
    ),
  );
}

function reverseObjectInsertionOrder(value) {
  if (Array.isArray(value)) return value.map(reverseObjectInsertionOrder);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .reverse()
        .map(([key, child]) => [key, reverseObjectInsertionOrder(child)]),
    );
  }
  return value;
}

test("synthetic participant publication has a stable derived generation identity", async () => {
  const value = await fixture();
  const identity = await participantPublicationGenerationIdentity(value, webcrypto);
  assert.deepEqual(identity, {
    generation_sha256: "cb85e4e22999088ffbd0589d74995b1a37571b613ed1b013588db1e1254244a1",
    generation_key: "kfpg1-cb85e4e22999088ffbd0589d74995b1a",
  });
  assert.equal("generation_sha256" in value, false);
  assert.equal("generation_key" in value, false);
});

test("generation identity is independent of JSON object key insertion order", async () => {
  const value = await fixture();
  const reordered = reverseObjectInsertionOrder(value);
  assert.equal(
    canonicalParticipantPublicationJson(value),
    canonicalParticipantPublicationJson(reordered),
  );
  assert.deepEqual(
    await participantPublicationGenerationIdentity(value, webcrypto),
    await participantPublicationGenerationIdentity(reordered, webcrypto),
  );
});

test("changing participant publication content changes generation identity", async () => {
  const value = await fixture();
  const changed = JSON.parse(JSON.stringify(value));
  changed.descriptor_instances[0].data.association.property.condominium_name =
    "Synthetic Participant Condominium Revised";
  assert.notDeepEqual(
    await participantPublicationGenerationIdentity(value, webcrypto),
    await participantPublicationGenerationIdentity(changed, webcrypto),
  );
});

test("generation canonicalization fails closed on non-finite JSON numbers", async () => {
  const value = await fixture();
  value.descriptor_instances[0].data.non_finite = Number.POSITIVE_INFINITY;
  await assert.rejects(
    () => participantPublicationGenerationIdentity(value, webcrypto),
    (error) =>
      error instanceof ParticipantPublicationGenerationError &&
      error.path.endsWith(".data.non_finite"),
  );
});

test("generation identity remains derived metadata rather than a participant-publication field", async () => {
  const value = await fixture();
  const before = JSON.stringify(value);
  const identity = await participantPublicationGenerationIdentity(value, webcrypto);
  assert.match(identity.generation_key, /^kfpg1-[0-9a-f]{32}$/);
  assert.match(identity.generation_sha256, /^[0-9a-f]{64}$/);
  assert.equal(JSON.stringify(value), before);
});
