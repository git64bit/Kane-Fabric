from __future__ import annotations

import hashlib
import unittest

from civic.accepted_participant_standing import (
    RECORD_TYPE,
    CivicParticipantStandingError,
    verify_accepted_participant_standing,
)
from civic.ecdsa import public_key_from_private_scalar
from civic.epoch_manifest import CRYPTO_PROFILE, derive_key_id
from civic.governing_profile import (
    PROFILE_MEDIA_TYPE,
    PROFILE_SEMANTIC_ROLE,
    encode_governing_profile,
    governing_source_set_sha256,
)
from civic.signed_history_record import (
    sign_history_record_fixture,
    verify_signed_history_record,
)
from civic.tests.test_epoch_manifest import P1, P2, fixture_manifest, h


P3 = public_key_from_private_scalar(3)

PROFILE_ID = "illinois-condominium-standing-v1"
STANDING_CLASS = "current-unit-owner-participant"
QUALIFICATION_PATH = "participant-claim-with-record-evidence"
PARTICIPATION_POLICY = "kane-sase-six-month-v1"

SOURCE_BYTES = b"fixture governing source for standing\n"
SOURCE_SHA256 = hashlib.sha256(SOURCE_BYTES).digest()

GOVERNING_SOURCES = [
    {
        "source_id": "fixture-governing-source",
        "role": "governing",
        "sha256": SOURCE_SHA256,
        "byte_length": len(SOURCE_BYTES),
        "media_type": "text/plain",
        "title": "Fixture governing source",
        "source_uri": None,
    }
]

SOURCE_SET_SHA256 = governing_source_set_sha256(GOVERNING_SOURCES)

PROFILE_VALUE = {
    "format": "kane-civic-governing-profile",
    "version": 1,
    "profile_id": PROFILE_ID,
    "source_set_sha256": SOURCE_SET_SHA256,
    "standing_classes": [
        {
            "standing_class": STANDING_CLASS,
            "qualification_path_ids": [QUALIFICATION_PATH],
            "participation_required": True,
            "participation_policy_ids": [PARTICIPATION_POLICY],
            "allow_open_ended_standing": False,
            "maximum_standing_duration": None,
            "provenance": {
                "kind": "governing_source",
                "source_ids": ["fixture-governing-source"],
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
                    "semantic_role": "standing-qualification-evidence",
                    "min_count": 1,
                    "max_count": 1,
                    "media_types": ["text/plain"],
                }
            ],
            "supplementary_evidence": [
                {
                    "semantic_role": "supplementary-corroboration",
                    "min_count": 0,
                    "max_count": 1,
                    "media_types": ["application/octet-stream"],
                }
            ],
            "provenance": {
                "kind": "governing_source",
                "source_ids": ["fixture-governing-source"],
            },
        }
    ],
    "participation_policies": [
        {
            "policy_id": PARTICIPATION_POLICY,
            "attestation_mode": "recording_operator",
            "interval_rule": {
                "kind": "explicit_bounded",
                "value": None,
            },
            "authority_evidence": [],
            "supplementary_evidence": [],
            "provenance": {
                "kind": "civic_mechanism",
                "source_ids": [],
            },
        }
    ],
}

PROFILE_BYTES = encode_governing_profile(
    PROFILE_VALUE,
    governing_sources=GOVERNING_SOURCES,
)
PROFILE_SHA256 = hashlib.sha256(PROFILE_BYTES).digest()

QUALIFICATION_BYTES = b"fixture qualification evidence\n"
QUALIFICATION_SHA256 = hashlib.sha256(QUALIFICATION_BYTES).digest()

SUPPLEMENTARY_SHA256 = hashlib.sha256(
    b"supplementary evidence not retained\n"
).digest()

VALID_FROM_MS = 1_800_000_000_000
VALID_UNTIL_MS = 1_800_000_600_000
EVALUATION_TIME_MS = 1_800_000_300_000


def _object_descriptor(
    *,
    sha256: bytes,
    byte_length: int,
    media_type: str,
    semantic_role: str,
    inline: bytes | None = None,
    name: str | None = None,
) -> dict[str, object]:
    return {
        "sha256": sha256,
        "byte_length": byte_length,
        "media_type": media_type,
        "semantic_role": semantic_role,
        "name": name,
        "cid": None,
        "inline": inline,
    }


