export class AssociationUnitIdentityError extends Error {
  constructor(message, path = "$") {
    super(`${path}: ${message}`);
    this.name = "AssociationUnitIdentityError";
    this.path = path;
  }
}

function requireObject(value, path) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new AssociationUnitIdentityError("must be an object", path);
  }
  return value;
}

function requireExactKeys(value, allowedKeys, path) {
  const allowed = new Set(allowedKeys);
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) {
      throw new AssociationUnitIdentityError(`unexpected field ${JSON.stringify(key)}`, `${path}.${key}`);
    }
  }
}

function requireString(value, path) {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new AssociationUnitIdentityError("must be a non-empty string", path);
  }
  return value;
}

function requireJurisdictionCode(value, path) {
  requireString(value, path);
  if (!/^[A-Z]{2}$/.test(value)) {
    throw new AssociationUnitIdentityError("must be exactly two uppercase ASCII letters", path);
  }
  return value;
}

export function validateAssociationUnitIdentity(value) {
  const contract = requireObject(value, "$");
  requireExactKeys(contract, ["format", "format_version", "association_anchor", "unit_anchors"], "$");

  if (contract.format !== "kane-fabric-association-unit-identity") {
    throw new AssociationUnitIdentityError("unsupported format", "$.format");
  }
  if (contract.format_version !== 1) {
    throw new AssociationUnitIdentityError("unsupported format_version", "$.format_version");
  }

  const association = requireObject(contract.association_anchor, "$.association_anchor");
  requireExactKeys(
    association,
    ["jurisdiction", "recording_authority_reference", "original_declaration_recording_reference"],
    "$.association_anchor",
  );

  const jurisdiction = requireObject(association.jurisdiction, "$.association_anchor.jurisdiction");
  requireExactKeys(jurisdiction, ["country_code", "state_code"], "$.association_anchor.jurisdiction");
  requireJurisdictionCode(jurisdiction.country_code, "$.association_anchor.jurisdiction.country_code");
  requireJurisdictionCode(jurisdiction.state_code, "$.association_anchor.jurisdiction.state_code");
  requireString(association.recording_authority_reference, "$.association_anchor.recording_authority_reference");
  requireString(
    association.original_declaration_recording_reference,
    "$.association_anchor.original_declaration_recording_reference",
  );

  if (!Array.isArray(contract.unit_anchors)) {
    throw new AssociationUnitIdentityError("must be an array", "$.unit_anchors");
  }

  const seenUnits = new Set();
  contract.unit_anchors.forEach((unitValue, index) => {
    const path = `$.unit_anchors[${index}]`;
    const unit = requireObject(unitValue, path);
    requireExactKeys(unit, ["recorded_unit_designation", "recorded_unit_reference"], path);
    requireString(unit.recorded_unit_designation, `${path}.recorded_unit_designation`);
    requireString(unit.recorded_unit_reference, `${path}.recorded_unit_reference`);

    const exactAnchor = JSON.stringify([unit.recorded_unit_designation, unit.recorded_unit_reference]);
    if (seenUnits.has(exactAnchor)) {
      throw new AssociationUnitIdentityError("duplicates an earlier exact unit anchor", path);
    }
    seenUnits.add(exactAnchor);
  });

  return contract;
}
