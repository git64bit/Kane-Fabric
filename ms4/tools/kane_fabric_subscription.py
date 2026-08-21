#!/usr/bin/env python3
"""MS4 subscription generation, coverage, and geographic-reference contract."""

from __future__ import annotations
import hashlib, re
from collections.abc import Mapping, Sequence, Set
from ms4.tools.kane_fabric_partition import canonical_json_bytes, normalize_jurisdiction, validate_partition_descriptor
from ms4.tools.kane_fabric_scope import normalize_bounds, partition_includes_bounds

OBJECTS_FORMAT="kane-fabric-subscription-objects"
MANIFEST_FORMAT="kane-fabric-subscription-manifest"
VERSION=1
_GENERATION_PREFIX="kfsg1-"
_SLUG_RE=re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SHA_RE=re.compile(r"^[0-9a-f]{64}$")
_PARTITION_RE=re.compile(r"^kfp1-[0-9a-f]{32}$")

class SubscriptionContractError(ValueError): pass

def _exact(value: Mapping[str, object], keys: set[str], label: str) -> None:
    if set(value) != keys:
        raise SubscriptionContractError(
            f"{label} keys mismatch: missing={sorted(keys-set(value))!r} extra={sorted(set(value)-keys)!r}"
        )

def _text(value: object, label: str) -> str:
    if not isinstance(value,str) or not value.strip():
        raise SubscriptionContractError(f"{label} must be a nonempty string")
    return value.strip()

def _slug(value: object, label: str) -> str:
    value=_text(value,label)
    if not _SLUG_RE.fullmatch(value):
        raise SubscriptionContractError(f"{label} must be a lowercase hyphenated key")
    return value

def _sha(value: object, label: str) -> str:
    value=str(value)
    if not _SHA_RE.fullmatch(value):
        raise SubscriptionContractError(f"{label} must be 64 lowercase hex characters")
    return value

def _partition_key(value: object) -> str:
    value=str(value)
    if not _PARTITION_RE.fullmatch(value):
        raise SubscriptionContractError("coverage partition key must match kfp1- followed by 32 lowercase hex characters")
    return value

def _jurisdiction(value: Mapping[str,object]) -> dict[str,str]:
    try: return normalize_jurisdiction(value)
    except ValueError as exc: raise SubscriptionContractError(f"subscription jurisdiction is invalid: {exc}") from exc

def _owner(value: Mapping[str,object]) -> dict[str,str]:
    _exact(value,{"application_key","name"},"subscription owner")
    return {"application_key":_slug(value["application_key"],"owner application_key"),"name":_text(value["name"],"owner name")}

def _rights(value: Mapping[str,object]) -> dict[str,str]:
    _exact(value,{"license","owner"},"subscription rights")
    return {"license":_text(value["license"],"rights license"),"owner":_text(value["owner"],"rights owner")}

def _json(value: object, label: str="payload") -> object:
    if value is None or isinstance(value,(bool,int,float,str)):
        canonical_json_bytes(value); return value
    if isinstance(value,Mapping):
        out={}
        for key,child in value.items():
            if not isinstance(key,str) or not key: raise SubscriptionContractError(f"{label} keys must be nonempty strings")
            out[key]=_json(child,f"{label}.{key}")
        return out
    if isinstance(value,Sequence) and not isinstance(value,(str,bytes,bytearray)):
        return [_json(child,f"{label}[]") for child in value]
    raise SubscriptionContractError(f"{label} contains unsupported value {type(value).__name__}")

def _partition_inventory(partitions: Sequence[Mapping[str,object]], jurisdiction: Mapping[str,object]) -> dict[str,dict[str,object]]:
    if not isinstance(partitions,Sequence) or isinstance(partitions,(str,bytes,bytearray)):
        raise SubscriptionContractError("partition inventory must be an array")
    jurisdiction=_jurisdiction(jurisdiction); out={}
    for item in partitions:
        if not isinstance(item,Mapping): raise SubscriptionContractError("partition inventory entries must be objects")
        try: descriptor=validate_partition_descriptor(item)
        except ValueError as exc: raise SubscriptionContractError(f"partition inventory contains invalid descriptor: {exc}") from exc
        if canonical_json_bytes(descriptor["jurisdiction"]) != canonical_json_bytes(jurisdiction):
            raise SubscriptionContractError("subscription coverage partition jurisdiction differs from manifest jurisdiction")
        key=str(descriptor["partition_key"])
        if key in out: raise SubscriptionContractError("subscription partition inventory contains duplicate partition identity")
        out[key]=descriptor
    return out

def _coverage(value: object, inventory: Mapping[str,Mapping[str,object]]) -> list[str]:
    if not isinstance(value,Sequence) or isinstance(value,(str,bytes,bytearray)):
        raise SubscriptionContractError("coverage_partition_keys must be an array")
    keys=[_partition_key(v) for v in value]
    if not keys: raise SubscriptionContractError("subscription must declare partition coverage")
    if keys != sorted(set(keys)): raise SubscriptionContractError("coverage_partition_keys must be unique and sorted")
    unknown=[k for k in keys if k not in inventory]
    if unknown: raise SubscriptionContractError(f"coverage_partition_keys contain unknown/unverified partition identities: {unknown!r}")
    return keys

