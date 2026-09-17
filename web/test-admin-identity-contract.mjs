import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import {
  AssociationUnitIdentityError,
  validateAssociationUnitIdentity,
} from "../administration/contracts/association-unit-identity-v1.mjs";

function fixture() {
  return {
    format: "kane-fabric-association-unit-identity",
    format_version: 1,
    association_anchor: {
      jurisdiction: {
        country_code: "US",
        state_code: "IL",
      },
      recording_authority_reference: "synthetic-public-recording-authority",
      original_declaration_recording_reference: "synthetic-original-declaration-reference",
    },
    unit_anchors: [
      {
        recorded_unit_designation: "Synthetic Unit 1",
        recorded_unit_reference: "synthetic-recorded-unit-reference-1",
      },
    ],
  };
}

test("association and unit identity v1 validates a bounded anchor set", () => {
  const value = fixture();
  assert.equal(validateAssociationUnitIdentity(value), value);
  assert.equal("association_id" in value, false);
  assert.equal("unit_id" in value.unit_anchors[0], false);
});

test("association identity can exist before any unit anchors are supplied", () => {
  const value = fixture();
  value.unit_anchors = [];
  assert.equal(validateAssociationUnitIdentity(value), value);
});

test("identity schema freezes only source-neutral anchor fields", async () => {
  const schema = JSON.parse(
    await readFile(new URL("../administration/contracts/association-unit-identity-v1.schema.json", import.meta.url), "utf8"),
  );
  assert.equal(schema.additionalProperties, false);
  assert.deepEqual(
    Object.keys(schema.properties).sort(),
    ["association_anchor", "format", "format_version", "unit_anchors"].sort(),
  );
  assert.deepEqual(
    Object.keys(schema.$defs.associationAnchor.properties).sort(),
    ["jurisdiction", "original_declaration_recording_reference", "recording_authority_reference"].sort(),
  );
  assert.deepEqual(
    Object.keys(schema.$defs.unitAnchor.properties).sort(),
    ["recorded_unit_designation", "recorded_unit_reference"].sort(),
  );
});

test("identity contract rejects portal, account, source, or device fields", () => {
  const value = fixture();
  value.association_anchor.portal_id = "not-civic-identity";
  assert.throws(
    () => validateAssociationUnitIdentity(value),
    (error) => error instanceof AssociationUnitIdentityError && error.path === "$.association_anchor.portal_id",
  );
});

test("identity contract requires the original declaration recording reference", () => {
  const value = fixture();
  value.association_anchor.original_declaration_recording_reference = "   ";
  assert.throws(
    () => validateAssociationUnitIdentity(value),
    (error) =>
      error instanceof AssociationUnitIdentityError &&
      error.path === "$.association_anchor.original_declaration_recording_reference",
  );
});

test("identity contract rejects malformed jurisdiction codes", () => {
  const value = fixture();
  value.association_anchor.jurisdiction.state_code = "Illinois";
  assert.throws(
    () => validateAssociationUnitIdentity(value),
    (error) => error instanceof AssociationUnitIdentityError && error.path.endsWith(".state_code"),
  );
});

test("unit identity requires both recorded designation and recorded reference", () => {
  const value = fixture();
  delete value.unit_anchors[0].recorded_unit_reference;
  assert.throws(
    () => validateAssociationUnitIdentity(value),
    (error) => error instanceof AssociationUnitIdentityError && error.path.endsWith(".recorded_unit_reference"),
  );
});

test("identity contract rejects duplicate exact unit anchors", () => {
  const value = fixture();
  value.unit_anchors.push({ ...value.unit_anchors[0] });
  assert.throws(
    () => validateAssociationUnitIdentity(value),
    (error) => error instanceof AssociationUnitIdentityError && error.path === "$.unit_anchors[1]",
  );
});
