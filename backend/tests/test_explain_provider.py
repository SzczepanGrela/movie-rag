from collections.abc import AsyncIterator
from types import SimpleNamespace
from typing import Any

import pytest

from app.explain.provider import (
    ContentDelta,
    GroqProvider,
    ProviderRateLimited,
    ToolCallsReady,
)


def _chunk(content: str | None = None, tool_calls: list[Any] | None = None) -> Any:
    delta = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta)])


def _tc_fragment(index: int, id_: str | None, name: str | None, args: str | None) -> Any:
    return SimpleNamespace(
        index=index,
        id=id_,
        function=SimpleNamespace(name=name, arguments=args),
    )


class _FakeStream:
    def __init__(self, chunks: list[Any]) -> None:
        self._chunks = chunks

    def __aiter__(self) -> AsyncIterator[Any]:
        return self._gen()

    async def _gen(self) -> AsyncIterator[Any]:
        for c in self._chunks:
            yield c


async def test_run_turn_assembles_content(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = GroqProvider(api_key="x", model="m", base_url="http://local")
    stream = _FakeStream([_chunk(content="Hel"), _chunk(content="lo")])

    async def fake_create(**kwargs: Any) -> Any:
        return stream

    monkeypatch.setattr(provider._client.chat.completions, "create", fake_create)
    events = [ev async for ev in provider.run_turn([], [])]
    assert [e.text for e in events if isinstance(e, ContentDelta)] == ["Hel", "lo"]


async def test_run_turn_assembles_tool_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = GroqProvider(api_key="x", model="m", base_url="http://local")
    stream = _FakeStream(
        [
            _chunk(tool_calls=[_tc_fragment(0, "call_1", "search_movies", '{"semantic_')]),
            _chunk(tool_calls=[_tc_fragment(0, None, None, 'query": "plane"}')]),
        ]
    )

    async def fake_create(**kwargs: Any) -> Any:
        return stream

    monkeypatch.setattr(provider._client.chat.completions, "create", fake_create)
    events = [ev async for ev in provider.run_turn([], [])]
    ready = [e for e in events if isinstance(e, ToolCallsReady)]
    assert len(ready) == 1
    call = ready[0].tool_calls[0]
    assert call.id == "call_1"
    assert call.name == "search_movies"
    assert call.arguments == {"semantic_query": "plane"}


async def test_run_turn_translates_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx
    import openai

    provider = GroqProvider(api_key="x", model="m", base_url="http://local")

    request = httpx.Request("POST", "http://local/chat/completions")
    response = httpx.Response(429, request=request)

    async def boom(**kwargs: Any) -> Any:
        raise openai.RateLimitError("429", response=response, body=None)

    monkeypatch.setattr(provider._client.chat.completions, "create", boom)
    with pytest.raises(ProviderRateLimited):
        async for _ in provider.run_turn([], []):
            pass


async def test_run_turn_translates_streaming_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx
    import openai

    provider = GroqProvider(api_key="x", model="m", base_url="http://local")

    request = httpx.Request("POST", "http://local/chat/completions")
    response = httpx.Response(429, request=request)

    class _RaisingStream:
        def __aiter__(self) -> AsyncIterator[Any]:
            return self._gen()

        async def _gen(self) -> AsyncIterator[Any]:
            raise openai.RateLimitError("429", response=response, body=None)
            yield  # pragma: no cover

    async def fake_create(**kwargs: Any) -> Any:
        return _RaisingStream()

    monkeypatch.setattr(provider._client.chat.completions, "create", fake_create)
    with pytest.raises(ProviderRateLimited):
        async for _ in provider.run_turn([], []):
            pass
