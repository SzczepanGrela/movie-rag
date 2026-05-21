from types import TracebackType
from typing import Any, Self

import httpx
from aiolimiter import AsyncLimiter

from lib.config import EtlSettings
from lib.retry import with_retry


class TmdbClient:
    def __init__(
        self,
        settings: EtlSettings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(
            base_url=settings.tmdb_base_url,
            headers={
                "Authorization": f"Bearer {settings.tmdb_api_token}",
                "Accept": "application/json",
            },
            timeout=settings.request_timeout_s,
            transport=transport,
        )
        self._limiter = AsyncLimiter(settings.tmdb_rate_max_requests, settings.tmdb_rate_period_s)
        self._get = with_retry(settings.max_retries)(self._request)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _request(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        async with self._limiter:
            response = await self._client.get(path, params=params)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data

    async def get_movie(self, tmdb_id: int, *, append_credits: bool = True) -> dict[str, Any]:
        params: dict[str, Any] | None = (
            {"append_to_response": "credits"} if append_credits else None
        )
        return await self._get(f"/movie/{tmdb_id}", params)

    async def discover(self, page: int = 1, **filters: Any) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, **filters}
        return await self._get("/discover/movie", params)
