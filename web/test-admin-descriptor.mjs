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
  Object.defineProperty(globalThis, "crypto", { value: webcrypto, configurable: true });
}

const descriptorUrls = {
  insurance: new URL("../administration/descriptors/illinois/condominium/insurance.v1.json", import.meta.url),
  records: new URL("../administration/descriptors/illinois/condominium/records.v1.json", import.meta.url),
  finance: new URL("../administration/descriptors/illinois/condominium/finance.v1.json", import.meta.url),
  governance: new URL("../administration/descriptors/illinois/condominium/governance.v1.json", import.meta.url),
  management: new URL("../administration/descriptors/illinois/condominium/management.v1.json", import.meta.url),
  resale: new URL("../administration/descriptors/illinois/condominium/resale.v1.json", import.meta.url),
  property: new URL("../administration/descriptors/illinois/condominium/property.v1.json", import.meta.url),
};

async function loadDescriptor(name) {
  return JSON.parse(await readFile(descriptorUrls[name], "utf8"));
}

const summaries = {
  insurance: { descriptor_id: "us.il.condominium.insurance", descriptor_version: 1, pages: 1, sections: 3, controls: 14, collections: 1 },
  records: { descriptor_id: "us.il.condominium.records", descriptor_version: 1, pages: 1, sections: 3, controls: 21, collections: 1 },
  finance: { descriptor_id: "us.il.condominium.finance", descriptor_version: 1, pages: 1, sections: 5, controls: 46, collections: 2 },
  governance: { descriptor_id: "us.il.condominium.governance", descriptor_version: 1, pages: 1, sections: 5, controls: 42, collections: 3 },
  management: { descriptor_id: "us.il.condominium.management", descriptor_version: 1, pages: 1, sections: 4, controls: 34, collections: 1 },
  resale: { descriptor_id: "us.il.condominium.resale", descriptor_version: 1, pages: 1, sections: 4, controls: 30, collections: 3 },
  property: { descriptor_id: "us.il.condominium.property", descriptor_version: 1, pages: 1, sections: 4, controls: 46, collections: 4 },
};

for (const [name, expected] of Object.entries(summaries)) {
  test(`Illinois condominium ${name} descriptor validates`, async () => {
    const descriptor = await loadDescriptor(name);
    assert.equal(validateAdministrativeDescriptor(descriptor), descriptor);
    assert.deepEqual(descriptorSummary(descriptor), expected);
  });
}

test("finance descriptor carries generic unit and format metadata", async () => {
  const descriptor = await loadDescriptor("finance");
  const budget = descriptor.pages[0].sections.find((section) => section.id === "annual-budget-summary");
  const expense = budget.controls.find((control) => control.id === "anticipated-common-expenses");
  assert.equal(expense.kind, "number");
  assert.equal(expense.unit, "USD");
  assert.equal(expense.format, "currency");

  const assessments = descriptor.pages[0].sections.find((section) => section.id === "assessment-administration");
  const separate = assessments.controls.find((control) => control.id === "separate-assessments");
  const years = separate.item_controls.find((control) => control.id === "separate-assessment-years");
  assert.equal(years.unit, "years");
  assert.equal(years.format, "integer");
});

test("governance descriptor preserves current statewide meeting and election rules", async () => {
  const descriptor = await loadDescriptor("governance");
  const framework = descriptor.pages[0].sections.find((section) => section.id === "statewide-governance-framework");
  assert.match(framework.controls.find((control) => control.id === "board-meeting-frequency").text, /at least 4 times annually/);
  assert.match(framework.controls.find((control) => control.id === "board-notice-window").text, /48 hours/);
  assert.match(framework.controls.find((control) => control.id === "membership-notice-window").text, /not less than 10 and not more than 30 days/);
  assert.ok(framework.controls.every((control) => control.data_role === "infrastructure"));

  const elections = descriptor.pages[0].sections.find((section) => section.id === "election-and-voting");
  const method = elections.controls.find((control) => control.id === "election-method");
  assert.deepEqual(new Set(method.options.map((option) => option.value)), new Set(["proxy", "association_ballot", "technology", "mixed_or_other", "unknown"]));
});

test("management descriptor preserves licensing and fund-safeguard boundaries", async () => {
  const descriptor = await loadDescriptor("management");
  const framework = descriptor.pages[0].sections.find((section) => section.id === "statewide-management-framework");
  assert.match(framework.controls.find((control) => control.id === "management-license-required").text, /requires a current valid Department license unless a statutory exemption applies/);
  assert.match(framework.controls.find((control) => control.id === "support-staff-boundary").text, /bookkeepers/);
  assert.ok(framework.controls.every((control) => control.data_role === "infrastructure"));

  const safeguards = descriptor.pages[0].sections.find((section) => section.id === "management-fund-safeguards");
  assert.match(safeguards.controls.find((control) => control.id === "segregated-accounts-rule").text, /may not commingle/);

  const contracts = descriptor.pages[0].sections.find((section) => section.id === "active-service-contracts");
  const collection = contracts.controls.find((control) => control.id === "service-contracts");
  const amount = collection.item_controls.find((control) => control.id === "service-contract-value");
  assert.equal(amount.unit, "USD");
  assert.equal(amount.format, "currency");
});

