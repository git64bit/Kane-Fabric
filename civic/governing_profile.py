from __future__ import annotations

import calendar
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
from typing import Protocol
import unicodedata

from civic.codec import CivicCodecError, decode_deterministic, encode_deterministic
from civic.epoch_manifest import CivicManifestError, validate_epoch_manifest


FORMAT = "kane-civic-governing-profile"
VERSION = 1

SOURCE_SET_FORMAT = "kane-civic-governing-source-set"
SOURCE_SET_VERSION = 1

PROFILE_MEDIA_TYPE = "application/kane-civic-governing-profile+cbor"
PROFILE_SEMANTIC_ROLE = "governing-profile"

SHA256_BYTES = 32
UINT64_MAX = 0xFFFFFFFFFFFFFFFF

TOP_LEVEL_FIELDS = {
    "format",
    "version",
    "profile_id",
    "source_set_sha256",
    "standing_classes",
    "qualification_paths",
    "participation_policies",
}

SOURCE_SET_FIELDS = {
    "format",
    "version",
    "sources",
}

SOURCE_SET_SOURCE_FIELDS = {
    "source_id",
    "role",
    "sha256",
    "byte_length",
    "media_type",
}

PROVENANCE_FIELDS = {
    "kind",
    "source_ids",
}

STANDING_CLASS_FIELDS = {
    "standing_class",
    "qualification_path_ids",
    "participation_required",
    "participation_policy_ids",
    "allow_open_ended_standing",
    "maximum_standing_duration",
}

STANDING_CLASS_FIELDS_WITH_PROVENANCE = STANDING_CLASS_FIELDS | {"provenance"}

DURATION_FIELDS = {
    "kind",
    "value",
}

QUALIFICATION_PATH_FIELDS = {
    "path_id",
    "permitted_claim_responsibility",
    "authority_evidence",
    "supplementary_evidence",
    "provenance",
}

EVIDENCE_REQUIREMENT_FIELDS = {
    "semantic_role",
    "min_count",
    "max_count",
    "media_types",
}

PARTICIPATION_POLICY_FIELDS = {
    "policy_id",
    "attestation_mode",
    "interval_rule",
    "authority_evidence",
    "supplementary_evidence",
    "provenance",
}

INTERVAL_RULE_FIELDS = {
    "kind",
    "value",
}

PROVENANCE_KINDS = frozenset(
    {
        "governing_source",
        "derived_profile_parameter",
        "civic_mechanism",
    }
)

CLAIM_RESPONSIBILITY_VALUES = frozenset(
    {
        "participant_claimed",
        "operator_attested",
        "other_published_attestation",
    }
)

ATTESTATION_MODES = frozenset(
    {
        "recording_operator",
        "authority_evidence",
    }
)

INTERVAL_RULE_KINDS = frozenset(
    {
        "explicit_bounded",
        "fixed_duration_ms",
        "calendar_months",
        "open_ended",
    }
)

MAXIMUM_STANDING_DURATION_KINDS = frozenset(
    {
        "fixed_duration_ms",
        "calendar_months",
    }
)


class CivicGoverningProfileError(ValueError):
    """Raised when a Civic governing profile violates its v1 contract."""


class StandingEvidenceLike(Protocol):
    sha256: bytes
    byte_length: int
    media_type: str
    semantic_role: str


class StandingRequestLike(Protocol):
    participant_record_sha256: bytes
    standing_class: str
    valid_from_ms: int
    valid_until_ms: int | None

    participation_required: bool
    participation_policy_id: str | None
    participation_valid_from_ms: int | None
    participation_valid_until_ms: int | None
    participation_authority_evidence: Sequence[StandingEvidenceLike]
    participation_supplementary_evidence: Sequence[StandingEvidenceLike]

    qualification_path_id: str
    claim_responsibility: str
    qualification_authority_evidence: Sequence[StandingEvidenceLike]
    qualification_supplementary_evidence: Sequence[StandingEvidenceLike]


@dataclass(frozen=True)
class Provenance:
    kind: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceRequirement:
    semantic_role: str
    min_count: int
    max_count: int | None
    media_types: tuple[str, ...]


@dataclass(frozen=True)
class DurationRule:
    kind: str
    value: int


@dataclass(frozen=True)
class StandingClassDefinition:
    standing_class: str
    qualification_path_ids: tuple[str, ...]
    participation_required: bool
    participation_policy_ids: tuple[str, ...]
    allow_open_ended_standing: bool
    maximum_standing_duration: DurationRule | None
    provenance: Provenance


@dataclass(frozen=True)
class QualificationPathDefinition:
    path_id: str
    permitted_claim_responsibility: tuple[str, ...]
    authority_evidence: tuple[EvidenceRequirement, ...]
    supplementary_evidence: tuple[EvidenceRequirement, ...]
    provenance: Provenance


@dataclass(frozen=True)
class ParticipationIntervalRule:
    kind: str
    value: int | None


@dataclass(frozen=True)
class ParticipationPolicyDefinition:
    policy_id: str
    attestation_mode: str
    interval_rule: ParticipationIntervalRule
    authority_evidence: tuple[EvidenceRequirement, ...]
    supplementary_evidence: tuple[EvidenceRequirement, ...]
    provenance: Provenance


@dataclass(frozen=True)
class VerifiedGoverningProfile:
    exact_bytes: bytes
    profile_sha256: bytes
    profile_id: str
    source_set_sha256: bytes
    canonical_source_set_bytes: bytes
    source_ids: tuple[str, ...]
    standing_classes: tuple[StandingClassDefinition, ...]
    qualification_paths: tuple[QualificationPathDefinition, ...]
    participation_policies: tuple[ParticipationPolicyDefinition, ...]

    def standing_class(self, identifier: str) -> StandingClassDefinition:
        for item in self.standing_classes:
            if item.standing_class == identifier:
                return item
        raise CivicGoverningProfileError(
            "standing_class is not recognized by governing profile"
        )

    def qualification_path(self, identifier: str) -> QualificationPathDefinition:
        for item in self.qualification_paths:
            if item.path_id == identifier:
                return item
        raise CivicGoverningProfileError(
            "qualification.path_id is not recognized by governing profile"
        )

    def participation_policy(
        self,
        identifier: str,
    ) -> ParticipationPolicyDefinition:
        for item in self.participation_policies:
            if item.policy_id == identifier:
                return item
        raise CivicGoverningProfileError(
            "participation.policy_id is not recognized by governing profile"
        )


