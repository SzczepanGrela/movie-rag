import argparse
import asyncio
from typing import NamedTuple

from app.models import Chunk, Movie, Scene
from sqlalchemy import delete, exists, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from lib.chunks import build_embed_input, chunk_row
from lib.config import EtlSettings
from lib.db import make_engine, make_session_factory
from lib.embeddings import Embedder, GemmaEmbedder, embed_async
from lib.scenes import compose_scene_text

SCENE_KIND = "scene"


class MovieMeta(NamedTuple):
    title: str
    year: int | None


class SceneChunkPlan(NamedTuple):
    scene_id: int
    movie_id: int
    scene_index: int
    content: str
    embed_input: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Embed schema-C scenes into the chunks table")
    parser.add_argument("--batch-size", type=int, default=50, help="Movies per batch")
    parser.add_argument("--limit", type=int, default=None, help="Cap on movies to process")
    parser.add_argument("--force", action="store_true", help="Re-embed all (DELETE scene chunks)")
    parser.add_argument("--dry-run", action="store_true", help="Count target movies; no writes")
    return parser.parse_args()


async def target_movie_ids(session: AsyncSession, *, force: bool, limit: int | None) -> list[int]:
    has_scenes = exists().where(Scene.movie_id == Movie.id)
    stmt = select(Movie.id).where(has_scenes).order_by(Movie.id)
    if not force:
        already = exists().where((Chunk.movie_id == Movie.id) & (Chunk.kind == SCENE_KIND))
        stmt = stmt.where(~already)
    ids = [row[0] for row in (await session.execute(stmt)).all()]
    if limit is not None:
        ids = ids[:limit]
    return ids


async def load_movie_meta(session: AsyncSession, ids: list[int]) -> dict[int, MovieMeta]:
    stmt = select(Movie.id, Movie.title, Movie.year).where(Movie.id.in_(ids))
    return {mid: MovieMeta(title, year) for mid, title, year in (await session.execute(stmt)).all()}


async def load_scenes(
    session: AsyncSession, ids: list[int]
) -> dict[int, list[tuple[int, int, str, str, str, list[str]]]]:
    stmt = select(
        Scene.id,
        Scene.movie_id,
        Scene.scene_index,
        Scene.title,
        Scene.description,
        Scene.mood,
        Scene.characters,
    ).where(Scene.movie_id.in_(ids))
    grouped: dict[int, list[tuple[int, int, str, str, str, list[str]]]] = {}
    for sid, movie_id, idx, title, desc, mood, chars in (await session.execute(stmt)).all():
        grouped.setdefault(movie_id, []).append((sid, idx, title, desc, mood, chars or []))
    return grouped


def plan_scene_chunks(
    meta: dict[int, MovieMeta],
    scenes_by_movie: dict[int, list[tuple[int, int, str, str, str, list[str]]]],
) -> list[SceneChunkPlan]:
    plans: list[SceneChunkPlan] = []
    for movie_id, scenes in scenes_by_movie.items():
        m = meta.get(movie_id)
        if m is None:
            continue
        for scene_id, scene_index, title, description, mood, characters in scenes:
            content = compose_scene_text(
                title=title, description=description, mood=mood, characters=characters
            )
            if not content.strip():
                continue
            plans.append(
                SceneChunkPlan(
                    scene_id=scene_id,
                    movie_id=movie_id,
                    scene_index=scene_index,
                    content=content,
                    embed_input=build_embed_input(m.title, m.year, content),
                )
            )
    return plans


async def process_batch(
    session: AsyncSession, embedder: Embedder, batch_ids: list[int], *, force: bool
) -> tuple[int, int]:
    meta = await load_movie_meta(session, batch_ids)
    scenes_by_movie = await load_scenes(session, batch_ids)
    plans = plan_scene_chunks(meta, scenes_by_movie)

    rows = []
    if plans:
        vectors = await embed_async(embedder, [p.embed_input for p in plans], kind="document")
        rows = [
            chunk_row(
                movie_id=p.movie_id,
                chunk_index=p.scene_index,
                content=p.content,
                embedding=vec,
                kind=SCENE_KIND,
                scene_id=p.scene_id,
            )
            for p, vec in zip(plans, vectors, strict=True)
        ]

    # --force deletes only scene chunks; plot/overview chunks are owned by 05_embed.py
    if force:
        await session.execute(
            delete(Chunk).where(Chunk.movie_id.in_(batch_ids) & (Chunk.kind == SCENE_KIND))
        )
    if rows:
        await session.execute(insert(Chunk).values(rows))
    await session.commit()
    return len(batch_ids), len(rows)


async def main() -> None:
    args = parse_args()
    settings = EtlSettings()

    print(f"loading embedder ({GemmaEmbedder.__name__})...")
    embedder = GemmaEmbedder()

    engine = make_engine(settings)
    session_factory = make_session_factory(engine)
    try:
        async with session_factory() as session:
            ids = await target_movie_ids(session, force=args.force, limit=args.limit)
            print(f"target movies for scene embedding: {len(ids)}")
            if args.dry_run:
                print(f"would embed scenes for {len(ids)} movies (dry-run)")
                return

            total_movies = 0
            total_chunks = 0
            for offset in range(0, len(ids), args.batch_size):
                batch_ids = ids[offset : offset + args.batch_size]
                movies, chunks = await process_batch(session, embedder, batch_ids, force=args.force)
                total_movies += movies
                total_chunks += chunks
                print(
                    f"batch {offset // args.batch_size + 1}: {movies} movies, "
                    f"+{chunks} scene chunks (total {total_movies}/{len(ids)})"
                )
            print(f"done: {total_movies} movies, {total_chunks} scene chunks")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
