import argparse
import asyncio
from typing import Any

import httpx
from app.models import Genre, Movie, movie_genres
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lib.config import EtlSettings
from lib.db import make_engine, make_session_factory, pg_insert_ignore, pg_upsert
from lib.enrich import genre_tmdb_ids, to_enrichment_row, to_genre_row
from lib.tmdb_client import TmdbClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enrich seeded movies via TMDb get_movie + populate genres M:N"
    )
    parser.add_argument("--batch-size", type=int, default=100, help="Movies fetched per batch")
    parser.add_argument("--limit", type=int, default=None, help="Cap on movies to process")
    parser.add_argument(
        "--force", action="store_true", help="Re-process all movies, not only seeded"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Count target movies; no fetch/write"
    )
    return parser.parse_args()


async def fetch_detail(client: TmdbClient, tmdb_id: int) -> dict[str, Any] | None:
    try:
        return await client.get_movie(tmdb_id, append_credits=False)
    except httpx.HTTPStatusError as exc:
        print(f"skip tmdb_id={tmdb_id}: HTTP {exc.response.status_code}")
        return None


async def fetch_batch(client: TmdbClient, tmdb_ids: list[int]) -> list[dict[str, Any]]:
    details = await asyncio.gather(*[fetch_detail(client, tid) for tid in tmdb_ids])
    return [d for d in details if d is not None]


async def seed_genres(session: AsyncSession, client: TmdbClient) -> dict[int, int]:
    data = await client.get_genres()
    genre_rows = [to_genre_row(g) for g in data.get("genres", [])]
    await pg_upsert(session, Genre, genre_rows, conflict_cols=["tmdb_id"])
    result = await session.execute(select(Genre.id, Genre.tmdb_id))
    return {tmdb_id: gid for gid, tmdb_id in result.all()}


async def target_tmdb_ids(session: AsyncSession, *, force: bool, limit: int | None) -> list[int]:
    stmt = select(Movie.tmdb_id).order_by(Movie.tmdb_id)
    if not force:
        stmt = stmt.where(Movie.etl_status == "seeded")
    result = await session.execute(stmt)
    ids = [row[0] for row in result.all()]
    if limit is not None:
        ids = ids[:limit]
    return ids


async def process_batch(
    session: AsyncSession,
    client: TmdbClient,
    batch: list[int],
    genre_id_by_tmdb: dict[int, int],
) -> tuple[int, int]:
    details = await fetch_batch(client, batch)
    if not details:
        return 0, 0

    enrich_rows = [to_enrichment_row(d) for d in details]
    await pg_upsert(session, Movie, enrich_rows, conflict_cols=["tmdb_id"])

    batch_tmdb = [d["id"] for d in details]
    result = await session.execute(
        select(Movie.id, Movie.tmdb_id).where(Movie.tmdb_id.in_(batch_tmdb))
    )
    movie_id_by_tmdb = {tmdb_id: mid for mid, tmdb_id in result.all()}

    link_rows: list[dict[str, Any]] = []
    for detail in details:
        movie_id = movie_id_by_tmdb[detail["id"]]
        for g_tmdb in genre_tmdb_ids(detail):
            genre_id = genre_id_by_tmdb.get(g_tmdb)
            if genre_id is not None:
                link_rows.append({"movie_id": movie_id, "genre_id": genre_id})

    links = await pg_insert_ignore(
        session, movie_genres, link_rows, conflict_cols=["movie_id", "genre_id"]
    )
    return len(details), links


async def main() -> None:
    args = parse_args()
    settings = EtlSettings()

    engine = make_engine(settings)
    session_factory = make_session_factory(engine)
    try:
        async with TmdbClient(settings) as client, session_factory() as session:
            genre_id_by_tmdb = await seed_genres(session, client)
            print(f"seeded {len(genre_id_by_tmdb)} genres")

            ids = await target_tmdb_ids(session, force=args.force, limit=args.limit)
            print(f"target movies to enrich: {len(ids)}")

            if args.dry_run:
                print(f"would enrich {len(ids)} movies (dry-run)")
                return

            total_enriched = 0
            total_links = 0
            for offset in range(0, len(ids), args.batch_size):
                batch = ids[offset : offset + args.batch_size]
                enriched, links = await process_batch(session, client, batch, genre_id_by_tmdb)
                total_enriched += enriched
                total_links += links
                print(
                    f"batch {offset // args.batch_size + 1}: "
                    f"enriched {enriched}, +{links} genre links "
                    f"(total {total_enriched}/{len(ids)})"
                )

            print(f"done: enriched {total_enriched} movies, {total_links} genre links")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
