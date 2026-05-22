import httpx
import pytest

from lib.config import EtlSettings
from lib.tmdb_client import TmdbClient


async def test_get_movie_sends_bearer_and_credits_param(etl_settings: EtlSettings) -> None:
    captured: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(200, json={"id": 550, "title": "Fight Club"})

    async with TmdbClient(etl_settings, transport=httpx.MockTransport(handler)) as client:
        data = await client.get_movie(550)

    assert data == {"id": 550, "title": "Fight Club"}
    request = captured["request"]
    assert request.url.path == "/3/movie/550"
    assert request.url.params["append_to_response"] == "credits"
    assert request.headers["authorization"] == "Bearer test-token"


async def test_get_movie_omits_credits_param_when_disabled(etl_settings: EtlSettings) -> None:
    captured: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(200, json={"id": 550, "title": "Fight Club"})

    async with TmdbClient(etl_settings, transport=httpx.MockTransport(handler)) as client:
        await client.get_movie(550, append_credits=False)

    assert "append_to_response" not in captured["request"].url.params


async def test_get_movie_retries_on_503_then_succeeds(etl_settings: EtlSettings) -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503)
        return httpx.Response(200, json={"id": 1, "title": "ok"})

    async with TmdbClient(etl_settings, transport=httpx.MockTransport(handler)) as client:
        data = await client.get_movie(1, append_credits=False)

    assert data == {"id": 1, "title": "ok"}
    assert calls["n"] == 2


async def test_get_movie_raises_on_404(etl_settings: EtlSettings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"status_message": "Not Found"})

    async with TmdbClient(etl_settings, transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_movie(999_999)


async def test_get_genres_hits_genre_list_endpoint(etl_settings: EtlSettings) -> None:
    captured: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(200, json={"genres": [{"id": 28, "name": "Action"}]})

    async with TmdbClient(etl_settings, transport=httpx.MockTransport(handler)) as client:
        data = await client.get_genres()

    assert data == {"genres": [{"id": 28, "name": "Action"}]}
    request = captured["request"]
    assert request.url.path == "/3/genre/movie/list"
    assert request.url.params["language"] == "en-US"


async def test_discover_passes_page_and_filters(etl_settings: EtlSettings) -> None:
    captured: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(200, json={"results": []})

    async with TmdbClient(etl_settings, transport=httpx.MockTransport(handler)) as client:
        await client.discover(page=3, sort_by="popularity.desc")

    request = captured["request"]
    assert request.url.path == "/3/discover/movie"
    assert request.url.params["page"] == "3"
    assert request.url.params["sort_by"] == "popularity.desc"
