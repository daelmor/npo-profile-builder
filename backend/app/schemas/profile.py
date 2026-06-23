"""The NonprofitProfile domain schema — the heart of the project.

Every field carries its own provenance: whether the value was extracted from a
source document, inferred by the model, provided by a user, or still missing,
plus a confidence score and a pointer back to the supporting evidence.

That provenance is what powers the gap-finding agent (Slice 2): it can look at a
profile and ask, field by field, "what's missing or low-confidence?" — and it's
what a funder needs to trust the data.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field, model_validator

T = TypeVar("T")


class FieldStatus(StrEnum):
    """Provenance of a single field's value."""

    extracted = "extracted"  # taken (near) verbatim from a source document
    inferred = "inferred"  # reasoned from the source, not stated outright
    user_provided = "user_provided"  # supplied by a human via the gap-finding agent
    missing = "missing"  # no value yet


class BudgetBand(StrEnum):
    under_100k = "under_100k"
    band_100k_1m = "100k_1m"
    band_1m_10m = "1m_10m"
    band_10m_50m = "10m_50m"
    over_50m = "over_50m"
    unknown = "unknown"


class GrowthStage(StrEnum):
    seed = "seed"
    startup = "startup"
    growth = "growth"
    scaling = "scaling"
    mature = "mature"
    unknown = "unknown"


class EvidenceStandard(StrEnum):
    """How rigorously the nonprofit's impact is evidenced (anecdotal → RCT)."""

    anecdotal = "anecdotal"
    observational = "observational"
    quasi_experimental = "quasi_experimental"
    rct = "rct"
    unknown = "unknown"


class TrackedField(BaseModel, Generic[T]):
    """A profile value plus its provenance.

    The model fills `value`, `status`, `confidence`, and a `source_quote`
    (a verbatim snippet supporting the value). `source_chunk_id` is resolved
    server-side by matching that quote back to a stored source chunk.
    """

    value: T | None = Field(default=None, description="The field value, or null if unknown.")
    status: FieldStatus = Field(
        default=FieldStatus.missing,
        description=(
            "extracted = stated in the source; inferred = reasoned from the source; "
            "user_provided = supplied by a person; missing = no value."
        ),
    )
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="0–1 confidence in the value. Null when missing.",
    )
    source_quote: str | None = Field(
        default=None,
        description="A short verbatim snippet from the source document supporting the value.",
    )
    source_chunk_id: int | None = Field(
        default=None,
        description="Resolved server-side; do not set during extraction.",
    )
    notes: str | None = Field(
        default=None,
        description="Optional rationale, e.g. why a value was inferred.",
    )

    @model_validator(mode="after")
    def _enforce_invariants(self) -> TrackedField[T]:
        # A field with no value is, by definition, missing — and carries no confidence.
        if self.value is None or (isinstance(self.value, list) and not self.value):
            self.status = FieldStatus.missing
            self.confidence = None
            self.source_quote = None
            self.source_chunk_id = None
        elif self.status is FieldStatus.missing:
            # A value with a stale "missing" status defaults to extracted.
            self.status = FieldStatus.extracted
        return self


def _f() -> TrackedField:
    """Default factory: an empty, missing field."""
    return TrackedField()


class NonprofitProfile(BaseModel):
    """Structured profile of a nonprofit, the way a funder evaluates one.

    Populate each field from the provided source text. For every field, set
    `status`, a `confidence` in [0,1], and a short `source_quote` when the value
    comes from the text. Leave a field's value null (status "missing") rather
    than guessing — missing fields are expected and drive follow-up questions.
    """

    # --- Identity ---
    legal_name: TrackedField[str] = Field(default_factory=_f, description="Registered legal name.")
    aka: TrackedField[list[str]] = Field(
        default_factory=_f, description="Also-known-as / trading names."
    )
    country: TrackedField[str] = Field(
        default_factory=_f, description="Primary country of operation."
    )
    region: TrackedField[str] = Field(
        default_factory=_f, description="State/province/region, if applicable."
    )
    year_founded: TrackedField[int] = Field(default_factory=_f, description="Year established.")
    website: TrackedField[str] = Field(default_factory=_f, description="Primary website URL.")
    registration_id: TrackedField[str] = Field(
        default_factory=_f, description="Tax/registration ID (e.g. EIN), if stated."
    )

    # --- Mission & programs ---
    mission_statement: TrackedField[str] = Field(
        default_factory=_f, description="One- or two-sentence mission."
    )
    cause_areas: TrackedField[list[str]] = Field(
        default_factory=_f, description="Cause area(s)/sector(s), e.g. education, public health."
    )
    target_populations: TrackedField[list[str]] = Field(
        default_factory=_f, description="Who the organization serves."
    )
    theory_of_change: TrackedField[str] = Field(
        default_factory=_f, description="How activities are meant to produce outcomes."
    )

    # --- Scale & stage ---
    annual_budget_band: TrackedField[BudgetBand] = Field(
        default_factory=_f, description="Approximate annual budget band."
    )
    staff_count: TrackedField[int] = Field(default_factory=_f, description="Paid staff headcount.")
    volunteer_count: TrackedField[int] = Field(default_factory=_f, description="Active volunteers.")
    growth_stage: TrackedField[GrowthStage] = Field(
        default_factory=_f, description="Organizational maturity."
    )

    # --- Impact ---
    key_outcomes: TrackedField[list[str]] = Field(
        default_factory=_f, description="Primary outcomes the org drives."
    )
    evidence_standard: TrackedField[EvidenceStandard] = Field(
        default_factory=_f, description="Rigor of impact evidence (anecdotal → RCT)."
    )
    notable_results: TrackedField[list[str]] = Field(
        default_factory=_f, description="Concrete results/metrics to date."
    )

    # --- Funding ---
    current_funders: TrackedField[list[str]] = Field(
        default_factory=_f, description="Named current funders, if stated."
    )
    funding_gaps: TrackedField[list[str]] = Field(
        default_factory=_f, description="Stated funding needs/gaps."
    )

    def tracked_fields(self) -> dict[str, TrackedField]:
        """All provenance-tracked fields, keyed by attribute name."""
        return {name: getattr(self, name) for name in type(self).model_fields}

    def missing_or_low_confidence(self, threshold: float = 0.5) -> list[str]:
        """Field names that are missing or below the confidence threshold.

        This is the gap-finding agent's entry point (Slice 2).
        """
        gaps: list[str] = []
        for name, field in self.tracked_fields().items():
            if field.status is FieldStatus.missing:
                gaps.append(name)
            elif field.confidence is not None and field.confidence < threshold:
                gaps.append(name)
        return gaps
