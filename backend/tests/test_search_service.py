from typing import Any

import pytest

from app.search import service
from app.search.embedder import FakeEmbedder


class _FakeResult:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return self._rows


class _FakeSession:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    async def execute(self, _stmt: Any) -> _FakeResult:
        return _FakeResult(self._rows)


@pytest.mark.asyncio
async def test_dedup_keeps_lowest_distance_per_movie() -> None:
    rows = [
        (1, "chunk A1 (best)", 0.10, "Inception", 2010),
        (1, "chunk A2", 0.30, "Inception", 2010),
        (2, "chunk B1", 0.20, "Matrix", 1999),
    ]
    session = _FakeSession(rows)

    response = await service.search(
        session,  # type: ignore[arg-type]
        FakeEmbedder(),
        query="dream",
        limit=5,
    )

    assert [r.movie_id for r in response.results] == [1, 2]
    assert response.results[0].best_chunk.text == "chunk A1 (best)"
    assert response.total_candidates == 3


@pytest.mark.asyncio
async def test_limit_trims_after_dedup() -> None:
    rows = [(i, f"chunk {i}", 0.1 * i, f"Movie {i}", 2000 + i) for i in range(1, 6)]
    session = _FakeSession(rows)

    response = await service.search(
        session,  # type: ignore[arg-type]
        FakeEmbedder(),
        query="x",
        limit=2,
    )

    assert len(response.results) == 2
    assert [r.movie_id for r in response.results] == [1, 2]


@pytest.mark.asyncio
async def test_score_is_one_minus_distance() -> None:
    rows = [(7, "txt", 0.25, "Title", 2020)]
    session = _FakeSession(rows)

    response = await service.search(
        session,  # type: ignore[arg-type]
        FakeEmbedder(),
        query="x",
        limit=1,
    )

    assert response.results[0].score == pytest.approx(0.75)
    assert response.results[0].best_chunk.score == pytest.approx(0.75)


@pytest.mark.asyncio
async def test_empty_result_returns_empty_response() -> None:
    session = _FakeSession([])

    response = await service.search(
        session,  # type: ignore[arg-type]
        FakeEmbedder(),
        query="x",
        limit=10,
    )

    assert response.results == []
    assert response.total_candidates == 0
    assert response.took_ms >= 0
