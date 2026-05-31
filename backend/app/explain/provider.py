import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol, cast

import openai
from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import ChatCompletionChunk

from app.config import settings


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ContentDelta:
    text: str


@dataclass
class ToolCallsReady:
    tool_calls: list[ToolCall]


TurnEvent = ContentDelta | ToolCallsReady


class ProviderError(Exception):
    """LLM provider failed (auth, 5xx, connection)."""


class ProviderRateLimited(ProviderError):  # noqa: N818
    """LLM provider returned a rate-limit / quota-exhausted error (HTTP 429)."""


class LLMProvider(Protocol):
    def run_turn(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> AsyncIterator[TurnEvent]:
        """Stream one assistant turn. Yields ContentDelta for text tokens and a single
        terminal ToolCallsReady if the model requested tools."""
        ...


class GroqProvider:
    def __init__(self, *, api_key: str, model: str, base_url: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    async def run_turn(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> AsyncIterator[TurnEvent]:
        try:
            stream = cast(
                AsyncStream[ChatCompletionChunk],
                await self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,  # type: ignore[arg-type]
                    tools=tools,  # type: ignore[arg-type]
                    stream=True,
                ),
            )
        except openai.RateLimitError as exc:
            raise ProviderRateLimited(str(exc)) from exc
        except openai.APIError as exc:
            raise ProviderError(str(exc)) from exc

        acc: dict[int, dict[str, str]] = {}
        try:
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta.content:
                    yield ContentDelta(text=delta.content)
                for tcd in delta.tool_calls or []:
                    slot = acc.setdefault(tcd.index, {"id": "", "name": "", "args": ""})
                    if tcd.id:
                        slot["id"] = tcd.id
                    if tcd.function and tcd.function.name:
                        slot["name"] = tcd.function.name
                    if tcd.function and tcd.function.arguments:
                        slot["args"] += tcd.function.arguments
        except openai.RateLimitError as exc:
            raise ProviderRateLimited(str(exc)) from exc
        except openai.APIError as exc:
            raise ProviderError(str(exc)) from exc

        if acc:
            calls = [
                ToolCall(
                    id=slot["id"],
                    name=slot["name"],
                    arguments=json.loads(slot["args"] or "{}"),
                )
                for slot in acc.values()
            ]
            yield ToolCallsReady(tool_calls=calls)


def build_provider() -> LLMProvider | None:
    if not settings.groq_api_key:
        return None
    return GroqProvider(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        base_url=settings.groq_base_url,
    )
