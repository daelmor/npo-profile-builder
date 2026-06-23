"""API request/response models. The frontend's TypeScript types mirror these."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.profile import FieldStatus, NonprofitProfile


class IngestTextRequest(BaseModel):
    """Ingest pasted text (the no-PDF path)."""

    text: str = Field(min_length=1, description="Raw nonprofit description / document text.")
    title: str | None = Field(default=None, description="Optional label for the source.")


class SourceInfo(BaseModel):
    id: uuid.UUID
    filename: str | None
    char_count: int
    chunk_count: int


class Completeness(BaseModel):
    """A quick at-a-glance breakdown of field provenance."""

    total: int
    extracted: int
    inferred: int
    user_provided: int
    missing: int

    @classmethod
    def from_profile(cls, profile: NonprofitProfile) -> Completeness:
        counts = dict.fromkeys(FieldStatus, 0)
        for field in profile.tracked_fields().values():
            counts[field.status] += 1
        return cls(
            total=sum(counts.values()),
            extracted=counts[FieldStatus.extracted],
            inferred=counts[FieldStatus.inferred],
            user_provided=counts[FieldStatus.user_provided],
            missing=counts[FieldStatus.missing],
        )


class ProfileDetail(BaseModel):
    """A profile with its source metadata and completeness summary."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    source: SourceInfo
    completeness: Completeness
    profile: NonprofitProfile


class ProfileSummary(BaseModel):
    """Compact profile row for list views."""

    id: uuid.UUID
    legal_name: str | None
    country: str | None
    cause_areas: list[str]
    completeness: Completeness
    created_at: datetime
