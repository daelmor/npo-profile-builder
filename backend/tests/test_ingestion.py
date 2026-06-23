"""Ingestion extraction with a mocked LLM (PydanticAI TestModel — no network)."""

from pydantic_ai.models.test import TestModel

from app.schemas.profile import FieldStatus, NonprofitProfile
from app.services.ingestion import extract_profile
from app.services.llm import extraction_agent


async def test_extract_profile_maps_model_output() -> None:
    mocked_output = {
        "legal_name": {
            "value": "Hope Forward",
            "status": "extracted",
            "confidence": 0.95,
            "source_quote": "Hope Forward is a charity",
        },
        "mission_statement": {
            "value": "End youth homelessness",
            "status": "extracted",
            "confidence": 0.9,
        },
        "cause_areas": {
            "value": ["housing", "youth"],
            "status": "extracted",
            "confidence": 0.8,
        },
    }

    agent = extraction_agent()
    with agent.override(model=TestModel(custom_output_args=mocked_output)):
        profile = await extract_profile("Hope Forward is a charity that helps youth.")

    assert isinstance(profile, NonprofitProfile)
    assert profile.legal_name.value == "Hope Forward"
    assert profile.legal_name.status is FieldStatus.extracted
    assert profile.cause_areas.value == ["housing", "youth"]


async def test_extracted_profile_drives_gap_detection() -> None:
    """The gap-finding agent (Slice 2) keys off exactly this signal."""
    mocked_output = {
        "legal_name": {"value": "Hope Forward", "status": "extracted", "confidence": 0.95},
    }

    agent = extraction_agent()
    with agent.override(model=TestModel(custom_output_args=mocked_output)):
        profile = await extract_profile("Hope Forward.")

    gaps = profile.missing_or_low_confidence()
    assert "legal_name" not in gaps
    assert "year_founded" in gaps
    assert "funding_gaps" in gaps
