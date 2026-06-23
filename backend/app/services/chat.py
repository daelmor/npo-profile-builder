"""Slice 2 — chat orchestration around the gap-finding agent.

Each turn: load the profile + prior conversation, run the agent (its tools mutate
the in-memory profile), then persist the updated profile and conversation. The
agent message history is stored for continuity; a simple transcript is stored for
the UI.
"""

from __future__ import annotations

import json
import uuid

from anthropic import APIError
from pydantic_ai.exceptions import AgentRunError
from pydantic_ai.messages import ModelMessagesTypeAdapter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import LLMError, NotFoundError
from app.models.conversation import Conversation
from app.models.profile import Profile
from app.schemas.api import Completeness
from app.schemas.chat import ChatMessage, ChatResponse, ConversationState
from app.schemas.profile import NonprofitProfile
from app.services.agent import GapDeps, gap_agent

OPENER_PROMPT = (
    "Greet me in one short sentence, then ask about the most important missing fields."
)


async def _load_profile_row(session: AsyncSession, profile_id: uuid.UUID) -> Profile:
    row = (
        await session.execute(select(Profile).where(Profile.id == profile_id))
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError("Profile not found.")
    return row


async def _load_conversation(
    session: AsyncSession, profile_id: uuid.UUID
) -> Conversation | None:
    return (
        await session.execute(
            select(Conversation).where(Conversation.profile_id == profile_id)
        )
    ).scalar_one_or_none()


def _save_profile(row: Profile, profile: NonprofitProfile) -> None:
    row.legal_name = profile.legal_name.value
    row.country = profile.country.value
    row.data = profile.model_dump(mode="json")


async def get_state(session: AsyncSession, profile_id: uuid.UUID) -> ConversationState:
    row = await _load_profile_row(session, profile_id)
    conv = await _load_conversation(session, profile_id)
    profile = NonprofitProfile.model_validate(row.data)
    transcript = [ChatMessage(**m) for m in (conv.transcript if conv else [])]
    return ConversationState(
        started=conv is not None,
        transcript=transcript,
        profile=profile,
        completeness=Completeness.from_profile(profile),
    )


async def _run(
    session: AsyncSession,
    profile_id: uuid.UUID,
    *,
    user_message: str | None,
    reset: bool,
) -> ChatResponse:
    row = await _load_profile_row(session, profile_id)
    profile = NonprofitProfile.model_validate(row.data)
    conv = await _load_conversation(session, profile_id)

    history = []
    transcript: list[dict] = []
    if conv is not None and not reset:
        history = ModelMessagesTypeAdapter.validate_python(conv.agent_messages)
        transcript = list(conv.transcript)

    deps = GapDeps(profile=profile)
    prompt = OPENER_PROMPT if user_message is None else user_message
    try:
        result = await gap_agent.run(prompt, deps=deps, message_history=history)
    except (AgentRunError, APIError) as exc:
        raise LLMError(f"The assistant could not respond: {exc}") from exc
    reply = result.output

    if user_message is not None:
        transcript.append({"role": "user", "text": user_message})
    transcript.append({"role": "assistant", "text": reply.message})

    if conv is None:
        conv = Conversation(profile_id=profile_id)
        session.add(conv)
    conv.agent_messages = json.loads(result.all_messages_json())
    conv.transcript = transcript

    _save_profile(row, profile)
    await session.commit()

    return ChatResponse(
        reply=reply,
        transcript=[ChatMessage(**m) for m in transcript],
        profile=profile,
        completeness=Completeness.from_profile(profile),
    )


async def start(session: AsyncSession, profile_id: uuid.UUID) -> ChatResponse:
    """Begin (or restart) the conversation with an opening question."""
    return await _run(session, profile_id, user_message=None, reset=True)


async def post_message(
    session: AsyncSession, profile_id: uuid.UUID, message: str
) -> ChatResponse:
    return await _run(session, profile_id, user_message=message, reset=False)
