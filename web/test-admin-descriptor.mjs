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

// The application executes in a browser, where Web Crypto is a global Web API.
// Older Node runtimes used by repository tests expose the same API through
// node:crypto rather than as globalThis.crypto. Supply only that test-runtime
// compatibility shim; the browser module remains free of Node-specific imports.
if (!globalThis.crypto) {
  Object.defineProperty(globalThis, "crypto", {
    value: webcrypto,
    configurable: true,
  });
}

const descriptorUrl = new URL("../administration/descriptors/illinois/condominium/insurance.v1.json", import.meta.url);

async function loadReferenceDescriptor() {
  return JSON.parse(await readFile(descriptorUrl, "utf8"));
}

test("Illinois condominium insurance reference descriptor validates", async () => {
  const descriptor = await loadReferenceDescriptor();
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

test("descriptor validation keeps category semantics separate from contract identity", async () => {
  const descriptor = await loadReferenceDescriptor();
  assert.equal(descriptor.descriptor_id, "us.il.condominium.insurance");
  assert.equal(descriptor.categories[0].id, "insurance.association");
  assert.notEqual(descriptor.descriptor_id, descriptor.categories[0].id);
});

test("descriptor rejects authority references that are not declared", async () => {
  const descriptor = await loadReferenceDescriptor();
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
  const descriptor = await loadReferenceDescriptor();
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

test("administrative bootstrap selects descriptor data without hard-coded form controls", async () => {
  const bootstrap = JSON.parse(await readFile(new URL("./admin-app.json", import.meta.url), "utf8"));
  assert.equal(bootstrap.format, "kane-fabric-administrative-bootstrap");
  assert.equal(bootstrap.version, 1);
  assert.equal(bootstrap.descriptor_sources.length, 1);
  assert.match(bootstrap.descriptor_sources[0].url, /administration\/descriptors\/illinois\/condominium\/insurance\.v1\.json$/);
});