def _evidence_descriptor(
    *,
    sha256: bytes,
    byte_length: int,
    media_type: str,
    semantic_role: str,
) -> dict[str, object]:
    return {
        "sha256": sha256,
        "byte_length": byte_length,
        "media_type": media_type,
        "semantic_role": semantic_role,
    }



def standing_fixture(
    *,
    signer_kind: str = "participant",
    stream: str = "accepted",
    evaluation_time_ms: int = EVALUATION_TIME_MS,
    valid_from_ms: int = VALID_FROM_MS,
    valid_until_ms: int | None = VALID_UNTIL_MS,
    participation_valid_from_ms: int = VALID_FROM_MS,
    participation_valid_until_ms: int | None = VALID_UNTIL_MS,
    standing_class: str = STANDING_CLASS,
    governing_profile_override: dict[str, object] | None = None,
    add_second_participant: bool = False,
    signer_participant_record_sha256: bytes | None = None,
    include_qualification_object: bool = True,
    qualification_loader_bytes: bytes | None = QUALIFICATION_BYTES,
    include_supplementary_reference: bool = True,
) -> tuple[
    dict[str, object],
    object,
    dict[bytes, bytes],
    int,
]:
    manifest = fixture_manifest()

    manifest["governing_profile"] = {
        "profile_id": PROFILE_ID,
        "profile_sha256": PROFILE_SHA256,
        "source_set_sha256": SOURCE_SET_SHA256,
    }
    manifest["governing_sources"] = [
        dict(source)
        for source in GOVERNING_SOURCES
    ]

    object_index = manifest["object_index"]
    assert isinstance(object_index, list)
    object_index.append(
        _object_descriptor(
            sha256=PROFILE_SHA256,
            byte_length=len(PROFILE_BYTES),
            media_type=PROFILE_MEDIA_TYPE,
            semantic_role=PROFILE_SEMANTIC_ROLE,
            inline=PROFILE_BYTES,
            name="standing-profile.fixture",
        )
    )
    if include_qualification_object:
        object_index.append(
            _object_descriptor(
                sha256=QUALIFICATION_SHA256,
                byte_length=len(QUALIFICATION_BYTES),
                media_type="text/plain",
                semantic_role="standing-qualification-evidence",
                inline=None,
                name="qualification-evidence.fixture",
            )
        )
    object_index.sort(key=lambda item: item["sha256"])

    if add_second_participant:
        participants = manifest["participants"]
        assert isinstance(participants, list)
        participants.append(
            {
                "participant_record_sha256": h(22),
                "participant_key_id": derive_key_id(P3),
                "participant_public_key": P3,
                "standing_record_sha256": h(23),
                "issuance_record_sha256": h(24),
            }
        )

    if signer_kind == "participant":
        if signer_participant_record_sha256 is None:
            signer_participant_record_sha256 = h(16)

        if signer_participant_record_sha256 == h(16):
            signer_key_id = derive_key_id(P1)
            private_scalar = 1
        elif signer_participant_record_sha256 == h(22):
            signer_key_id = derive_key_id(P3)
            private_scalar = 3
        else:
            raise AssertionError("unsupported fixture participant signer")

        signer = {
            "kind": "participant",
            "key_id": signer_key_id,
            "participant_record_sha256": signer_participant_record_sha256,
        }
    elif signer_kind == "signing_node":
        signer = {
            "kind": "signing_node",
            "key_id": derive_key_id(P2),
            "participant_record_sha256": None,
        }
        private_scalar = 2
    else:
        raise AssertionError("unsupported fixture signer kind")

    body_profile = (
        governing_profile_override
        if governing_profile_override is not None
        else dict(manifest["governing_profile"])  # type: ignore[arg-type]
    )

    supplementary = (
        [
            _evidence_descriptor(
                sha256=SUPPLEMENTARY_SHA256,
                byte_length=999,
                media_type="application/octet-stream",
                semantic_role="supplementary-corroboration",
            )
        ]
        if include_supplementary_reference
        else []
    )

    payload = {
        "format": "kane-civic-history-record",
        "version": 1,
        "crypto_profile": CRYPTO_PROFILE,
        "hoa_root_id": manifest["hoa_root_id"],
        "epoch_sequence": manifest["epoch_sequence"],
        "ceremony_record_sha256": manifest["ceremony"]["ceremony_record_sha256"],  # type: ignore[index]
        "record_type": RECORD_TYPE,
        "history_link": {
            "stream": stream,
            "predecessor_record_sha256": None,
        },
        "signer": signer,
        "body": {
            "participant_record_sha256": h(16),
            "governing_profile": body_profile,
            "standing_class": standing_class,
            "valid_from_ms": valid_from_ms,
            "valid_until_ms": valid_until_ms,
            "participation": {
                "required": True,
                "policy_id": PARTICIPATION_POLICY,
                "valid_from_ms": participation_valid_from_ms,
                "valid_until_ms": participation_valid_until_ms,
                "authority_evidence": [],
                "supplementary_evidence": [],
            },
            "qualification": {
                "path_id": QUALIFICATION_PATH,
                "claim_responsibility": "participant_claimed",
                "authority_evidence": [
                    _evidence_descriptor(
                        sha256=QUALIFICATION_SHA256,
                        byte_length=len(QUALIFICATION_BYTES),
                        media_type="text/plain",
                        semantic_role="standing-qualification-evidence",
                    )
                ],
                "supplementary_evidence": supplementary,
            },
            "recording_operator_participant_record_sha256": h(16),
        },
    }

    signed = sign_history_record_fixture(
        payload,
        epoch_manifest=manifest,
        private_scalar=private_scalar,
        nonce_scalar=47,
    )

    participants = manifest["participants"]
    assert isinstance(participants, list)
    participant_matches = [
        item
        for item in participants
        if item["participant_record_sha256"] == h(16)
    ]
    assert len(participant_matches) == 1
    participant_matches[0]["standing_record_sha256"] = hashlib.sha256(signed).digest()

    verified = verify_signed_history_record(
        signed,
        epoch_manifests=[manifest],
    )

    objects = {
        SOURCE_SHA256: SOURCE_BYTES,
    }
    if qualification_loader_bytes is not None:
        objects[QUALIFICATION_SHA256] = qualification_loader_bytes

    return manifest, verified, objects, evaluation_time_ms


