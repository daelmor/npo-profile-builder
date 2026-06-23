"""Import nonprofits from the ProPublica Nonprofit Explorer API.

Selects a country/sector-diverse set (international foreign-HQ filers via NTEE-6
blank-state orgs, plus US orgs across sectors), maps each deterministically to a
NonprofitProfile, embeds a synthesized summary so it's searchable, and writes
SourceDocument + chunk + Profile rows — the same shape as LLM ingestion, no LLM.

Run from backend/:
    uv run python -m scripts.import_propublica --count 100
    uv run python -m scripts.import_propublica --count 5 --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter

import httpx
from sqlalchemy import text

from app.db import SessionLocal, engine
from app.models.profile import Profile, SourceChunk, SourceDocument
from app.services.embeddings import embed_texts
from app.services.propublica import ProPublicaClient, map_organization, summarize

# Sectors to sample for US breadth (NTEE major group ids).
US_SECTORS = (5, 2, 4, 1, 3, 7)  # human services, education, health, arts, environment, public


async def select_targets(client: ProPublicaClient, count: int) -> list[dict]:
    """Return up to `count` slim org dicts, weighted toward country diversity."""
    intl_target = max(20, count * 40 // 100)
    chosen: dict[int, dict] = {}

    # International: NTEE-6 organizations with a blank state (foreign-HQ).
    for page in range(0, 10):
        intl = sum(1 for o in chosen.values() if not (o.get("state") or "").strip())
        if intl >= intl_target:
            break
        try:
            data = await client.search(ntee=6, page=page)
        except httpx.HTTPError:
            break
        for o in data.get("organizations", []):
            ein = o.get("ein")
            if ein and ein not in chosen and not (o.get("state") or "").strip() and o.get("city"):
                chosen[ein] = o
        await asyncio.sleep(0.2)

    # US breadth across sectors.
    for ntee in US_SECTORS:
        if len(chosen) >= count:
            break
        for page in (0, 1):
            if len(chosen) >= count:
                break
            try:
                data = await client.search(ntee=ntee, page=page)
            except httpx.HTTPError:
                break
            for o in data.get("organizations", []):
                ein = o.get("ein")
                if ein and ein not in chosen and (o.get("state") or "").strip().upper() != "":
                    chosen[ein] = o
            await asyncio.sleep(0.2)

    return list(chosen.values())[:count]


async def run(count: int, dry_run: bool) -> None:
    async with httpx.AsyncClient(timeout=30) as http:
        client = ProPublicaClient(http)
        print(f"Selecting up to {count} organizations…")
        targets = await select_targets(client, count)
        print(f"Selected {len(targets)} candidates. Fetching details + mapping…\n")

        async with SessionLocal() as session:
            existing = set(
                (
                    await session.execute(
                        text("select data->'registration_id'->>'value' from profiles")
                    )
                ).scalars().all()
            )

            records = []  # (profile, summary, org)
            for slim in targets:
                ein = slim["ein"]
                try:
                    detail = await client.get_organization(ein)
                except httpx.HTTPError:
                    continue
                org = detail.get("organization") or {}
                filings = detail.get("filings_with_data") or []
                profile = map_organization(org, filings)
                if not profile.legal_name.value:
                    continue
                strein = profile.registration_id.value
                if strein and strein in existing:
                    continue
                records.append((profile, summarize(org, profile, filings), org))
                if strein:
                    existing.add(strein)
                await asyncio.sleep(0.2)

            countries = Counter((p.country.value or "unknown") for p, _, _ in records)
            sectors = Counter(
                (p.cause_areas.value[0] if p.cause_areas.value else "unclassified")
                for p, _, _ in records
            )
            print(f"Mapped {len(records)} new orgs.")
            print("  countries:", dict(countries))
            print("  sectors:  ", dict(sectors))

            if dry_run:
                print("\n[dry-run] sample:")
                for p, s, _ in records[:5]:
                    cause = (p.cause_areas.value or ["?"])[0]
                    print(
                        f"  - {p.legal_name.value} | {p.country.value} | {cause} | "
                        f"budget={p.annual_budget_band.value} | founded~{p.year_founded.value}"
                    )
                    print(f"      {s[:120]}")
                return

            if not records:
                print("Nothing new to import.")
                return

            print("\nEmbedding summaries…")
            vectors = await asyncio.to_thread(embed_texts, [s for _, s, _ in records])

            for (profile, summary, _), vec in zip(records, vectors, strict=True):
                doc = SourceDocument(
                    filename=None,
                    content_type="application/x-propublica-990",
                    raw_text=summary,
                    char_count=len(summary),
                )
                doc.chunks.append(SourceChunk(chunk_index=0, text=summary, embedding=vec))
                session.add(doc)
                await session.flush()
                session.add(
                    Profile(
                        legal_name=profile.legal_name.value,
                        country=profile.country.value,
                        data=profile.model_dump(mode="json"),
                        source_document=doc,
                    )
                )
            await session.commit()
            print(f"\nImported {len(records)} profiles across {len(countries)} countries.")

    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import nonprofits from ProPublica.")
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true", help="map + report, don't write DB")
    args = parser.parse_args()
    asyncio.run(run(args.count, args.dry_run))


if __name__ == "__main__":
    main()
