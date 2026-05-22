from types import TracebackType
from typing import Any, Self

import httpx
from aiolimiter import AsyncLimiter

from lib.config import EtlSettings
from lib.retry import with_retry

_PLOT_HEADINGS = {"plot", "plot summary"}


class WikipediaClient:
    def __init__(
        self,
        settings: EtlSettings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(
            base_url=settings.wikipedia_api_url,
            headers={
                "User-Agent": settings.wikipedia_user_agent,
                "Accept": "application/json",
            },
            timeout=settings.request_timeout_s,
            transport=transport,
            follow_redirects=True,
        )
        self._limiter = AsyncLimiter(1, settings.wikipedia_min_interval_s)
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

    async def _request(self, params: dict[str, Any]) -> dict[str, Any]:
        async with self._limiter:
            response = await self._client.get("", params=params)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data

    async def get_plot(self, title: str) -> str | None:
        sections_response = await self._get(
            {"action": "parse", "page": title, "prop": "sections", "format": "json"}
        )
        plot_index = _find_plot_section_index(sections_response)
        if plot_index is None:
            return None

        body_response = await self._get(
            {
                "action": "parse",
                "page": title,
                "section": plot_index,
                "prop": "text",
                "format": "json",
            }
        )
        return _extract_text_html(body_response)


def _find_plot_section_index(payload: dict[str, Any]) -> str | None:
    parse = payload.get("parse")
    if not isinstance(parse, dict):
        return None
    sections = parse.get("sections")
    if not isinstance(sections, list):
        return None
    for section in sections:
        if not isinstance(section, dict):
            continue
        line = section.get("line")
        if isinstance(line, str) and line.strip().lower() in _PLOT_HEADINGS:
            index = section.get("index")
            if isinstance(index, str | int):
                return str(index)
    return None


def _extract_text_html(payload: dict[str, Any]) -> str | None:
    parse = payload.get("parse")
    if not isinstance(parse, dict):
        return None
    text = parse.get("text")
    if not isinstance(text, dict):
        return None
    value = text.get("*")
    return value if isinstance(value, str) else None
