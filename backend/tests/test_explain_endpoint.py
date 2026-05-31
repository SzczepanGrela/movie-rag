from collections.abc import AsyncIterator
from typing import Any

from httpx import ASGITransport, AsyncClient

from app.db import get_session
from app.explain.provider import ContentDelta, TurnEvent
from app.explain.router import get_provider
from app.main import app
from app.search.embedder import FakeEmbedder, get_embedder


class _ScriptedProvider:
    def __init__(self, script: list[list[TurnEvent]]) -> None:
        self._script = script
        self._i = 0

    async def run_turn(self, messages: Any, tools: Any) -> AsyncIterator[TurnEvent]:
        turn = self._script[self._i]
        self._i += 1
        for ev in turn:
            yield ev


async def _fake_session() -> AsyncIterator[Any]:
    yield object()


async def test_explain_endpoint_streams_sse() -> None:
    script: list[list[TurnEvent]] = [[ContentDelta("Hi "), ContentDelta("there.")]]
    app.dependency_overrides[get_embedder] = FakeEmbedder
    app.dependency_overrides[get_session] = _fake_session
    app.dependency_overrides[get_provider] = lambda: _ScriptedProvider(script)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/explain", json={"query": "something happy"})
            assert resp.status_code == 200
            assert resp.headers["content-type"].startswith("text/event-stream")
            assert "event: chunk" in resp.text
            assert "event: done" in resp.text
    finally:
        app.dependency_overrides.clear()


async def test_explain_endpoint_503_without_provider() -> None:
    app.dependency_overrides[get_embedder] = FakeEmbedder
    app.dependency_overrides[get_session] = _fake_session
    app.dependency_overrides[get_provider] = lambda: None
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/explain", json={"query": "x"})
            assert resp.status_code == 503
    finally:
        app.dependency_overrides.clear()


async def test_explain_endpoint_422_on_empty_query() -> None:
    app.dependency_overrides[get_embedder] = FakeEmbedder
    app.dependency_overrides[get_session] = _fake_session
    app.dependency_overrides[get_provider] = lambda: object()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/explain", json={"query": ""})
            assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()
