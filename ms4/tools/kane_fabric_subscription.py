#!/usr/bin/env python3
"""MS4 subscription-generation and geographic-reference contract."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence

from ms4.tools.kane_fabric_partition import canonical_json_bytes, normalize_jurisdiction, validate_partition_descriptor
from ms4.tools.kane_fabric_scope import normalize_bounds, partition_includes_bounds

OBJECTS_FORMAT = "kane-fabric-subscription-objects"
MANIFEST_FORMAT = "kane-fabric-subscription-manifest"
VERSION = 1
_GENERATION_PREFIX = "kfsg1-"
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class SubscriptionContractError(ValueError):
    pass


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SubscriptionContractError(f"{label} must be a nonempty string")
    return value.strip()


def _slug(value: object, label: str) -> str:
    text = _text(value, label)
    if not _SLUG_RE.fullmatch(text):
        raise SubscriptionContractError(f"{label} must be a lowercase hyphenated key")
    return text


def _sha(value: object, label: str) -> str:
    text = str(value)
    if not _SHA256_RE.fullmatch(text):
        raise SubscriptionContractError(f"{label} must be 64 lowercase hex characters")
    return text


def _normalize_json(value: object, label: str = "payload") -> object:
    if value is None or isinstance(value, (bool, int, float, str)):
        canonical_json_bytes(value)
        return value
    if isinstance(value, Mapping):
        result: dict[str, object] = {}
        for key, child in value.items():
            if not isinstance(key, str) or not key:
                raise SubscriptionContractError(f"{label} keys must be nonempty strings")
            result[key] = _normalize_json(child, f"{label}.{key}")
        return result
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return [_normalize_json(item, f"{label}[]") for item in value]
    raise SubscriptionContractError(f"{label} contains unsupported value {type(value).__name__}")


def normalize_fabric_reference(value: Mapping[str, object]) -> dict[str, str]:
    required = {"kind", "dataset_key", "release_key", "source_content_sha256", "object_key"}
    if set(value) != required:
        raise SubscriptionContractError("Fabric geographic reference keys are invalid")
    return {
        "kind": _slug(value["kind"], "Fabric reference kind"),
        "dataset_key": _slug(value["dataset_key"], "Fabric reference dataset_key"),
        "release_key": _text(value["release_key"], "Fabric reference release_key"),
        "source_content_sha256": _sha(value["source_content_sha256"], "Fabric reference source_content_sha256"),
        "object_key": _text(value["object_key"], "Fabric reference object_key"),
    }


def validate_reference_authority(reference: Mapping[str, object], accepted_releases: Mapping[str, Mapping[str, object]]) -> None:
    normalized = normalize_fabric_reference(reference)
    release = accepted_releases.get(normalized["dataset_key"])
    if release is None:
        raise SubscriptionContractError("Fabric reference dataset is not an accepted geographic release")
    if release.get("release_key") != normalized["release_key"] or release.get("content_sha256") != normalized["source_content_sha256"]:
        raise SubscriptionContractError("Fabric reference does not match accepted geographic release identity")


def normalize_subscription_object(value: Mapping[str, object]) -> dict[str, object]:
    required = {"object_key", "bounds", "geographic_refs", "payload"}
    if set(value) != required:
        raise SubscriptionContractError("subscription object keys are invalid")
    refs = value["geographic_refs"]
    if not isinstance(refs, Sequence) or isinstance(refs, (str, bytes, bytearray)):
        raise SubscriptionContractError("subscription geographic_refs must be an array")
    normalized_refs = sorted(
        [normalize_fabric_reference(item) for item in refs if isinstance(item, Mapping)],
        key=lambda item: canonical_json_bytes(item),
    )
    if len(normalized_refs) != len(refs):
        raise SubscriptionContractError("subscription geographic_refs entries must be objects")
    body = {
        "object_key": _text(value["object_key"], "subscription object_key"),
        "bounds": normalize_bounds(value["bounds"]),
        "geographic_refs": normalized_refs,
        "payload": _normalize_json(value["payload"]),
    }
    return {**body, "object_sha256": hashlib.sha256(canonical_json_bytes(body)).hexdigest()}


def build_subscription_documents(
    *,
    subscription_key: str,
    owner: Mapping[str, object],
    jurisdiction: Mapping[str, object],
    substrate_content_sha256: str,
    coverage_partition_keys: Sequence[str],
    rights: Mapping[str, object],
    objects: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], dict[str, object]]:
    subscription_key = _slug(subscription_key, "subscription_key")
    if set(owner) != {"application_key", "name"}:
        raise SubscriptionContractError("subscription owner keys are invalid")
    owner_doc = {
        "application_key": _slug(owner["application_key"], "owner application_key"),
        "name": _text(owner["name"], "owner name"),
    }
    if set(rights) != {"license", "owner"}:
        raise SubscriptionContractError("subscription rights keys are invalid")
    rights_doc = {
        "license": _text(rights["license"], "rights license"),
        "owner": _text(rights["owner"], "rights owner"),
    }
    jurisdiction_doc = normalize_jurisdiction(jurisdiction)
    substrate_sha = _sha(substrate_content_sha256, "substrate_content_sha256")
    coverage = sorted({_text(item, "coverage partition key") for item in coverage_partition_keys})
    if not coverage:
        raise SubscriptionContractError("subscription must declare partition coverage")
    normalized_objects = sorted(
        [normalize_subscription_object(item) for item in objects],
        key=lambda item: str(item["object_key"]),
    )
    if len({item["object_key"] for item in normalized_objects}) != len(normalized_objects):
        raise SubscriptionContractError("subscription object_key values must be unique")
    objects_doc = {
        "format": OBJECTS_FORMAT,
        "version": VERSION,
        "subscription_key": subscription_key,
        "objects": normalized_objects,
    }
    objects_bytes = canonical_json_bytes(objects_doc)
    component = {
        "path": "objects.json",
        "byte_length": len(objects_bytes),
        "sha256": hashlib.sha256(objects_bytes).hexdigest(),
        "object_count": len(normalized_objects),
    }
    generation_body = {
        "format": MANIFEST_FORMAT,
        "version": VERSION,
        "subscription_key": subscription_key,
        "owner": owner_doc,
        "jurisdiction": jurisdiction_doc,
        "substrate_content_sha256": substrate_sha,
        "coverage_partition_keys": coverage,
        "rights": rights_doc,
        "component": component,
        "dependencies": [],
    }
    generation_sha = hashlib.sha256(canonical_json_bytes(generation_body)).hexdigest()
    manifest = {
        **generation_body,
        "generation_sha256": generation_sha,
        "generation_key": _GENERATION_PREFIX + generation_sha[:32],
    }
    return manifest, objects_doc


def validate_subscription_documents(
    manifest: Mapping[str, object],
    objects_doc: Mapping[str, object],
    *,
    accepted_releases: Mapping[str, Mapping[str, object]] | None = None,
) -> None:
    if manifest.get("format") != MANIFEST_FORMAT or manifest.get("version") != VERSION:
        raise SubscriptionContractError("subscription manifest format/version is unsupported")
    if objects_doc.get("format") != OBJECTS_FORMAT or objects_doc.get("version") != VERSION:
        raise SubscriptionContractError("subscription objects format/version is unsupported")
    if manifest.get("subscription_key") != objects_doc.get("subscription_key"):
        raise SubscriptionContractError("subscription manifest/object keys disagree")
    objects_bytes = canonical_json_bytes(objects_doc)
    component = manifest.get("component")
    if not isinstance(component, Mapping):
        raise SubscriptionContractError("subscription component descriptor is invalid")
    if component.get("path") != "objects.json" or component.get("byte_length") != len(objects_bytes) or component.get("sha256") != hashlib.sha256(objects_bytes).hexdigest():
        raise SubscriptionContractError("subscription component bytes disagree with manifest")
    objects = objects_doc.get("objects")
    if not isinstance(objects, list) or component.get("object_count") != len(objects):
        raise SubscriptionContractError("subscription object count disagrees with manifest")
    for item in objects:
        if not isinstance(item, Mapping) or set(item) != {"object_key", "bounds", "geographic_refs", "payload", "object_sha256"}:
            raise SubscriptionContractError("subscription object entry is invalid")
        object_body = {key: item[key] for key in ("object_key", "bounds", "geographic_refs", "payload")}
        normalized = normalize_subscription_object(object_body)
        if normalized != dict(item):
            raise SubscriptionContractError("subscription object identity is invalid")
    if accepted_releases is not None:
        for item in objects:
            if not isinstance(item, Mapping):
                raise SubscriptionContractError("subscription object entry is invalid")
            refs = item.get("geographic_refs")
            if not isinstance(refs, list):
                raise SubscriptionContractError("subscription geographic_refs are invalid")
            for reference in refs:
                if not isinstance(reference, Mapping):
                    raise SubscriptionContractError("subscription geographic reference is invalid")
                validate_reference_authority(reference, accepted_releases)
    body = {key: value for key, value in manifest.items() if key not in {"generation_sha256", "generation_key"}}
    expected = hashlib.sha256(canonical_json_bytes(body)).hexdigest()
    if manifest.get("generation_sha256") != expected or manifest.get("generation_key") != _GENERATION_PREFIX + expected[:32]:
        raise SubscriptionContractError("subscription generation identity is invalid")


def select_objects_for_partition(
    partition: Mapping[str, object], objects_doc: Mapping[str, object]
) -> list[dict[str, object]]:
    validate_partition_descriptor(partition)
    objects = objects_doc.get("objects")
    if not isinstance(objects, list):
        raise SubscriptionContractError("subscription objects array is invalid")
    selected: list[dict[str, object]] = []
    for item in objects:
        if not isinstance(item, dict) or not isinstance(item.get("bounds"), list):
            raise SubscriptionContractError("subscription object is invalid")
        if partition_includes_bounds(partition, item["bounds"]):
            selected.append(item)
    return selected
