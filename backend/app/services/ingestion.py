"""Slice 1 — turn a PDF or pasted text into a persisted, structured profile.

Pipeline: text -> (size guard) -> LLM structured extraction -> resolve evidence
to chunks -> persist document + chunks + profile.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from anthropic import APIError
from pydantic_ai.exceptions import AgentRunError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import IngestionError, LLMError
from app.models.profile import Profile, SourceChunk, SourceDocument
from app.schemas.profile import NonprofitProfile
from app.services.chunking import chunk_text
from app.services.llm import extraction_agent


@dataclass
class IngestionResult:
    profile_row: Profile
    document: SourceDocument
    profile: NonprofitProfile
    chunk_count: int


async def extract_profile(text: str) -> NonprofitProfile:
    """Run the structured-extraction agent. Wraps model failures cleanly."""
    try:
        result = await extraction_agent().run(text)
    except (AgentRunError, APIError) as exc:
        raise LLMError(f"The model failed to extract a profile: {exc}") from exc
    return result.output


def _resolve_source_chunks(profile: NonprofitProfile, chunks: Iterable[SourceChunk]) -> None:
    """Best-effort: link each field's source_quote back to the chunk it came from."""
    normalized = [(c.id, " ".join(c.text.lower().split())) for c in chunks]
    for field in profile.tracked_fields().values():
        if not field.source_quote:
            continue
        probe = " ".join(field.source_quote.lower().split())[:60]
        if not probe:
            continue
        for chunk_id, chunk_text_norm in normalized:
            if probe in chunk_text_norm:
                field.source_chunk_id = chunk_id
                break


async def ingest(
    *,
    session: AsyncSession,
    raw_text: str,
    filename: str | None = None,
    content_type: str | None = None,
) -> IngestionResult:
    text = raw_text.strip()
    if not text:
        raise IngestionError("The provided input contains no text to ingest.")

    # Context-window guard: cap what we send to the model; store the full text.
    llm_input = text[: settings.max_input_chars]
    profile = await extract_profile(llm_input)

    document = SourceDocument(
        filename=filename,
        content_type=content_type,
        raw_text=text,
        char_count=len(text),
    )
    for index, chunk in enumerate(chunk_text(text)):
        document.chunks.append(SourceChunk(chunk_index=index, text=chunk))

    session.add(document)
    await session.flush()  # assigns document.id and chunk ids

    _resolve_source_chunks(profile, document.chunks)

    profile_row = Profile(
        legal_name=profile.legal_name.value,
        country=profile.country.value,
        data=profile.model_dump(mode="json"),
        source_document=document,
    )
    session.add(profile_row)
    await session.commit()
    await session.refresh(profile_row)

    return IngestionResult(
        profile_row=profile_row,
        document=document,
        profile=profile,
        chunk_count=len(document.chunks),
    )
