from typing import Any, cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.explain import tools


class _FakeEmbedder:
    def embed(self, texts: list[str], *, kind: str) -> list[list[float]]:
        return [[0.0] for _ in texts]


async def test_dispatch_search_movies(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_run_search(session: Any, embedder: Any, q: str) -> list[dict[str, Any]]:
        return [
            {
                "movie_id": 1,
                "title": "Con Air",
                "year": 1997,
                "score": 0.9,
                "best_chunk": "jumps from a plane",
            }
        ]

    monkeypatch.setattr(tools, "run_search_movies", fake_run_search)
    cited: dict[int, dict[str, Any]] = {}
    result = await tools.dispatch(
        cast(AsyncSession, None),
        _FakeEmbedder(),
        "search_movies",
        {"semantic_query": "plane"},
        cited,
    )
    assert result[0]["title"] == "Con Air"
    assert cited == {}  # search results are NOT cited until model zooms in


async def test_dispatch_get_movie_detail_marks_cited(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_brief(session: Any, movie_id: int) -> tuple[str, int | None] | None:
        return ("Con Air", 1997)

    async def fake_detail(session: Any, movie_id: int) -> dict[str, Any]:
        return {"id": movie_id, "title": "Con Air", "scenes": []}

    monkeypatch.setattr(tools, "movie_brief", fake_brief)
    monkeypatch.setattr(tools, "run_get_movie_detail", fake_detail)
    cited: dict[int, dict[str, Any]] = {}
    result = await tools.dispatch(
        cast(AsyncSession, None), _FakeEmbedder(), "get_movie_detail", {"movie_id": 123}, cited
    )
    assert result["title"] == "Con Air"
    assert cited == {123: {"movie_id": 123, "title": "Con Air", "year": 1997}}


async def test_dispatch_missing_movie_returns_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_brief(session: Any, movie_id: int) -> tuple[str, int | None] | None:
        return None

    monkeypatch.setattr(tools, "movie_brief", fake_brief)
    cited: dict[int, dict[str, Any]] = {}
    result = await tools.dispatch(
        cast(AsyncSession, None), _FakeEmbedder(), "get_movie_scenes", {"movie_id": 999}, cited
    )
    assert result == {"error": "movie_not_found", "movie_id": 999}
    assert cited == {}


def test_tool_schemas_cover_four_tools() -> None:
    names = {t["function"]["name"] for t in tools.TOOL_SCHEMAS}
    assert names == {"search_movies", "get_movie_detail", "get_movie_scenes", "get_movie_quotes"}
