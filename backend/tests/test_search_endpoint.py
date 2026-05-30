from collections.abc import AsyncIterator, Callable
from typing import Any

from httpx import ASGITransport, AsyncClient

from app.db import get_session
from app.main import app
from app.search.embedder import FakeEmbedder, get_embedder


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


def _override_session_with(rows: list[Any]) -> Callable[[], AsyncIterator[_FakeSession]]:
    async def _fake() -> AsyncIterator[_FakeSession]:
        yield _FakeSession(rows)

    return _fake


async def test_search_endpoint_returns_results_with_fake_deps() -> None:
    rows = [
        (1, "Cobb plants an idea", 0.10, "Inception", 2010, 27205, "/inception.jpg", "LKO2hash"),
        (2, "The Matrix is everywhere", 0.20, "The Matrix", 1999, 603, None, None),
    ]
    app.dependency_overrides[get_embedder] = FakeEmbedder
    app.dependency_overrides[get_session] = _override_session_with(rows)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/search", json={"query": "dream within a dream", "limit": 2}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["total_candidates"] == 2
    assert "took_ms" in body
    assert len(body["results"]) == 2
    first = body["results"][0]
    assert first["movie_id"] == 1
    assert first["title"] == "Inception"
    assert first["score"] == 0.9
    assert first["best_chunk"]["text"] == "Cobb plants an idea"
    assert first["poster"]["url"] == "https://movierag-assets.grela.dev/posters/w500/27205.jpg"
    assert (
        first["poster"]["thumb_url"] == "https://movierag-assets.grela.dev/posters/w154/27205.jpg"
    )
    assert first["poster"]["blurhash"] == "LKO2hash"
    assert body["results"][1]["poster"] is None


async def test_search_endpoint_rejects_empty_query() -> None:
    app.dependency_overrides[get_embedder] = FakeEmbedder
    app.dependency_overrides[get_session] = _override_session_with([])

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/search", json={"query": "", "limit": 5})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
