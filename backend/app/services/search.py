"""Slice 3 — RAG retrieval over source chunks, grouped into profile results.

A query is embedded and matched against chunk embeddings (pgvector cosine
distance). Chunks are grouped by their parent profile, keeping each profile's
best-matching chunk as the linked evidence.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile, SourceChunk
from app.schemas.search import SearchEvidence, SearchResponse, SearchResult
from app.services.embeddings import embed_query, embed_texts

CANDIDATE_POOL = 40


@dataclass
class Candidate:
    profile_id: uuid.UUID
    legal_name: str | None
    country: str | None
    cause_areas: list[str]
    mission: str | None
    chunk_id: int
    document_id: uuid.UUID
    text: str
    distance: float


def _score(distance: float) -> float:
    """Cosine distance (0..2) -> similarity (0..1), clamped."""
    return max(0.0, min(1.0, 1.0 - distance))


def group_candidates(candidates: list[Candidate], limit: int) -> list[SearchResult]:
    """Keep each profile's best (smallest-distance) chunk; return top `limit`."""
    best: dict[uuid.UUID, Candidate] = {}
    for cand in candidates:
        current = best.get(cand.profile_id)
        if current is None or cand.distance < current.distance:
            best[cand.profile_id] = cand

    ordered = sorted(best.values(), key=lambda c: c.distance)[:limit]
    return [
        SearchResult(
            profile_id=c.profile_id,
            legal_name=c.legal_name,
            country=c.country,
            cause_areas=c.cause_areas,
            mission=c.mission,
            score=_score(c.distance),
            evidence=SearchEvidence(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                text=c.text,
                score=_score(c.distance),
            ),
        )
        for c in ordered
    ]


def _field_value(data: dict, name: str):
    field = data.get(name) or {}
    return field.get("value")


async def search(session: AsyncSession, query: str, limit: int = 5) -> SearchResponse:
    query_vector = await asyncio.to_thread(embed_query, query)
    distance = SourceChunk.embedding.cosine_distance(query_vector).label("distance")
    stmt = (
        select(
            SourceChunk.id,
            SourceChunk.document_id,
            SourceChunk.text,
            distance,
            Profile.id,
            Profile.legal_name,
            Profile.country,
            Profile.data,
        )
        .join(Profile, Profile.source_document_id == SourceChunk.document_id)
        .where(SourceChunk.embedding.is_not(None))
        .order_by(distance)
        .limit(CANDIDATE_POOL)
    )
    rows = (await session.execute(stmt)).all()

    candidates = [
        Candidate(
            profile_id=profile_id,
            legal_name=legal_name,
            country=country,
            cause_areas=_field_value(data, "cause_areas") or [],
            mission=_field_value(data, "mission_statement"),
            chunk_id=chunk_id,
            document_id=document_id,
            text=text,
            distance=float(dist),
        )
        for (chunk_id, document_id, text, dist, profile_id, legal_name, country, data) in rows
    ]
    return SearchResponse(query=query, results=group_candidates(candidates, limit))


async def backfill_embeddings(session: AsyncSession) -> int:
    """Embed any chunks that don't yet have an embedding (e.g. ingested pre-RAG)."""
    rows = (
        await session.execute(select(SourceChunk).where(SourceChunk.embedding.is_(None)))
    ).scalars().all()
    if not rows:
        return 0
    vectors = await asyncio.to_thread(embed_texts, [row.text for row in rows])
    for row, vector in zip(rows, vectors, strict=True):
        row.embedding = vector
    await session.commit()
    return len(rows)
