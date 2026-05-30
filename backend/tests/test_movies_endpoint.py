from collections.abc import AsyncIterator, Callable
from datetime import date
from typing import Any

from httpx import ASGITransport, AsyncClient

from app.db import get_session
from app.main import app
from app.models import Genre, Movie


class _FakeResultOrm:
    def __init__(self, entity: Any) -> None:
        self._entity = entity

    def scalar_one_or_none(self) -> Any:
        return self._entity


class _FakeSessionOrm:
    def __init__(self, entity: Any) -> None:
        self._entity = entity

    async def execute(self, _stmt: Any) -> _FakeResultOrm:
        return _FakeResultOrm(self._entity)


def _override_session_with(entity: Any) -> Callable[[], AsyncIterator[_FakeSessionOrm]]:
    async def _fake() -> AsyncIterator[_FakeSessionOrm]:
        yield _FakeSessionOrm(entity)

    return _fake


def _make_movie() -> Movie:
    m = Movie(
        id=1,
        tmdb_id=27205,
        imdb_id="tt1375666",
        title="Inception",
        original_title="Inception",
        year=2010,
        runtime=148,
        release_date=date(2010, 7, 16),
        overview="A thief...",
        tagline="Your mind is the scene of the crime.",
        vote_average=8.4,
        vote_count=35000,
        original_language="en",
        poster_path="/inception.jpg",
        blurhash="LKO2hash",
        etl_status="done",
        schema_c_status="done",
    )
    m.genres = [Genre(id=1, tmdb_id=28, name="Action")]
    m.cast = []
    m.crew = []
    m.source_texts = []
    m.plot_variants = []
    m.scenes = []
    m.themes = []
    m.atmosphere = None
    m.quotes = []
    m.character_descriptions = []
    return m


async def test_endpoint_returns_200_for_existing_movie() -> None:
    app.dependency_overrides[get_session] = _override_session_with(_make_movie())

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/movies/1")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == "Inception"
    assert body["tmdb_id"] == 27205
    assert body["schema_c_status"] == "done"
    assert body["genres"] == [{"name": "Action"}]
    assert body["scenes"] == []
    assert body["atmosphere"] is None
    assert body["poster"]["url"] == "https://movierag-assets.grela.dev/posters/w500/27205.jpg"
    assert body["poster"]["blurhash"] == "LKO2hash"


async def test_endpoint_returns_404_for_missing_movie() -> None:
    app.dependency_overrides[get_session] = _override_session_with(None)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/movies/999999")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "movie_not_found"}
