"""Gap-finding agent with a mocked LLM (PydanticAI FunctionModel).

Exercises the tool loop: the agent calls update_field, which writes the answer
back into the in-memory profile as user_provided and closes the gap.
"""

from pydantic_ai.messages import ModelResponse, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from app.schemas.profile import FieldStatus, NonprofitProfile, TrackedField
from app.services.agent import GapDeps, gap_agent


def _already_updated(messages) -> bool:
    return any(
        isinstance(part, ToolReturnPart) and part.tool_name == "update_field"
        for message in messages
        for part in message.parts
    )


def _record_year_then_finish(messages, info: AgentInfo) -> ModelResponse:
    if not _already_updated(messages):
        return ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name="update_field",
                    args={"field_name": "year_founded", "value": "2015", "confidence": 0.95},
                )
            ]
        )
    return ModelResponse(
        parts=[
            ToolCallPart(
                tool_name="final_result",
                args={
                    "message": "Thanks — recorded that.",
                    "asked_fields": ["staff_count"],
                    "complete": False,
                },
            )
        ]
    )


async def test_agent_records_user_answer_and_closes_gap() -> None:
    profile = NonprofitProfile(
        legal_name=TrackedField(
            value="Hope Forward", status=FieldStatus.extracted, confidence=0.95
        )
    )
    assert "year_founded" in profile.missing_or_low_confidence()

    deps = GapDeps(profile=profile)
    with gap_agent.override(model=FunctionModel(_record_year_then_finish)):
        result = await gap_agent.run("We were founded in 2015.", deps=deps)

    assert result.output.message
    assert profile.year_founded.value == 2015
    assert profile.year_founded.status is FieldStatus.user_provided
    assert "year_founded" not in profile.missing_or_low_confidence()


def _bad_enum_then_finish(messages, info: AgentInfo) -> ModelResponse:
    if not _already_updated(messages):
        return ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name="update_field",
                    args={"field_name": "evidence_standard", "value": "super-rigorous"},
                )
            ]
        )
    return ModelResponse(
        parts=[
            ToolCallPart(
                tool_name="final_result",
                args={"message": "ok", "asked_fields": [], "complete": False},
            )
        ]
    )


async def test_update_field_rejects_invalid_enum() -> None:
    profile = NonprofitProfile()
    deps = GapDeps(profile=profile)
    with gap_agent.override(model=FunctionModel(_bad_enum_then_finish)):
        await gap_agent.run("our evidence is super rigorous", deps=deps)

    # The invalid enum option was rejected, so the field stays missing.
    assert profile.evidence_standard.status is FieldStatus.missing
