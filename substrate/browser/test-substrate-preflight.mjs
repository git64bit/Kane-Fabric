#!/usr/bin/env node

import assert from "node:assert/strict";
import { webcrypto } from "node:crypto";
import test from "node:test";

import {
  assertSubstrateVerificationCapability,
  fetchExactRange,
  loadManifest,
  loadSubstrateMetadata,
  sha256Hex,
  SubstrateError,
} from "./kane-fabric-substrate.js";

const INSECURE_MESSAGE =
  "Kane Fabric substrate verification requires Web Crypto SHA-256. " +
  "This browser context is not secure. Use a secure HTTPS origin or a " +
  "browser-recognized trustworthy local development origin.";
const UNAVAILABLE_MESSAGE =
  "Kane Fabric substrate verification requires Web Crypto SHA-256, but " +
  "crypto.subtle.digest is unavailable in this runtime.";

function capableRuntime(overrides = {}) {
  return {
    crypto: {
      subtle: {
        digest: async () => new Uint8Array(32).buffer,
      },
    },
    ...overrides,
  };
}

function assertCapabilityFailure(runtime, expectedMessage) {
  assert.throws(
    () => assertSubstrateVerificationCapability(runtime),
    (error) =>
      error instanceof SubstrateError && error.message === expectedMessage,
  );
}

test("Web Crypto SHA-256 available passes preflight", () => {
  assert.doesNotThrow(() => assertSubstrateVerificationCapability(capableRuntime()));
});

test("crypto absent fails closed", () => {
  assertCapabilityFailure({}, UNAVAILABLE_MESSAGE);
});

test("crypto.subtle absent fails closed", () => {
  assertCapabilityFailure({ crypto: {} }, UNAVAILABLE_MESSAGE);
});

test("crypto.subtle.digest absent or non-callable fails closed", () => {
  assertCapabilityFailure({ crypto: { subtle: {} } }, UNAVAILABLE_MESSAGE);
  assertCapabilityFailure({ crypto: { subtle: { digest: "no" } } }, UNAVAILABLE_MESSAGE);
});

test("insecure browser context gets explicit diagnostic when Web Crypto is unavailable", () => {
  assertCapabilityFailure({ isSecureContext: false }, INSECURE_MESSAGE);
});

test("secure browser context missing Web Crypto gets capability diagnostic", () => {
  assertCapabilityFailure({ isSecureContext: true }, UNAVAILABLE_MESSAGE);
});

test("isSecureContext is diagnostic only when capability is actually present", () => {
  assert.doesNotThrow(() =>
    assertSubstrateVerificationCapability(capableRuntime({ isSecureContext: false })),
  );
});

test("Node-style runtime with callable digest and no isSecureContext passes", async () => {
  const runtime = { crypto: webcrypto };
  assert.equal("isSecureContext" in runtime, false);
  assert.doesNotThrow(() => assertSubstrateVerificationCapability(runtime));
  assert.equal(
    await sha256Hex(new TextEncoder().encode("abc"), { runtime }),
    "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
  );
});

test("high-level preflight rejects before the first publication fetch", async () => {
  let fetchCount = 0;
  const fetchImpl = async () => {
    fetchCount += 1;
    throw new Error("fetch must not run");
  };
  await assert.rejects(
    loadSubstrateMetadata("http://example.invalid/substrate/", {
      fetchImpl,
      runtime: {},
    }),
    (error) => error instanceof SubstrateError && error.message === UNAVAILABLE_MESSAGE,
  );
  assert.equal(fetchCount, 0);
});

test("direct manifest access cannot bypass the network capability guard", async () => {
  let fetchCount = 0;
  const fetchImpl = async () => {
    fetchCount += 1;
    throw new Error("fetch must not run");
  };
  await assert.rejects(
    loadManifest("http://example.invalid/substrate/", { fetchImpl, runtime: {} }),
    (error) => error instanceof SubstrateError && error.message === UNAVAILABLE_MESSAGE,
  );
  assert.equal(fetchCount, 0);
});

test("direct range access cannot bypass the network capability guard", async () => {
  let fetchCount = 0;
  const fetchImpl = async () => {
    fetchCount += 1;
    throw new Error("fetch must not run");
  };
  await assert.rejects(
    fetchExactRange("http://example.invalid/roads-lod.kfs", 0, 15, {
      expectedTotal: 100,
      fetchImpl,
      runtime: {},
    }),
    (error) => error instanceof SubstrateError && error.message === UNAVAILABLE_MESSAGE,
  );
  assert.equal(fetchCount, 0);
});

test("inner hash safeguard fails if digest disappears after preflight", async () => {
  const runtime = capableRuntime();
  assert.doesNotThrow(() => assertSubstrateVerificationCapability(runtime));
  runtime.crypto.subtle.digest = undefined;
  await assert.rejects(
    sha256Hex(new Uint8Array([1, 2, 3]), { runtime }),
    (error) => error instanceof SubstrateError && error.message === UNAVAILABLE_MESSAGE,
  );
});
