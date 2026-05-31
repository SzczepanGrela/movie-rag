from collections.abc import AsyncIterator
from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.explain import service
from app.explain.provider import (
    ContentDelta,
    ProviderError,
    ProviderRateLimited,
    ToolCall,
    ToolCallsReady,
    TurnEvent,
)
from app.search.embedder import Embedder


def test_groq_config_defaults() -> None:
    assert settings.groq_model == "llama-3.3-70b-versatile"
    assert settings.groq_base_url == "https://api.groq.com/openai/v1"
    assert settings.explain_max_iterations == 4
    # groq_api_key may be None (dev) or set from infra/.env; type must allow None
    assert settings.groq_api_key is None or isinstance(settings.groq_api_key, str)


def test_provider_value_types() -> None:
    tc = ToolCall(id="call_1", name="search_movies", arguments={"semantic_query": "x"})
    assert tc.name == "search_movies"
    assert ContentDelta(text="hi").text == "hi"
    assert ToolCallsReady(tool_calls=[tc]).tool_calls[0].id == "call_1"
    assert issubclass(ProviderRateLimited, ProviderError)


class _ScriptedProvider:
    """Each call to run_turn pops the next scripted list of TurnEvents."""

    def __init__(self, script: list[list[TurnEvent]]) -> None:
        self._script = script
        self._i = 0

    async def run_turn(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> AsyncIterator[TurnEvent]:
        turn = self._script[self._i]
        self._i += 1
        for ev in turn:
            yield ev


class _RaisingProvider:
    async def run_turn(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> AsyncIterator[TurnEvent]:
        raise ProviderRateLimited("429")
        yield  # pragma: no cover  (makes this an async generator)


async def _collect(agen: AsyncIterator[str]) -> str:
    return "".join([chunk async for chunk in agen])


async def _fake_dispatch(
    session: Any, embedder: Any, name: str, args: dict[str, Any], cited: dict[int, dict[str, Any]]
) -> Any:
    cited[123] = {"movie_id": 123, "title": "Con Air", "year": 1997}
    return {"ok": True}


async def test_explain_stream_tool_then_answer() -> None:
    script: list[list[TurnEvent]] = [
        [
            ToolCallsReady(
                [ToolCall(id="c1", name="search_movies", arguments={"semantic_query": "plane"})]
            )
        ],
        [ContentDelta("The film is "), ContentDelta("**Con Air**.")],
    ]
    out = await _collect(
        service.explain_stream(
            cast(AsyncSession, None),
            cast(Embedder, None),
            _ScriptedProvider(script),
            "plane",
            dispatch=_fake_dispatch,
        )
    )
    assert "event: tool_call" in out
    assert '"tool": "search_movies"' in out
    assert "event: chunk" in out
    assert "Con Air" in out
    assert "event: cited_movie" in out
    assert '"movie_id": 123' in out
    assert "event: done" in out
    # ordering: tool_call before chunk before cited_movie before done
    assert (
        out.index("tool_call") < out.index("chunk") < out.index("cited_movie") < out.index("done")
    )


async def test_explain_stream_max_iterations() -> None:
    # provider always asks for a tool -> never answers
    forever: list[list[TurnEvent]] = [
        [
            ToolCallsReady(
                [ToolCall(id=f"c{i}", name="search_movies", arguments={"semantic_query": "x"})]
            )
        ]
        for i in range(10)
    ]
    out = await _collect(
        service.explain_stream(
            cast(AsyncSession, None),
            cast(Embedder, None),
            _ScriptedProvider(forever),
            "x",
            dispatch=_fake_dispatch,
            max_iterations=3,
        )
    )
    assert '"code": "max_iterations"' in out


async def test_explain_stream_rate_limited() -> None:
    out = await _collect(
        service.explain_stream(
            cast(AsyncSession, None),
            cast(Embedder, None),
            _RaisingProvider(),
            "x",
            dispatch=_fake_dispatch,
        )
    )
    assert '"code": "rate_limited"' in out
