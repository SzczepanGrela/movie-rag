from typing import Any

import pytest

from app.config import settings
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


@pytest.fixture(autouse=True)
def _scene_weight(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "search_scene_weight", 0.9)


@pytest.mark.asyncio
async def test_dedup_keeps_best_weighted_per_movie() -> None:
    rows = [
        (
            1,
            "chunk A1 (best)",
            0.10,
            "plot",
            "Inception",
            2010,
            27205,
            "/inception.jpg",
            "LKO2hash",
        ),
        (1, "chunk A2", 0.30, "plot", "Inception", 2010, 27205, "/inception.jpg", "LKO2hash"),
        (2, "chunk B1", 0.20, "plot", "Matrix", 1999, 603, None, None),
    ]
    response = await service.search(_FakeSession(rows), FakeEmbedder(), query="dream", limit=5)  # type: ignore[arg-type]

    assert [r.movie_id for r in response.results] == [1, 2]
    assert response.results[0].best_chunk.text == "chunk A1 (best)"
    assert response.total_candidates == 3
    assert response.results[0].poster is not None
    assert (
        response.results[0].poster.url == "https://movierag-assets.grela.dev/posters/w500/27205.jpg"
    )
    assert response.results[1].poster is None


@pytest.mark.asyncio
async def test_limit_trims_after_dedup() -> None:
    rows = [
        (i, f"chunk {i}", 0.1 * i, "plot", f"Movie {i}", 2000 + i, 1000 + i, None, None)
        for i in range(1, 6)
    ]
    response = await service.search(_FakeSession(rows), FakeEmbedder(), query="x", limit=2)  # type: ignore[arg-type]
    assert [r.movie_id for r in response.results] == [1, 2]


@pytest.mark.asyncio
async def test_plot_score_is_one_minus_distance() -> None:
    rows = [(7, "txt", 0.25, "plot", "Title", 2020, 700, None, None)]
    response = await service.search(_FakeSession(rows), FakeEmbedder(), query="x", limit=1)  # type: ignore[arg-type]
    assert response.results[0].score == pytest.approx(0.75)
    assert response.results[0].best_chunk.score == pytest.approx(0.75)


@pytest.mark.asyncio
async def test_scene_weight_downranks_equal_distance_scene() -> None:
    rows = [
        (1, "plot chunk", 0.20, "plot", "PlotFilm", 2000, 1, None, None),
        (2, "scene chunk", 0.20, "scene", "SceneFilm", 2001, 2, None, None),
    ]
    response = await service.search(_FakeSession(rows), FakeEmbedder(), query="x", limit=5)  # type: ignore[arg-type]
    assert [r.movie_id for r in response.results] == [1, 2]
    assert response.results[0].score == pytest.approx(0.80)
    assert response.results[1].score == pytest.approx(0.72)


@pytest.mark.asyncio
async def test_best_chunk_can_be_a_scene_when_strong_enough() -> None:
    rows = [
        (1, "weak plot", 0.40, "plot", "Film", 2000, 1, None, None),
        (1, "strong scene", 0.10, "scene", "Film", 2000, 1, None, None),
    ]
    response = await service.search(_FakeSession(rows), FakeEmbedder(), query="x", limit=5)  # type: ignore[arg-type]
    assert response.results[0].best_chunk.text == "strong scene"
    assert response.results[0].score == pytest.approx(0.81)


@pytest.mark.asyncio
async def test_many_chunks_one_movie_yield_single_result() -> None:
    rows = [(1, f"c{i}", 0.05 * i, "scene", "Big", 2000, 1, None, None) for i in range(10)]
    rows.append((2, "other", 0.30, "plot", "Other", 2001, 2, None, None))
    response = await service.search(_FakeSession(rows), FakeEmbedder(), query="x", limit=10)  # type: ignore[arg-type]
    assert sorted(r.movie_id for r in response.results) == [1, 2]
    big = next(r for r in response.results if r.movie_id == 1)
    assert big.best_chunk.text == "c0"
    assert big.score == pytest.approx(0.9)


@pytest.mark.asyncio
async def test_negative_distance_score_is_clamped_to_zero() -> None:
    rows = [(1, "anti", 1.05, "scene", "Film", 2000, 1, None, None)]
    response = await service.search(_FakeSession(rows), FakeEmbedder(), query="x", limit=1)  # type: ignore[arg-type]
    assert response.results[0].score == 0.0


@pytest.mark.asyncio
async def test_weight_one_disables_scene_penalty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "search_scene_weight", 1.0)
    rows = [
        (1, "plot chunk", 0.20, "plot", "PlotFilm", 2000, 1, None, None),
        (2, "scene chunk", 0.20, "scene", "SceneFilm", 2001, 2, None, None),
    ]
    response = await service.search(_FakeSession(rows), FakeEmbedder(), query="x", limit=5)  # type: ignore[arg-type]
    assert response.results[0].score == pytest.approx(0.80)
    assert response.results[1].score == pytest.approx(0.80)


@pytest.mark.asyncio
async def test_empty_result_returns_empty_response() -> None:
    response = await service.search(_FakeSession([]), FakeEmbedder(), query="x", limit=10)  # type: ignore[arg-type]
    assert response.results == []
    assert response.total_candidates == 0
    assert response.took_ms >= 0