def _map(
    value: object,
    label: str,
    required_fields: set[str] | None = None,
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise CivicGoverningProfileError(f"{label} must be a map")
    if any(not isinstance(key, str) for key in value):
        raise CivicGoverningProfileError(f"{label} map keys must be text")
    if required_fields is not None and set(value) != required_fields:
        raise CivicGoverningProfileError(f"{label} fields are invalid")
    return value


def _text(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or unicodedata.normalize("NFC", value) != value
    ):
        raise CivicGoverningProfileError(
            f"{label} must be nonempty NFC text"
        )
    return value


def _sha256(value: object, label: str) -> bytes:
    if not isinstance(value, bytes) or len(value) != SHA256_BYTES:
        raise CivicGoverningProfileError(
            f"{label} must be exactly 32 bytes"
        )
    return value


def _uint(
    value: object,
    label: str,
    *,
    positive: bool = False,
    optional: bool = False,
) -> int | None:
    if optional and value is None:
        return None

    minimum = 1 if positive else 0
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < minimum
        or value > UINT64_MAX
    ):
        qualifier = "positive " if positive else ""
        raise CivicGoverningProfileError(
            f"{label} must be a {qualifier}uint64"
        )
    return value


def _bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise CivicGoverningProfileError(f"{label} must be boolean")
    return value


