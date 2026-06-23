"""Search result grouping (pure logic — no DB, no embeddings)."""

import uuid

from app.services.search import Candidate, group_candidates


def _candidate(profile_id: uuid.UUID, distance: float, chunk_id: int) -> Candidate:
    return Candidate(
        profile_id=profile_id,
        legal_name="Name",
        country="Country",
        cause_areas=["education"],
        mission="A mission",
        chunk_id=chunk_id,
        document_id=uuid.uuid4(),
        text=f"chunk {chunk_id}",
        distance=distance,
    )


def test_group_keeps_best_chunk_per_profile_and_orders_by_score() -> None:
    p1, p2 = uuid.uuid4(), uuid.uuid4()
    candidates = [
        _candidate(p1, 0.6, 1),  # p1 weak match
        _candidate(p1, 0.2, 2),  # p1 strong match (should win for p1)
        _candidate(p2, 0.3, 3),
    ]
    results = group_candidates(candidates, limit=5)

    assert len(results) == 2  # one row per profile
    assert results[0].profile_id == p1  # best (smallest distance) ranks first
    assert results[0].evidence.chunk_id == 2  # the stronger chunk is the evidence
    assert results[0].score > results[1].score
    assert abs(results[0].score - 0.8) < 1e-6  # score = 1 - distance


def test_group_respects_limit() -> None:
    candidates = [_candidate(uuid.uuid4(), 0.1 * i, i) for i in range(1, 6)]
    results = group_candidates(candidates, limit=2)
    assert len(results) == 2
