"""RAG search API schemas — structured results with linked evidence."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class SearchEvidence(BaseModel):
    """The source chunk that matched, linking a result back to its provenance."""

    chunk_id: int
    document_id: uuid.UUID
    text: str
    score: float


class SearchResult(BaseModel):
    profile_id: uuid.UUID
    legal_name: str | None
    country: str | None
    cause_areas: list[str]
    mission: str | None
    score: float
    evidence: SearchEvidence


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
