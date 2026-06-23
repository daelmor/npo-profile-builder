"""Read-side service: load profiles from the DB and shape them for the API."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profile import Profile, SourceChunk
from app.schemas.api import Completeness, ProfileDetail, ProfileSummary, SourceInfo
from app.schemas.profile import NonprofitProfile
from app.services.ingestion import IngestionResult


def _build_detail(
    row: Profile,
    profile: NonprofitProfile,
    *,
    filename: str | None,
    char_count: int,
    chunk_count: int,
) -> ProfileDetail:
    return ProfileDetail(
        id=row.id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        source=SourceInfo(
            id=row.source_document_id,
            filename=filename,
            char_count=char_count,
            chunk_count=chunk_count,
        ),
        completeness=Completeness.from_profile(profile),
        profile=profile,
    )


def detail_from_result(result: IngestionResult) -> ProfileDetail:
    """Build the API view straight from a fresh ingestion (no extra queries)."""
    return _build_detail(
        result.profile_row,
        result.profile,
        filename=result.document.filename,
        char_count=result.document.char_count,
        chunk_count=result.chunk_count,
    )


async def get_profile_detail(session: AsyncSession, profile_id: uuid.UUID) -> ProfileDetail | None:
    row = (
        await session.execute(
            select(Profile)
            .where(Profile.id == profile_id)
            .options(selectinload(Profile.source_document))
        )
    ).scalar_one_or_none()
    if row is None:
        return None

    chunk_count = (
        await session.execute(
            select(func.count())
            .select_from(SourceChunk)
            .where(SourceChunk.document_id == row.source_document_id)
        )
    ).scalar_one()

    profile = NonprofitProfile.model_validate(row.data)
    return _build_detail(
        row,
        profile,
        filename=row.source_document.filename,
        char_count=row.source_document.char_count,
        chunk_count=chunk_count,
    )


async def list_profile_summaries(session: AsyncSession, limit: int = 50) -> list[ProfileSummary]:
    rows = (
        await session.execute(select(Profile).order_by(Profile.created_at.desc()).limit(limit))
    ).scalars().all()

    summaries: list[ProfileSummary] = []
    for row in rows:
        profile = NonprofitProfile.model_validate(row.data)
        summaries.append(
            ProfileSummary(
                id=row.id,
                legal_name=row.legal_name,
                country=row.country,
                cause_areas=profile.cause_areas.value or [],
                completeness=Completeness.from_profile(profile),
                created_at=row.created_at,
            )
        )
    return summaries
