import time
from collections.abc import AsyncIterator
from typing import Any

from httpx import ASGITransport, AsyncClient

from app.db import get_session
from app.explain.provider import ContentDelta, TurnEvent
from app.explain.ratelimit import RateLimiter
from app.explain.router import get_provider, get_rate_limiter, get_turnstile_verifier
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
    app.dependency_overrides[get_turnstile_verifier] = _ok_verifier
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
    app.dependency_overrides[get_turnstile_verifier] = _ok_verifier
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


def _ok_verifier() -> Any:
    async def _v(token: str | None, ip: str) -> bool:
        return True

    return _v


def _fail_verifier() -> Any:
    async def _v(token: str | None, ip: str) -> bool:
        return False

    return _v


async def test_explain_403_when_turnstile_fails() -> None:
    script: list[list[TurnEvent]] = [[ContentDelta("hi")]]
    app.dependency_overrides[get_embedder] = FakeEmbedder
    app.dependency_overrides[get_session] = _fake_session
    app.dependency_overrides[get_provider] = lambda: _ScriptedProvider(script)
    app.dependency_overrides[get_turnstile_verifier] = _fail_verifier
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/explain", json={"query": "x"})
            assert resp.status_code == 403
            assert resp.json()["detail"] == "turnstile_failed"
    finally:
        app.dependency_overrides.clear()


async def test_explain_429_when_per_ip_limit_exceeded() -> None:
    script: list[list[TurnEvent]] = [[ContentDelta("hi")]]
    rl = RateLimiter(per_ip_limit=1, window_seconds=3600, global_daily_cap=100)
    rl.check("testclient", now=time.time())
    app.dependency_overrides[get_embedder] = FakeEmbedder
    app.dependency_overrides[get_session] = _fake_session
    app.dependency_overrides[get_provider] = lambda: _ScriptedProvider(script)
    app.dependency_overrides[get_turnstile_verifier] = _ok_verifier
    app.dependency_overrides[get_rate_limiter] = lambda: rl
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/explain",
                json={"query": "x"},
                headers={"x-forwarded-for": "testclient"},
            )
            assert resp.status_code == 429
            assert resp.json()["detail"] == "rate_limited"
            assert resp.headers.get("retry-after") is not None
    finally:
        app.dependency_overrides.clear()


async def test_explain_503_when_global_cap_exceeded() -> None:
    script: list[list[TurnEvent]] = [[ContentDelta("hi")]]
    rl = RateLimiter(per_ip_limit=100, window_seconds=3600, global_daily_cap=1)
    rl.check("other", now=time.time())
    app.dependency_overrides[get_embedder] = FakeEmbedder
    app.dependency_overrides[get_session] = _fake_session
    app.dependency_overrides[get_provider] = lambda: _ScriptedProvider(script)
    app.dependency_overrides[get_turnstile_verifier] = _ok_verifier
    app.dependency_overrides[get_rate_limiter] = lambda: rl
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/explain",
                json={"query": "x"},
                headers={"x-forwarded-for": "1.2.3.4"},
            )
            assert resp.status_code == 503
            assert resp.json()["detail"] == "service_busy"
    finally:
        app.dependency_overrides.clear()


async def test_explain_200_happy_path_with_protection() -> None:
    script: list[list[TurnEvent]] = [[ContentDelta("Hi "), ContentDelta("there.")]]
    rl = RateLimiter(per_ip_limit=10, window_seconds=3600, global_daily_cap=100)
    app.dependency_overrides[get_embedder] = FakeEmbedder
    app.dependency_overrides[get_session] = _fake_session
    app.dependency_overrides[get_provider] = lambda: _ScriptedProvider(script)
    app.dependency_overrides[get_turnstile_verifier] = _ok_verifier
    app.dependency_overrides[get_rate_limiter] = lambda: rl
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/explain", json={"query": "happy"})
            assert resp.status_code == 200
            assert "event: done" in resp.text
    finally:
        app.dependency_overrides.clear()
