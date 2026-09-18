import { validateParticipantPublication } from "./participant-publication-v1.mjs";

export const PARTICIPANT_PUBLICATION_GENERATION_PREFIX = "kfpg1-";

export class ParticipantPublicationGenerationError extends Error {
  constructor(message, path = "$") {
    super(`${path}: ${message}`);
    this.name = "ParticipantPublicationGenerationError";
    this.path = path;
  }
}

function canonicalJson(value, path) {
  if (value === null) return "null";

  if (typeof value === "string" || typeof value === "boolean") {
    return JSON.stringify(value);
  }

  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      throw new ParticipantPublicationGenerationError("number must be finite", path);
    }
    return JSON.stringify(value);
  }

  if (Array.isArray(value)) {
    const entries = [];
    for (let index = 0; index < value.length; index += 1) {
      if (!(index in value)) {
        throw new ParticipantPublicationGenerationError("sparse arrays are not canonical JSON", `${path}[${index}]`);
      }
      entries.push(canonicalJson(value[index], `${path}[${index}]`));
    }
    return `[${entries.join(",")}]`;
  }

  if (typeof value === "object") {
    const prototype = Object.getPrototypeOf(value);
    if (prototype !== Object.prototype && prototype !== null) {
      throw new ParticipantPublicationGenerationError("must be a plain JSON object", path);
    }
    const entries = Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key], `${path}.${key}`)}`);
    return `{${entries.join(",")}}`;
  }

  throw new ParticipantPublicationGenerationError(
    `unsupported JSON value type ${typeof value}`,
    path,
  );
}

export function canonicalParticipantPublicationJson(publicationValue) {
  const publication = validateParticipantPublication(publicationValue);
  return canonicalJson(publication, "$");
}

export async function participantPublicationGenerationIdentity(
  publicationValue,
  cryptoProvider = globalThis.crypto,
) {
  const canonical = canonicalParticipantPublicationJson(publicationValue);
  if (!cryptoProvider?.subtle) {
    throw new ParticipantPublicationGenerationError("Web Crypto SHA-256 is unavailable");
  }
  const bytes = new TextEncoder().encode(canonical);
  const digestBytes = await cryptoProvider.subtle.digest("SHA-256", bytes);
  const generationSha256 = Array.from(
    new Uint8Array(digestBytes),
    (byte) => byte.toString(16).padStart(2, "0"),
  ).join("");
  return {
    generation_sha256: generationSha256,
    generation_key: `${PARTICIPANT_PUBLICATION_GENERATION_PREFIX}${generationSha256.slice(0, 32)}`,
  };
}
