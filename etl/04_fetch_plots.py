import argparse
import asyncio
from typing import Any, NamedTuple

import httpx
from app.models import Movie, SourceText
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from lib.config import EtlSettings
from lib.db import make_engine, make_session_factory, pg_upsert
from lib.plots import build_search_query, html_to_text, source_text_row
from lib.wikipedia_client import WikipediaClient


class MovieTarget(NamedTuple):
    id: int
    title: str
    year: int | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch Wikipedia plot summaries and populate source_texts"
    )
    parser.add_argument("--batch-size", type=int, default=50, help="Movies fetched per batch")
    parser.add_argument("--limit", type=int, default=None, help="Cap on movies to process")
    parser.add_argument(
        "--force", action="store_true", help="Re-process all movies, not only credited"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Count target movies; no fetch/write"
    )
    return parser.parse_args()


async def target_movies(
    session: AsyncSession, *, force: bool, limit: int | None
) -> list[MovieTarget]:
    stmt = select(Movie.id, Movie.title, Movie.year).order_by(Movie.id)
    if not force:
        stmt = stmt.where(Movie.etl_status == "credited")
    result = await session.execute(stmt)
    rows = [MovieTarget(mid, title, year) for mid, title, year in result.all()]
    if limit is not None:
        rows = rows[:limit]
    return rows


async def fetch_plot(client: WikipediaClient, movie: MovieTarget) -> tuple[str, str] | None:
    try:
        page_title = await client.search_title(build_search_query(movie.title, movie.year))
        if page_title is None:
            return None
        html = await client.get_plot(page_title)
        if html is None:
            return None
        text = html_to_text(html)
        if not text:
            return None
        return page_title, text
    except httpx.HTTPStatusError as exc:
        print(f"skip movie_id={movie.id} ({movie.title!r}): HTTP {exc.response.status_code}")
        return None


async def process_batch(
    session: AsyncSession, client: WikipediaClient, batch: list[MovieTarget]
) -> tuple[int, int]:
    results = await asyncio.gather(*[fetch_plot(client, m) for m in batch])

    rows: list[dict[str, Any]] = []
    for movie, res in zip(batch, results, strict=True):
        if res is None:
            continue
        page_title, text = res
        rows.append(source_text_row(movie.id, page_title, text))

    stored = await pg_upsert(
        session, SourceText, rows, conflict_cols=["movie_id", "source", "lang"]
    )

    await session.execute(
        update(Movie).where(Movie.id.in_([m.id for m in batch])).values(etl_status="sourced")
    )
    await session.commit()

    return len(batch), stored


async def main() -> None:
    args = parse_args()
    settings = EtlSettings()

    engine = make_engine(settings)
    session_factory = make_session_factory(engine)
    try:
        async with WikipediaClient(settings) as client, session_factory() as session:
            movies = await target_movies(session, force=args.force, limit=args.limit)
            print(f"target movies to source: {len(movies)}")

            if args.dry_run:
                print(f"would source {len(movies)} movies (dry-run)")
                return

            total_processed = 0
            total_stored = 0
            for offset in range(0, len(movies), args.batch_size):
                batch = movies[offset : offset + args.batch_size]
                processed, stored = await process_batch(session, client, batch)
                total_processed += processed
                total_stored += stored
                print(
                    f"batch {offset // args.batch_size + 1}: "
                    f"processed {processed}, +{stored} plots "
                    f"(total {total_processed}/{len(movies)}, plots {total_stored})"
                )

            print(f"done: processed {total_processed} movies, stored {total_stored} plots")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
