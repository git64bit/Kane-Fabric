from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import unicodedata

from civic.ceremony import (
    CivicCeremonyError,
    VerifiedCeremonyRecord,
    validate_ceremony_record,
)
from civic.codec import CivicCodecError, decode_deterministic, encode_deterministic
from civic.cose import (
    CivicCoseError,
    build_cose_sign1,
    build_sig_structure,
    parse_cose_sign1,
)
from civic.ecdsa import (
    CivicEcdsaError,
    public_key_from_private_scalar,
    sign_sig_structure_fixture,
    verify_sig_structure,
)
from civic.epoch_manifest import (
    CRYPTO_PROFILE,
    CivicManifestError,
    derive_key_id,
    validate_epoch_manifest,
)
from civic.governing_profile import (
    CivicGoverningProfileError,
    governing_source_set_sha256,
)


SUBJECT_FORMAT = "kane-civic-governance-transition-subject"
SUBJECT_VERSION = 1

POLICY_FORMAT = "kane-civic-governance-policy"
POLICY_VERSION = 1
POLICY_MEDIA_TYPE = "application/kane-civic-governance-policy+cbor"
POLICY_SEMANTIC_ROLE = "governance-policy"

PROOF_FORMAT = "kane-civic-governance-proof"
PROOF_VERSION = 1
PROOF_CONTENT_TYPE = "application/kane-civic-governance-proof+cbor"
PROOF_MEDIA_TYPE = "application/kane-civic-governance-proof+cose"
PROOF_SEMANTIC_ROLE = "governance-proof"

SHA256_BYTES = 32
UINT64_MAX = 0xFFFFFFFFFFFFFFFF

SUBJECT_FIELDS = {
    "format",
    "version",
    "crypto_profile",
    "transition_kind",
    "hoa_root_id",
    "epoch_sequence",
    "predecessor_manifest_sha256",
    "effective_time_ms",
    "governing_profile",
    "participants",
    "operator_participant_record_sha256",
    "signing_node",
    "governance_policy",
}

POLICY_FIELDS = {
    "format",
    "version",
    "policy_id",
    "source_set_sha256",
    "transition_kinds",
    "electorate",
    "decision_rule",
    "authority_evidence",
    "supplementary_evidence",
    "provenance",
}

ELECTORATE_FIELDS = {
    "basis",
    "standing_class",
    "membership_rule",
    "weight_mode",
    "members",
    "operator_must_be_elector",
    "provenance",
}

ELECTORATE_MEMBER_FIELDS = {
    "participant_record_sha256",
    "weight",
}

DECISION_RULE_FIELDS = {
    "quorum",
    "approval",
    "provenance",
}

PROVENANCE_FIELDS = {
    "kind",
    "source_ids",
}

EVIDENCE_REQUIREMENT_FIELDS = {
    "semantic_role",
    "min_count",
    "max_count",
    "media_types",
    "provenance",
}

PROOF_FIELDS = {
    "format",
    "version",
    "crypto_profile",
    "subject_sha256",
    "governance_policy",
    "signer",
    "decision",
    "authority_evidence",
    "supplementary_evidence",
}

PROOF_POLICY_FIELDS = {
    "policy_id",
    "policy_sha256",
}

PROOF_SIGNER_FIELDS = {
    "participant_record_sha256",
    "participant_key_id",
}

EVIDENCE_DESCRIPTOR_FIELDS = {
    "sha256",
    "byte_length",
    "media_type",
    "semantic_role",
}

TRANSITION_KINDS = frozenset({"bootstrap", "successor"})
ELECTORATE_BASES = frozenset(
    {"candidate_participants", "predecessor_participants"}
)
MEMBERSHIP_RULES = frozenset({"all_matching_standing_class"})
WEIGHT_MODES = frozenset({"equal", "explicit_uint"})
PROVENANCE_KINDS = frozenset(
    {"governing_source", "derived_policy_parameter", "civic_mechanism"}
)
DECISIONS = frozenset({"approve", "reject", "abstain"})
THRESHOLD_KINDS = frozenset(
    {"all", "count_at_least", "weight_at_least", "fraction_at_least"}
)


class CivicGovernanceError(ValueError):
    """Raised when Civic governance authority data violates the v1 contract."""


@dataclass(frozen=True)
class GovernanceProvenance:
    kind: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class GovernanceEvidenceRequirement:
    semantic_role: str
    min_count: int
    max_count: int | None
    media_types: tuple[str, ...]
    provenance: GovernanceProvenance


@dataclass(frozen=True)
class GovernanceElectorateMember:
    participant_record_sha256: bytes
    weight: int


@dataclass(frozen=True)
class GovernanceThreshold:
    kind: str
    value: int | None = None
    numerator: int | None = None
    denominator: int | None = None
    base: str | None = None


