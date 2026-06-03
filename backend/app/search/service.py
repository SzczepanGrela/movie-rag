from time import perf_counter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Chunk, Movie
from app.posters import build_poster
from app.schemas.search import BestChunk, SearchResponse, SearchResult
from app.search.embedder import Embedder, embed_async

SCENE_KIND = "scene"


def _weight(kind: str) -> float:
    return settings.search_scene_weight if kind == SCENE_KIND else 1.0


async def search(
    session: AsyncSession,
    embedder: Embedder,
    *,
    query: str,
    limit: int,
) -> SearchResponse:
    t0 = perf_counter()

    [vec] = await embed_async(embedder, [query], kind="query")

    distance = Chunk.embedding.cosine_distance(vec).label("dist")
    stmt = (
        select(
            Chunk.movie_id,
            Chunk.content,
            distance,
            Chunk.kind,
            Movie.title,
            Movie.year,
            Movie.tmdb_id,
            Movie.poster_path,
            Movie.blurhash,
        )
        .join(Movie, Movie.id == Chunk.movie_id)
        .order_by(distance)
        .limit(settings.search_candidate_pool)
    )
    rows = (await session.execute(stmt)).all()

    best: dict[int, SearchResult] = {}
    for movie_id, content, dist, kind, title, year, tmdb_id, poster_path, blurhash in rows:
        # cosine_distance is [0,2]; clamp keeps anti-correlated chunks from
        # surfacing negative relevance scores in the API and the LLM tool output.
        # The kind weight applies within a movie too, so a movie's score stays
        # consistent with the best_chunk it exposes.
        score = max(0.0, (1.0 - float(dist)) * _weight(kind))
        current = best.get(movie_id)
        if current is None or score > current.score:
            best[movie_id] = SearchResult(
                movie_id=movie_id,
                title=title,
                year=year,
                score=score,
                best_chunk=BestChunk(text=content, score=score),
                poster=build_poster(tmdb_id, poster_path, blurhash),
            )

    results = sorted(best.values(), key=lambda r: r.score, reverse=True)[:limit]

    took_ms = int((perf_counter() - t0) * 1000)
    return SearchResponse(results=results, total_candidates=len(rows), took_ms=took_ms)
