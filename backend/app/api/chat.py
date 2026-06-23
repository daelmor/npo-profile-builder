"""Gap-finding chat endpoints."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.chat import ChatRequest, ChatResponse, ConversationState
from app.services import chat

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/{profile_id}", response_model=ConversationState)
async def get_conversation(
    profile_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> ConversationState:
    return await chat.get_state(session, profile_id)


@router.post("/{profile_id}/start", response_model=ChatResponse)
async def start_conversation(
    profile_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> ChatResponse:
    return await chat.start(session, profile_id)


@router.post("/{profile_id}/messages", response_model=ChatResponse)
async def post_message(
    profile_id: uuid.UUID,
    payload: ChatRequest,
    session: AsyncSession = Depends(get_session),
) -> ChatResponse:
    return await chat.post_message(session, profile_id, payload.message)