@dataclass(frozen=True)
class VerifiedGovernancePolicy:
    exact_bytes: bytes
    policy_sha256: bytes
    policy_id: str
    source_set_sha256: bytes
    transition_kinds: tuple[str, ...]
    electorate_basis: str
    electorate_standing_class: str
    electorate_members: tuple[GovernanceElectorateMember, ...]
    weight_mode: str
    operator_must_be_elector: bool
    quorum: GovernanceThreshold | None
    approval: GovernanceThreshold | None
    authority_evidence: tuple[GovernanceEvidenceRequirement, ...]
    supplementary_evidence: tuple[GovernanceEvidenceRequirement, ...]
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class GovernanceEvidenceDescriptor:
    sha256: bytes
    byte_length: int
    media_type: str
    semantic_role: str


@dataclass(frozen=True)
class VerifiedGovernanceProof:
    signed_bytes: bytes
    proof_sha256: bytes
    payload: dict[str, object]
    subject_sha256: bytes
    policy_id: str
    policy_sha256: bytes
    participant_record_sha256: bytes
    participant_key_id: bytes
    participant_public_key: bytes
    decision: str | None
    authority_evidence: tuple[GovernanceEvidenceDescriptor, ...]
    supplementary_evidence: tuple[GovernanceEvidenceDescriptor, ...]