def _loader(objects: dict[bytes, bytes]):
    def load(sha256: bytes) -> bytes:
        return objects[sha256]

    return load


class CivicAcceptedParticipantStandingTests(unittest.TestCase):
    def test_valid_operator_participant_signed_standing_binds_profile_time_and_evidence(self) -> None:
        manifest, verified, objects, evaluation_time = standing_fixture()

        result = verify_accepted_participant_standing(
            verified,
            epoch_manifest=manifest,
            evaluation_time_ms=evaluation_time,
            load_object=_loader(objects),
        )

        self.assertEqual(verified.record_sha256, result.record_sha256)
        self.assertEqual(h(16), result.participant_record_sha256)
        self.assertEqual(PROFILE_SHA256, result.profile_sha256)
        self.assertEqual(SOURCE_SET_SHA256, result.source_set_sha256)
        self.assertEqual(
            "current-unit-owner-participant",
            result.standing_class,
        )
        self.assertEqual(
            "participant_claimed",
            result.claim_responsibility,
        )
        self.assertTrue(result.participation_required)
        self.assertEqual(h(16), result.recording_operator_participant_record_sha256)
        self.assertEqual("participant", result.signer_kind)
        self.assertEqual(derive_key_id(P1), result.signer_key_id)
        self.assertEqual(
            QUALIFICATION_SHA256,
            result.qualification_authority_evidence[0].sha256,
        )

    def test_valid_signing_node_signed_standing_preserves_operator_provenance(self) -> None:
        manifest, verified, objects, evaluation_time = standing_fixture(
            signer_kind="signing_node",
        )

        result = verify_accepted_participant_standing(
            verified,
            epoch_manifest=manifest,
            evaluation_time_ms=evaluation_time,
            load_object=_loader(objects),
        )

        self.assertEqual("signing_node", result.signer_kind)
        self.assertEqual(derive_key_id(P2), result.signer_key_id)
        self.assertEqual(h(16), result.recording_operator_participant_record_sha256)

    def test_wrong_stream_is_rejected(self) -> None:
        manifest, verified, objects, evaluation_time = standing_fixture(
            stream="witness",
        )

        with self.assertRaises(CivicParticipantStandingError):
            verify_accepted_participant_standing(
                verified,
                epoch_manifest=manifest,
                evaluation_time_ms=evaluation_time,
                load_object=_loader(objects),
            )

    def test_expired_standing_is_rejected_even_when_manifest_still_lists_participant(self) -> None:
        manifest, verified, objects, _ = standing_fixture()

        with self.assertRaises(CivicParticipantStandingError):
            verify_accepted_participant_standing(
                verified,
                epoch_manifest=manifest,
                evaluation_time_ms=VALID_UNTIL_MS,
                load_object=_loader(objects),
            )

    def test_standing_must_not_extend_beyond_required_participation(self) -> None:
        manifest, verified, objects, evaluation_time = standing_fixture(
            valid_until_ms=VALID_UNTIL_MS + 1,
            participation_valid_until_ms=VALID_UNTIL_MS,
        )

        with self.assertRaises(CivicParticipantStandingError):
            verify_accepted_participant_standing(
                verified,
                epoch_manifest=manifest,
                evaluation_time_ms=evaluation_time,
                load_object=_loader(objects),
            )

    def test_missing_or_corrupt_authority_evidence_is_rejected(self) -> None:
        missing_manifest, missing_verified, missing_objects, evaluation_time = standing_fixture(
            qualification_loader_bytes=None,
        )

        with self.assertRaises(CivicParticipantStandingError):
            verify_accepted_participant_standing(
                missing_verified,
                epoch_manifest=missing_manifest,
                evaluation_time_ms=evaluation_time,
                load_object=_loader(missing_objects),
            )

        corrupt_manifest, corrupt_verified, corrupt_objects, evaluation_time = standing_fixture(
            qualification_loader_bytes=b"corrupted qualification evidence",
        )

        with self.assertRaises(CivicParticipantStandingError):
            verify_accepted_participant_standing(
                corrupt_verified,
                epoch_manifest=corrupt_manifest,
                evaluation_time_ms=evaluation_time,
                load_object=_loader(corrupt_objects),
            )

    def test_authority_evidence_must_be_declared_in_manifest_object_index(self) -> None:
        manifest, verified, objects, evaluation_time = standing_fixture(
            include_qualification_object=False,
        )

        with self.assertRaises(CivicParticipantStandingError):
            verify_accepted_participant_standing(
                verified,
                epoch_manifest=manifest,
                evaluation_time_ms=evaluation_time,
                load_object=_loader(objects),
            )

    def test_supplementary_evidence_need_not_be_locally_available(self) -> None:
        manifest, verified, objects, evaluation_time = standing_fixture(
            include_supplementary_reference=True,
        )
        self.assertNotIn(SUPPLEMENTARY_SHA256, objects)

        result = verify_accepted_participant_standing(
            verified,
            epoch_manifest=manifest,
            evaluation_time_ms=evaluation_time,
            load_object=_loader(objects),
        )

        self.assertEqual(
            SUPPLEMENTARY_SHA256,
            result.qualification_supplementary_evidence[0].sha256,
        )

    def test_non_operator_participant_signer_is_rejected(self) -> None:
        manifest, verified, objects, evaluation_time = standing_fixture(
            add_second_participant=True,
            signer_participant_record_sha256=h(22),
        )

        with self.assertRaises(CivicParticipantStandingError):
            verify_accepted_participant_standing(
                verified,
                epoch_manifest=manifest,
                evaluation_time_ms=evaluation_time,
                load_object=_loader(objects),
            )

    def test_governing_profile_mismatch_is_rejected(self) -> None:
        manifest, verified, objects, evaluation_time = standing_fixture(
            governing_profile_override={
                "profile_id": "different-profile",
                "profile_sha256": h(40),
                "source_set_sha256": h(41),
            },
        )

        with self.assertRaises(CivicParticipantStandingError):
            verify_accepted_participant_standing(
                verified,
                epoch_manifest=manifest,
                evaluation_time_ms=evaluation_time,
                load_object=_loader(objects),
            )

    def test_canonical_profile_semantic_rejection_fails_standing(self) -> None:
        manifest, verified, objects, evaluation_time = standing_fixture(
            standing_class="not-recognized-by-profile",
        )

        with self.assertRaises(CivicParticipantStandingError):
            verify_accepted_participant_standing(
                verified,
                epoch_manifest=manifest,
                evaluation_time_ms=evaluation_time,
                load_object=_loader(objects),
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
