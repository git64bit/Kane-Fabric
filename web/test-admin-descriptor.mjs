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
  collections: new URL("../administration/descriptors/illinois/condominium/collections.v1.json", import.meta.url),
  enforcement: new URL("../administration/descriptors/illinois/condominium/enforcement.v1.json", import.meta.url),
  maintenance: new URL("../administration/descriptors/illinois/condominium/maintenance.v1.json", import.meta.url),
  turnover: new URL("../administration/descriptors/illinois/condominium/turnover.v1.json", import.meta.url),
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
  collections: { descriptor_id: "us.il.condominium.collections", descriptor_version: 1, pages: 1, sections: 4, controls: 42, collections: 2 },
  enforcement: { descriptor_id: "us.il.condominium.enforcement", descriptor_version: 1, pages: 1, sections: 4, controls: 43, collections: 2 },
  maintenance: { descriptor_id: "us.il.condominium.maintenance", descriptor_version: 1, pages: 1, sections: 4, controls: 37, collections: 2 },
  turnover: { descriptor_id: "us.il.condominium.turnover", descriptor_version: 1, pages: 1, sections: 4, controls: 43, collections: 2 },
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

test("collections descriptor preserves lien, fee, and successor boundaries", async () => {
  const descriptor = await loadDescriptor("collections");
  assert.equal(descriptor.scope.as_of_date, "2026-09-17");
  const framework = descriptor.pages[0].sections.find((section) => section.id === "statewide-collection-framework");
  assert.match(framework.controls.find((control) => control.id === "statutory-lien-scope").text, /statutory lien/);
  assert.match(framework.controls.find((control) => control.id === "six-month-successor-rule").text, /6 months immediately preceding/);
  assert.match(framework.controls.find((control) => control.id === "encumbrancer-statement-rule").text, /within 20 days/);
  assert.match(framework.controls.find((control) => control.id === "manager-fee-boundary").text, /management contract/);
  assert.match(framework.controls.find((control) => control.id === "fine-due-process-boundary").text, /notice and an opportunity to be heard/);
  assert.ok(framework.controls.every((control) => control.data_role === "infrastructure"));

  const cases = descriptor.pages[0].sections.find((section) => section.id === "active-collection-cases");
  const collection = cases.controls.find((control) => control.id === "collection-cases");
  const fees = collection.item_controls.find((control) => control.id === "collection-attorney-fees");
  assert.equal(fees.unit, "USD");
  assert.equal(fees.format, "currency");
});

test("enforcement descriptor preserves rule-adoption and fine due-process boundaries", async () => {
  const descriptor = await loadDescriptor("enforcement");
  assert.equal(descriptor.scope.as_of_date, "2026-09-17");
  const framework = descriptor.pages[0].sections.find((section) => section.id === "statewide-enforcement-framework");
  assert.match(framework.controls.find((control) => control.id === "rule-discussion-meeting-rule").text, /specific purpose of discussing/);
  assert.match(framework.controls.find((control) => control.id === "full-text-notice-rule").text, /full text/);
  assert.match(framework.controls.find((control) => control.id === "rule-meeting-quorum-rule").text, /No quorum is required/);
  assert.match(framework.controls.find((control) => control.id === "fine-due-process-rule").text, /notice and an opportunity to be heard/);
  assert.match(framework.controls.find((control) => control.id === "no-universal-fine-notice-period").text, /does not itself state a universal numeric notice period/);
  assert.ok(framework.controls.every((control) => control.data_role === "infrastructure"));

  const cases = descriptor.pages[0].sections.find((section) => section.id === "violation-cases");
  const collection = cases.controls.find((control) => control.id === "violation-cases-collection");
  const fine = collection.item_controls.find((control) => control.id === "violation-fine-amount");
  assert.equal(fine.unit, "USD");
  assert.equal(fine.format, "currency");
});

