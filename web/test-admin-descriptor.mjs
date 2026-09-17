import assert from "node:assert/strict";
import { webcrypto } from "node:crypto";
import { readFile } from "node:fs/promises";
import test from "node:test";
import {
  AdministrativeDescriptorError,
  canonicalizeJson,
  descriptorSummary,
  sha256CanonicalJson,
  validateAdministrativeDescriptor,
} from "./admin-descriptor.js";

if (!globalThis.crypto) {
  Object.defineProperty(globalThis, "crypto", {
    value: webcrypto,
    configurable: true,
  });
}

const insuranceDescriptorUrl = new URL("../administration/descriptors/illinois/condominium/insurance.v1.json", import.meta.url);
const recordsDescriptorUrl = new URL("../administration/descriptors/illinois/condominium/records.v1.json", import.meta.url);

async function loadDescriptor(url) {
  return JSON.parse(await readFile(url, "utf8"));
}

test("Illinois condominium insurance reference descriptor validates", async () => {
  const descriptor = await loadDescriptor(insuranceDescriptorUrl);
  assert.equal(validateAdministrativeDescriptor(descriptor), descriptor);
  assert.deepEqual(descriptorSummary(descriptor), {
    descriptor_id: "us.il.condominium.insurance",
    descriptor_version: 1,
    pages: 1,
    sections: 3,
    controls: 14,
    collections: 1,
  });
});

test("Illinois condominium association-records descriptor validates", async () => {
  const descriptor = await loadDescriptor(recordsDescriptorUrl);
  assert.equal(validateAdministrativeDescriptor(descriptor), descriptor);
  assert.deepEqual(descriptorSummary(descriptor), {
    descriptor_id: "us.il.condominium.records",
    descriptor_version: 1,
    pages: 1,
    sections: 3,
    controls: 21,
    collections: 1,
  });

  const inventory = descriptor.pages[0].sections.find((section) => section.id === "association-record-inventory");
  const recordSets = inventory.controls.find((control) => control.id === "required-record-sets");
  const category = recordSets.item_controls.find((control) => control.id === "record-set-category");
  assert.equal(category.options.length, 10);
  assert.deepEqual(
    new Set(category.options.map((option) => option.value)),
    new Set([
      "declaration_bylaws_plats",
      "rules_regulations",
      "articles_incorporation",
      "meeting_minutes",
      "insurance_policies",
      "contracts_leases_agreements",
      "member_voter_listing",
      "ballots_proxies",
      "books_records",
      "reserve_study",
    ]),
  );
});

test("records descriptor preserves statewide access rules as infrastructure notices", async () => {
  const descriptor = await loadDescriptor(recordsDescriptorUrl);
  const access = descriptor.pages[0].sections.find((section) => section.id === "member-examination-framework");
  assert.ok(access.controls.every((control) => control.kind === "notice"));
  assert.ok(access.controls.every((control) => control.data_role === "infrastructure"));
  assert.match(access.controls.find((control) => control.id === "general-record-access").text, /10 business days/);
});

test("descriptor validation keeps category semantics separate from contract identity", async () => {
  const descriptor = await loadDescriptor(insuranceDescriptorUrl);
  assert.equal(descriptor.descriptor_id, "us.il.condominium.insurance");
  assert.equal(descriptor.categories[0].id, "insurance.association");
  assert.notEqual(descriptor.descriptor_id, descriptor.categories[0].id);
});

test("descriptor rejects authority references that are not declared", async () => {
  const descriptor = await loadDescriptor(insuranceDescriptorUrl);
  descriptor.pages[0].sections[0].controls[0].authority_refs = ["missing-authority"];
  assert.throws(() => validateAdministrativeDescriptor(descriptor), AdministrativeDescriptorError);
});

test("canonical JSON identity is independent of object key insertion order", async () => {
  const a = { z: 1, a: { beta: 2, alpha: 1 }, list: [3, 2, 1] };
  const b = { list: [3, 2, 1], a: { alpha: 1, beta: 2 }, z: 1 };
  assert.equal(canonicalizeJson(a), canonicalizeJson(b));
  assert.equal(await sha256CanonicalJson(a), await sha256CanonicalJson(b));
});

test("descriptor presentation placement remains separate from semantic binding", async () => {
  const descriptor = await loadDescriptor(insuranceDescriptorUrl);
  const policy = descriptor.pages[0].sections[1].controls[0];
  const insurer = policy.item_controls.find((control) => control.id === "policy-insurer-name");
  assert.equal(insurer.binding, "insurer_name");
  assert.equal(insurer.layout.column, 1);
  assert.equal(insurer.layout.span, 4);
});

test("generic descriptor engine contains no Illinois condominium domain vocabulary", async () => {
  const source = await readFile(new URL("./admin-descriptor.js", import.meta.url), "utf8");
  assert.doesNotMatch(source, /Illinois|condominium|insurance|county|parish/i);
});

test("administrative bootstrap selects multiple descriptors without hard-coded form controls", async () => {
  const bootstrap = JSON.parse(await readFile(new URL("./admin-app.json", import.meta.url), "utf8"));
  assert.equal(bootstrap.format, "kane-fabric-administrative-bootstrap");
  assert.equal(bootstrap.version, 1);
  assert.equal(bootstrap.descriptor_sources.length, 2);
  assert.match(bootstrap.descriptor_sources[0].url, /administration\/descriptors\/illinois\/condominium\/insurance\.v1\.json$/);
  assert.match(bootstrap.descriptor_sources[1].url, /administration\/descriptors\/illinois\/condominium\/records\.v1\.json$/);
  assert.ok(bootstrap.descriptor_sources.every((source) => source.enabled !== false));
});
