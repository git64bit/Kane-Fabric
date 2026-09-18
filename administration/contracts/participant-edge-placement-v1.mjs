import {
  PARTICIPANT_PUBLICATION_GENERATION_PREFIX,
} from "./participant-publication-generation-v1.mjs";

const SHA_RE = /^[0-9a-f]{64}$/;
const GENERATION_KEY_RE = /^kfpg1-[0-9a-f]{32}$/;

export class ParticipantEdgePlacementError extends Error {
  constructor(message, path = "$") {
    super(`${path}: ${message}`);
    this.name = "ParticipantEdgePlacementError";
    this.path = path;
  }
}

function requireObject(value, path) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new ParticipantEdgePlacementError("must be an object", path);
  }
  return value;
}

function requireExactKeys(value, allowedKeys, path) {
  const allowed = new Set(allowedKeys);
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) {
      throw new ParticipantEdgePlacementError(
        `unexpected field ${JSON.stringify(key)}`,
        `${path}.${key}`,
      );
    }
  }
  for (const key of allowedKeys) {
    if (!(key in value)) {
      throw new ParticipantEdgePlacementError("required field is missing", `${path}.${key}`);
    }
  }
}

function normalizeGeneration(value, path) {
  const generation = requireObject(value, path);
  requireExactKeys(generation, ["generation_sha256", "generation_key"], path);

  if (typeof generation.generation_sha256 !== "string" || !SHA_RE.test(generation.generation_sha256)) {
    throw new ParticipantEdgePlacementError(
      "must be 64 lowercase hexadecimal characters",
      `${path}.generation_sha256`,
    );
  }
  if (typeof generation.generation_key !== "string" || !GENERATION_KEY_RE.test(generation.generation_key)) {
    throw new ParticipantEdgePlacementError(
      "must match kfpg1- followed by 32 lowercase hexadecimal characters",
      `${path}.generation_key`,
    );
  }

  const expectedKey =
    `${PARTICIPANT_PUBLICATION_GENERATION_PREFIX}${generation.generation_sha256.slice(0, 32)}`;
  if (generation.generation_key !== expectedKey) {
    throw new ParticipantEdgePlacementError(
      "does not match generation_sha256",
      `${path}.generation_key`,
    );
  }

  return {
    generation_sha256: generation.generation_sha256,
    generation_key: generation.generation_key,
  };
}

function canonicalJson(value) {
  if (Array.isArray(value)) {
    return `[${value.map((entry) => canonicalJson(entry)).join(",")}]`;
  }
  if (value !== null && typeof value === "object") {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

async function sha256Canonical(value, cryptoProvider) {
  if (!cryptoProvider?.subtle) {
    throw new ParticipantEdgePlacementError("Web Crypto SHA-256 is unavailable");
  }
  const bytes = new TextEncoder().encode(canonicalJson(value));
  const digest = await cryptoProvider.subtle.digest("SHA-256", bytes);
  return Array.from(
    new Uint8Array(digest),
    (byte) => byte.toString(16).padStart(2, "0"),
  ).join("");
}

export async function buildParticipantEdgePlacement(
  publicationGenerationValue,
  cryptoProvider = globalThis.crypto,
) {
  const publicationGeneration = normalizeGeneration(
    publicationGenerationValue,
    "$.publication_generation",
  );
  const body = {
    format: "kane-fabric-participant-edge-placement",
    format_version: 1,
    publication_generation: publicationGeneration,
  };
  return {
    ...body,
    logical_placement_sha256: await sha256Canonical(body, cryptoProvider),
  };
}

export async function validateParticipantEdgePlacement(
  value,
  cryptoProvider = globalThis.crypto,
) {
  const placement = requireObject(value, "$");
  requireExactKeys(
    placement,
    ["format", "format_version", "publication_generation", "logical_placement_sha256"],
    "$",
  );
  if (placement.format !== "kane-fabric-participant-edge-placement") {
    throw new ParticipantEdgePlacementError("unsupported format", "$.format");
  }
  if (placement.format_version !== 1) {
    throw new ParticipantEdgePlacementError("unsupported format_version", "$.format_version");
  }

  const publicationGeneration = normalizeGeneration(
    placement.publication_generation,
    "$.publication_generation",
  );
  if (typeof placement.logical_placement_sha256 !== "string" ||
      !SHA_RE.test(placement.logical_placement_sha256)) {
    throw new ParticipantEdgePlacementError(
      "must be 64 lowercase hexadecimal characters",
      "$.logical_placement_sha256",
    );
  }

  const body = {
    format: placement.format,
    format_version: placement.format_version,
    publication_generation: publicationGeneration,
  };
  const expected = await sha256Canonical(body, cryptoProvider);
  if (placement.logical_placement_sha256 !== expected) {
    throw new ParticipantEdgePlacementError(
      "does not match canonical logical placement content",
      "$.logical_placement_sha256",
    );
  }

  return placement;
}