test("maintenance descriptor preserves repair, improvement, emergency, and unit-access boundaries", async () => {
  const descriptor = await loadDescriptor("maintenance");
  assert.equal(descriptor.scope.as_of_date, "2026-09-17");
  const framework = descriptor.pages[0].sections.find((section) => section.id === "statewide-maintenance-framework");
  assert.match(framework.controls.find((control) => control.id === "common-element-duty").text, /maintenance, replacement, and improvement/);
  assert.match(framework.controls.find((control) => control.id === "repair-limit-boundary").text, /do not apply to expenditures for repair, replacement, or restoration/);
  assert.match(framework.controls.find((control) => control.id === "improvement-petition-rule").text, /exceeding 5%.*20%.*21 days.*30 days/);
  assert.match(framework.controls.find((control) => control.id === "emergency-definition").text, /immediate danger to the structural integrity/);
  assert.match(framework.controls.find((control) => control.id === "unit-access-rule").text, /access to each unit/);
  assert.ok(framework.controls.every((control) => control.data_role === "infrastructure"));

  const events = descriptor.pages[0].sections.find((section) => section.id === "maintenance-events");
  const collection = events.controls.find((control) => control.id === "maintenance-events-collection");
  const cost = collection.item_controls.find((control) => control.id === "maintenance-event-cost");
  assert.equal(cost.unit, "USD");
  assert.equal(cost.format, "currency");
});

test("turnover descriptor preserves first-board, delivery, and contract-review boundaries", async () => {
  const descriptor = await loadDescriptor("turnover");
  assert.equal(descriptor.scope.as_of_date, "2026-09-17");
  const framework = descriptor.pages[0].sections.find((section) => section.id === "statewide-turnover-framework");
  assert.match(framework.controls.find((control) => control.id === "initial-election-trigger").text, /60 days.*75%.*3 years/);
  assert.match(framework.controls.find((control) => control.id === "initial-election-notice").text, /21 days/);
  assert.match(framework.controls.find((control) => control.id === "owner-petition-election").text, /20%/);
  assert.match(framework.controls.find((control) => control.id === "turnover-delivery-deadline").text, /Within 60 days/);
  assert.match(framework.controls.find((control) => control.id === "turnover-demand-remedy").text, /10 days/);
  assert.match(framework.controls.find((control) => control.id === "developer-contract-cancellation").text, /more than 2 years.*180-day.*60 days.*30 days/);
  assert.match(framework.controls.find((control) => control.id === "association-limitations-tolling").text, /does not begin to run/);
  assert.ok(framework.controls.every((control) => control.data_role === "infrastructure"));

  const packageSection = descriptor.pages[0].sections.find((section) => section.id === "turnover-package");
  const packageCollection = packageSection.controls.find((control) => control.id === "turnover-package-items");
  const category = packageCollection.item_controls.find((control) => control.id === "turnover-package-category");
  assert.equal(category.options.length, 5);
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
  const domainWords = /Illinois|condominium|insurance|budget|assessment|reserve|governance|board|election|management|manager|license|resale|disclosure|lender|mortgage|\bproperty\b|plat|surveyor|tax|county|parish|\blien\b|foreclosure|encumbrancer|violation|\bfine\b|common[- ]element|emergency repair|unit access|developer|turnover/i;
  assert.doesNotMatch(engine, domainWords);
  assert.doesNotMatch(bootstrap, domainWords);
});

test("administrative bootstrap selects multiple descriptors without hard-coded form controls", async () => {
  const bootstrap = JSON.parse(await readFile(new URL("./admin-app.json", import.meta.url), "utf8"));
  assert.equal(bootstrap.format, "kane-fabric-administrative-bootstrap");
  assert.equal(bootstrap.version, 1);
  assert.equal(bootstrap.descriptor_sources.length, 11);
  const expected = ["insurance", "records", "finance", "governance", "management", "resale", "property", "collections", "enforcement", "maintenance", "turnover"];
  expected.forEach((name, index) => {
    assert.match(bootstrap.descriptor_sources[index].url, new RegExp(`administration/descriptors/illinois/condominium/${name}\\.v1\\.json$`));
  });
  assert.ok(bootstrap.descriptor_sources.every((source) => source.enabled !== false));
});
