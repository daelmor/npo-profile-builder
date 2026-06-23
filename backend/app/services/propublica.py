"""ProPublica Nonprofit Explorer API client + mapping to NonprofitProfile.

US IRS Form 990 data. Deterministic mapping (no LLM): identity, location/country,
NTEE-derived cause areas, IRS ruling date (approx. founding), and a budget band
from the latest filing's total revenue. Qualitative fields stay `missing`.

See .claude/skills/propublica-nonprofits/SKILL.md for the API reference.
"""

from __future__ import annotations

import httpx

from app.schemas.profile import (
    BudgetBand,
    FieldStatus,
    NonprofitProfile,
    TrackedField,
)

BASE_URL = "https://projects.propublica.org/nonprofits/api/v2"

# NTEE major group (first letter of the code) -> a readable cause area.
NTEE_MAJOR: dict[str, str] = {
    "A": "arts & culture",
    "B": "education",
    "C": "environment",
    "D": "animals",
    "E": "health care",
    "F": "mental health",
    "G": "disease & medical disciplines",
    "H": "medical research",
    "I": "crime & legal",
    "J": "employment",
    "K": "food & agriculture",
    "L": "housing & shelter",
    "M": "disaster & public safety",
    "N": "recreation & sports",
    "O": "youth development",
    "P": "human services",
    "Q": "international development",
    "R": "civil rights & advocacy",
    "S": "community development",
    "T": "philanthropy & grantmaking",
    "U": "science & technology",
    "V": "social science",
    "W": "public & societal benefit",
    "X": "religion",
    "Y": "membership benefit",
    "Z": "other",
}

US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL",
    "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT",
    "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC", "PR",
    "VI", "GU", "AS", "MP",
}

_PROV = "Imported from ProPublica Nonprofit Explorer (IRS Form 990)."


class ProPublicaClient:
    """Thin async client. Brackets in query params must stay literal (not %5B)."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._c = client

    async def search(
        self, *, ntee: int | None = None, state: str | None = None, page: int = 0
    ) -> dict:
        parts = [f"page={page}"]
        if ntee is not None:
            parts.append(f"ntee[id]={ntee}")
        if state is not None:
            parts.append(f"state[id]={state}")
        # Pass the query as raw bytes so httpx does not percent-encode the brackets.
        url = httpx.URL(f"{BASE_URL}/search.json", query="&".join(parts).encode())
        resp = await self._c.get(url)
        resp.raise_for_status()
        return resp.json()

    async def get_organization(self, ein: int | str) -> dict:
        resp = await self._c.get(f"{BASE_URL}/organizations/{ein}.json")
        resp.raise_for_status()
        return resp.json()


def _format_ein(ein: object) -> str | None:
    """The org detail returns `ein` as an int; format as XX-XXXXXXX."""
    digits = "".join(ch for ch in str(ein or "") if ch.isdigit())
    if not digits:
        return None
    digits = digits.zfill(9)
    return f"{digits[:2]}-{digits[2:]}"


def _ruling_year(ruling_date: str | None) -> int | None:
    if not ruling_date:
        return None
    digits = "".join(ch for ch in str(ruling_date) if ch.isdigit())
    if len(digits) >= 4:
        year = int(digits[:4])
        if 1700 < year < 2100:
            return year
    return None


def _latest_revenue(filings: list[dict]) -> tuple[int, int] | None:
    """(revenue, year) from the most recent filing that reports total revenue."""
    best: tuple[int, int] | None = None
    for f in filings:
        rev = f.get("totrevenue")
        yr = f.get("tax_prd_yr")
        if rev in (None, "") or yr in (None, ""):
            continue
        try:
            rev_i, yr_i = int(rev), int(yr)
        except (ValueError, TypeError):
            continue
        if best is None or yr_i > best[1]:
            best = (rev_i, yr_i)
    return best


def _budget_band(revenue: int) -> BudgetBand | None:
    if revenue <= 0:
        return None
    if revenue < 100_000:
        return BudgetBand.under_100k
    if revenue < 1_000_000:
        return BudgetBand.band_100k_1m
    if revenue < 10_000_000:
        return BudgetBand.band_1m_10m
    if revenue < 50_000_000:
        return BudgetBand.band_10m_50m
    return BudgetBand.over_50m


def map_organization(org: dict, filings: list[dict]) -> NonprofitProfile:
    """Map a ProPublica organization + its filings into a NonprofitProfile."""
    fields: dict[str, TrackedField] = {}

    name = (org.get("name") or "").strip()
    if name:
        fields["legal_name"] = TrackedField(
            value=name, status=FieldStatus.extracted, confidence=0.98, notes=_PROV
        )

    strein = (org.get("strein") or "").strip() or _format_ein(org.get("ein"))
    if strein:
        fields["registration_id"] = TrackedField(
            value=strein, status=FieldStatus.extracted, confidence=0.99, notes=_PROV
        )

    state = (org.get("state") or "").strip().upper()
    city = (org.get("city") or "").strip()
    if state in US_STATES:
        fields["country"] = TrackedField(
            value="United States", status=FieldStatus.inferred, confidence=0.97, notes=_PROV
        )
        fields["region"] = TrackedField(
            value=state, status=FieldStatus.extracted, confidence=0.9, notes=_PROV
        )
    elif not state and city:
        # Foreign-HQ 990 filers: the IRS puts the country in the city field.
        fields["country"] = TrackedField(
            value=city,
            status=FieldStatus.inferred,
            confidence=0.85,
            notes="From the IRS foreign address (country is in the city field).",
        )

    ntee = (org.get("ntee_code") or "").strip().upper()
    if ntee:
        cause = NTEE_MAJOR.get(ntee[0])
        if cause:
            fields["cause_areas"] = TrackedField(
                value=[cause],
                status=FieldStatus.extracted,
                confidence=0.85,
                source_quote=f"NTEE code {ntee}",
                notes=_PROV,
            )

    year = _ruling_year(org.get("ruling_date"))
    if year:
        fields["year_founded"] = TrackedField(
            value=year,
            status=FieldStatus.inferred,
            confidence=0.4,
            notes="From the IRS ruling date (tax-exempt grant date; approximates founding).",
        )

    latest = _latest_revenue(filings)
    if latest:
        revenue, fyear = latest
        band = _budget_band(revenue)
        if band:
            fields["annual_budget_band"] = TrackedField(
                value=band,
                status=FieldStatus.extracted,
                confidence=0.8,
                source_quote=f"Form 990 total revenue ${revenue:,} (FY{fyear})",
                notes=_PROV,
            )

    return NonprofitProfile(**fields)


def summarize(org: dict, profile: NonprofitProfile, filings: list[dict]) -> str:
    """A short text blob to embed so imported orgs are searchable."""
    name = profile.legal_name.value or org.get("name") or "This organization"
    state = (org.get("state") or "").strip().upper()
    city = (org.get("city") or "").strip()
    location = f"{city}, {state}" if state in US_STATES else (city or "an unspecified location")
    cause = ", ".join(profile.cause_areas.value or []) or "an unclassified cause area"
    parts = [
        f"{name} is a tax-exempt nonprofit (EIN {profile.registration_id.value or 'unknown'}) "
        f"based in {location}.",
        f"It is classified under {cause} (NTEE {org.get('ntee_code') or 'n/a'}).",
    ]
    latest = _latest_revenue(filings)
    if latest:
        parts.append(f"Most recent reported annual revenue: ${latest[0]:,} (FY{latest[1]}).")
    if profile.year_founded.value:
        parts.append(f"IRS tax-exempt ruling year: {profile.year_founded.value}.")
    return " ".join(parts)
