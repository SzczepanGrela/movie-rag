import json
from collections.abc import AsyncIterator, Awaitable, Callable
from time import perf_counter
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.explain import tools as tools_module
from app.explain.provider import (
    ContentDelta,
    LLMProvider,
    ProviderError,
    ProviderRateLimited,
    ToolCall,
    ToolCallsReady,
)
from app.explain.sse import sse_event
from app.search.embedder import Embedder

DispatchFn = Callable[
    [AsyncSession, Embedder, str, dict[str, Any], dict[int, dict[str, Any]]],
    Awaitable[Any],
]

SYSTEM_PROMPT = (
    "You are a film expert assistant for a movie search engine. "
    "When the user describes a plot, scene, vibe or theme, use the provided tools to "
    "find concrete movies in the database, then answer in English. "
    "Always call search_movies first to discover candidates by their movie_id, then "
    "use get_movie_detail / get_movie_scenes / get_movie_quotes to confirm before you "
    "name a film. Cite specific movies by title and year. Be concise. "
    "Never invent movies that the tools did not return."
)


def _initial_messages(query: str) -> list[dict[str, Any]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]


def _assistant_tool_calls_message(tool_calls: list[ToolCall], content: str) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": content or None,
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
            }
            for tc in tool_calls
        ],
    }


def _tool_result_message(tool_call_id: str, name: str, result: Any) -> dict[str, Any]:
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "name": name,
        "content": json.dumps(result, ensure_ascii=False),
    }


async def explain_stream(
    session: AsyncSession,
    embedder: Embedder,
    provider: LLMProvider,
    query: str,
    *,
    dispatch: DispatchFn = tools_module.dispatch,
    max_iterations: int | None = None,
) -> AsyncIterator[str]:
    limit = max_iterations or settings.explain_max_iterations
    messages = _initial_messages(query)
    cited: dict[int, dict[str, Any]] = {}
    t0 = perf_counter()

    try:
        for iteration in range(1, limit + 1):
            turn_tool_calls: list[ToolCall] = []
            content = ""
            async for ev in provider.run_turn(messages, tools_module.TOOL_SCHEMAS):
                if isinstance(ev, ContentDelta):
                    content += ev.text
                    yield sse_event("chunk", {"text": ev.text})
                elif isinstance(ev, ToolCallsReady):
                    turn_tool_calls = ev.tool_calls

            if not turn_tool_calls:
                for movie in cited.values():
                    yield sse_event("cited_movie", movie)
                took_ms = int((perf_counter() - t0) * 1000)
                yield sse_event("done", {"took_ms": took_ms, "iterations": iteration})
                return

            messages.append(_assistant_tool_calls_message(turn_tool_calls, content))
            for tc in turn_tool_calls:
                yield sse_event("tool_call", {"tool": tc.name, "args": tc.arguments})
                result = await dispatch(session, embedder, tc.name, tc.arguments, cited)
                messages.append(_tool_result_message(tc.id, tc.name, result))

        yield sse_event("error", {"code": "max_iterations"})
        return
    except ProviderRateLimited:
        yield sse_event(
            "error",
            {"code": "rate_limited", "message": "LLM rate limit reached, try again shortly."},
        )
    except ProviderError:
        yield sse_event("error", {"code": "provider_error", "message": "LLM provider error."})
