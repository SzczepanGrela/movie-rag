import pytest

from lib.config import EtlSettings


@pytest.fixture
def etl_settings() -> EtlSettings:
    return EtlSettings(
        tmdb_api_token="test-token",
        tmdb_rate_max_requests=1000,
        tmdb_rate_period_s=0.001,
        wikipedia_min_interval_s=0.001,
        max_retries=2,
    )
