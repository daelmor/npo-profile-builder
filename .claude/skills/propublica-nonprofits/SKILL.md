---
name: propublica-nonprofits
description: >-
  Consume the ProPublica Nonprofit Explorer API (US IRS Form 990 data) and map
  organizations into this project's NonprofitProfile. Use when ingesting,
  searching, or enriching nonprofit records from ProPublica, or when asked about
  what data that API provides.
---

# ProPublica Nonprofit Explorer API

US IRS tax-exempt organizations, built from Form 990/990-EZ/990-PF filings. Free,
no API key. **It is US-IRS data — there is no global charity coverage**, but it
does include foreign-headquartered orgs that file US 990s (see "International").

Base URL: `https://projects.propublica.org/nonprofits/api/v2` · GET only · JSON.

## Endpoints

- `GET /search.json` — params (all optional, **brackets must be literal, not
  URL-encoded** — `%5Bid%5D` returns 404):
  - `q` — keyword (name/city); `page` — zero-indexed; **25 results/page**.
  - `ntee[id]` — NTEE **major group 1–10** (1 Arts, 2 Education, 3 Environment/Animals,
    4 Health, 5 Human Services, **6 International**, 7 Public/Societal, 8 Religion,
    9 Mutual/Membership, 10 Unknown).
  - `state[id]` — 2-letter US code. **Note: the documented `ZZ` for international
    returns 404** — don't use it.
  - `c_code[id]` — 501(c) subsection.
  - Returns `total_results`, `num_pages`, `organizations[]` (slim: `ein`, `name`,
    `city`, `state`, `ntee_code`, …). `total_results` caps at 10000.
- `GET /organizations/{ein}.json` — full record:
  - `organization` — rich: `ein`, `strein` ("XX-XXXXXXX"), `name`, `sub_name`,
    `address`, `city`, `state`, `zipcode`, `ntee_code`, `ruling_date`,
    `subsection_code`, `revenue_amount`/`income_amount`/`asset_amount`, …
  - `filings_with_data[]` — one per tax year (often 10+ years, **through ~2023** —
    the docs say 2012–2019 but live data is current). ~68 numeric fields incl.
    `tax_prd_yr`, `totrevenue`, `totfuncexpns`, `totassetsend`, `totliabend`,
    `pdf_url`. **No mission/program/website/employee text** — purely financial.
  - `filings_without_data[]` — PDF-only years.

## International / "country"

Foreign-HQ filers have a **blank `state`** and the **`city` field holds the
country** (e.g. `city="Canada"`, `"Switzerland"`). Reach them via `ntee[id]=6`
(or other groups) and filter `state == ""`. Derive `country`: US state → "United
States"; blank state → `city`.

## Mapping to NonprofitProfile (what this project does)

Deterministic, no LLM. See `backend/app/services/propublica.py`.

| Profile field | Source | Status |
|---|---|---|
| `legal_name` | `organization.name` | extracted |
| `registration_id` | `organization.strein` (EIN) | extracted |
| `country` | US state → "United States"; blank state → `city` | inferred |
| `region` | `state` (US) | extracted / missing for foreign |
| `cause_areas` | `ntee_code` first letter → NTEE major group | extracted |
| `year_founded` | `ruling_date` year | **inferred** (IRS ruling ≠ founding) |
| `annual_budget_band` | latest filing `totrevenue` → band | extracted |
| everything qualitative | — (not in the API) | **missing** |

## Etiquette

No documented JSON rate limit, but be polite: ~3–5 req/s with a small delay,
cache org responses, and honor the
[Data Terms of Use](https://www.propublica.org/about/propublica-data-terms-of-use).
PDF downloads *are* rate-limited.

## Importing into the database

`python -m scripts.import_propublica --count 100` (run from `backend/`, with
`DATABASE_URL`/`DB_REQUIRE_SSL` pointed at the target DB). It selects a
country/sector-diverse set, maps each org, synthesizes a short summary, embeds it
(local fastembed) so it's searchable, and writes `SourceDocument` + chunk +
`Profile` rows — the same shape as LLM ingestion, minus the LLM.
