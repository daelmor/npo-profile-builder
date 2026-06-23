"""ORM models: source documents, their text chunks, and extracted profiles.

The full structured profile is stored as JSONB (`Profile.data`) — it's a rich,
evolving nested document, and Postgres JSONB keeps it queryable without an ORM
table per field. A couple of hot fields (legal_name, country) are denormalized
into columns for cheap listing and filtering.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class SourceDocument(Base):
    __tablename__ = "source_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str | None] = mapped_column(String(512))
    content_type: Mapped[str | None] = mapped_column(String(128))
    raw_text: Mapped[str] = mapped_column(Text)
    char_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    chunks: Mapped[list[SourceChunk]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="SourceChunk.chunk_index",
    )
    profile: Mapped[Profile | None] = relationship(back_populates="source_document")


class SourceChunk(Base):
    __tablename__ = "source_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    # NOTE: a pgvector `embedding` column is added in Slice 3 (RAG).

    document: Mapped[SourceDocument] = relationship(back_populates="chunks")


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Denormalized for list/search; the source of truth is `data`.
    legal_name: Mapped[str | None] = mapped_column(String(512), index=True)
    country: Mapped[str | None] = mapped_column(String(128))
    # Serialized NonprofitProfile (model_dump(mode="json")).
    data: Mapped[dict] = mapped_column(JSONB)
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    source_document: Mapped[SourceDocument] = relationship(back_populates="profile")
