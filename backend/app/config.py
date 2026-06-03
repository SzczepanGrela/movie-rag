from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[2] / "infra" / ".env"


class Settings(BaseSettings):
    database_url: str
    app_env: str = "dev"
    r2_public_base: str = "https://movierag-assets.grela.dev"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    explain_max_iterations: int = 4
    explain_max_retries: int = 2
    turnstile_secret: str | None = None
    turnstile_verify_url: str = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    explain_rate_per_ip: int = 10
    explain_rate_window_seconds: int = 3600
    explain_global_daily_cap: int = 300
    trusted_proxy_hops: int = 2
    search_candidate_pool: int = 400
    search_scene_weight: float = 0.9

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
