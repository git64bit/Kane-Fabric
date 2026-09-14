export class AppStatusError extends Error {
  constructor(message) {
    super(message);
    this.name = "AppStatusError";
  }
}

function fail(message) {
  throw new AppStatusError(message);
}

function boolean(value, label) {
  if (typeof value !== "boolean") fail(`${label} must be boolean`);
  return value;
}

function errorName(error) {
  return typeof error?.name === "string" && error.name ? error.name : "Error";
}

function errorMessage(error) {
  if (typeof error?.message === "string" && error.message.trim()) return error.message.trim();
  return String(error ?? "Unknown application failure");
}

export function classifyLoadFailure(error, { online = true } = {}) {
  const isOnline = boolean(online, "online");
  const name = errorName(error);
  const message = errorMessage(error);

  if (!isOnline) {
    return {
      kind: "offline",
      title: "Offline — artifacts not verified",
      detail: "The browser reports no network connection. No unverified Fabric data is being presented as accepted.",
      technical_detail: message,
      retryable: true,
      verified: false,
    };
  }

  if (name === "TypeError" || /failed to fetch|networkerror|network request|load failed/i.test(message)) {
    return {
      kind: "network",
      title: "Artifact source unavailable",
      detail: "The browser could not reach a configured artifact source. Verification did not complete.",
      technical_detail: message,
      retryable: true,
      verified: false,
    };
  }

  if (
    ["SubstrateError", "Ms4CompositionError", "AppViewError"].includes(name) ||
    /sha-?256|canonical|mismatch|invalid|unsupported|disagree|verification|expected 206|content-range/i.test(message)
  ) {
    return {
      kind: "verification",
      title: "Artifact verification failed",
      detail: "Received artifact bytes did not satisfy the Kane Fabric verification contract. They are not accepted for display.",
      technical_detail: message,
      retryable: true,
      verified: false,
    };
  }

  return {
    kind: "error",
    title: "Unable to verify Fabric artifacts",
    detail: "The application stopped before accepted Fabric data could be verified.",
    technical_detail: message,
    retryable: true,
    verified: false,
  };
}

export function verificationPresentation({ phase, online = true, failure = null } = {}) {
  const isOnline = boolean(online, "online");

  if (phase === "loading") {
    return {
      kind: "checking",
      title: "Verifying Fabric artifacts",
      detail: "Loading configured artifact sources and verifying their accepted identities before presentation.",
      verified: false,
      retryable: false,
      availability: isOnline ? "online" : "offline",
    };
  }

  if (phase === "verified") {
    return {
      kind: isOnline ? "verified" : "verified-offline",
      title: isOnline ? "Fabric artifacts verified" : "Verified data — browser is offline",
      detail: isOnline
        ? "The displayed substrate and subscription composition passed Kane Fabric verification."
        : "The displayed data was verified before connectivity was lost. No new artifact fetch is being claimed.",
      verified: true,
      retryable: false,
      availability: isOnline ? "online" : "offline",
    };
  }

  if (phase === "failed") {
    if (!failure || typeof failure !== "object") fail("failed phase requires a failure object");
    return {
      kind: String(failure.kind || "error"),
      title: String(failure.title || "Unable to verify Fabric artifacts"),
      detail: String(failure.detail || "Verification did not complete."),
      verified: false,
      retryable: Boolean(failure.retryable),
      availability: isOnline ? "online" : "offline",
    };
  }

  if (phase === "unconfigured") {
    return {
      kind: "unconfigured",
      title: "Artifact source configuration required",
      detail: "No Fabric artifacts have been loaded or verified.",
      verified: false,
      retryable: false,
      availability: isOnline ? "online" : "offline",
    };
  }

  fail(`unsupported verification phase: ${String(phase)}`);
}

export function recoveryStatusPayload({ phase, online = true, failure = null } = {}) {
  const presentation = verificationPresentation({ phase, online, failure });
  return {
    verification_status: presentation.verified ? "verified" : "not-verified",
    availability: presentation.availability,
    failure_kind: phase === "failed" ? presentation.kind : null,
    retry_available: presentation.retryable,
    physical_platform_assumed: false,
  };
}
