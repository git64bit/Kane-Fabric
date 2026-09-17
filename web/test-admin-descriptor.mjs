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
const financeDescriptorUrl = new URL("../administration/descriptors/illinois/condominium/finance.v1.json", import.meta.url);
const governanceDescriptorUrl = new URL("../administration/descriptors/illinois/condominium/governance.v1.json", import.meta.url);
const managementDescriptorUrl = new URL("../administration/descriptors/illinois/condominium/management.v1.json", import.meta.url);
const resaleDescriptorUrl = new URL("../administration/descriptors/illinois/condominium/resale.v1.json", import.meta.url);

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

test("Illinois condominium finance descriptor validates", async () => {
  const descriptor = await loadDescriptor(financeDescriptorUrl);
  assert.equal(validateAdministrativeDescriptor(descriptor), descriptor);
  assert.deepEqual(descriptorSummary(descriptor), {
    descriptor_id: "us.il.condominium.finance",
    descriptor_version: 1,
    pages: 1,
    sections: 5,
    controls: 46,
    collections: 2,
  });
});

test("finance descriptor carries generic unit and format metadata", async () => {
  const descriptor = await loadDescriptor(financeDescriptorUrl);
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

test("Illinois condominium governance descriptor validates", async () => {
  const descriptor = await loadDescriptor(governanceDescriptorUrl);
  assert.equal(validateAdministrativeDescriptor(descriptor), descriptor);
  assert.deepEqual(descriptorSummary(descriptor), {
    descriptor_id: "us.il.condominium.governance",
    descriptor_version: 1,
    pages: 1,
    sections: 5,
    controls: 42,
    collections: 3,
  });
});

test("governance descriptor preserves current statewide meeting and election rules", async () => {
  const descriptor = await loadDescriptor(governanceDescriptorUrl);
  const framework = descriptor.pages[0].sections.find((section) => section.id === "statewide-governance-framework");
  assert.match(framework.controls.find((control) => control.id === "board-meeting-frequency").text, /at least 4 times annually/);
  assert.match(framework.controls.find((control) => control.id === "board-notice-window").text, /48 hours/);
  assert.match(framework.controls.find((control) => control.id === "membership-notice-window").text, /not less than 10 and not more than 30 days/);
  assert.ok(framework.controls.every((control) => control.data_role === "infrastructure"));

  const elections = descriptor.pages[0].sections.find((section) => section.id === "election-and-voting");
  const method = elections.controls.find((control) => control.id === "election-method");
  assert.deepEqual(new Set(method.options.map((option) => option.value)), new Set(["proxy", "association_ballot", "technology", "mixed_or_other", "unknown"]));
});

test("Illinois condominium management descriptor validates", async () => {
  const descriptor = await loadDescriptor(managementDescriptorUrl);
  assert.equal(validateAdministrativeDescriptor(descriptor), descriptor);
  assert.deepEqual(descriptorSummary(descriptor), {
    descriptor_id: "us.il.condominium.management",
    descriptor_version: 1,
    pages: 1,
    sections: 4,
    controls: 34,
    collections: 1,
  });
});

test("management descriptor preserves licensing and fund-safeguard boundaries", async () => {
  const descriptor = await loadDescriptor(managementDescriptorUrl);
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

test("Illinois condominium resale descriptor validates", async () => {
  const descriptor = await loadDescriptor(resaleDescriptorUrl);
  assert.equal(validateAdministrativeDescriptor(descriptor), descriptor);
  assert.deepEqual(descriptorSummary(descriptor), {
    descriptor_id: "us.il.condominium.resale",
    descriptor_version: 1,
    pages: 1,
    sections: 4,
    controls: 30,
    collections: 3,
  });
});

test("resale descriptor preserves current-effective disclosure and timing boundary", async () => {
  const descriptor = await loadDescriptor(resaleDescriptorUrl);
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

test("generic descriptor browser code contains no Illinois condominium domain vocabulary", async () => {
  const engine = await readFile(new URL("./admin-descriptor.js", import.meta.url), "utf8");
  const bootstrap = await readFile(new URL("./admin-app.js", import.meta.url), "utf8");
  assert.doesNotMatch(engine, /Illinois|condominium|insurance|budget|assessment|reserve|governance|board|election|management|manager|license|resale|disclosure|lender|mortgage|county|parish/i);
  assert.doesNotMatch(bootstrap, /Illinois|condominium|insurance|budget|assessment|reserve|governance|board|election|management|manager|license|resale|disclosure|lender|mortgage|county|parish/i);
});

test("administrative bootstrap selects multiple descriptors without hard-coded form controls", async () => {
  const bootstrap = JSON.parse(await readFile(new URL("./admin-app.json", import.meta.url), "utf8"));
  assert.equal(bootstrap.format, "kane-fabric-administrative-bootstrap");
  assert.equal(bootstrap.version, 1);
  assert.equal(bootstrap.descriptor_sources.length, 6);
  assert.match(bootstrap.descriptor_sources[0].url, /administration\/descriptors\/illinois\/condominium\/insurance\.v1\.json$/);
  assert.match(bootstrap.descriptor_sources[1].url, /administration\/descriptors\/illinois\/condominium\/records\.v1\.json$/);
  assert.match(bootstrap.descriptor_sources[2].url, /administration\/descriptors\/illinois\/condominium\/finance\.v1\.json$/);
  assert.match(bootstrap.descriptor_sources[3].url, /administration\/descriptors\/illinois\/condominium\/governance\.v1\.json$/);
  assert.match(bootstrap.descriptor_sources[4].url, /administration\/descriptors\/illinois\/condominium\/management\.v1\.json$/);
  assert.match(bootstrap.descriptor_sources[5].url, /administration\/descriptors\/illinois\/condominium\/resale\.v1\.json$/);
  assert.ok(bootstrap.descriptor_sources.every((source) => source.enabled !== false));
});
