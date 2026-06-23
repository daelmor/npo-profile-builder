"""RAG search endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.search import SearchResponse
from app.services import search

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search_profiles(
    q: str = Query(min_length=1, description="Natural-language query."),
    limit: int = Query(5, ge=1, le=20),
    session: AsyncSession = Depends(get_session),
) -> SearchResponse:
    return await search.search(session, q, limit)


@router.post("/reindex")
async def reindex(session: AsyncSession = Depends(get_session)) -> dict[str, int]:
    """Embed any chunks that don't yet have embeddings (one-off backfill)."""
    embedded = await search.backfill_embeddings(session)
    return {"embedded": embedded}
