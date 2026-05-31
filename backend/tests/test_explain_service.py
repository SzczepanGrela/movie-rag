from app.config import settings
from app.explain.provider import (
    ContentDelta,
    ProviderError,
    ProviderRateLimited,
    ToolCall,
    ToolCallsReady,
)


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
