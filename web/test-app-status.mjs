import test from "node:test";
import assert from "node:assert/strict";

import {
  classifyLoadFailure,
  recoveryStatusPayload,
  verificationPresentation,
} from "./app-status.js";

test("loading state is explicitly not verified", () => {
  const value = verificationPresentation({ phase: "loading", online: true });
  assert.equal(value.kind, "checking");
  assert.equal(value.verified, false);
  assert.equal(value.retryable, false);
});

test("verified online state reports accepted presentation", () => {
  const value = verificationPresentation({ phase: "verified", online: true });
  assert.equal(value.kind, "verified");
  assert.equal(value.verified, true);
  assert.equal(value.availability, "online");
});

test("verified data remains explicitly verified when connectivity is later lost", () => {
  const value = verificationPresentation({ phase: "verified", online: false });
  assert.equal(value.kind, "verified-offline");
  assert.equal(value.verified, true);
  assert.match(value.detail, /verified before connectivity was lost/i);
});

test("offline load failure never claims verification", () => {
  const failure = classifyLoadFailure(new TypeError("Failed to fetch"), { online: false });
  assert.equal(failure.kind, "offline");
  assert.equal(failure.verified, false);
  assert.equal(failure.retryable, true);
});

test("browser fetch rejection is classified as a network failure", () => {
  const failure = classifyLoadFailure(new TypeError("Failed to fetch"), { online: true });
  assert.equal(failure.kind, "network");
  assert.equal(failure.verified, false);
});

test("accepted loader contract errors are classified as verification failures", () => {
  const error = new Error("MS4 publication byte SHA-256 mismatch");
  error.name = "Ms4CompositionError";
  const failure = classifyLoadFailure(error, { online: true });
  assert.equal(failure.kind, "verification");
  assert.match(failure.title, /verification failed/i);
});

test("recovery payload is fail-closed and platform neutral", () => {
  const error = new Error("county overview bytes disagree with manifest");
  error.name = "SubstrateError";
  const failure = classifyLoadFailure(error, { online: true });
  const payload = recoveryStatusPayload({ phase: "failed", online: true, failure });
  assert.deepEqual(payload, {
    verification_status: "not-verified",
    availability: "online",
    failure_kind: "verification",
    retry_available: true,
    physical_platform_assumed: false,
  });
  assert.doesNotMatch(JSON.stringify(payload), /esp32|idf|hardware/i);
});