def _sorted_unique_text_array(
    value: object,
    label: str,
    *,
    nonempty: bool = False,
    permitted: frozenset[str] | None = None,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise CivicGoverningProfileError(f"{label} must be an array")

    items = tuple(
        _text(item, f"{label}[{index}]")
        for index, item in enumerate(value)
    )

    if nonempty and not items:
        raise CivicGoverningProfileError(f"{label} must be nonempty")

    if tuple(sorted(items, key=lambda item: item.encode("utf-8"))) != items:
        raise CivicGoverningProfileError(
            f"{label} must be sorted by UTF-8 bytes"
        )

    if len(set(items)) != len(items):
        raise CivicGoverningProfileError(
            f"{label} must not contain duplicates"
        )

    if permitted is not None and any(item not in permitted for item in items):
        raise CivicGoverningProfileError(
            f"{label} contains an unsupported value"
        )

    return items


def _validate_provenance(
    value: object,
    label: str,
    *,
    source_ids: frozenset[str],
) -> Provenance:
    item = _map(value, label, PROVENANCE_FIELDS)

    kind = _text(item["kind"], f"{label}.kind")
    if kind not in PROVENANCE_KINDS:
        raise CivicGoverningProfileError(
            f"{label}.kind is not supported"
        )

    referenced_sources = _sorted_unique_text_array(
        item["source_ids"],
        f"{label}.source_ids",
    )

    if (
        kind in {"governing_source", "derived_profile_parameter"}
        and not referenced_sources
    ):
        raise CivicGoverningProfileError(
            f"{label}.source_ids must be nonempty for {kind}"
        )

    if any(source_id not in source_ids for source_id in referenced_sources):
        raise CivicGoverningProfileError(
            f"{label}.source_ids references a source outside governing source set"
        )

    return Provenance(
        kind=kind,
        source_ids=referenced_sources,
    )


def _validate_evidence_requirements(
    value: object,
    label: str,
    *,
    supplementary: bool,
) -> tuple[EvidenceRequirement, ...]:
    if not isinstance(value, list):
        raise CivicGoverningProfileError(f"{label} must be an array")

    result: list[EvidenceRequirement] = []
    roles: list[str] = []

    for index, raw in enumerate(value):
        item_label = f"{label}[{index}]"
        item = _map(
            raw,
            item_label,
            EVIDENCE_REQUIREMENT_FIELDS,
        )

        semantic_role = _text(
            item["semantic_role"],
            f"{item_label}.semantic_role",
        )
        min_count = _uint(
            item["min_count"],
            f"{item_label}.min_count",
        )
        max_count = _uint(
            item["max_count"],
            f"{item_label}.max_count",
            optional=True,
        )
        assert isinstance(min_count, int)

        if supplementary:
            if min_count != 0:
                raise CivicGoverningProfileError(
                    f"{item_label}.min_count must be zero for supplementary evidence"
                )
        else:
            if min_count < 1:
                raise CivicGoverningProfileError(
                    f"{item_label}.min_count must be at least one for authority evidence"
                )

        if max_count is not None and max_count < min_count:
            raise CivicGoverningProfileError(
                f"{item_label}.max_count must be >= min_count"
            )

        media_types = _sorted_unique_text_array(
            item["media_types"],
            f"{item_label}.media_types",
        )

        roles.append(semantic_role)
        result.append(
            EvidenceRequirement(
                semantic_role=semantic_role,
                min_count=min_count,
                max_count=max_count,
                media_types=media_types,
            )
        )

    if roles != sorted(roles, key=lambda item: item.encode("utf-8")):
        raise CivicGoverningProfileError(
            f"{label} must be sorted by semantic_role UTF-8 bytes"
        )
    if len(set(roles)) != len(roles):
        raise CivicGoverningProfileError(
            f"{label} semantic_role values must be unique"
        )

    return tuple(result)


def _validate_duration_rule(
    value: object,
    label: str,
) -> DurationRule | None:
    if value is None:
        return None

    item = _map(value, label, DURATION_FIELDS)
    kind = _text(item["kind"], f"{label}.kind")
    if kind not in MAXIMUM_STANDING_DURATION_KINDS:
        raise CivicGoverningProfileError(
            f"{label}.kind is not supported"
        )

    raw_value = _uint(
        item["value"],
        f"{label}.value",
        positive=True,
    )
    assert isinstance(raw_value, int)

    return DurationRule(kind=kind, value=raw_value)


def _validate_standing_classes(
    value: object,
    *,
    source_ids: frozenset[str],
) -> tuple[StandingClassDefinition, ...]:
    if not isinstance(value, list) or not value:
        raise CivicGoverningProfileError(
            "standing_classes must be a nonempty array"
        )

    result: list[StandingClassDefinition] = []
    identifiers: list[str] = []

    for index, raw in enumerate(value):
        label = f"standing_classes[{index}]"
        item = _map(
            raw,
            label,
            STANDING_CLASS_FIELDS_WITH_PROVENANCE,
        )

        standing_class = _text(
            item["standing_class"],
            f"{label}.standing_class",
        )
        qualification_path_ids = _sorted_unique_text_array(
            item["qualification_path_ids"],
            f"{label}.qualification_path_ids",
            nonempty=True,
        )
        participation_required = _bool(
            item["participation_required"],
            f"{label}.participation_required",
        )
        participation_policy_ids = _sorted_unique_text_array(
            item["participation_policy_ids"],
            f"{label}.participation_policy_ids",
            nonempty=participation_required,
        )
        allow_open_ended_standing = _bool(
            item["allow_open_ended_standing"],
            f"{label}.allow_open_ended_standing",
        )

        if not participation_required and participation_policy_ids:
            raise CivicGoverningProfileError(
                f"{label}.participation_policy_ids must be empty when participation is not required"
            )

        maximum_standing_duration = _validate_duration_rule(
            item["maximum_standing_duration"],
            f"{label}.maximum_standing_duration",
        )
        provenance = _validate_provenance(
            item["provenance"],
            f"{label}.provenance",
            source_ids=source_ids,
        )

        identifiers.append(standing_class)
        result.append(
            StandingClassDefinition(
                standing_class=standing_class,
                qualification_path_ids=qualification_path_ids,
                participation_required=participation_required,
                participation_policy_ids=participation_policy_ids,
                allow_open_ended_standing=allow_open_ended_standing,
                maximum_standing_duration=maximum_standing_duration,
                provenance=provenance,
            )
        )

    if identifiers != sorted(
        identifiers,
        key=lambda item: item.encode("utf-8"),
    ):
        raise CivicGoverningProfileError(
            "standing_classes must be sorted by standing_class UTF-8 bytes"
        )
    if len(set(identifiers)) != len(identifiers):
        raise CivicGoverningProfileError(
            "standing_class values must be unique"
        )

    return tuple(result)


def _validate_qualification_paths(
    value: object,
    *,
    source_ids: frozenset[str],
) -> tuple[QualificationPathDefinition, ...]:
    if not isinstance(value, list) or not value:
        raise CivicGoverningProfileError(
            "qualification_paths must be a nonempty array"
        )

    result: list[QualificationPathDefinition] = []
    identifiers: list[str] = []

    for index, raw in enumerate(value):
        label = f"qualification_paths[{index}]"
        item = _map(raw, label, QUALIFICATION_PATH_FIELDS)

        path_id = _text(item["path_id"], f"{label}.path_id")
        responsibilities = _sorted_unique_text_array(
            item["permitted_claim_responsibility"],
            f"{label}.permitted_claim_responsibility",
            nonempty=True,
            permitted=CLAIM_RESPONSIBILITY_VALUES,
        )
        authority_evidence = _validate_evidence_requirements(
            item["authority_evidence"],
            f"{label}.authority_evidence",
            supplementary=False,
        )
        supplementary_evidence = _validate_evidence_requirements(
            item["supplementary_evidence"],
            f"{label}.supplementary_evidence",
            supplementary=True,
        )
        provenance = _validate_provenance(
            item["provenance"],
            f"{label}.provenance",
            source_ids=source_ids,
        )

        identifiers.append(path_id)
        result.append(
            QualificationPathDefinition(
                path_id=path_id,
                permitted_claim_responsibility=responsibilities,
                authority_evidence=authority_evidence,
                supplementary_evidence=supplementary_evidence,
                provenance=provenance,
            )
        )

    if identifiers != sorted(
        identifiers,
        key=lambda item: item.encode("utf-8"),
    ):
        raise CivicGoverningProfileError(
            "qualification_paths must be sorted by path_id UTF-8 bytes"
        )
    if len(set(identifiers)) != len(identifiers):
        raise CivicGoverningProfileError(
            "qualification path_id values must be unique"
        )

    return tuple(result)


def _validate_interval_rule(
    value: object,
    label: str,
) -> ParticipationIntervalRule:
    item = _map(value, label, INTERVAL_RULE_FIELDS)

    kind = _text(item["kind"], f"{label}.kind")
    if kind not in INTERVAL_RULE_KINDS:
        raise CivicGoverningProfileError(
            f"{label}.kind is not supported"
        )

    raw_value = item["value"]

    if kind in {"explicit_bounded", "open_ended"}:
        if raw_value is not None:
            raise CivicGoverningProfileError(
                f"{label}.value must be null for {kind}"
            )
        value_int = None
    else:
        parsed = _uint(
            raw_value,
            f"{label}.value",
            positive=True,
        )
        assert isinstance(parsed, int)
        value_int = parsed

    return ParticipationIntervalRule(
        kind=kind,
        value=value_int,
    )


def _validate_participation_policies(
    value: object,
    *,
    source_ids: frozenset[str],
) -> tuple[ParticipationPolicyDefinition, ...]:
    if not isinstance(value, list):
        raise CivicGoverningProfileError(
            "participation_policies must be an array"
        )

    result: list[ParticipationPolicyDefinition] = []
    identifiers: list[str] = []

    for index, raw in enumerate(value):
        label = f"participation_policies[{index}]"
        item = _map(raw, label, PARTICIPATION_POLICY_FIELDS)

        policy_id = _text(item["policy_id"], f"{label}.policy_id")
        attestation_mode = _text(
            item["attestation_mode"],
            f"{label}.attestation_mode",
        )
        if attestation_mode not in ATTESTATION_MODES:
            raise CivicGoverningProfileError(
                f"{label}.attestation_mode is not supported"
            )

        interval_rule = _validate_interval_rule(
            item["interval_rule"],
            f"{label}.interval_rule",
        )
        authority_evidence = _validate_evidence_requirements(
            item["authority_evidence"],
            f"{label}.authority_evidence",
            supplementary=False,
        )
        supplementary_evidence = _validate_evidence_requirements(
            item["supplementary_evidence"],
            f"{label}.supplementary_evidence",
            supplementary=True,
        )
        provenance = _validate_provenance(
            item["provenance"],
            f"{label}.provenance",
            source_ids=source_ids,
        )

        if attestation_mode == "authority_evidence" and not authority_evidence:
            raise CivicGoverningProfileError(
                f"{label} authority_evidence attestation requires at least one authority-evidence rule"
            )

        identifiers.append(policy_id)
        result.append(
            ParticipationPolicyDefinition(
                policy_id=policy_id,
                attestation_mode=attestation_mode,
                interval_rule=interval_rule,
                authority_evidence=authority_evidence,
                supplementary_evidence=supplementary_evidence,
                provenance=provenance,
            )
        )

    if identifiers != sorted(
        identifiers,
        key=lambda item: item.encode("utf-8"),
    ):
        raise CivicGoverningProfileError(
            "participation_policies must be sorted by policy_id UTF-8 bytes"
        )
    if len(set(identifiers)) != len(identifiers):
        raise CivicGoverningProfileError(
            "participation policy_id values must be unique"
        )

    return tuple(result)


def _validate_referential_integrity(
    standing_classes: tuple[StandingClassDefinition, ...],
    qualification_paths: tuple[QualificationPathDefinition, ...],
    participation_policies: tuple[ParticipationPolicyDefinition, ...],
) -> None:
    path_ids = {item.path_id for item in qualification_paths}
    policy_ids = {item.policy_id for item in participation_policies}

    referenced_paths: set[str] = set()
    referenced_policies: set[str] = set()

    for standing_class in standing_classes:
        for path_id in standing_class.qualification_path_ids:
            if path_id not in path_ids:
                raise CivicGoverningProfileError(
                    "standing class references unknown qualification path"
                )
            referenced_paths.add(path_id)

        for policy_id in standing_class.participation_policy_ids:
            if policy_id not in policy_ids:
                raise CivicGoverningProfileError(
                    "standing class references unknown participation policy"
                )
            referenced_policies.add(policy_id)

    if referenced_paths != path_ids:
        raise CivicGoverningProfileError(
            "qualification_paths contains an unused definition"
        )

    if referenced_policies != policy_ids:
        raise CivicGoverningProfileError(
            "participation_policies contains an unused definition"
        )

    policy_by_id = {
        item.policy_id: item
        for item in participation_policies
    }

    for standing_class in standing_classes:
        for policy_id in standing_class.participation_policy_ids:
            policy = policy_by_id[policy_id]
            if (
                policy.interval_rule.kind == "open_ended"
                and not standing_class.allow_open_ended_standing
            ):
                raise CivicGoverningProfileError(
                    "open-ended participation policy requires standing class to permit open-ended standing"
                )


def canonical_governing_source_set(
    governing_sources: object,
) -> dict[str, object]:
    """Return the canonical v1 source-set projection from manifest descriptors."""

    if not isinstance(governing_sources, list):
        raise CivicGoverningProfileError(
            "governing_sources must be an array"
        )

    sources: list[dict[str, object]] = []
    source_ids: list[str] = []

    for index, raw in enumerate(governing_sources):
        label = f"governing_sources[{index}]"
        item = _map(raw, label)

        required_manifest_fields = {
            "source_id",
            "role",
            "sha256",
            "byte_length",
            "media_type",
            "title",
            "source_uri",
        }
        if set(item) != required_manifest_fields:
            raise CivicGoverningProfileError(
                f"{label} fields are invalid"
            )

        source_id = _text(item["source_id"], f"{label}.source_id")
        role = _text(item["role"], f"{label}.role")
        digest = _sha256(item["sha256"], f"{label}.sha256")
        byte_length = _uint(
            item["byte_length"],
            f"{label}.byte_length",
        )
        media_type = _text(
            item["media_type"],
            f"{label}.media_type",
        )
        assert isinstance(byte_length, int)

        title = item["title"]
        if title is not None:
            _text(title, f"{label}.title")

        source_uri = item["source_uri"]
        if source_uri is not None:
            _text(source_uri, f"{label}.source_uri")

        source_ids.append(source_id)
        sources.append(
            {
                "source_id": source_id,
                "role": role,
                "sha256": digest,
                "byte_length": byte_length,
                "media_type": media_type,
            }
        )

    if source_ids != sorted(
        source_ids,
        key=lambda item: item.encode("utf-8"),
    ):
        raise CivicGoverningProfileError(
            "governing_sources must be sorted by source_id UTF-8 bytes"
        )
    if len(set(source_ids)) != len(source_ids):
        raise CivicGoverningProfileError(
            "governing_sources source_id values must be unique"
        )

    return {
        "format": SOURCE_SET_FORMAT,
        "version": SOURCE_SET_VERSION,
        "sources": sources,
    }


def validate_governing_source_set(value: Mapping[str, object]) -> None:
    source_set = _map(
        value,
        "governing_source_set",
        SOURCE_SET_FIELDS,
    )

    if (
        source_set["format"] != SOURCE_SET_FORMAT
        or source_set["version"] != SOURCE_SET_VERSION
    ):
        raise CivicGoverningProfileError(
            "governing source-set format/version is unsupported"
        )

    sources = source_set["sources"]
    if not isinstance(sources, list):
        raise CivicGoverningProfileError(
            "governing source-set sources must be an array"
        )

    identifiers: list[str] = []

    for index, raw in enumerate(sources):
        label = f"governing_source_set.sources[{index}]"
        item = _map(raw, label, SOURCE_SET_SOURCE_FIELDS)

        source_id = _text(item["source_id"], f"{label}.source_id")
        _text(item["role"], f"{label}.role")
        _sha256(item["sha256"], f"{label}.sha256")
        _uint(item["byte_length"], f"{label}.byte_length")
        _text(item["media_type"], f"{label}.media_type")
        identifiers.append(source_id)

    if identifiers != sorted(
        identifiers,
        key=lambda item: item.encode("utf-8"),
    ):
        raise CivicGoverningProfileError(
            "governing source-set sources must be sorted by source_id UTF-8 bytes"
        )
    if len(set(identifiers)) != len(identifiers):
        raise CivicGoverningProfileError(
            "governing source-set source_id values must be unique"
        )

    try:
        encode_deterministic(dict(source_set))
    except CivicCodecError as exc:
        raise CivicGoverningProfileError(str(exc)) from exc


def encode_governing_source_set(
    governing_sources: object,
) -> bytes:
    value = canonical_governing_source_set(governing_sources)
    validate_governing_source_set(value)
    return encode_deterministic(value)


def governing_source_set_sha256(
    governing_sources: object,
) -> bytes:
    return hashlib.sha256(
        encode_governing_source_set(governing_sources)
    ).digest()


def _parse_profile(
    value: Mapping[str, object],
    *,
    governing_sources: object,
) -> tuple[
    str,
    bytes,
    tuple[str, ...],
    tuple[StandingClassDefinition, ...],
    tuple[QualificationPathDefinition, ...],
    tuple[ParticipationPolicyDefinition, ...],
]:
    profile = _map(value, "governing_profile", TOP_LEVEL_FIELDS)

    if profile["format"] != FORMAT or profile["version"] != VERSION:
        raise CivicGoverningProfileError(
            "governing profile format/version is unsupported"
        )

    profile_id = _text(profile["profile_id"], "profile_id")
    declared_source_set_sha256 = _sha256(
        profile["source_set_sha256"],
        "source_set_sha256",
    )

    canonical_source_set = canonical_governing_source_set(
        governing_sources
    )
    source_ids = tuple(
        item["source_id"]
        for item in canonical_source_set["sources"]  # type: ignore[index]
    )
    if not all(isinstance(item, str) for item in source_ids):
        raise CivicGoverningProfileError(
            "canonical governing source-set source IDs are invalid"
        )

    actual_source_set_sha256 = governing_source_set_sha256(
        governing_sources
    )
    if declared_source_set_sha256 != actual_source_set_sha256:
        raise CivicGoverningProfileError(
            "governing profile source_set_sha256 does not match governing sources"
        )

    source_id_set = frozenset(source_ids)

    standing_classes = _validate_standing_classes(
        profile["standing_classes"],
        source_ids=source_id_set,
    )
    qualification_paths = _validate_qualification_paths(
        profile["qualification_paths"],
        source_ids=source_id_set,
    )
    participation_policies = _validate_participation_policies(
        profile["participation_policies"],
        source_ids=source_id_set,
    )

    _validate_referential_integrity(
        standing_classes,
        qualification_paths,
        participation_policies,
    )

    try:
        encode_deterministic(dict(profile))
    except CivicCodecError as exc:
        raise CivicGoverningProfileError(str(exc)) from exc

    return (
        profile_id,
        declared_source_set_sha256,
        source_ids,
        standing_classes,
        qualification_paths,
        participation_policies,
    )


def validate_governing_profile(
    value: Mapping[str, object],
    *,
    governing_sources: object,
) -> None:
    """Validate one canonical logical governing-profile value."""

    _parse_profile(
        value,
        governing_sources=governing_sources,
    )


def encode_governing_profile(
    value: Mapping[str, object],
    *,
    governing_sources: object,
) -> bytes:
    validate_governing_profile(
        value,
        governing_sources=governing_sources,
    )
    return encode_deterministic(dict(value))


def decode_governing_profile(
    data: bytes,
    *,
    governing_sources: object,
) -> dict[str, object]:
    try:
        value = decode_deterministic(data)
    except CivicCodecError as exc:
        raise CivicGoverningProfileError(str(exc)) from exc

    if (
        not isinstance(value, dict)
        or any(not isinstance(key, str) for key in value)
    ):
        raise CivicGoverningProfileError(
            "governing profile must decode to a text-keyed map"
        )

    validate_governing_profile(
        value,
        governing_sources=governing_sources,
    )
    return value  # type: ignore[return-value]


def governing_profile_sha256(
    value_or_bytes: Mapping[str, object] | bytes,
    *,
    governing_sources: object,
) -> bytes:
    if isinstance(value_or_bytes, bytes):
        decode_governing_profile(
            value_or_bytes,
            governing_sources=governing_sources,
        )
        data = value_or_bytes
    else:
        data = encode_governing_profile(
            value_or_bytes,
            governing_sources=governing_sources,
        )

    return hashlib.sha256(data).digest()


def verify_governing_profile(
    profile_bytes: bytes,
    *,
    epoch_manifest: Mapping[str, object],
) -> VerifiedGoverningProfile:
    """Verify exact governing-profile bytes against one accepted Epoch Manifest."""

    try:
        validate_epoch_manifest(epoch_manifest)
    except CivicManifestError as exc:
        raise CivicGoverningProfileError(
            "referenced Epoch Manifest is invalid"
        ) from exc

    if not isinstance(profile_bytes, bytes):
        raise CivicGoverningProfileError(
            "governing profile exact bytes must be bytes"
        )

    governing_sources = epoch_manifest["governing_sources"]
    profile_value = decode_governing_profile(
        profile_bytes,
        governing_sources=governing_sources,
    )

    (
        profile_id,
        source_set_id,
        source_ids,
        standing_classes,
        qualification_paths,
        participation_policies,
    ) = _parse_profile(
        profile_value,
        governing_sources=governing_sources,
    )

    manifest_profile = _map(
        epoch_manifest["governing_profile"],
        "Epoch Manifest governing_profile",
        {"profile_id", "profile_sha256", "source_set_sha256"},
    )

    manifest_profile_id = _text(
        manifest_profile["profile_id"],
        "Epoch Manifest governing_profile.profile_id",
    )
    manifest_profile_sha256 = _sha256(
        manifest_profile["profile_sha256"],
        "Epoch Manifest governing_profile.profile_sha256",
    )
    manifest_source_set_sha256 = _sha256(
        manifest_profile["source_set_sha256"],
        "Epoch Manifest governing_profile.source_set_sha256",
    )

    actual_profile_sha256 = hashlib.sha256(profile_bytes).digest()

    if profile_id != manifest_profile_id:
        raise CivicGoverningProfileError(
            "governing profile profile_id does not match Epoch Manifest"
        )
    if actual_profile_sha256 != manifest_profile_sha256:
        raise CivicGoverningProfileError(
            "governing profile exact-byte identity does not match Epoch Manifest"
        )
    if source_set_id != manifest_source_set_sha256:
        raise CivicGoverningProfileError(
            "governing profile source-set identity does not match Epoch Manifest"
        )

    canonical_source_set_bytes = encode_governing_source_set(
        governing_sources
    )
    if (
        hashlib.sha256(canonical_source_set_bytes).digest()
        != manifest_source_set_sha256
    ):
        raise CivicGoverningProfileError(
            "canonical governing source-set identity does not match Epoch Manifest"
        )

    object_index = epoch_manifest["object_index"]
    if not isinstance(object_index, list):
        raise CivicGoverningProfileError(
            "Epoch Manifest object_index must be an array"
        )

    profile_descriptors = [
        item
        for item in object_index
        if isinstance(item, Mapping)
        and item.get("sha256") == actual_profile_sha256
    ]
    if len(profile_descriptors) != 1:
        raise CivicGoverningProfileError(
            "governing profile must resolve to exactly one Epoch Manifest object descriptor"
        )

    descriptor = profile_descriptors[0]
    descriptor_length = _uint(
        descriptor.get("byte_length"),
        "governing profile object_index.byte_length",
    )
    descriptor_media_type = _text(
        descriptor.get("media_type"),
        "governing profile object_index.media_type",
    )
    descriptor_semantic_role = _text(
        descriptor.get("semantic_role"),
        "governing profile object_index.semantic_role",
    )
    assert isinstance(descriptor_length, int)

    if descriptor_length != len(profile_bytes):
        raise CivicGoverningProfileError(
            "governing profile byte length does not match Epoch Manifest object descriptor"
        )
    if descriptor_media_type != PROFILE_MEDIA_TYPE:
        raise CivicGoverningProfileError(
            "governing profile object media_type is invalid"
        )
    if descriptor_semantic_role != PROFILE_SEMANTIC_ROLE:
        raise CivicGoverningProfileError(
            "governing profile object semantic_role is invalid"
        )

    inline = descriptor.get("inline")
    if inline is not None:
        if not isinstance(inline, bytes):
            raise CivicGoverningProfileError(
                "governing profile inline object must be bytes or null"
            )
        if inline != profile_bytes:
            raise CivicGoverningProfileError(
                "governing profile inline bytes do not equal verified exact profile bytes"
            )

    return VerifiedGoverningProfile(
        exact_bytes=profile_bytes,
        profile_sha256=actual_profile_sha256,
        profile_id=profile_id,
        source_set_sha256=source_set_id,
        canonical_source_set_bytes=canonical_source_set_bytes,
        source_ids=source_ids,
        standing_classes=standing_classes,
        qualification_paths=qualification_paths,
        participation_policies=participation_policies,
    )


def _evidence_role_counts(
    evidence: Sequence[StandingEvidenceLike],
    label: str,
) -> dict[str, list[StandingEvidenceLike]]:
    grouped: dict[str, list[StandingEvidenceLike]] = {}

    for index, item in enumerate(evidence):
        role = getattr(item, "semantic_role", None)
        media_type = getattr(item, "media_type", None)
        digest = getattr(item, "sha256", None)
        byte_length = getattr(item, "byte_length", None)

        if not isinstance(role, str) or not role:
            raise CivicGoverningProfileError(
                f"{label}[{index}].semantic_role must be nonempty text"
            )
        if not isinstance(media_type, str) or not media_type:
            raise CivicGoverningProfileError(
                f"{label}[{index}].media_type must be nonempty text"
            )
        if not isinstance(digest, bytes) or len(digest) != SHA256_BYTES:
            raise CivicGoverningProfileError(
                f"{label}[{index}].sha256 must be exactly 32 bytes"
            )
        if (
            not isinstance(byte_length, int)
            or isinstance(byte_length, bool)
            or byte_length < 0
            or byte_length > UINT64_MAX
        ):
            raise CivicGoverningProfileError(
                f"{label}[{index}].byte_length must be a uint64"
            )

        grouped.setdefault(role, []).append(item)

    return grouped


def _validate_evidence_against_requirements(
    evidence: Sequence[StandingEvidenceLike],
    requirements: tuple[EvidenceRequirement, ...],
    label: str,
) -> None:
    grouped = _evidence_role_counts(evidence, label)
    by_role = {
        requirement.semantic_role: requirement
        for requirement in requirements
    }

    for role in grouped:
        if role not in by_role:
            raise CivicGoverningProfileError(
                f"{label} contains an undeclared semantic_role"
            )

    for requirement in requirements:
        matching = grouped.get(requirement.semantic_role, [])
        count = len(matching)

        if count < requirement.min_count:
            raise CivicGoverningProfileError(
                f"{label} does not satisfy minimum evidence count for semantic_role"
            )
        if (
            requirement.max_count is not None
            and count > requirement.max_count
        ):
            raise CivicGoverningProfileError(
                f"{label} exceeds maximum evidence count for semantic_role"
            )

        if requirement.media_types:
            allowed = set(requirement.media_types)
            if any(item.media_type not in allowed for item in matching):
                raise CivicGoverningProfileError(
                    f"{label} contains a media_type not permitted for semantic_role"
                )


def _checked_add_uint64(left: int, right: int, label: str) -> int:
    result = left + right
    if result > UINT64_MAX:
        raise CivicGoverningProfileError(
            f"{label} exceeds uint64 range"
        )
    return result


def _unix_ms_to_utc_datetime(value: int, label: str) -> datetime:
    try:
        return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(
            milliseconds=value
        )
    except (OverflowError, ValueError) as exc:
        raise CivicGoverningProfileError(
            f"{label} cannot be represented as an exact UTC datetime"
        ) from exc


def _utc_datetime_to_unix_ms(value: datetime, label: str) -> int:
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    delta = value - epoch

    whole_seconds = (
        delta.days * 86400
        + delta.seconds
    )
    result = whole_seconds * 1000 + delta.microseconds // 1000

    if result < 0 or result > UINT64_MAX:
        raise CivicGoverningProfileError(
            f"{label} cannot be represented as uint64 Unix milliseconds"
        )
    return result


def add_utc_calendar_months(
    unix_ms: int,
    months: int,
) -> int:
    """Add positive Gregorian calendar months in UTC using the v1 clamp rule."""

    parsed_unix_ms = _uint(
        unix_ms,
        "unix_ms",
    )
    parsed_months = _uint(
        months,
        "months",
        positive=True,
    )
    assert isinstance(parsed_unix_ms, int)
    assert isinstance(parsed_months, int)

    source = _unix_ms_to_utc_datetime(
        parsed_unix_ms,
        "unix_ms",
    )

    month_index = (
        source.year * 12
        + (source.month - 1)
        + parsed_months
    )
    target_year, zero_based_month = divmod(month_index, 12)
    target_month = zero_based_month + 1

    if target_year < 1 or target_year > 9999:
        raise CivicGoverningProfileError(
            "calendar-month result is outside supported UTC datetime range"
        )

    last_day = calendar.monthrange(
        target_year,
        target_month,
    )[1]
    target_day = min(source.day, last_day)

    try:
        target = source.replace(
            year=target_year,
            month=target_month,
            day=target_day,
        )
    except ValueError as exc:
        raise CivicGoverningProfileError(
            "calendar-month result cannot be represented"
        ) from exc

    return _utc_datetime_to_unix_ms(
        target,
        "calendar-month result",
    )


def _duration_limit(
    valid_from_ms: int,
    rule: DurationRule,
) -> int:
    if rule.kind == "fixed_duration_ms":
        return _checked_add_uint64(
            valid_from_ms,
            rule.value,
            "maximum standing duration",
        )

    if rule.kind == "calendar_months":
        return add_utc_calendar_months(
            valid_from_ms,
            rule.value,
        )

    raise CivicGoverningProfileError(
        "maximum standing duration kind is unsupported"
    )


def _validate_participation_interval(
    rule: ParticipationIntervalRule,
    *,
    valid_from_ms: int,
    valid_until_ms: int | None,
) -> None:
    if rule.kind == "explicit_bounded":
        if valid_until_ms is None or valid_until_ms <= valid_from_ms:
            raise CivicGoverningProfileError(
                "participation interval must be explicitly bounded"
            )
        return

    if rule.kind == "fixed_duration_ms":
        assert rule.value is not None
        expected = _checked_add_uint64(
            valid_from_ms,
            rule.value,
            "participation fixed-duration interval",
        )
        if valid_until_ms != expected:
            raise CivicGoverningProfileError(
                "participation interval does not match fixed_duration_ms policy"
            )
        return

    if rule.kind == "calendar_months":
        assert rule.value is not None
        expected = add_utc_calendar_months(
            valid_from_ms,
            rule.value,
        )
        if valid_until_ms != expected:
            raise CivicGoverningProfileError(
                "participation interval does not match calendar_months policy"
            )
        return

    if rule.kind == "open_ended":
        if valid_until_ms is not None:
            raise CivicGoverningProfileError(
                "open-ended participation policy requires null valid_until_ms"
            )
        return

    raise CivicGoverningProfileError(
        "participation interval rule kind is unsupported"
    )


def validate_standing_against_profile(
    profile: VerifiedGoverningProfile,
    request: StandingRequestLike,
) -> None:
    """Apply mandatory v1 profile semantics to one authenticated standing request."""

    if not isinstance(profile, VerifiedGoverningProfile):
        raise CivicGoverningProfileError(
            "profile must be a verified governing profile"
        )

    standing_class_id = _text(
        getattr(request, "standing_class", None),
        "standing_class",
    )
    qualification_path_id = _text(
        getattr(request, "qualification_path_id", None),
        "qualification.path_id",
    )
    claim_responsibility = _text(
        getattr(request, "claim_responsibility", None),
        "qualification.claim_responsibility",
    )

    valid_from_ms = _uint(
        getattr(request, "valid_from_ms", None),
        "valid_from_ms",
    )
    valid_until_ms = _uint(
        getattr(request, "valid_until_ms", None),
        "valid_until_ms",
        optional=True,
    )
    assert isinstance(valid_from_ms, int)

    if valid_until_ms is not None and valid_until_ms <= valid_from_ms:
        raise CivicGoverningProfileError(
            "standing valid_until_ms must be greater than valid_from_ms"
        )

    standing_class = profile.standing_class(
        standing_class_id
    )
    qualification_path = profile.qualification_path(
        qualification_path_id
    )

    if (
        qualification_path_id
        not in standing_class.qualification_path_ids
    ):
        raise CivicGoverningProfileError(
            "qualification path is not permitted by standing class"
        )

    if (
        claim_responsibility
        not in qualification_path.permitted_claim_responsibility
    ):
        raise CivicGoverningProfileError(
            "claim responsibility is not permitted by qualification path"
        )

    qualification_authority_evidence = getattr(
        request,
        "qualification_authority_evidence",
        None,
    )
    qualification_supplementary_evidence = getattr(
        request,
        "qualification_supplementary_evidence",
        None,
    )

    if not isinstance(
        qualification_authority_evidence,
        Sequence,
    ):
        raise CivicGoverningProfileError(
            "qualification.authority_evidence must be a sequence"
        )
    if not isinstance(
        qualification_supplementary_evidence,
        Sequence,
    ):
        raise CivicGoverningProfileError(
            "qualification.supplementary_evidence must be a sequence"
        )

    _validate_evidence_against_requirements(
        qualification_authority_evidence,
        qualification_path.authority_evidence,
        "qualification.authority_evidence",
    )
    _validate_evidence_against_requirements(
        qualification_supplementary_evidence,
        qualification_path.supplementary_evidence,
        "qualification.supplementary_evidence",
    )

    participation_required = getattr(
        request,
        "participation_required",
        None,
    )
    if not isinstance(participation_required, bool):
        raise CivicGoverningProfileError(
            "participation.required must be boolean"
        )

    if participation_required != standing_class.participation_required:
        raise CivicGoverningProfileError(
            "participation.required does not match standing-class policy"
        )

    participation_policy_id = getattr(
        request,
        "participation_policy_id",
        None,
    )
    participation_valid_from_ms = getattr(
        request,
        "participation_valid_from_ms",
        None,
    )
    participation_valid_until_ms = getattr(
        request,
        "participation_valid_until_ms",
        None,
    )
    participation_authority_evidence = getattr(
        request,
        "participation_authority_evidence",
        None,
    )
    participation_supplementary_evidence = getattr(
        request,
        "participation_supplementary_evidence",
        None,
    )

    if not isinstance(participation_authority_evidence, Sequence):
        raise CivicGoverningProfileError(
            "participation.authority_evidence must be a sequence"
        )
    if not isinstance(participation_supplementary_evidence, Sequence):
        raise CivicGoverningProfileError(
            "participation.supplementary_evidence must be a sequence"
        )

    selected_policy: ParticipationPolicyDefinition | None = None

    if participation_required:
        policy_id = _text(
            participation_policy_id,
            "participation.policy_id",
        )

        if policy_id not in standing_class.participation_policy_ids:
            raise CivicGoverningProfileError(
                "participation policy is not permitted by standing class"
            )

        selected_policy = profile.participation_policy(
            policy_id
        )

        participation_from = _uint(
            participation_valid_from_ms,
            "participation.valid_from_ms",
        )
        participation_until = _uint(
            participation_valid_until_ms,
            "participation.valid_until_ms",
            optional=True,
        )
        assert isinstance(participation_from, int)

        _validate_evidence_against_requirements(
            participation_authority_evidence,
            selected_policy.authority_evidence,
            "participation.authority_evidence",
        )
        _validate_evidence_against_requirements(
            participation_supplementary_evidence,
            selected_policy.supplementary_evidence,
            "participation.supplementary_evidence",
        )

        if (
            selected_policy.attestation_mode == "authority_evidence"
            and not participation_authority_evidence
        ):
            raise CivicGoverningProfileError(
                "participation authority_evidence attestation requires authority evidence"
            )

        _validate_participation_interval(
            selected_policy.interval_rule,
            valid_from_ms=participation_from,
            valid_until_ms=participation_until,
        )
    else:
        if participation_policy_id is not None:
            raise CivicGoverningProfileError(
                "participation.policy_id must be null when participation is not required"
            )
        if participation_valid_from_ms is not None:
            raise CivicGoverningProfileError(
                "participation.valid_from_ms must be null when participation is not required"
            )
        if participation_valid_until_ms is not None:
            raise CivicGoverningProfileError(
                "participation.valid_until_ms must be null when participation is not required"
            )
        if participation_authority_evidence:
            raise CivicGoverningProfileError(
                "participation.authority_evidence must be empty when participation is not required"
            )
        if participation_supplementary_evidence:
            raise CivicGoverningProfileError(
                "participation.supplementary_evidence must be empty when participation is not required"
            )

    if valid_until_ms is None:
        if not standing_class.allow_open_ended_standing:
            raise CivicGoverningProfileError(
                "standing class does not permit open-ended standing"
            )
        if (
            selected_policy is not None
            and selected_policy.interval_rule.kind != "open_ended"
        ):
            raise CivicGoverningProfileError(
                "bounded participation policy does not permit open-ended standing"
            )

    maximum_duration = standing_class.maximum_standing_duration
    if maximum_duration is not None:
        if valid_until_ms is None:
            raise CivicGoverningProfileError(
                "maximum standing duration requires non-null valid_until_ms"
            )

        maximum_end = _duration_limit(
            valid_from_ms,
            maximum_duration,
        )
        if valid_until_ms > maximum_end:
            raise CivicGoverningProfileError(
                "standing interval exceeds profile maximum duration"
            )


def make_standing_semantics_validator(
    profile: VerifiedGoverningProfile,
):
    """Return the accepted-standing callback shape backed by one verified profile."""

    if not isinstance(profile, VerifiedGoverningProfile):
        raise CivicGoverningProfileError(
            "profile must be a verified governing profile"
        )

    def validate(context: object, request: StandingRequestLike) -> None:
        context_profile_id = getattr(context, "profile_id", None)
        context_profile_sha256 = getattr(
            context,
            "profile_sha256",
            None,
        )
        context_source_set_sha256 = getattr(
            context,
            "source_set_sha256",
            None,
        )
        context_profile_bytes = getattr(
            context,
            "profile_bytes",
            None,
        )

        if context_profile_id != profile.profile_id:
            raise CivicGoverningProfileError(
                "standing profile context profile_id does not match verified governing profile"
            )
        if context_profile_sha256 != profile.profile_sha256:
            raise CivicGoverningProfileError(
                "standing profile context profile_sha256 does not match verified governing profile"
            )
        if context_source_set_sha256 != profile.source_set_sha256:
            raise CivicGoverningProfileError(
                "standing profile context source_set_sha256 does not match verified governing profile"
            )
        if context_profile_bytes != profile.exact_bytes:
            raise CivicGoverningProfileError(
                "standing profile context exact bytes do not match verified governing profile"
            )

        validate_standing_against_profile(
            profile,
            request,
        )

    return validate
