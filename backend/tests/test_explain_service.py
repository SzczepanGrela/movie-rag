from app.config import settings


def test_groq_config_defaults() -> None:
    assert settings.groq_model == "llama-3.3-70b-versatile"
    assert settings.groq_base_url == "https://api.groq.com/openai/v1"
    assert settings.explain_max_iterations == 4
    # groq_api_key may be None (dev) or set from infra/.env; type must allow None
    assert settings.groq_api_key is None or isinstance(settings.groq_api_key, str)