def normalize_fabric_reference(value: Mapping[str,object]) -> dict[str,str]:
    _exact(value,{"kind","dataset_key","release_key","source_content_sha256","object_key"},"Fabric geographic reference")
    return {
        "kind":_slug(value["kind"],"Fabric reference kind"),
        "dataset_key":_slug(value["dataset_key"],"Fabric reference dataset_key"),
        "release_key":_text(value["release_key"],"Fabric reference release_key"),
        "source_content_sha256":_sha(value["source_content_sha256"],"Fabric reference source_content_sha256"),
        "object_key":_text(value["object_key"],"Fabric reference object_key"),
    }

def validate_reference_authority(reference: Mapping[str,object], accepted_releases: Mapping[str,Mapping[str,object]], authoritative_object_keys: Mapping[str,Set[str]]) -> None:
    ref=normalize_fabric_reference(reference); release=accepted_releases.get(ref["dataset_key"])
    if release is None: raise SubscriptionContractError("Fabric reference dataset is not an accepted geographic release")
    if release.get("release_key") != ref["release_key"] or release.get("content_sha256") != ref["source_content_sha256"]:
        raise SubscriptionContractError("Fabric reference does not match accepted geographic release identity")
    keys=authoritative_object_keys.get(ref["dataset_key"])
    if keys is None: raise SubscriptionContractError("Fabric reference dataset has no authoritative object-key inventory")
    if ref["object_key"] not in keys: raise SubscriptionContractError("Fabric reference object_key is not an authoritative accepted identity")

def normalize_subscription_object(value: Mapping[str,object]) -> dict[str,object]:
    _exact(value,{"object_key","bounds","geographic_refs","payload"},"subscription object")
    refs=value["geographic_refs"]
    if not isinstance(refs,Sequence) or isinstance(refs,(str,bytes,bytearray)): raise SubscriptionContractError("subscription geographic_refs must be an array")
    normalized=[normalize_fabric_reference(v) for v in refs if isinstance(v,Mapping)]
    if len(normalized) != len(refs): raise SubscriptionContractError("subscription geographic_refs entries must be objects")
    normalized.sort(key=canonical_json_bytes)
    body={"object_key":_text(value["object_key"],"subscription object_key"),"bounds":normalize_bounds(value["bounds"]),"geographic_refs":normalized,"payload":_json(value["payload"])}
    return {**body,"object_sha256":hashlib.sha256(canonical_json_bytes(body)).hexdigest()}

def build_subscription_documents(*,subscription_key:str,owner:Mapping[str,object],jurisdiction:Mapping[str,object],substrate_content_sha256:str,coverage_partitions:Sequence[Mapping[str,object]],rights:Mapping[str,object],objects:Sequence[Mapping[str,object]]) -> tuple[dict[str,object],dict[str,object]]:
    subscription_key=_slug(subscription_key,"subscription_key"); jurisdiction=_jurisdiction(jurisdiction)
    inventory=_partition_inventory(coverage_partitions,jurisdiction)
    if not inventory: raise SubscriptionContractError("subscription must declare partition coverage")
    normalized=sorted((normalize_subscription_object(v) for v in objects),key=lambda v:str(v["object_key"]))
    if len({v["object_key"] for v in normalized}) != len(normalized): raise SubscriptionContractError("subscription object_key values must be unique")
    objects_doc={"format":OBJECTS_FORMAT,"version":VERSION,"subscription_key":subscription_key,"objects":normalized}
    data=canonical_json_bytes(objects_doc)
    component={"path":"objects.json","byte_length":len(data),"sha256":hashlib.sha256(data).hexdigest(),"object_count":len(normalized)}
    body={"format":MANIFEST_FORMAT,"version":VERSION,"subscription_key":subscription_key,"owner":_owner(owner),"jurisdiction":jurisdiction,
          "substrate_content_sha256":_sha(substrate_content_sha256,"substrate_content_sha256"),"coverage_partition_keys":sorted(inventory),
          "rights":_rights(rights),"component":component,"dependencies":[]}
    digest=hashlib.sha256(canonical_json_bytes(body)).hexdigest()
    return {**body,"generation_sha256":digest,"generation_key":_GENERATION_PREFIX+digest[:32]},objects_doc

