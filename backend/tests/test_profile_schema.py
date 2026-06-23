"""The NonprofitProfile schema: round-trip + provenance invariants + gap logic."""

from app.schemas.profile import FieldStatus, NonprofitProfile, TrackedField


def test_profile_round_trips() -> None:
    profile = NonprofitProfile(
        legal_name=TrackedField(
            value="Hope Forward", status=FieldStatus.extracted, confidence=0.95
        ),
        cause_areas=TrackedField(
            value=["housing", "youth"], status=FieldStatus.inferred, confidence=0.6
        ),
    )
    dumped = profile.model_dump(mode="json")
    restored = NonprofitProfile.model_validate(dumped)

    assert restored == profile
    assert restored.legal_name.value == "Hope Forward"
    assert restored.cause_areas.status is FieldStatus.inferred


def test_missing_value_forces_missing_status() -> None:
    # A status/confidence with no value is inconsistent — the model corrects it.
    field: TrackedField[str] = TrackedField(
        value=None, status=FieldStatus.extracted, confidence=0.9
    )
    assert field.status is FieldStatus.missing
    assert field.confidence is None


def test_empty_list_counts_as_missing() -> None:
    field: TrackedField[list[str]] = TrackedField(value=[], status=FieldStatus.extracted)
    assert field.status is FieldStatus.missing


def test_value_without_status_defaults_to_extracted() -> None:
    field: TrackedField[str] = TrackedField(value="present")
    assert field.status is FieldStatus.extracted


def test_default_profile_is_entirely_missing() -> None:
    profile = NonprofitProfile()
    gaps = profile.missing_or_low_confidence()
    assert set(gaps) == set(NonprofitProfile.model_fields)


def test_low_confidence_is_a_gap() -> None:
    profile = NonprofitProfile(
        legal_name=TrackedField(
            value="Hope Forward", status=FieldStatus.extracted, confidence=0.95
        ),
        mission_statement=TrackedField(
            value="A guess", status=FieldStatus.inferred, confidence=0.2
        ),
    )
    gaps = profile.missing_or_low_confidence(threshold=0.5)
    assert "legal_name" not in gaps  # high confidence
    assert "mission_statement" in gaps  # low confidence
    assert "year_founded" in gaps  # missing
