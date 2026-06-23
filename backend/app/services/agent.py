"""Slice 2 — PydanticAI gap-finding conversational agent.

Idiomatic PydanticAI: typed dependencies hold the in-memory profile; a read tool
(`list_gaps`) inspects provenance, and a write tool (`update_field`) records user
answers as `user_provided`. The structured `AgentReply` output carries the next
question. The caller persists the mutated profile + conversation after each run.
"""

from __future__ import annotations

import typing
from dataclasses import dataclass
from enum import StrEnum

from pydantic_ai import Agent, RunContext

from app.config import settings
from app.schemas.chat import AgentReply
from app.schemas.profile import FieldStatus, NonprofitProfile
from app.services.llm import ensure_provider_env

# Human labels for fields (server-side mirror of the frontend's).
FIELD_LABELS: dict[str, str] = {
    "legal_name": "Legal name",
    "aka": "Also known as",
    "country": "Country",
    "region": "Region",
    "year_founded": "Year founded",
    "website": "Website",
    "registration_id": "Registration / tax ID",
    "mission_statement": "Mission",
    "cause_areas": "Cause areas",
    "target_populations": "Target populations",
    "theory_of_change": "Theory of change",
    "annual_budget_band": "Annual budget",
    "staff_count": "Staff",
    "volunteer_count": "Volunteers",
    "growth_stage": "Growth stage",
    "key_outcomes": "Key outcomes",
    "evidence_standard": "Evidence standard",
    "notable_results": "Notable results",
    "current_funders": "Current funders",
    "funding_gaps": "Funding gaps",
}


def _inner_type(field_name: str) -> type:
    """The T inside a TrackedField[T] for the given profile field.

    TrackedField[int] is a *concrete* Pydantic generic subclass, not a typing
    alias, so the type arg lives in `__pydantic_generic_metadata__`, not get_args.
    """
    annotation = NonprofitProfile.model_fields[field_name].annotation
    meta = getattr(annotation, "__pydantic_generic_metadata__", None)
    if meta and meta.get("args"):
        return meta["args"][0]
    args = typing.get_args(annotation)
    return args[0] if args else str


def _enum_options(field_name: str) -> list[str] | None:
    inner = _inner_type(field_name)
    if isinstance(inner, type) and issubclass(inner, StrEnum):
        return [member.value for member in inner]
    return None


def _coerce(field_name: str, value: object) -> object:
    """Coerce a user-supplied value into the field's declared type."""
    inner = _inner_type(field_name)
    if typing.get_origin(inner) is list:
        items = value if isinstance(value, list) else str(value).split(",")
        return [str(item).strip() for item in items if str(item).strip()]
    if inner is int:
        return int(str(value).strip())
    if isinstance(inner, type) and issubclass(inner, StrEnum):
        return inner(str(value).strip())  # raises ValueError for an invalid option
    return str(value).strip()


@dataclass
class GapDeps:
    """Dependencies for a gap-finding run: the live, mutable profile."""

    profile: NonprofitProfile


GAP_SYSTEM_PROMPT = """\
You are a warm, concise assistant helping complete a nonprofit's profile so funders
can evaluate it.

Each turn:
1. Call `list_gaps` to see which fields are missing or low-confidence (it also shows
   the allowed options for constrained fields).
2. Ask about 1-3 of those fields, prioritizing the most decision-relevant ones
   (mission, country, cause areas, budget, impact/evidence, funding needs).
3. When the user answers, call `update_field` once per value they give. For fields
   that list options, pass exactly one of those option values.

Keep messages short and friendly — a sentence or two. Never invent answers or fill
fields the user didn't confirm. In your final reply, set `asked_fields` to the fields
you just asked about and `complete` to true only once nothing important is missing.
"""


ensure_provider_env()

gap_agent = Agent(
    settings.llm_model,
    deps_type=GapDeps,
    output_type=AgentReply,
    system_prompt=GAP_SYSTEM_PROMPT,
    model_settings={"max_tokens": settings.llm_max_tokens},
    retries=2,
)


@gap_agent.tool
async def list_gaps(ctx: RunContext[GapDeps]) -> list[dict]:
    """List profile fields that are missing or low-confidence, with their options."""
    profile = ctx.deps.profile
    gaps: list[dict] = []
    for name in profile.missing_or_low_confidence():
        field = getattr(profile, name)
        gaps.append(
            {
                "field": name,
                "label": FIELD_LABELS.get(name, name),
                "status": field.status.value,
                "current_value": field.value,
                "options": _enum_options(name),
            }
        )
    return gaps


@gap_agent.tool
async def update_field(
    ctx: RunContext[GapDeps],
    field_name: str,
    value: str,
    confidence: float = 0.9,
) -> str:
    """Record a user-provided value for a profile field (status -> user_provided)."""
    if field_name not in NonprofitProfile.model_fields:
        valid = ", ".join(FIELD_LABELS)
        return f"Unknown field '{field_name}'. Valid fields: {valid}."

    try:
        coerced = _coerce(field_name, value)
    except (ValueError, TypeError):
        options = _enum_options(field_name)
        if options:
            return f"'{value}' is not valid for {field_name}. Choose one of: {', '.join(options)}."
        expected = _inner_type(field_name).__name__
        return f"Could not interpret '{value}' for {field_name} (expected {expected})."

    if coerced in (None, "", []):
        return f"No usable value given for {field_name}."

    field = getattr(ctx.deps.profile, field_name)
    field.value = coerced
    field.status = FieldStatus.user_provided
    field.confidence = max(0.0, min(1.0, confidence))
    field.source_quote = None
    field.source_chunk_id = None
    field.notes = "Provided by the user via chat."
    return f"Recorded {field_name} = {coerced!r}."
