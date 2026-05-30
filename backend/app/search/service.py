from time import perf_counter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chunk, Movie
from app.posters import build_poster
from app.schemas.search import BestChunk, SearchResponse, SearchResult
from app.search.embedder import Embedder, embed_async

OVERSAMPLE_FACTOR = 5


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
            Movie.title,
            Movie.year,
            Movie.tmdb_id,
            Movie.poster_path,
            Movie.blurhash,
        )
        .join(Movie, Movie.id == Chunk.movie_id)
        .order_by(distance)
        .limit(limit * OVERSAMPLE_FACTOR)
    )
    rows = (await session.execute(stmt)).all()

    seen: set[int] = set()
    results: list[SearchResult] = []
    for movie_id, content, dist, title, year, tmdb_id, poster_path, blurhash in rows:
        if movie_id in seen:
            continue
        seen.add(movie_id)
        results.append(
            SearchResult(
                movie_id=movie_id,
                title=title,
                year=year,
                score=1.0 - float(dist),
                best_chunk=BestChunk(text=content, score=1.0 - float(dist)),
                poster=build_poster(tmdb_id, poster_path, blurhash),
            )
        )
        if len(results) >= limit:
            break

    took_ms = int((perf_counter() - t0) * 1000)
    return SearchResponse(results=results, total_candidates=len(rows), took_ms=took_ms)
