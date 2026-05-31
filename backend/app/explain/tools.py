from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Movie, Quote, Scene
from app.movies import service as movies_service
from app.search import service as search_service
from app.search.embedder import Embedder

SEARCH_LIMIT = 10

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_movies",
            "description": (
                "Semantic search over the film corpus. Returns candidate movies with a "
                "matching text snippet. Use this first to find movies from a plot, vibe, "
                "scene, or theme description."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "semantic_query": {
                        "type": "string",
                        "description": (
                            "Natural-language description of plot, vibe, scene or theme."
                        ),
                    }
                },
                "required": ["semantic_query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_movie_detail",
            "description": (
                "Full details for one movie by its movie_id: overview, plot summary, "
                "themes, atmosphere, cast, scenes, quotes and characters."
            ),
            "parameters": {
                "type": "object",
                "properties": {"movie_id": {"type": "integer"}},
                "required": ["movie_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_movie_scenes",
            "description": "All scenes of one movie (index, title, description, mood, characters).",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_id": {"type": "integer"},
                    "query": {
                        "type": "string",
                        "description": (
                            "Keyword or theme to focus on (reserved for future filtering)."
                        ),
                    },
                },
                "required": ["movie_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_movie_quotes",
            "description": "All quotes of one movie (quote text and who said it).",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_id": {"type": "integer"},
                    "query": {
                        "type": "string",
                        "description": (
                            "Keyword or theme to focus on (reserved for future filtering)."
                        ),
                    },
                },
                "required": ["movie_id"],
            },
        },
    },
]


async def run_search_movies(
    session: AsyncSession, embedder: Embedder, semantic_query: str
) -> list[dict[str, Any]]:
    resp = await search_service.search(
        session, embedder, query=semantic_query, limit=SEARCH_LIMIT
    )
    return [
        {
            "movie_id": r.movie_id,
            "title": r.title,
            "year": r.year,
            "score": round(r.score, 3),
            "best_chunk": r.best_chunk.text,
        }
        for r in resp.results
    ]


async def movie_brief(session: AsyncSession, movie_id: int) -> tuple[str, int | None] | None:
    row = (
        await session.execute(select(Movie.title, Movie.year).where(Movie.id == movie_id))
    ).first()
    if row is None:
        return None
    return (row[0], row[1])


async def run_get_movie_detail(session: AsyncSession, movie_id: int) -> dict[str, Any]:
    movie = await movies_service.get_by_id(session, movie_id)
    if movie is None:
        return {"error": "movie_not_found", "movie_id": movie_id}
    return movies_service.to_detail(movie).model_dump(mode="json")


async def run_get_movie_scenes(session: AsyncSession, movie_id: int) -> list[dict[str, Any]]:
    scenes = (
        (await session.execute(
            select(Scene).where(Scene.movie_id == movie_id).order_by(Scene.scene_index)
        )).scalars().all()
    )
    return [
        {
            "scene_index": s.scene_index,
            "title": s.title,
            "description": s.description,
            "mood": s.mood,
            "characters": s.characters,
        }
        for s in scenes
    ]


async def run_get_movie_quotes(session: AsyncSession, movie_id: int) -> list[dict[str, Any]]:
    quotes = (
        (await session.execute(
            select(Quote).where(Quote.movie_id == movie_id).order_by(Quote.quote_index)
        )).scalars().all()
    )
    return [{"quote_text": q.quote_text, "attributed_to": q.attributed_to} for q in quotes]


async def dispatch(
    session: AsyncSession,
    embedder: Embedder,
    name: str,
    args: dict[str, Any],
    cited: dict[int, dict[str, Any]],
) -> Any:
    if name == "search_movies":
        return await run_search_movies(session, embedder, args["semantic_query"])

    movie_id = int(args["movie_id"])
    brief = await movie_brief(session, movie_id)
    if brief is None:
        return {"error": "movie_not_found", "movie_id": movie_id}
    cited[movie_id] = {"movie_id": movie_id, "title": brief[0], "year": brief[1]}

    if name == "get_movie_detail":
        return await run_get_movie_detail(session, movie_id)
    if name == "get_movie_scenes":
        return await run_get_movie_scenes(session, movie_id)
    if name == "get_movie_quotes":
        return await run_get_movie_quotes(session, movie_id)
    return {"error": "unknown_tool", "tool": name}
