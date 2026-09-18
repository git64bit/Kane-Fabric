import test from "node:test";
import assert from "node:assert/strict";

import {
  composeParticipantPublication,
  ParticipantCompositionError,
} from "./participant-publication.js";

const geographicRef = {
  kind: "building",
  dataset_key: "synthetic-buildings",
  release_key: "synthetic-release-1",
  source_content_sha256: "1".repeat(64),
  object_key: "synthetic-building-1",
};

function publication() {
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
      unit_anchors: [],
    },
    descriptor_instances: [
      {
        descriptor_id: "us.il.condominium.property",
        descriptor_version: 1,
        subject: { kind: "association" },
        geographic_refs: [{ ...geographicRef }],
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

const compositionResult = {
  subscriptions: [
    {
      objects: [
        {
          geographic_refs: [{ ...geographicRef }],
        },
      ],
    },
  ],
};

const descriptorRegistry = new Map([
  [
    "us.il.condominium.property",
    {
      descriptor_id: "us.il.condominium.property",
      descriptor_version: 1,
    },
  ],
]);

test("participant instance composes only against a reference in the verified county composition", () => {
  const composed = composeParticipantPublication(publication(), compositionResult, descriptorRegistry);
  assert.equal(composed.length, 1);
  assert.equal(
    composed[0].instance.data.association.property.condominium_name,
    "Synthetic Participant Condominium",
  );
});

test("unknown participant geographic reference fails closed", () => {
  const value = publication();
  value.descriptor_instances[0].geographic_refs[0].object_key = "unknown-building";
  assert.throws(
    () => composeParticipantPublication(value, compositionResult, descriptorRegistry),
    ParticipantCompositionError,
  );
});

test("unknown administrative descriptor fails closed", () => {
  assert.throws(
    () => composeParticipantPublication(publication(), compositionResult, new Map()),
    ParticipantCompositionError,
  );
});

test("descriptor version mismatch fails closed", () => {
  const wrongVersion = new Map([
    [
      "us.il.condominium.property",
      {
        descriptor_id: "us.il.condominium.property",
        descriptor_version: 2,
      },
    ],
  ]);
  assert.throws(
    () => composeParticipantPublication(publication(), compositionResult, wrongVersion),
    ParticipantCompositionError,
  );
});
