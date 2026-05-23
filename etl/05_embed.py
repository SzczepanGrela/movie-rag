import argparse
import asyncio
from typing import NamedTuple

from app.models import Chunk, Genre, Movie, SourceText, movie_genres
from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from lib.chunks import CHUNK_OVERLAP, CHUNK_SIZE, build_embed_input, chunk_body, chunk_row
from lib.config import EtlSettings
from lib.db import make_engine, make_session_factory
from lib.embeddings import Embedder, GemmaEmbedder, embed_async


class MovieMeta(NamedTuple):
    title: str
    year: int | None
    genres: list[str]


class ChunkPlan(NamedTuple):
    source_text_id: int
    movie_id: int
    chunk_index: int
    body: str
    embed_input: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chunk + embed source_texts into chunks table")
    parser.add_argument("--batch-size", type=int, default=50, help="Movies per batch")
    parser.add_argument("--limit", type=int, default=None, help="Cap on movies to process")
    parser.add_argument(
        "--force", action="store_true", help="Re-process all movies (DELETE+INSERT)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Count target movies; no writes")
    return parser.parse_args()


async def target_movie_ids(session: AsyncSession, *, force: bool, limit: int | None) -> list[int]:
    stmt = select(Movie.id).order_by(Movie.id)
    if not force:
        stmt = stmt.where(Movie.etl_status == "sourced")
    result = await session.execute(stmt)
    ids = [row[0] for row in result.all()]
    if limit is not None:
        ids = ids[:limit]
    return ids


async def load_movie_meta(session: AsyncSession, ids: list[int]) -> dict[int, MovieMeta]:
    stmt = (
        select(Movie.id, Movie.title, Movie.year, Genre.name)
        .select_from(Movie)
        .outerjoin(movie_genres, movie_genres.c.movie_id == Movie.id)
        .outerjoin(Genre, Genre.id == movie_genres.c.genre_id)
        .where(Movie.id.in_(ids))
    )
    result = await session.execute(stmt)
    meta: dict[int, MovieMeta] = {}
    for movie_id, title, year, genre_name in result.all():
        if movie_id not in meta:
            meta[movie_id] = MovieMeta(title=title, year=year, genres=[])
        if genre_name is not None:
            meta[movie_id].genres.append(genre_name)
    return meta


async def load_source_texts(
    session: AsyncSession, ids: list[int]
) -> dict[int, list[tuple[int, str]]]:
    stmt = select(SourceText.id, SourceText.movie_id, SourceText.content).where(
        SourceText.movie_id.in_(ids)
    )
    result = await session.execute(stmt)
    grouped: dict[int, list[tuple[int, str]]] = {}
    for source_text_id, movie_id, content in result.all():
        grouped.setdefault(movie_id, []).append((source_text_id, content))
    return grouped


def plan_chunks(
    meta: dict[int, MovieMeta],
    texts_by_movie: dict[int, list[tuple[int, str]]],
) -> list[ChunkPlan]:
    plans: list[ChunkPlan] = []
    for movie_id, source_texts in texts_by_movie.items():
        m = meta.get(movie_id)
        if m is None:
            continue
        for source_text_id, content in source_texts:
            bodies = chunk_body(content, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
            for chunk_index, (body, _token_count) in enumerate(bodies):
                plans.append(
                    ChunkPlan(
                        source_text_id=source_text_id,
                        movie_id=movie_id,
                        chunk_index=chunk_index,
                        body=body,
                        embed_input=build_embed_input(m.title, m.year, body),
                    )
                )
    return plans


async def process_batch(
    session: AsyncSession,
    embedder: Embedder,
    batch_ids: list[int],
    *,
    force: bool,
) -> tuple[int, int]:
    meta = await load_movie_meta(session, batch_ids)
    texts_by_movie = await load_source_texts(session, batch_ids)
    plans = plan_chunks(meta, texts_by_movie)

    if plans:
        texts_to_embed = [p.embed_input for p in plans]
        vectors = await embed_async(embedder, texts_to_embed, kind="document")
        rows = [
            chunk_row(
                source_text_id=p.source_text_id,
                movie_id=p.movie_id,
                chunk_index=p.chunk_index,
                content=p.body,
                embedding=vec,
            )
            for p, vec in zip(plans, vectors, strict=True)
        ]
    else:
        rows = []

    if force:
        await session.execute(delete(Chunk).where(Chunk.movie_id.in_(batch_ids)))
    if rows:
        await session.execute(insert(Chunk).values(rows))
    await session.execute(
        update(Movie).where(Movie.id.in_(batch_ids)).values(etl_status="embedded")
    )
    await session.commit()
    return len(batch_ids), len(rows)


async def main() -> None:
    args = parse_args()
    settings = EtlSettings()

    print(f"loading embedder ({GemmaEmbedder.__name__}); first time may download model...")
    embedder = GemmaEmbedder()

    engine = make_engine(settings)
    session_factory = make_session_factory(engine)
    try:
        async with session_factory() as session:
            ids = await target_movie_ids(session, force=args.force, limit=args.limit)
            print(f"target movies to embed: {len(ids)}")

            if args.dry_run:
                print(f"would embed {len(ids)} movies (dry-run)")
                return

            total_movies = 0
            total_chunks = 0
            for offset in range(0, len(ids), args.batch_size):
                batch_ids = ids[offset : offset + args.batch_size]
                movies, chunks = await process_batch(session, embedder, batch_ids, force=args.force)
                total_movies += movies
                total_chunks += chunks
                print(
                    f"batch {offset // args.batch_size + 1}: "
                    f"embedded {movies} movies, +{chunks} chunks "
                    f"(total {total_movies}/{len(ids)})"
                )

            print(f"done: embedded {total_movies} movies, {total_chunks} chunks")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
