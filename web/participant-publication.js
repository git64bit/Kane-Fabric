import {
  geographicReferenceKey,
  validateParticipantPublication,
} from "../administration/contracts/participant-publication-v1.mjs";

export class ParticipantCompositionError extends Error {
  constructor(message, path = "participant publication") {
    super(`${path}: ${message}`);
    this.name = "ParticipantCompositionError";
    this.path = path;
  }
}

function requireCompositionResult(result) {
  if (!result || typeof result !== "object" || Array.isArray(result)) {
    throw new ParticipantCompositionError("verified composition result must be an object", "county composition");
  }
  if (!Array.isArray(result.subscriptions)) {
    throw new ParticipantCompositionError("subscriptions must be an array", "county composition");
  }
  return result;
}

function descriptorRegistryValue(registry, descriptorId) {
  if (registry instanceof Map) return registry.get(descriptorId);
  if (registry && typeof registry === "object" && !Array.isArray(registry)) return registry[descriptorId];
  throw new ParticipantCompositionError("descriptor registry must be a Map or object", "descriptor registry");
}

export function acceptedGeographicReferenceKeys(result) {
  requireCompositionResult(result);
  const accepted = new Set();
  result.subscriptions.forEach((subscription) => {
    if (!Array.isArray(subscription?.objects)) {
      throw new ParticipantCompositionError("subscription objects must be an array", "county composition");
    }
    subscription.objects.forEach((object) => {
      if (!Array.isArray(object?.geographic_refs)) return;
      object.geographic_refs.forEach((ref) => accepted.add(geographicReferenceKey(ref)));
    });
  });
  return accepted;
}

export function composeParticipantPublication(publicationValue, result, descriptorRegistry) {
  const publication = validateParticipantPublication(publicationValue);
  const acceptedRefs = acceptedGeographicReferenceKeys(result);

  return publication.descriptor_instances.map((instance, index) => {
    const path = `$.descriptor_instances[${index}]`;
    const descriptor = descriptorRegistryValue(descriptorRegistry, instance.descriptor_id);
    if (!descriptor) {
      throw new ParticipantCompositionError(
        `descriptor ${instance.descriptor_id} is not present in the administrative baseline`,
        `${path}.descriptor_id`,
      );
    }
    if (descriptor.descriptor_id !== instance.descriptor_id || descriptor.descriptor_version !== instance.descriptor_version) {
      throw new ParticipantCompositionError(
        `descriptor ${instance.descriptor_id} version ${instance.descriptor_version} does not match the loaded administrative descriptor`,
        `${path}.descriptor_version`,
      );
    }

    instance.geographic_refs.forEach((ref, refIndex) => {
      if (!acceptedRefs.has(geographicReferenceKey(ref))) {
        throw new ParticipantCompositionError(
          "geographic reference is not present in the verified county composition",
          `${path}.geographic_refs[${refIndex}]`,
        );
      }
    });

    return { descriptor, instance };
  });
}

export async function loadParticipantPublication(url, { fetchImpl = fetch } = {}) {
  const response = await fetchImpl(url, { cache: "no-store" });
  if (!response.ok) {
    throw new ParticipantCompositionError(`GET ${url} returned HTTP ${response.status}`, "participant source");
  }
  let publication;
  try {
    publication = await response.json();
  } catch (error) {
    throw new ParticipantCompositionError(`response is not valid JSON: ${error.message}`, "participant source");
  }
  return validateParticipantPublication(publication);
}
