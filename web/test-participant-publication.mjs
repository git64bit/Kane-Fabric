import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

import {
  ParticipantPublicationError,
  validateParticipantPublication,
} from "../administration/contracts/participant-publication-v1.mjs";

function fixture() {
  return {
    format: "kane-fabric-participant-publication",
    format_version: 1,
    association_unit_identity: {
      format: "kane-fabric-association-unit-identity",
      format_version: 1,
      association_anchor: {
        jurisdiction: { country_code: "US", state_code: "IL" },
        recording_authority_reference: "synthetic-public-recording-authority",
        original_declaration_recording_reference: "Synthetic Tract Book 14, Page 27",
      },
      unit_anchors: [
        {
          recorded_unit_designation: "Synthetic Unit 1",
          recorded_unit_reference: "Synthetic Unit Book 2, Page 9",
        },
      ],
    },
    descriptor_instances: [
      {
        descriptor_id: "us.il.condominium.property",
        descriptor_version: 1,
        subject: { kind: "association" },
        geographic_refs: [
          {
            kind: "building",
            dataset_key: "synthetic-buildings",
            release_key: "synthetic-release-1",
            source_content_sha256: "1".repeat(64),
            object_key: "synthetic-building-1",
          },
        ],
        data: {
          association: {
            property: {
              condominium_name: "Synthetic Participant Condominium",
            },
          },
        },
      },
    ],
  };
}

test("minimal public participant publication validates without source, device, classification, or generation fields", () => {
  const value = fixture();
  assert.equal(validateParticipantPublication(value), value);
  assert.equal("classification" in value, false);
  assert.equal("generation_sha256" in value, false);
  assert.equal("generation_key" in value, false);
  assert.equal("source" in value, false);
  assert.equal("device" in value, false);
});

test("synthetic conformance fixture validates without claiming real Recorder evidence", async () => {
  const value = JSON.parse(
    await readFile(new URL("../administration/fixtures/participant-publication-v1.synthetic.json", import.meta.url), "utf8"),
  );
  assert.equal(validateParticipantPublication(value), value);
  assert.match(value.association_unit_identity.association_anchor.original_declaration_recording_reference, /^Synthetic /);
});

test("schema keeps first publication public-only by scope rather than a visibility subsystem", async () => {
  const schema = JSON.parse(
    await readFile(new URL("../administration/contracts/participant-publication-v1.schema.json", import.meta.url), "utf8"),
  );
  const fields = Object.keys(schema.properties);
  assert.deepEqual(fields.sort(), ["association_unit_identity", "descriptor_instances", "format", "format_version"].sort());
  assert.equal(fields.includes("classification"), false);
  assert.equal(fields.includes("generation_sha256"), false);
  assert.equal(fields.includes("source"), false);
});

test("unit subject must repeat an accepted raw unit anchor", () => {
  const value = fixture();
  value.descriptor_instances[0].subject = {
    kind: "unit",
    unit_anchor: { ...value.association_unit_identity.unit_anchors[0] },
  };
  assert.equal(validateParticipantPublication(value), value);

  value.descriptor_instances[0].subject.unit_anchor.recorded_unit_reference = "not-in-identity-set";
  assert.throws(
    () => validateParticipantPublication(value),
    (error) => error instanceof ParticipantPublicationError && error.path.endsWith(".unit_anchor"),
  );
});

test("each descriptor instance must attach to at least one geographic reference", () => {
  const value = fixture();
  value.descriptor_instances[0].geographic_refs = [];
  assert.throws(
    () => validateParticipantPublication(value),
    (error) => error instanceof ParticipantPublicationError && error.path.endsWith(".geographic_refs"),
  );
});

test("contract rejects duplicate exact geographic references", () => {
  const value = fixture();
  value.descriptor_instances[0].geographic_refs.push({ ...value.descriptor_instances[0].geographic_refs[0] });
  assert.throws(() => validateParticipantPublication(value), ParticipantPublicationError);
});

test("contract rejects physical-source metadata", () => {
  const value = fixture();
  value.device = { platform: "esp32-s3" };
  assert.throws(
    () => validateParticipantPublication(value),
    (error) => error instanceof ParticipantPublicationError && error.path === "$.device",
  );
});

test("contract rejects a duplicate descriptor instance for the same subject", () => {
  const value = fixture();
  value.descriptor_instances.push(JSON.parse(JSON.stringify(value.descriptor_instances[0])));
  assert.throws(() => validateParticipantPublication(value), ParticipantPublicationError);
});
