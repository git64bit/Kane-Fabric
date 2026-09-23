from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import unittest

from civic.accepted_participant_standing import (
    StandingEvidence,
    StandingProfileContext,
    StandingProfileRequest,
)
from civic.governing_profile import (
    FORMAT,
    VERSION,
    PROFILE_MEDIA_TYPE,
    PROFILE_SEMANTIC_ROLE,
    CivicGoverningProfileError,
    add_utc_calendar_months,
    canonical_governing_source_set,
    decode_governing_profile,
    encode_governing_profile,
    governing_profile_sha256,
    governing_source_set_sha256,
    make_standing_semantics_validator,
    validate_governing_profile,
    validate_standing_against_profile,
    verify_governing_profile,
)
from civic.tests.test_epoch_manifest import fixture_manifest, h


PROFILE_ID = "kane-il-condominium-standing-v1"
STANDING_CLASS = "current-unit-owner-participant"
QUALIFICATION_PATH = "unit-owner-record"
PARTICIPATION_POLICY = "kane-sase-six-month-v1"

QUALIFICATION_BYTES = b"fixture unit-owner evidence\n"
QUALIFICATION_SHA256 = hashlib.sha256(QUALIFICATION_BYTES).digest()

SUPPLEMENTARY_SHA256 = hashlib.sha256(
    b"fixture supplementary corroboration\n"
).digest()


def _utc_ms(year: int, month: int, day: int) -> int:
    return int(
        datetime(
            year,
            month,
            day,
            tzinfo=timezone.utc,
        ).timestamp()
        * 1000
    )


def governing_sources_fixture() -> list[dict[str, object]]:
    declaration = b"fixture declaration\n"
    statute = b"fixture statute\n"

    return [
        {
            "source_id": "declaration",
            "role": "condominium-instrument",
            "sha256": hashlib.sha256(declaration).digest(),
            "byte_length": len(declaration),
            "media_type": "text/plain",
            "title": "Fixture Declaration",
            "source_uri": "https://example.invalid/declaration",
        },
        {
            "source_id": "statute",
            "role": "statute",
            "sha256": hashlib.sha256(statute).digest(),
            "byte_length": len(statute),
            "media_type": "text/plain",
            "title": "Fixture Statute",
            "source_uri": "https://example.invalid/statute",
        },
    ]


