from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[2] / "infra" / ".env"


class EtlSettings(BaseSettings):
    database_url: str
    tmdb_api_token: str
    tmdb_base_url: str = "https://api.themoviedb.org/3"
    tmdb_rate_max_requests: int = 40
    tmdb_rate_period_s: float = 10.0
    wikipedia_api_url: str = "https://en.wikipedia.org/w/api.php"
    wikipedia_user_agent: str = "movie-rag/0.1 (admin@grela.dev)"
    wikipedia_min_interval_s: float = 0.5
    request_timeout_s: float = 15.0
    max_retries: int = 6

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        case_sensitive=False,
        extra="ignore",
    )
