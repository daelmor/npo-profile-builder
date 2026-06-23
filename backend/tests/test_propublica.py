"""ProPublica → NonprofitProfile mapping (pure, no network)."""

from app.schemas.profile import BudgetBand, FieldStatus
from app.services.propublica import _budget_band, _ruling_year, map_organization


def test_map_us_org() -> None:
    org = {
        "name": "Helping Hands Inc",
        "strein": "12-3456789",
        "state": "CA",
        "city": "OAKLAND",
        "ntee_code": "P20",
        "ruling_date": "1998-05-01",
    }
    filings = [
        {"totrevenue": 2_500_000, "tax_prd_yr": 2022},
        {"totrevenue": 1_800_000, "tax_prd_yr": 2020},
    ]
    p = map_organization(org, filings)

    assert p.legal_name.value == "Helping Hands Inc"
    assert p.registration_id.value == "12-3456789"
    assert p.country.value == "United States"
    assert p.country.status is FieldStatus.inferred
    assert p.region.value == "CA"
    assert p.cause_areas.value == ["human services"]
    assert p.year_founded.value == 1998
    assert p.year_founded.status is FieldStatus.inferred
    assert p.annual_budget_band.value is BudgetBand.band_1m_10m  # latest = $2.5M
    # The API has no narrative — those stay missing.
    assert p.mission_statement.status is FieldStatus.missing
    assert p.website.status is FieldStatus.missing


def test_map_foreign_org_takes_country_from_city() -> None:
    org = {
        "name": "Global Aid",
        "strein": "98-0001111",
        "state": "",
        "city": "Switzerland",
        "ntee_code": "Q30",
        "ruling_date": "2005-01-01",
    }
    p = map_organization(org, [{"totrevenue": 80_000_000, "tax_prd_yr": 2023}])

    assert p.country.value == "Switzerland"
    assert p.country.status is FieldStatus.inferred
    assert p.region.status is FieldStatus.missing  # no US state
    assert p.cause_areas.value == ["international development"]
    assert p.annual_budget_band.value is BudgetBand.over_50m


def test_budget_band_and_ruling_year() -> None:
    assert _budget_band(0) is None
    assert _budget_band(50_000) is BudgetBand.under_100k
    assert _budget_band(2_500_000) is BudgetBand.band_1m_10m
    assert _budget_band(60_000_000) is BudgetBand.over_50m
    assert _ruling_year("1998-05-01") == 1998
    assert _ruling_year("199804") == 1998
    assert _ruling_year("") is None