def validate_subscription_documents(manifest:Mapping[str,object],objects_doc:Mapping[str,object],*,partition_descriptors:Sequence[Mapping[str,object]],accepted_releases:Mapping[str,Mapping[str,object]]|None=None,authoritative_object_keys:Mapping[str,Set[str]]|None=None)->None:
    _exact(manifest,{"format","version","subscription_key","owner","jurisdiction","substrate_content_sha256","coverage_partition_keys","rights","component","dependencies","generation_sha256","generation_key"},"subscription manifest")
    _exact(objects_doc,{"format","version","subscription_key","objects"},"subscription objects document")
    if manifest["format"]!=MANIFEST_FORMAT or manifest["version"]!=VERSION: raise SubscriptionContractError("subscription manifest format/version is unsupported")
    if objects_doc["format"]!=OBJECTS_FORMAT or objects_doc["version"]!=VERSION: raise SubscriptionContractError("subscription objects format/version is unsupported")
    key=_slug(manifest["subscription_key"],"subscription_key")
    if key != objects_doc["subscription_key"]: raise SubscriptionContractError("subscription manifest/object keys disagree")
    if not isinstance(manifest["owner"],Mapping) or not isinstance(manifest["jurisdiction"],Mapping) or not isinstance(manifest["rights"],Mapping):
        raise SubscriptionContractError("subscription owner, jurisdiction, and rights must be objects")
    owner=_owner(manifest["owner"]); jurisdiction=_jurisdiction(manifest["jurisdiction"]); rights=_rights(manifest["rights"])
    substrate=_sha(manifest["substrate_content_sha256"],"substrate_content_sha256")
    if manifest["dependencies"] != []: raise SubscriptionContractError("v1 subscription dependencies must be the empty array")
    inventory=_partition_inventory(partition_descriptors,jurisdiction); coverage=_coverage(manifest["coverage_partition_keys"],inventory)
    component=manifest["component"]
    if not isinstance(component,Mapping): raise SubscriptionContractError("subscription component descriptor is invalid")
    _exact(component,{"path","byte_length","sha256","object_count"},"subscription component")
    if component["path"]!="objects.json": raise SubscriptionContractError("subscription component path must be objects.json")
    if isinstance(component["byte_length"],bool) or not isinstance(component["byte_length"],int) or component["byte_length"]<0: raise SubscriptionContractError("subscription component byte_length is invalid")
    csha=_sha(component["sha256"],"subscription component sha256")
    if isinstance(component["object_count"],bool) or not isinstance(component["object_count"],int) or component["object_count"]<0: raise SubscriptionContractError("subscription component object_count is invalid")
    objects=objects_doc["objects"]
    if not isinstance(objects,list) or component["object_count"]!=len(objects): raise SubscriptionContractError("subscription object count disagrees with manifest")
    data=canonical_json_bytes(objects_doc)
    if component["byte_length"]!=len(data) or csha!=hashlib.sha256(data).hexdigest(): raise SubscriptionContractError("subscription component bytes disagree with manifest")
    seen=set()
    for item in objects:
        if not isinstance(item,Mapping): raise SubscriptionContractError("subscription object entry is invalid")
        _exact(item,{"object_key","bounds","geographic_refs","payload","object_sha256"},"subscription object entry")
        normalized=normalize_subscription_object({k:item[k] for k in ("object_key","bounds","geographic_refs","payload")})
        if normalized != dict(item): raise SubscriptionContractError("subscription object identity is invalid")
        if item["object_key"] in seen: raise SubscriptionContractError("subscription object_key values must be unique")
        seen.add(item["object_key"])
    if (accepted_releases is None)!=(authoritative_object_keys is None): raise SubscriptionContractError("accepted release and authoritative object-key inventories must be supplied together")
    if accepted_releases is not None and authoritative_object_keys is not None:
        for item in objects:
            for ref in item["geographic_refs"]: validate_reference_authority(ref,accepted_releases,authoritative_object_keys)
    body={"format":MANIFEST_FORMAT,"version":VERSION,"subscription_key":key,"owner":owner,"jurisdiction":jurisdiction,"substrate_content_sha256":substrate,
          "coverage_partition_keys":coverage,"rights":rights,"component":dict(component),"dependencies":[]}
    digest=hashlib.sha256(canonical_json_bytes(body)).hexdigest()
    if manifest["generation_sha256"]!=digest or manifest["generation_key"]!=_GENERATION_PREFIX+digest[:32]:
        raise SubscriptionContractError("subscription generation identity is invalid")

def select_objects_for_partition(partition:Mapping[str,object],manifest:Mapping[str,object],objects_doc:Mapping[str,object])->list[dict[str,object]]:
    try: descriptor=validate_partition_descriptor(partition)
    except ValueError as exc: raise SubscriptionContractError(f"partition is invalid: {exc}") from exc
    coverage=manifest.get("coverage_partition_keys")
    if not isinstance(coverage,list): raise SubscriptionContractError("subscription coverage_partition_keys are invalid")
    keys=[_partition_key(v) for v in coverage]
    if keys!=sorted(set(keys)): raise SubscriptionContractError("coverage_partition_keys must be unique and sorted")
    if descriptor["partition_key"] not in keys: raise SubscriptionContractError("partition is not declared in subscription coverage")
    if manifest.get("subscription_key") != objects_doc.get("subscription_key"): raise SubscriptionContractError("subscription manifest/object keys disagree")
    objects=objects_doc.get("objects")
    if not isinstance(objects,list): raise SubscriptionContractError("subscription objects array is invalid")
    out=[]
    for item in objects:
        if not isinstance(item,dict) or not isinstance(item.get("bounds"),list): raise SubscriptionContractError("subscription object is invalid")
        if partition_includes_bounds(descriptor,item["bounds"]): out.append(item)
    return out
