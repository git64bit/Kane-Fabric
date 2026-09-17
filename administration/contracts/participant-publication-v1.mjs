import { validateAssociationUnitIdentity } from "./association-unit-identity-v1.mjs";

const SHA_RE = /^[0-9a-f]{64}$/;
const SLUG_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

export class ParticipantPublicationError extends Error {
  constructor(message, path = "$") {
    super(`${path}: ${message}`);
    this.name = "ParticipantPublicationError";
    this.path = path;
  }
}

function requireObject(value, path) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new ParticipantPublicationError("must be an object", path);
  }
  return value;
}

function requireExactKeys(value, allowedKeys, path) {
  const allowed = new Set(allowedKeys);
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) throw new ParticipantPublicationError(`unexpected field ${JSON.stringify(key)}`, `${path}.${key}`);
  }
  for (const key of allowedKeys) {
    if (!(key in value)) throw new ParticipantPublicationError("required field is missing", `${path}.${key}`);
  }
}

function requireString(value, path) {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new ParticipantPublicationError("must be a non-empty string", path);
  }
  return value;
}

function requirePositiveInteger(value, path) {
  if (!Number.isInteger(value) || value < 1) throw new ParticipantPublicationError("must be a positive integer", path);
  return value;
}

function unitKey(unit) {
  return JSON.stringify([unit.recorded_unit_designation, unit.recorded_unit_reference]);
}

export function geographicReferenceKey(ref) {
  return JSON.stringify([ref.kind, ref.dataset_key, ref.release_key, ref.source_content_sha256, ref.object_key]);
}

function validateGeographicReference(value, path) {
  const ref = requireObject(value, path);
  requireExactKeys(ref, ["kind", "dataset_key", "release_key", "source_content_sha256", "object_key"], path);
  requireString(ref.kind, `${path}.kind`);
  requireString(ref.dataset_key, `${path}.dataset_key`);
  requireString(ref.release_key, `${path}.release_key`);
  requireString(ref.source_content_sha256, `${path}.source_content_sha256`);
  requireString(ref.object_key, `${path}.object_key`);
  if (!SLUG_RE.test(ref.kind)) throw new ParticipantPublicationError("must be a lowercase hyphenated slug", `${path}.kind`);
  if (!SLUG_RE.test(ref.dataset_key)) throw new ParticipantPublicationError("must be a lowercase hyphenated slug", `${path}.dataset_key`);
  if (!SHA_RE.test(ref.source_content_sha256)) throw new ParticipantPublicationError("must be 64 lowercase hexadecimal characters", `${path}.source_content_sha256`);
  return ref;
}

function validateSubject(subjectValue, path, identity) {
  const subject = requireObject(subjectValue, path);
  requireString(subject.kind, `${path}.kind`);
  if (subject.kind === "association") {
    requireExactKeys(subject, ["kind"], path);
    return subject;
  }
  if (subject.kind === "unit") {
    requireExactKeys(subject, ["kind", "unit_anchor"], path);
    const unit = requireObject(subject.unit_anchor, `${path}.unit_anchor`);
    requireExactKeys(unit, ["recorded_unit_designation", "recorded_unit_reference"], `${path}.unit_anchor`);
    requireString(unit.recorded_unit_designation, `${path}.unit_anchor.recorded_unit_designation`);
    requireString(unit.recorded_unit_reference, `${path}.unit_anchor.recorded_unit_reference`);
    const known = new Set(identity.unit_anchors.map(unitKey));
    if (!known.has(unitKey(unit))) {
      throw new ParticipantPublicationError("unit anchor is not present in association_unit_identity.unit_anchors", `${path}.unit_anchor`);
    }
    return subject;
  }
  throw new ParticipantPublicationError("must be association or unit", `${path}.kind`);
}

function subjectKey(subject) {
  return subject.kind === "association" ? "association" : `unit:${unitKey(subject.unit_anchor)}`;
}

export function validateParticipantPublication(value) {
  const publication = requireObject(value, "$");
  requireExactKeys(publication, ["format", "format_version", "association_unit_identity", "descriptor_instances"], "$");
  if (publication.format !== "kane-fabric-participant-publication") {
    throw new ParticipantPublicationError("unsupported format", "$.format");
  }
  if (publication.format_version !== 1) {
    throw new ParticipantPublicationError("unsupported format_version", "$.format_version");
  }

  try {
    validateAssociationUnitIdentity(publication.association_unit_identity);
  } catch (error) {
    const nestedPath = typeof error?.path === "string" && error.path.startsWith("$")
      ? `$.association_unit_identity${error.path.slice(1)}`
      : "$.association_unit_identity";
    throw new ParticipantPublicationError(String(error?.message ?? error), nestedPath);
  }

  if (!Array.isArray(publication.descriptor_instances) || publication.descriptor_instances.length === 0) {
    throw new ParticipantPublicationError("must be a non-empty array", "$.descriptor_instances");
  }

  const seenInstances = new Set();
  publication.descriptor_instances.forEach((instanceValue, index) => {
    const path = `$.descriptor_instances[${index}]`;
    const instance = requireObject(instanceValue, path);
    requireExactKeys(instance, ["descriptor_id", "descriptor_version", "subject", "geographic_refs", "data"], path);
    requireString(instance.descriptor_id, `${path}.descriptor_id`);
    requirePositiveInteger(instance.descriptor_version, `${path}.descriptor_version`);
    const subject = validateSubject(instance.subject, `${path}.subject`, publication.association_unit_identity);
    requireObject(instance.data, `${path}.data`);

    if (!Array.isArray(instance.geographic_refs) || instance.geographic_refs.length === 0) {
      throw new ParticipantPublicationError("must be a non-empty array", `${path}.geographic_refs`);
    }
    const seenRefs = new Set();
    instance.geographic_refs.forEach((refValue, refIndex) => {
      const refPath = `${path}.geographic_refs[${refIndex}]`;
      const ref = validateGeographicReference(refValue, refPath);
      const key = geographicReferenceKey(ref);
      if (seenRefs.has(key)) throw new ParticipantPublicationError("duplicates an earlier exact geographic reference", refPath);
      seenRefs.add(key);
    });

    const key = JSON.stringify([instance.descriptor_id, instance.descriptor_version, subjectKey(subject)]);
    if (seenInstances.has(key)) {
      throw new ParticipantPublicationError("duplicates an earlier descriptor instance for the same subject", path);
    }
    seenInstances.add(key);
  });

  return publication;
}