def _map(
    value: object,
    label: str,
    required_fields: set[str] | None = None,
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise CivicGovernanceError(f"{label} must be a map")
    if any(not isinstance(key, str) for key in value):
        raise CivicGovernanceError(f"{label} map keys must be text")
    if required_fields is not None and set(value) != required_fields:
        raise CivicGovernanceError(f"{label} fields are invalid")
    return value


def _text(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or unicodedata.normalize("NFC", value) != value
    ):
        raise CivicGovernanceError(f"{label} must be nonempty NFC text")
    return value


def _bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise CivicGovernanceError(f"{label} must be boolean")
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
        raise CivicGovernanceError(
            f"{label} must be a {qualifier}uint64"
        )
    return value


def _sha256(
    value: object,
    label: str,
    *,
    optional: bool = False,
) -> bytes | None:
    if optional and value is None:
        return None
    if not isinstance(value, bytes) or len(value) != SHA256_BYTES:
        raise CivicGovernanceError(f"{label} must be exactly 32 bytes")
    return value


def _sorted_unique_texts(
    value: object,
    label: str,
    *,
    nonempty: bool = False,
    permitted: frozenset[str] | None = None,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise CivicGovernanceError(f"{label} must be an array")

    parsed = tuple(
        _text(item, f"{label}[{index}]")
        for index, item in enumerate(value)
    )

    if nonempty and not parsed:
        raise CivicGovernanceError(f"{label} must be nonempty")

    if parsed != tuple(
        sorted(parsed, key=lambda item: item.encode("utf-8"))
    ):
        raise CivicGovernanceError(
            f"{label} must be sorted by UTF-8 bytes"
        )

    if len(parsed) != len(set(parsed)):
        raise CivicGovernanceError(f"{label} values must be unique")

    if permitted is not None and any(item not in permitted for item in parsed):
        raise CivicGovernanceError(f"{label} contains an unsupported value")

    return parsed


def _validate_provenance(
    value: object,
    label: str,
    *,
    source_ids: frozenset[str],
) -> GovernanceProvenance:
    item = _map(value, label, PROVENANCE_FIELDS)
    kind = _text(item["kind"], f"{label}.kind")
    if kind not in PROVENANCE_KINDS:
        raise CivicGovernanceError(f"{label}.kind is unsupported")

    referenced = _sorted_unique_texts(
        item["source_ids"],
        f"{label}.source_ids",
    )

    if kind in {"governing_source", "derived_policy_parameter"} and not referenced:
        raise CivicGovernanceError(
            f"{label}.source_ids must be nonempty for {kind}"
        )

    unknown = set(referenced) - set(source_ids)
    if unknown:
        raise CivicGovernanceError(
            f"{label}.source_ids references an unknown governing source"
        )

    return GovernanceProvenance(kind=kind, source_ids=referenced)


def _validate_threshold(
    value: object,
    label: str,
    *,
    quorum: bool,
) -> GovernanceThreshold | None:
    if value is None:
        return None

    item = _map(value, label)
    kind = _text(item.get("kind"), f"{label}.kind")

    if kind not in THRESHOLD_KINDS:
        raise CivicGovernanceError(f"{label}.kind is unsupported")

    if kind == "all":
        if set(item) != {"kind"}:
            raise CivicGovernanceError(f"{label} fields are invalid")
        return GovernanceThreshold(kind=kind)

    if kind in {"count_at_least", "weight_at_least"}:
        if set(item) != {"kind", "value"}:
            raise CivicGovernanceError(f"{label} fields are invalid")
        threshold = _uint(item["value"], f"{label}.value", positive=True)
        assert isinstance(threshold, int)
        return GovernanceThreshold(kind=kind, value=threshold)

    if set(item) != {"kind", "numerator", "denominator", "base"}:
        raise CivicGovernanceError(f"{label} fields are invalid")

    numerator = _uint(
        item["numerator"],
        f"{label}.numerator",
        positive=True,
    )
    denominator = _uint(
        item["denominator"],
        f"{label}.denominator",
        positive=True,
    )
    assert isinstance(numerator, int)
    assert isinstance(denominator, int)

    if numerator > denominator:
        raise CivicGovernanceError(
            f"{label}.numerator must not exceed denominator"
        )

    base = _text(item["base"], f"{label}.base")
    if base not in {"electorate", "participating"}:
        raise CivicGovernanceError(f"{label}.base is unsupported")
    if quorum and base != "electorate":
        raise CivicGovernanceError(
            "quorum fraction_at_least base must be electorate"
        )

    return GovernanceThreshold(
        kind=kind,
        numerator=numerator,
        denominator=denominator,
        base=base,
    )


def _validate_evidence_requirements(
    value: object,
    label: str,
    *,
    source_ids: frozenset[str],
    supplementary: bool,
) -> tuple[GovernanceEvidenceRequirement, ...]:
    if not isinstance(value, list):
        raise CivicGovernanceError(f"{label} must be an array")

    result: list[GovernanceEvidenceRequirement] = []
    roles: list[str] = []

    for index, raw in enumerate(value):
        item_label = f"{label}[{index}]"
        item = _map(raw, item_label, EVIDENCE_REQUIREMENT_FIELDS)

        role = _text(item["semantic_role"], f"{item_label}.semantic_role")
        minimum = _uint(item["min_count"], f"{item_label}.min_count")
        maximum = _uint(
            item["max_count"],
            f"{item_label}.max_count",
            optional=True,
        )
        assert isinstance(minimum, int)
        assert maximum is None or isinstance(maximum, int)

        if supplementary and minimum != 0:
            raise CivicGovernanceError(
                f"{item_label}.min_count must be zero for supplementary evidence"
            )
        if maximum is not None and maximum < minimum:
            raise CivicGovernanceError(
                f"{item_label}.max_count must be >= min_count"
            )

        media_types = _sorted_unique_texts(
            item["media_types"],
            f"{item_label}.media_types",
        )
        provenance = _validate_provenance(
            item["provenance"],
            f"{item_label}.provenance",
            source_ids=source_ids,
        )

        roles.append(role)
        result.append(
            GovernanceEvidenceRequirement(
                semantic_role=role,
                min_count=minimum,
                max_count=maximum,
                media_types=media_types,
                provenance=provenance,
            )
        )

    if roles != sorted(roles, key=lambda item: item.encode("utf-8")):
        raise CivicGovernanceError(
            f"{label} must be sorted by semantic_role UTF-8 bytes"
        )
    if len(roles) != len(set(roles)):
        raise CivicGovernanceError(
            f"{label} semantic_role values must be unique"
        )

    return tuple(result)


def _source_ids_from_manifest(
    epoch_manifest: Mapping[str, object],
) -> tuple[str, ...]:
    sources = epoch_manifest["governing_sources"]
    assert isinstance(sources, list)

    result: list[str] = []
    for raw in sources:
        if not isinstance(raw, Mapping):
            raise CivicGovernanceError("governing source descriptor is invalid")
        source_id = raw.get("source_id")
        if not isinstance(source_id, str):
            raise CivicGovernanceError("governing source_id is invalid")
        result.append(source_id)

    return tuple(result)


def _parse_policy(
    value: Mapping[str, object],
    *,
    governing_sources: object,
) -> tuple[
    str,
    bytes,
    tuple[str, ...],
    str,
    str,
    tuple[GovernanceElectorateMember, ...],
    str,
    bool,
    GovernanceThreshold | None,
    GovernanceThreshold | None,
    tuple[GovernanceEvidenceRequirement, ...],
    tuple[GovernanceEvidenceRequirement, ...],
    tuple[str, ...],
]:
    policy = _map(value, "governance policy", POLICY_FIELDS)

    if policy["format"] != POLICY_FORMAT or policy["version"] != POLICY_VERSION:
        raise CivicGovernanceError(
            "governance policy format/version is unsupported"
        )

    policy_id = _text(policy["policy_id"], "policy_id")
    declared_source_set_sha256 = _sha256(
        policy["source_set_sha256"],
        "source_set_sha256",
    )
    assert isinstance(declared_source_set_sha256, bytes)

    try:
        actual_source_set_sha256 = governing_source_set_sha256(
            governing_sources
        )
    except CivicGoverningProfileError as exc:
        raise CivicGovernanceError(str(exc)) from exc

    if declared_source_set_sha256 != actual_source_set_sha256:
        raise CivicGovernanceError(
            "governance policy source_set_sha256 does not match governing sources"
        )

    if not isinstance(governing_sources, list):
        raise CivicGovernanceError("governing_sources must be an array")

    source_ids_list: list[str] = []
    for index, raw in enumerate(governing_sources):
        if not isinstance(raw, Mapping):
            raise CivicGovernanceError(
                f"governing_sources[{index}] must be a map"
            )
        source_id = raw.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise CivicGovernanceError(
                f"governing_sources[{index}].source_id is invalid"
            )
        source_ids_list.append(source_id)
    source_ids = tuple(source_ids_list)
    source_id_set = frozenset(source_ids)

    transition_kinds = _sorted_unique_texts(
        policy["transition_kinds"],
        "transition_kinds",
        nonempty=True,
        permitted=TRANSITION_KINDS,
    )

    electorate = _map(
        policy["electorate"],
        "electorate",
        ELECTORATE_FIELDS,
    )

    electorate_basis = _text(
        electorate["basis"],
        "electorate.basis",
    )
    if electorate_basis not in ELECTORATE_BASES:
        raise CivicGovernanceError("electorate.basis is unsupported")

    standing_class = _text(
        electorate["standing_class"],
        "electorate.standing_class",
    )

    membership_rule = _text(
        electorate["membership_rule"],
        "electorate.membership_rule",
    )
    if membership_rule not in MEMBERSHIP_RULES:
        raise CivicGovernanceError(
            "electorate.membership_rule is unsupported"
        )

    weight_mode = _text(
        electorate["weight_mode"],
        "electorate.weight_mode",
    )
    if weight_mode not in WEIGHT_MODES:
        raise CivicGovernanceError("electorate.weight_mode is unsupported")

    members_raw = electorate["members"]
    if not isinstance(members_raw, list) or not members_raw:
        raise CivicGovernanceError(
            "electorate.members must be a nonempty array"
        )

    members: list[GovernanceElectorateMember] = []
    member_ids: list[bytes] = []

    for index, raw in enumerate(members_raw):
        label = f"electorate.members[{index}]"
        member = _map(raw, label, ELECTORATE_MEMBER_FIELDS)

        participant_id = _sha256(
            member["participant_record_sha256"],
            f"{label}.participant_record_sha256",
        )
        weight = _uint(
            member["weight"],
            f"{label}.weight",
            positive=True,
        )
        assert isinstance(participant_id, bytes)
        assert isinstance(weight, int)

        if weight_mode == "equal" and weight != 1:
            raise CivicGovernanceError(
                "equal-weight electorate members must have weight 1"
            )

        member_ids.append(participant_id)
        members.append(
            GovernanceElectorateMember(
                participant_record_sha256=participant_id,
                weight=weight,
            )
        )

    if member_ids != sorted(member_ids):
        raise CivicGovernanceError(
            "electorate.members must be sorted by participant_record_sha256"
        )
    if len(member_ids) != len(set(member_ids)):
        raise CivicGovernanceError(
            "electorate member participant identities must be unique"
        )

    operator_must_be_elector = _bool(
        electorate["operator_must_be_elector"],
        "electorate.operator_must_be_elector",
    )

    _validate_provenance(
        electorate["provenance"],
        "electorate.provenance",
        source_ids=source_id_set,
    )

    decision_rule = _map(
        policy["decision_rule"],
        "decision_rule",
        DECISION_RULE_FIELDS,
    )
    quorum = _validate_threshold(
        decision_rule["quorum"],
        "decision_rule.quorum",
        quorum=True,
    )
    approval = _validate_threshold(
        decision_rule["approval"],
        "decision_rule.approval",
        quorum=False,
    )
    _validate_provenance(
        decision_rule["provenance"],
        "decision_rule.provenance",
        source_ids=source_id_set,
    )

    authority_evidence = _validate_evidence_requirements(
        policy["authority_evidence"],
        "authority_evidence",
        source_ids=source_id_set,
        supplementary=False,
    )
    supplementary_evidence = _validate_evidence_requirements(
        policy["supplementary_evidence"],
        "supplementary_evidence",
        source_ids=source_id_set,
        supplementary=True,
    )

    if (
        approval is None
        and not any(item.min_count > 0 for item in authority_evidence)
    ):
        raise CivicGovernanceError(
            "evidence-only governance requires required authority evidence"
        )

    _validate_provenance(
        policy["provenance"],
        "provenance",
        source_ids=source_id_set,
    )

    try:
        encode_deterministic(dict(policy))
    except CivicCodecError as exc:
        raise CivicGovernanceError(str(exc)) from exc

    return (
        policy_id,
        declared_source_set_sha256,
        transition_kinds,
        electorate_basis,
        standing_class,
        tuple(members),
        weight_mode,
        operator_must_be_elector,
        quorum,
        approval,
        authority_evidence,
        supplementary_evidence,
        source_ids,
    )


def validate_governance_policy(
    value: Mapping[str, object],
    *,
    governing_sources: object,
) -> None:
    """Validate one canonical logical governance-policy value."""

    _parse_policy(value, governing_sources=governing_sources)


def encode_governance_policy(
    value: Mapping[str, object],
    *,
    governing_sources: object,
) -> bytes:
    """Encode one canonical governance-policy value."""

    validate_governance_policy(
        value,
        governing_sources=governing_sources,
    )
    return encode_deterministic(dict(value))


def decode_governance_policy(
    data: bytes,
    *,
    governing_sources: object,
) -> dict[str, object]:
    """Decode exact deterministic-CBOR governance-policy bytes."""

    try:
        value = decode_deterministic(data)
    except CivicCodecError as exc:
        raise CivicGovernanceError(str(exc)) from exc

    if (
        not isinstance(value, dict)
        or any(not isinstance(key, str) for key in value)
    ):
        raise CivicGovernanceError(
            "governance policy must decode to a text-keyed map"
        )

    validate_governance_policy(
        value,
        governing_sources=governing_sources,
    )
    return value  # type: ignore[return-value]


def governance_policy_sha256(
    value_or_bytes: Mapping[str, object] | bytes,
    *,
    governing_sources: object,
) -> bytes:
    """Return SHA-256 identity of exact canonical governance-policy bytes."""

    if isinstance(value_or_bytes, bytes):
        decode_governance_policy(
            value_or_bytes,
            governing_sources=governing_sources,
        )
        data = value_or_bytes
    else:
        data = encode_governance_policy(
            value_or_bytes,
            governing_sources=governing_sources,
        )

    return hashlib.sha256(data).digest()


def _verify_object_descriptor(
    exact_bytes: bytes,
    digest: bytes,
    *,
    epoch_manifest: Mapping[str, object],
    media_type: str,
    semantic_role: str,
    label: str,
) -> None:
    object_index = epoch_manifest["object_index"]
    assert isinstance(object_index, list)

    matches = [
        item
        for item in object_index
        if isinstance(item, Mapping) and item.get("sha256") == digest
    ]

    if len(matches) != 1:
        raise CivicGovernanceError(
            f"Epoch Manifest must contain exactly one {label} object descriptor"
        )

    descriptor = matches[0]

    if descriptor.get("byte_length") != len(exact_bytes):
        raise CivicGovernanceError(
            f"{label} object descriptor byte_length does not match exact bytes"
        )
    if descriptor.get("media_type") != media_type:
        raise CivicGovernanceError(
            f"{label} object descriptor media_type is invalid"
        )
    if descriptor.get("semantic_role") != semantic_role:
        raise CivicGovernanceError(
            f"{label} object descriptor semantic_role is invalid"
        )

    inline = descriptor.get("inline")
    if inline is not None and inline != exact_bytes:
        raise CivicGovernanceError(
            f"{label} object descriptor inline bytes do not match exact bytes"
        )


def verify_governance_policy(
    policy_bytes: bytes,
    *,
    ceremony: VerifiedCeremonyRecord,
    epoch_manifest: Mapping[str, object],
) -> VerifiedGovernancePolicy:
    """Verify exact governance-policy bytes against ceremony and manifest."""

    try:
        validate_epoch_manifest(epoch_manifest)
    except CivicManifestError as exc:
        raise CivicGovernanceError(
            "referenced Epoch Manifest is invalid"
        ) from exc

    if not isinstance(ceremony, VerifiedCeremonyRecord):
        raise CivicGovernanceError(
            "ceremony must be a VerifiedCeremonyRecord"
        )
    if not isinstance(policy_bytes, bytes):
        raise CivicGovernanceError(
            "governance policy exact bytes must be bytes"
        )

    governing_sources = epoch_manifest["governing_sources"]
    policy_value = decode_governance_policy(
        policy_bytes,
        governing_sources=governing_sources,
    )
    digest = hashlib.sha256(policy_bytes).digest()

    ceremony_policy = ceremony.value["governance_policy"]
    assert isinstance(ceremony_policy, Mapping)

    if ceremony_policy["policy_id"] != policy_value["policy_id"]:
        raise CivicGovernanceError(
            "governance policy_id does not match ceremony"
        )
    if ceremony_policy["policy_sha256"] != digest:
        raise CivicGovernanceError(
            "governance policy SHA-256 does not match ceremony"
        )

    ceremony_profile = ceremony.value["governing_profile"]
    assert isinstance(ceremony_profile, Mapping)

    if (
        policy_value["source_set_sha256"]
        != ceremony_profile["source_set_sha256"]
    ):
        raise CivicGovernanceError(
            "governance policy source_set_sha256 does not match ceremony governing profile"
        )

    (
        policy_id,
        source_set_sha256,
        transition_kinds,
        electorate_basis,
        standing_class,
        members,
        weight_mode,
        operator_must_be_elector,
        quorum,
        approval,
        authority_evidence,
        supplementary_evidence,
        source_ids,
    ) = _parse_policy(
        policy_value,
        governing_sources=governing_sources,
    )

    if ceremony.transition_kind not in transition_kinds:
        raise CivicGovernanceError(
            "governance policy does not permit ceremony transition kind"
        )

    expected_basis = (
        "candidate_participants"
        if ceremony.transition_kind == "bootstrap"
        else "predecessor_participants"
    )
    if electorate_basis != expected_basis:
        raise CivicGovernanceError(
            "governance policy electorate basis does not match transition kind"
        )

    if operator_must_be_elector:
        member_ids = {
            item.participant_record_sha256
            for item in members
        }
        operator_id = ceremony.value[
            "operator_participant_record_sha256"
        ]
        if operator_id not in member_ids:
            raise CivicGovernanceError(
                "ceremony operator is required to be an electorate member"
            )

    _verify_object_descriptor(
        policy_bytes,
        digest,
        epoch_manifest=epoch_manifest,
        media_type=POLICY_MEDIA_TYPE,
        semantic_role=POLICY_SEMANTIC_ROLE,
        label="governance-policy",
    )

    return VerifiedGovernancePolicy(
        exact_bytes=policy_bytes,
        policy_sha256=digest,
        policy_id=policy_id,
        source_set_sha256=source_set_sha256,
        transition_kinds=transition_kinds,
        electorate_basis=electorate_basis,
        electorate_standing_class=standing_class,
        electorate_members=members,
        weight_mode=weight_mode,
        operator_must_be_elector=operator_must_be_elector,
        quorum=quorum,
        approval=approval,
        authority_evidence=authority_evidence,
        supplementary_evidence=supplementary_evidence,
        source_ids=source_ids,
    )


def canonical_governance_transition_subject(
    ceremony: VerifiedCeremonyRecord | Mapping[str, object],
) -> dict[str, object]:
    """Return the deterministic non-recursive governance subject projection."""

    if isinstance(ceremony, VerifiedCeremonyRecord):
        value = ceremony.value
    else:
        value = ceremony
        try:
            validate_ceremony_record(value)
        except CivicCeremonyError as exc:
            raise CivicGovernanceError(str(exc)) from exc

    return {
        "format": SUBJECT_FORMAT,
        "version": SUBJECT_VERSION,
        "crypto_profile": value["crypto_profile"],
        "transition_kind": value["transition_kind"],
        "hoa_root_id": value["hoa_root_id"],
        "epoch_sequence": value["epoch_sequence"],
        "predecessor_manifest_sha256": value[
            "predecessor_manifest_sha256"
        ],
        "effective_time_ms": value["effective_time_ms"],
        "governing_profile": value["governing_profile"],
        "participants": value["participants"],
        "operator_participant_record_sha256": value[
            "operator_participant_record_sha256"
        ],
        "signing_node": value["signing_node"],
        "governance_policy": value["governance_policy"],
    }


def encode_governance_transition_subject(
    ceremony: VerifiedCeremonyRecord | Mapping[str, object],
) -> bytes:
    """Encode the canonical governance transition subject."""

    value = canonical_governance_transition_subject(ceremony)

    if set(value) != SUBJECT_FIELDS:
        raise CivicGovernanceError(
            "governance transition subject fields are invalid"
        )

    try:
        return encode_deterministic(value)
    except CivicCodecError as exc:
        raise CivicGovernanceError(str(exc)) from exc


def governance_transition_subject_sha256(
    ceremony: VerifiedCeremonyRecord | Mapping[str, object],
) -> bytes:
    """Return exact SHA-256 identity of the derived transition subject."""

    return hashlib.sha256(
        encode_governance_transition_subject(ceremony)
    ).digest()


def _validate_evidence_descriptors(
    value: object,
    label: str,
) -> tuple[GovernanceEvidenceDescriptor, ...]:
    if not isinstance(value, list):
        raise CivicGovernanceError(f"{label} must be an array")

    result: list[GovernanceEvidenceDescriptor] = []
    hashes: list[bytes] = []

    for index, raw in enumerate(value):
        item_label = f"{label}[{index}]"
        item = _map(raw, item_label, EVIDENCE_DESCRIPTOR_FIELDS)

        digest = _sha256(item["sha256"], f"{item_label}.sha256")
        byte_length = _uint(
            item["byte_length"],
            f"{item_label}.byte_length",
        )
        media_type = _text(
            item["media_type"],
            f"{item_label}.media_type",
        )
        semantic_role = _text(
            item["semantic_role"],
            f"{item_label}.semantic_role",
        )

        assert isinstance(digest, bytes)
        assert isinstance(byte_length, int)

        hashes.append(digest)
        result.append(
            GovernanceEvidenceDescriptor(
                sha256=digest,
                byte_length=byte_length,
                media_type=media_type,
                semantic_role=semantic_role,
            )
        )

    if hashes != sorted(hashes):
        raise CivicGovernanceError(
            f"{label} must be sorted by SHA-256 bytes"
        )
    if len(hashes) != len(set(hashes)):
        raise CivicGovernanceError(
            f"{label} evidence SHA-256 values must be unique"
        )

    return tuple(result)


def _parse_proof_payload(
    value: Mapping[str, object],
) -> tuple[
    bytes,
    str,
    bytes,
    bytes,
    bytes,
    str | None,
    tuple[GovernanceEvidenceDescriptor, ...],
    tuple[GovernanceEvidenceDescriptor, ...],
]:
    proof = _map(value, "governance proof", PROOF_FIELDS)

    if proof["format"] != PROOF_FORMAT or proof["version"] != PROOF_VERSION:
        raise CivicGovernanceError(
            "governance proof format/version is unsupported"
        )
    if proof["crypto_profile"] != CRYPTO_PROFILE:
        raise CivicGovernanceError(
            "governance proof cryptographic profile is unsupported"
        )

    subject_sha256 = _sha256(
        proof["subject_sha256"],
        "subject_sha256",
    )
    assert isinstance(subject_sha256, bytes)

    policy = _map(
        proof["governance_policy"],
        "governance_policy",
        PROOF_POLICY_FIELDS,
    )
    policy_id = _text(
        policy["policy_id"],
        "governance_policy.policy_id",
    )
    policy_sha256 = _sha256(
        policy["policy_sha256"],
        "governance_policy.policy_sha256",
    )
    assert isinstance(policy_sha256, bytes)

    signer = _map(
        proof["signer"],
        "signer",
        PROOF_SIGNER_FIELDS,
    )
    participant_id = _sha256(
        signer["participant_record_sha256"],
        "signer.participant_record_sha256",
    )
    participant_key_id = _sha256(
        signer["participant_key_id"],
        "signer.participant_key_id",
    )
    assert isinstance(participant_id, bytes)
    assert isinstance(participant_key_id, bytes)

    decision_raw = proof["decision"]
    if decision_raw is None:
        decision = None
    else:
        decision = _text(decision_raw, "decision")
        if decision not in DECISIONS:
            raise CivicGovernanceError("decision is unsupported")

    authority_evidence = _validate_evidence_descriptors(
        proof["authority_evidence"],
        "authority_evidence",
    )
    supplementary_evidence = _validate_evidence_descriptors(
        proof["supplementary_evidence"],
        "supplementary_evidence",
    )

    all_evidence_hashes = [
        item.sha256
        for item in (*authority_evidence, *supplementary_evidence)
    ]
    if len(all_evidence_hashes) != len(set(all_evidence_hashes)):
        raise CivicGovernanceError(
            "one evidence SHA-256 must not appear more than once in a governance proof"
        )

    try:
        encode_deterministic(dict(proof))
    except CivicCodecError as exc:
        raise CivicGovernanceError(str(exc)) from exc

    return (
        subject_sha256,
        policy_id,
        policy_sha256,
        participant_id,
        participant_key_id,
        decision,
        authority_evidence,
        supplementary_evidence,
    )


def validate_governance_proof_payload(
    value: Mapping[str, object],
) -> None:
    """Validate one logical unsigned governance-proof payload."""

    _parse_proof_payload(value)


def encode_governance_proof_payload(
    value: Mapping[str, object],
) -> bytes:
    """Encode one canonical governance-proof payload."""

    validate_governance_proof_payload(value)
    return encode_deterministic(dict(value))


def decode_governance_proof_payload(
    data: bytes,
) -> dict[str, object]:
    """Decode exact deterministic-CBOR governance-proof payload bytes."""

    try:
        value = decode_deterministic(data)
    except CivicCodecError as exc:
        raise CivicGovernanceError(str(exc)) from exc

    if (
        not isinstance(value, dict)
        or any(not isinstance(key, str) for key in value)
    ):
        raise CivicGovernanceError(
            "governance proof payload must decode to a text-keyed map"
        )

    validate_governance_proof_payload(value)
    return value  # type: ignore[return-value]


def sign_governance_proof_fixture(
    payload: Mapping[str, object],
    *,
    expected_public_key: bytes,
    private_scalar: int,
    nonce_scalar: int,
) -> bytes:
    """Create a deterministic fixture-only signed governance proof.

    This helper does not generate or persist production key material.
    """

    (
        _,
        _,
        _,
        _,
        participant_key_id,
        _,
        _,
        _,
    ) = _parse_proof_payload(payload)

    try:
        fixture_public_key = public_key_from_private_scalar(private_scalar)
        if fixture_public_key != expected_public_key:
            raise CivicGovernanceError(
                "fixture private scalar does not match expected proof signer public key"
            )

        if derive_key_id(expected_public_key) != participant_key_id:
            raise CivicGovernanceError(
                "proof signer participant_key_id does not match expected public key"
            )

        payload_bytes = encode_governance_proof_payload(payload)
        sig_structure = build_sig_structure(
            payload_bytes,
            participant_key_id,
            content_type=PROOF_CONTENT_TYPE,
        )
        signature = sign_sig_structure_fixture(
            private_scalar=private_scalar,
            nonce_scalar=nonce_scalar,
            sig_structure=sig_structure,
        )
        return build_cose_sign1(
            payload_bytes,
            participant_key_id,
            signature,
            content_type=PROOF_CONTENT_TYPE,
        )
    except (CivicManifestError, CivicCoseError, CivicEcdsaError) as exc:
        raise CivicGovernanceError(str(exc)) from exc


def _resolve_policy_member(
    policy: VerifiedGovernancePolicy,
    participant_id: bytes,
) -> GovernanceElectorateMember:
    matches = [
        item
        for item in policy.electorate_members
        if item.participant_record_sha256 == participant_id
    ]
    if len(matches) != 1:
        raise CivicGovernanceError(
            "governance proof signer is not exactly one policy electorate member"
        )
    return matches[0]


def _resolve_proof_signer_public_key(
    participant_id: bytes,
    participant_key_id: bytes,
    *,
    ceremony: VerifiedCeremonyRecord,
    predecessor_manifest: Mapping[str, object] | None,
) -> bytes:
    if ceremony.transition_kind == "bootstrap":
        participants = ceremony.value["participants"]
        assert isinstance(participants, list)
    else:
        if predecessor_manifest is None:
            raise CivicGovernanceError(
                "successor governance proof verification requires predecessor manifest"
            )
        try:
            validate_epoch_manifest(predecessor_manifest)
        except CivicManifestError as exc:
            raise CivicGovernanceError(
                "predecessor Epoch Manifest is invalid"
            ) from exc
        participants = predecessor_manifest["participants"]
        assert isinstance(participants, list)

    matches = [
        item
        for item in participants
        if (
            isinstance(item, Mapping)
            and item.get("participant_record_sha256") == participant_id
        )
    ]
    if len(matches) != 1:
        raise CivicGovernanceError(
            "governance proof signer is not uniquely present in required participant set"
        )

    participant = matches[0]
    expected_key_id = participant.get("participant_key_id")
    public_key = participant.get("participant_public_key")

    if expected_key_id != participant_key_id:
        raise CivicGovernanceError(
            "governance proof signer key does not match required participant epoch key"
        )
    if not isinstance(public_key, bytes):
        raise CivicGovernanceError(
            "resolved governance proof signer public key is invalid"
        )

    try:
        if derive_key_id(public_key) != participant_key_id:
            raise CivicGovernanceError(
                "resolved governance proof signer key identifier does not match public key"
            )
    except CivicManifestError as exc:
        raise CivicGovernanceError(str(exc)) from exc

    return public_key


def verify_signed_governance_proof(
    proof_bytes: bytes,
    *,
    expected_proof_sha256: bytes,
    ceremony: VerifiedCeremonyRecord,
    policy: VerifiedGovernancePolicy,
    epoch_manifest: Mapping[str, object],
    predecessor_manifest: Mapping[str, object] | None = None,
) -> VerifiedGovernanceProof:
    """Verify one signed governance proof and its exact authority bindings."""

    if not isinstance(proof_bytes, bytes):
        raise CivicGovernanceError(
            "governance proof exact bytes must be bytes"
        )
    expected_digest = _sha256(
        expected_proof_sha256,
        "expected_proof_sha256",
    )
    assert isinstance(expected_digest, bytes)

    if expected_digest not in ceremony.governance_proof_sha256:
        raise CivicGovernanceError(
            "expected governance proof is not listed by ceremony"
        )

    actual_digest = hashlib.sha256(proof_bytes).digest()
    if actual_digest != expected_digest:
        raise CivicGovernanceError(
            "governance proof SHA-256 does not match expected identity"
        )

    try:
        validate_epoch_manifest(epoch_manifest)
    except CivicManifestError as exc:
        raise CivicGovernanceError(
            "referenced Epoch Manifest is invalid"
        ) from exc

    try:
        parsed = parse_cose_sign1(
            proof_bytes,
            expected_content_type=PROOF_CONTENT_TYPE,
        )
    except CivicCoseError as exc:
        raise CivicGovernanceError(str(exc)) from exc

    payload = decode_governance_proof_payload(parsed.payload)
    (
        subject_sha256,
        policy_id,
        policy_sha256,
        participant_id,
        participant_key_id,
        decision,
        authority_evidence,
        supplementary_evidence,
    ) = _parse_proof_payload(payload)

    expected_subject_sha256 = governance_transition_subject_sha256(
        ceremony
    )
    if subject_sha256 != expected_subject_sha256:
        raise CivicGovernanceError(
            "governance proof subject_sha256 does not match ceremony transition subject"
        )

    if (
        policy_id != policy.policy_id
        or policy_sha256 != policy.policy_sha256
    ):
        raise CivicGovernanceError(
            "governance proof policy descriptor does not match verified governance policy"
        )

    _resolve_policy_member(policy, participant_id)

    public_key = _resolve_proof_signer_public_key(
        participant_id,
        participant_key_id,
        ceremony=ceremony,
        predecessor_manifest=predecessor_manifest,
    )

    if parsed.key_id != participant_key_id:
        raise CivicGovernanceError(
            "COSE kid does not match governance proof signer participant_key_id"
        )

    if policy.approval is None and decision is not None:
        raise CivicGovernanceError(
            "evidence-only governance policy does not permit non-null decisions"
        )

    try:
        sig_structure = build_sig_structure(
            parsed.payload,
            parsed.key_id,
            content_type=PROOF_CONTENT_TYPE,
        )
        valid = verify_sig_structure(
            public_key,
            sig_structure,
            parsed.signature,
        )
    except (CivicCoseError, CivicEcdsaError) as exc:
        raise CivicGovernanceError(str(exc)) from exc

    if not valid:
        raise CivicGovernanceError(
            "governance proof signature is invalid"
        )

    _verify_object_descriptor(
        proof_bytes,
        actual_digest,
        epoch_manifest=epoch_manifest,
        media_type=PROOF_MEDIA_TYPE,
        semantic_role=PROOF_SEMANTIC_ROLE,
        label="governance-proof",
    )

    return VerifiedGovernanceProof(
        signed_bytes=proof_bytes,
        proof_sha256=actual_digest,
        payload=payload,
        subject_sha256=subject_sha256,
        policy_id=policy_id,
        policy_sha256=policy_sha256,
        participant_record_sha256=participant_id,
        participant_key_id=participant_key_id,
        participant_public_key=public_key,
        decision=decision,
        authority_evidence=authority_evidence,
        supplementary_evidence=supplementary_evidence,
    )
