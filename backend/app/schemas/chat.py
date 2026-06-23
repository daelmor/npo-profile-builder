"""Chat / gap-finding API schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.api import Completeness
from app.schemas.profile import NonprofitProfile


class AgentReply(BaseModel):
    """Structured result the gap-finding agent returns each turn."""

    message: str = Field(description="A short, friendly message/question for the user.")
    asked_fields: list[str] = Field(
        default_factory=list, description="Profile field names this turn asked about."
    )
    complete: bool = Field(
        default=False, description="True only when no important gaps remain."
    )


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    text: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ConversationState(BaseModel):
    """Current conversation + live profile (for the Chat page)."""

    started: bool
    transcript: list[ChatMessage]
    profile: NonprofitProfile
    completeness: Completeness


class ChatResponse(BaseModel):
    """Result of a single chat turn."""

    reply: AgentReply
    transcript: list[ChatMessage]
    profile: NonprofitProfile
    completeness: Completeness
