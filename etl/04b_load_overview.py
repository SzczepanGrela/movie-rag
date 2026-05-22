import argparse
import asyncio
from typing import NamedTuple

from app.models import Movie, SourceText
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from lib.config import EtlSettings
from lib.db import make_engine, make_session_factory, pg_upsert
from lib.overview import OVERVIEW_LANG, OVERVIEW_SOURCE, overview_row


class MovieOverview(NamedTuple):
    id: int
    overview: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load TMDb Movie.overview into source_texts (source='tmdb_overview')"
    )
    parser.add_argument("--batch-size", type=int, default=500, help="Movies per batch")
    parser.add_argument("--limit", type=int, default=None, help="Cap on movies to process")
    parser.add_argument(
        "--force", action="store_true", help="Re-upsert even if source_text already exists"
    )
    parser.add_argument("--dry-run", action="store_true", help="Count target movies; no writes")
    return parser.parse_args()


async def target_movies(
    session: AsyncSession, *, force: bool, limit: int | None
) -> list[MovieOverview]:
    stmt = (
        select(Movie.id, Movie.overview)
        .where(Movie.overview.is_not(None), Movie.overview != "")
        .order_by(Movie.id)
    )
    if not force:
        stmt = stmt.where(
            ~exists().where(
                SourceText.movie_id == Movie.id,
                SourceText.source == OVERVIEW_SOURCE,
                SourceText.lang == OVERVIEW_LANG,
            )
        )
    result = await session.execute(stmt)
    movies = [MovieOverview(id=row[0], overview=row[1]) for row in result.all()]
    if limit is not None:
        movies = movies[:limit]
    return movies


async def process_batch(session: AsyncSession, batch: list[MovieOverview]) -> int:
    rows = [overview_row(m.id, m.overview) for m in batch]
    return await pg_upsert(session, SourceText, rows, conflict_cols=["movie_id", "source", "lang"])


async def main() -> None:
    args = parse_args()
    settings = EtlSettings()

    engine = make_engine(settings)
    session_factory = make_session_factory(engine)
    try:
        async with session_factory() as session:
            movies = await target_movies(session, force=args.force, limit=args.limit)
            print(f"target movies to load overview: {len(movies)}")

            if args.dry_run:
                print(f"would load {len(movies)} overviews (dry-run)")
                return

            total_stored = 0
            for offset in range(0, len(movies), args.batch_size):
                batch = movies[offset : offset + args.batch_size]
                stored = await process_batch(session, batch)
                total_stored += stored
                print(
                    f"batch {offset // args.batch_size + 1}: "
                    f"upserted {stored} (total {total_stored}/{len(movies)})"
                )

            print(f"done: upserted {total_stored} overview rows")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
