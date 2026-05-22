import argparse
import asyncio
from typing import Any

import httpx
from app.models import Movie, MovieCast, MovieCrew, Person
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from lib.build_list import dedupe_by_tmdb_id
from lib.config import EtlSettings
from lib.credits import key_crew, person_rows, to_cast_row, to_crew_row, top_cast
from lib.db import make_engine, make_session_factory, pg_insert_ignore, pg_upsert
from lib.tmdb_client import TmdbClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch TMDb credits and populate people + movie_cast + movie_crew"
    )
    parser.add_argument("--batch-size", type=int, default=100, help="Movies fetched per batch")
    parser.add_argument("--limit", type=int, default=None, help="Cap on movies to process")
    parser.add_argument(
        "--force", action="store_true", help="Re-process all movies, not only enriched"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Count target movies; no fetch/write"
    )
    return parser.parse_args()


async def fetch_detail(client: TmdbClient, tmdb_id: int) -> dict[str, Any] | None:
    try:
        return await client.get_movie(tmdb_id, append_credits=True)
    except httpx.HTTPStatusError as exc:
        print(f"skip tmdb_id={tmdb_id}: HTTP {exc.response.status_code}")
        return None


async def fetch_batch(client: TmdbClient, tmdb_ids: list[int]) -> list[dict[str, Any]]:
    details = await asyncio.gather(*[fetch_detail(client, tid) for tid in tmdb_ids])
    return [d for d in details if d is not None]


async def target_tmdb_ids(session: AsyncSession, *, force: bool, limit: int | None) -> list[int]:
    stmt = select(Movie.tmdb_id).order_by(Movie.tmdb_id)
    if not force:
        stmt = stmt.where(Movie.etl_status == "enriched")
    result = await session.execute(stmt)
    ids = [row[0] for row in result.all()]
    if limit is not None:
        ids = ids[:limit]
    return ids


async def process_batch(
    session: AsyncSession, client: TmdbClient, batch: list[int]
) -> tuple[int, int, int]:
    details = await fetch_batch(client, batch)
    if not details:
        return 0, 0, 0

    people = dedupe_by_tmdb_id([row for d in details for row in person_rows(d)])
    await pg_upsert(session, Person, people, conflict_cols=["tmdb_id"])

    person_tmdb = [p["tmdb_id"] for p in people]
    result = await session.execute(
        select(Person.id, Person.tmdb_id).where(Person.tmdb_id.in_(person_tmdb))
    )
    person_id_by_tmdb = {tmdb_id: pid for pid, tmdb_id in result.all()}

    batch_tmdb = [d["id"] for d in details]
    result = await session.execute(
        select(Movie.id, Movie.tmdb_id).where(Movie.tmdb_id.in_(batch_tmdb))
    )
    movie_id_by_tmdb = {tmdb_id: mid for mid, tmdb_id in result.all()}

    cast_rows: list[dict[str, Any]] = []
    crew_rows: list[dict[str, Any]] = []
    for detail in details:
        movie_id = movie_id_by_tmdb[detail["id"]]
        for entry in top_cast(detail):
            person_id = person_id_by_tmdb.get(entry["id"])
            if person_id is not None:
                cast_rows.append(to_cast_row(entry, movie_id, person_id))
        for entry in key_crew(detail):
            person_id = person_id_by_tmdb.get(entry["id"])
            if person_id is not None:
                crew_rows.append(to_crew_row(entry, movie_id, person_id))

    cast_links = await pg_insert_ignore(
        session, MovieCast, cast_rows, conflict_cols=["movie_id", "person_id"]
    )
    crew_links = await pg_insert_ignore(
        session, MovieCrew, crew_rows, conflict_cols=["movie_id", "person_id", "job"]
    )

    await session.execute(
        update(Movie).where(Movie.tmdb_id.in_(batch_tmdb)).values(etl_status="credited")
    )
    await session.commit()

    return len(details), cast_links, crew_links


async def main() -> None:
    args = parse_args()
    settings = EtlSettings()

    engine = make_engine(settings)
    session_factory = make_session_factory(engine)
    try:
        async with TmdbClient(settings) as client, session_factory() as session:
            ids = await target_tmdb_ids(session, force=args.force, limit=args.limit)
            print(f"target movies to credit: {len(ids)}")

            if args.dry_run:
                print(f"would credit {len(ids)} movies (dry-run)")
                return

            total_movies = 0
            total_cast = 0
            total_crew = 0
            for offset in range(0, len(ids), args.batch_size):
                batch = ids[offset : offset + args.batch_size]
                movies, cast_links, crew_links = await process_batch(session, client, batch)
                total_movies += movies
                total_cast += cast_links
                total_crew += crew_links
                print(
                    f"batch {offset // args.batch_size + 1}: "
                    f"credited {movies}, +{cast_links} cast, +{crew_links} crew "
                    f"(total {total_movies}/{len(ids)})"
                )

            print(
                f"done: credited {total_movies} movies, "
                f"{total_cast} cast links, {total_crew} crew links"
            )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
