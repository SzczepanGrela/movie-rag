from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[2] / "infra" / ".env"


class Settings(BaseSettings):
    database_url: str
    app_env: str = "dev"
    r2_public_base: str = "https://movierag-assets.grela.dev"

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