def profile_fixture(
    governing_sources: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    sources = (
        governing_sources
        if governing_sources is not None
        else governing_sources_fixture()
    )

    return {
        "format": FORMAT,
        "version": VERSION,
        "profile_id": PROFILE_ID,
        "source_set_sha256": governing_source_set_sha256(sources),
        "standing_classes": [
            {
                "standing_class": STANDING_CLASS,
                "qualification_path_ids": [QUALIFICATION_PATH],
                "participation_required": True,
                "participation_policy_ids": [PARTICIPATION_POLICY],
                "allow_open_ended_standing": False,
                "maximum_standing_duration": {
                    "kind": "calendar_months",
                    "value": 6,
                },
                "provenance": {
                    "kind": "governing_source",
                    "source_ids": ["declaration", "statute"],
                },
            }
        ],
        "qualification_paths": [
            {
                "path_id": QUALIFICATION_PATH,
                "permitted_claim_responsibility": [
                    "participant_claimed",
                ],
                "authority_evidence": [
                    {
                        "semantic_role": "unit-owner-evidence",
                        "min_count": 1,
                        "max_count": 1,
                        "media_types": [
                            "application/pdf",
                            "text/plain",
                        ],
                    }
                ],
                "supplementary_evidence": [
                    {
                        "semantic_role": "corroboration",
                        "min_count": 0,
                        "max_count": 2,
                        "media_types": [],
                    }
                ],
                "provenance": {
                    "kind": "governing_source",
                    "source_ids": ["declaration", "statute"],
                },
            }
        ],
        "participation_policies": [
            {
                "policy_id": PARTICIPATION_POLICY,
                "attestation_mode": "recording_operator",
                "interval_rule": {
                    "kind": "calendar_months",
                    "value": 6,
                },
                "authority_evidence": [],
                "supplementary_evidence": [
                    {
                        "semantic_role": "sase-corroboration",
                        "min_count": 0,
                        "max_count": 1,
                        "media_types": [],
                    }
                ],
                "provenance": {
                    "kind": "civic_mechanism",
                    "source_ids": [],
                },
            }
        ],
    }


def manifest_with_profile(
    profile: dict[str, object] | None = None,
    governing_sources: list[dict[str, object]] | None = None,
) -> tuple[dict[str, object], dict[str, object], bytes]:
    sources = (
        copy.deepcopy(governing_sources)
        if governing_sources is not None
        else governing_sources_fixture()
    )
    profile_value = (
        copy.deepcopy(profile)
        if profile is not None
        else profile_fixture(sources)
    )
    profile_bytes = encode_governing_profile(
        profile_value,
        governing_sources=sources,
    )
    profile_sha256 = hashlib.sha256(profile_bytes).digest()

    manifest = fixture_manifest()
    manifest["governing_sources"] = sources
    manifest["governing_profile"] = {
        "profile_id": profile_value["profile_id"],
        "profile_sha256": profile_sha256,
        "source_set_sha256": profile_value["source_set_sha256"],
    }

    object_index = manifest["object_index"]
    assert isinstance(object_index, list)
    object_index.append(
        {
            "sha256": profile_sha256,
            "byte_length": len(profile_bytes),
            "media_type": PROFILE_MEDIA_TYPE,
            "semantic_role": PROFILE_SEMANTIC_ROLE,
            "name": "governing-profile.cbor",
            "cid": None,
            "inline": profile_bytes,
        }
    )
    object_index.sort(key=lambda item: item["sha256"])

    return manifest, profile_value, profile_bytes


def standing_request(
    *,
    valid_from_ms: int | None = None,
    valid_until_ms: int | None = None,
    participation_valid_from_ms: int | None = None,
    participation_valid_until_ms: int | None = None,
    claim_responsibility: str = "participant_claimed",
    qualification_media_type: str = "application/pdf",
    qualification_role: str = "unit-owner-evidence",
    include_qualification_evidence: bool = True,
    participation_required: bool = True,
    participation_policy_id: str | None = PARTICIPATION_POLICY,
) -> StandingProfileRequest:
    start = (
        valid_from_ms
        if valid_from_ms is not None
        else _utc_ms(2027, 1, 31)
    )
    end = (
        valid_until_ms
        if valid_until_ms is not None
        else add_utc_calendar_months(start, 6)
    )
    participation_start = (
        participation_valid_from_ms
        if participation_valid_from_ms is not None
        else start
    )
    participation_end = (
        participation_valid_until_ms
        if participation_valid_until_ms is not None
        else add_utc_calendar_months(participation_start, 6)
    )

    qualification_evidence = (
        (
            StandingEvidence(
                sha256=QUALIFICATION_SHA256,
                byte_length=len(QUALIFICATION_BYTES),
                media_type=qualification_media_type,
                semantic_role=qualification_role,
            ),
        )
        if include_qualification_evidence
        else ()
    )

    return StandingProfileRequest(
        participant_record_sha256=h(16),
        standing_class=STANDING_CLASS,
        valid_from_ms=start,
        valid_until_ms=end,
        participation_required=participation_required,
        participation_policy_id=participation_policy_id,
        participation_valid_from_ms=(
            participation_start
            if participation_required
            else None
        ),
        participation_valid_until_ms=(
            participation_end
            if participation_required
            else None
        ),
        participation_authority_evidence=(),
        participation_supplementary_evidence=(),
        qualification_path_id=QUALIFICATION_PATH,
        claim_responsibility=claim_responsibility,
        qualification_authority_evidence=qualification_evidence,
        qualification_supplementary_evidence=(),
    )


class CivicGoverningProfileTests(unittest.TestCase):
    def test_valid_profile_round_trips_and_binds_manifest_exact_bytes(self) -> None:
        manifest, profile, profile_bytes = manifest_with_profile()

        decoded = decode_governing_profile(
            profile_bytes,
            governing_sources=manifest["governing_sources"],
        )
        self.assertEqual(profile, decoded)
        self.assertEqual(
            profile_bytes,
            encode_governing_profile(
                decoded,
                governing_sources=manifest["governing_sources"],
            ),
        )

        verified = verify_governing_profile(
            profile_bytes,
            epoch_manifest=manifest,
        )

        self.assertEqual(PROFILE_ID, verified.profile_id)
        self.assertEqual(
            hashlib.sha256(profile_bytes).digest(),
            verified.profile_sha256,
        )
        self.assertEqual(
            profile["source_set_sha256"],
            verified.source_set_sha256,
        )
        self.assertEqual(
            ("declaration", "statute"),
            verified.source_ids,
        )
        self.assertEqual(
            profile_bytes,
            verified.exact_bytes,
        )

    def test_source_set_identity_excludes_title_and_uri_but_binds_semantic_fields(self) -> None:
        sources = governing_sources_fixture()
        baseline = governing_source_set_sha256(sources)

        metadata_only = copy.deepcopy(sources)
        metadata_only[0]["title"] = "Changed display title"
        metadata_only[0]["source_uri"] = "https://elsewhere.invalid/declaration"
        self.assertEqual(
            baseline,
            governing_source_set_sha256(metadata_only),
        )

        semantic_change = copy.deepcopy(sources)
        semantic_change[0]["role"] = "different-role"
        self.assertNotEqual(
            baseline,
            governing_source_set_sha256(semantic_change),
        )

        projection = canonical_governing_source_set(sources)
        projected_source = projection["sources"][0]  # type: ignore[index]
        self.assertNotIn("title", projected_source)
        self.assertNotIn("source_uri", projected_source)

    def test_profile_sha256_changes_with_canonical_profile_semantics(self) -> None:
        sources = governing_sources_fixture()
        profile = profile_fixture(sources)
        baseline = governing_profile_sha256(
            profile,
            governing_sources=sources,
        )

        changed = copy.deepcopy(profile)
        changed["standing_classes"][0]["maximum_standing_duration"]["value"] = 5  # type: ignore[index]
        changed_hash = governing_profile_sha256(
            changed,
            governing_sources=sources,
        )

        self.assertNotEqual(baseline, changed_hash)

    def test_unsorted_and_unused_profile_definitions_are_rejected(self) -> None:
        sources = governing_sources_fixture()

        unsorted = profile_fixture(sources)
        unsorted["qualification_paths"][0]["permitted_claim_responsibility"] = [  # type: ignore[index]
            "participant_claimed",
            "operator_attested",
        ]
        with self.assertRaises(CivicGoverningProfileError):
            validate_governing_profile(
                unsorted,
                governing_sources=sources,
            )

        unused = profile_fixture(sources)
        unused["qualification_paths"].append(  # type: ignore[union-attr]
            {
                "path_id": "unused-path",
                "permitted_claim_responsibility": [
                    "participant_claimed",
                ],
                "authority_evidence": [
                    {
                        "semantic_role": "unit-owner-evidence",
                        "min_count": 1,
                        "max_count": 1,
                        "media_types": [],
                    }
                ],
                "supplementary_evidence": [],
                "provenance": {
                    "kind": "civic_mechanism",
                    "source_ids": [],
                },
            }
        )
        with self.assertRaises(CivicGoverningProfileError):
            validate_governing_profile(
                unused,
                governing_sources=sources,
            )

    def test_provenance_must_reference_declared_governing_source(self) -> None:
        sources = governing_sources_fixture()
        profile = profile_fixture(sources)
        profile["standing_classes"][0]["provenance"]["source_ids"] = [  # type: ignore[index]
            "not-in-source-set"
        ]

        with self.assertRaises(CivicGoverningProfileError):
            validate_governing_profile(
                profile,
                governing_sources=sources,
            )

    def test_open_ended_participation_policy_requires_open_ended_standing_class(self) -> None:
        sources = governing_sources_fixture()
        profile = profile_fixture(sources)
        profile["participation_policies"][0]["interval_rule"] = {  # type: ignore[index]
            "kind": "open_ended",
            "value": None,
        }

        with self.assertRaises(CivicGoverningProfileError):
            validate_governing_profile(
                profile,
                governing_sources=sources,
            )

    def test_manifest_profile_hash_and_object_descriptor_are_authority_bindings(self) -> None:
        manifest, _profile, profile_bytes = manifest_with_profile()

        wrong_hash = copy.deepcopy(manifest)
        wrong_hash["governing_profile"]["profile_sha256"] = h(44)  # type: ignore[index]
        with self.assertRaises(CivicGoverningProfileError):
            verify_governing_profile(
                profile_bytes,
                epoch_manifest=wrong_hash,
            )

        wrong_media = copy.deepcopy(manifest)
        profile_sha = hashlib.sha256(profile_bytes).digest()
        matching = [
            item
            for item in wrong_media["object_index"]  # type: ignore[union-attr]
            if item["sha256"] == profile_sha
        ]
        self.assertEqual(1, len(matching))
        matching[0]["media_type"] = "application/octet-stream"

        with self.assertRaises(CivicGoverningProfileError):
            verify_governing_profile(
                profile_bytes,
                epoch_manifest=wrong_media,
            )

    def test_valid_standing_request_satisfies_profile(self) -> None:
        manifest, _profile, profile_bytes = manifest_with_profile()
        verified = verify_governing_profile(
            profile_bytes,
            epoch_manifest=manifest,
        )

        request = standing_request()
        validate_standing_against_profile(
            verified,
            request,
        )

    def test_claim_responsibility_and_evidence_role_are_profile_enforced(self) -> None:
        manifest, _profile, profile_bytes = manifest_with_profile()
        verified = verify_governing_profile(
            profile_bytes,
            epoch_manifest=manifest,
        )

        with self.assertRaises(CivicGoverningProfileError):
            validate_standing_against_profile(
                verified,
                standing_request(
                    claim_responsibility="operator_attested",
                ),
            )

        with self.assertRaises(CivicGoverningProfileError):
            validate_standing_against_profile(
                verified,
                standing_request(
                    qualification_role="undeclared-role",
                ),
            )

    def test_authority_evidence_count_and_media_type_are_profile_enforced(self) -> None:
        manifest, _profile, profile_bytes = manifest_with_profile()
        verified = verify_governing_profile(
            profile_bytes,
            epoch_manifest=manifest,
        )

        with self.assertRaises(CivicGoverningProfileError):
            validate_standing_against_profile(
                verified,
                standing_request(
                    include_qualification_evidence=False,
                ),
            )

        with self.assertRaises(CivicGoverningProfileError):
            validate_standing_against_profile(
                verified,
                standing_request(
                    qualification_media_type="image/png",
                ),
            )

    def test_participation_requirement_and_calendar_month_interval_are_profile_enforced(self) -> None:
        manifest, _profile, profile_bytes = manifest_with_profile()
        verified = verify_governing_profile(
            profile_bytes,
            epoch_manifest=manifest,
        )

        with self.assertRaises(CivicGoverningProfileError):
            validate_standing_against_profile(
                verified,
                standing_request(
                    participation_required=False,
                    participation_policy_id=None,
                ),
            )

        start = _utc_ms(2027, 1, 31)
        wrong_end = _utc_ms(2027, 7, 30)
        with self.assertRaises(CivicGoverningProfileError):
            validate_standing_against_profile(
                verified,
                standing_request(
                    valid_from_ms=start,
                    valid_until_ms=add_utc_calendar_months(start, 6),
                    participation_valid_from_ms=start,
                    participation_valid_until_ms=wrong_end,
                ),
            )

    def test_calendar_month_addition_clamps_month_end_deterministically(self) -> None:
        january_31 = _utc_ms(2027, 1, 31)
        self.assertEqual(
            _utc_ms(2027, 2, 28),
            add_utc_calendar_months(january_31, 1),
        )

        leap_january_31 = _utc_ms(2028, 1, 31)
        self.assertEqual(
            _utc_ms(2028, 2, 29),
            add_utc_calendar_months(leap_january_31, 1),
        )

        august_31 = _utc_ms(2027, 8, 31)
        self.assertEqual(
            _utc_ms(2028, 2, 29),
            add_utc_calendar_months(august_31, 6),
        )

    def test_maximum_standing_duration_is_profile_enforced(self) -> None:
        manifest, _profile, profile_bytes = manifest_with_profile()
        verified = verify_governing_profile(
            profile_bytes,
            epoch_manifest=manifest,
        )

        start = _utc_ms(2027, 1, 31)
        too_late = add_utc_calendar_months(start, 6) + 1

        with self.assertRaises(CivicGoverningProfileError):
            validate_standing_against_profile(
                verified,
                standing_request(
                    valid_from_ms=start,
                    valid_until_ms=too_late,
                    participation_valid_from_ms=start,
                    participation_valid_until_ms=add_utc_calendar_months(
                        start,
                        6,
                    ),
                ),
            )

    def test_callback_adapter_requires_exact_verified_profile_context(self) -> None:
        manifest, _profile, profile_bytes = manifest_with_profile()
        verified = verify_governing_profile(
            profile_bytes,
            epoch_manifest=manifest,
        )
        validator = make_standing_semantics_validator(
            verified,
        )

        context = StandingProfileContext(
            profile_id=verified.profile_id,
            profile_sha256=verified.profile_sha256,
            source_set_sha256=verified.source_set_sha256,
            profile_bytes=verified.exact_bytes,
            governing_sources=(),
        )
        validator(
            context,
            standing_request(),
        )

        wrong_context = StandingProfileContext(
            profile_id=verified.profile_id,
            profile_sha256=h(55),
            source_set_sha256=verified.source_set_sha256,
            profile_bytes=verified.exact_bytes,
            governing_sources=(),
        )

        with self.assertRaises(CivicGoverningProfileError):
            validator(
                wrong_context,
                standing_request(),
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