test("resale descriptor preserves current-effective disclosure and timing boundary", async () => {
  const descriptor = await loadDescriptor("resale");
  assert.equal(descriptor.scope.as_of_date, "2026-09-17");
  assert.match(descriptor.scope.admission_rule, /January 1, 2027/);

  const framework = descriptor.pages[0].sections.find((section) => section.id === "statewide-resale-framework");
  assert.match(framework.controls.find((control) => control.id === "association-response-deadline").text, /10 business days/);
  assert.match(framework.controls.find((control) => control.id === "resale-rush-framework").text, /\$100.*72 hours/);
  assert.match(framework.controls.find((control) => control.id === "lender-notice-framework").text, /Within 15 days/);
  assert.ok(framework.controls.every((control) => control.data_role === "infrastructure"));

  const inventory = descriptor.pages[0].sections.find((section) => section.id === "current-disclosure-inventory");
  const collection = inventory.controls.find((control) => control.id === "resale-disclosure-items");
  const category = collection.item_controls.find((control) => control.id === "resale-disclosure-category");
  assert.equal(category.options.length, 9);
  assert.ok(!category.options.some((option) => option.value === "collection_policy"));
});

test("property descriptor preserves recording, legal-form, and separate-tax boundaries", async () => {
  const descriptor = await loadDescriptor("property");
  const framework = descriptor.pages[0].sections.find((section) => section.id === "statewide-property-framework");
  assert.match(framework.controls.find((control) => control.id === "plat-recording-rule").text, /recorded simultaneously with the declaration/);
  assert.match(framework.controls.find((control) => control.id === "association-form-neutrality").text, /incorporated or unincorporated/);
  assert.match(framework.controls.find((control) => control.id === "separate-taxation-rule").text, /not against the condominium property as a whole/);
  assert.match(framework.controls.find((control) => control.id === "association-owned-residential-tax-rule").text, /\$1\.00 per year/);
  assert.ok(framework.controls.every((control) => control.data_role === "infrastructure"));

  const units = descriptor.pages[0].sections.find((section) => section.id === "unit-common-element-instance");
  const unitInventory = units.controls.find((control) => control.id === "unit-inventory");
  const interest = unitInventory.item_controls.find((control) => control.id === "property-unit-common-interest");
  assert.equal(interest.unit, "%");
  assert.equal(interest.format, "percent");

  const legalForm = units.controls.find((control) => control.id === "association-legal-form");
  assert.deepEqual(new Set(legalForm.options.map((option) => option.value)), new Set(["incorporated", "unincorporated", "unknown"]));
});

test("records descriptor preserves statewide access rules as infrastructure notices", async () => {
  const descriptor = await loadDescriptor("records");
  const access = descriptor.pages[0].sections.find((section) => section.id === "member-examination-framework");
  assert.ok(access.controls.every((control) => control.kind === "notice"));
  assert.ok(access.controls.every((control) => control.data_role === "infrastructure"));
  assert.match(access.controls.find((control) => control.id === "general-record-access").text, /10 business days/);
});

test("descriptor validation keeps category semantics separate from contract identity", async () => {
  const descriptor = await loadDescriptor("insurance");
  assert.equal(descriptor.descriptor_id, "us.il.condominium.insurance");
  assert.equal(descriptor.categories[0].id, "insurance.association");
  assert.notEqual(descriptor.descriptor_id, descriptor.categories[0].id);
});

test("descriptor rejects authority references that are not declared", async () => {
  const descriptor = await loadDescriptor("insurance");
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
  const descriptor = await loadDescriptor("insurance");
  const policy = descriptor.pages[0].sections[1].controls[0];
  const insurer = policy.item_controls.find((control) => control.id === "policy-insurer-name");
  assert.equal(insurer.binding, "insurer_name");
  assert.equal(insurer.layout.column, 1);
  assert.equal(insurer.layout.span, 4);
});

test("generic descriptor browser code contains no Illinois condominium domain vocabulary", async () => {
  const engine = await readFile(new URL("./admin-descriptor.js", import.meta.url), "utf8");
  const bootstrap = await readFile(new URL("./admin-app.js", import.meta.url), "utf8");
  const domainWords = /Illinois|condominium|insurance|budget|assessment|reserve|governance|board|election|management|manager|license|resale|disclosure|lender|mortgage|\bproperty\b|plat|surveyor|tax|county|parish/i;
  assert.doesNotMatch(engine, domainWords);
  assert.doesNotMatch(bootstrap, domainWords);
});

test("administrative bootstrap selects multiple descriptors without hard-coded form controls", async () => {
  const bootstrap = JSON.parse(await readFile(new URL("./admin-app.json", import.meta.url), "utf8"));
  assert.equal(bootstrap.format, "kane-fabric-administrative-bootstrap");
  assert.equal(bootstrap.version, 1);
  assert.equal(bootstrap.descriptor_sources.length, 7);
  const expected = ["insurance", "records", "finance", "governance", "management", "resale", "property"];
  expected.forEach((name, index) => {
    assert.match(bootstrap.descriptor_sources[index].url, new RegExp(`administration/descriptors/illinois/condominium/${name}\\.v1\\.json$`));
  });
  assert.ok(bootstrap.descriptor_sources.every((source) => source.enabled !== false));
});
