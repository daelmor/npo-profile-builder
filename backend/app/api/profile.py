"""Profile read endpoints."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.db import get_session
from app.schemas.api import ProfileDetail, ProfileSummary
from app.services import profiles

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("", response_model=list[ProfileSummary])
async def list_profiles(session: AsyncSession = Depends(get_session)) -> list[ProfileSummary]:
    return await profiles.list_profile_summaries(session)


@router.get("/{profile_id}", response_model=ProfileDetail)
async def get_profile(
    profile_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> ProfileDetail:
    detail = await profiles.get_profile_detail(session, profile_id)
    if detail is None:
        raise NotFoundError("Profile not found.")
    return detail
