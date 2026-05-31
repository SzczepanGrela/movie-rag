from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol


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
