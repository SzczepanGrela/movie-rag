import argparse
import asyncio
from typing import Any

from app.models import Movie

from lib.build_list import dedupe_by_tmdb_id, to_movie_row
from lib.config import EtlSettings
from lib.db import make_engine, make_session_factory, pg_upsert
from lib.tmdb_client import TmdbClient

BASE_FILTERS: dict[str, Any] = {
    "primary_release_date.gte": "1970-01-01",
    "vote_count.gte": 100,
    "with_runtime.gte": 60,
    "with_original_language": "en",
    "language": "en-US",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build seed movie list from TMDb (popular + top-rated)"
    )
    parser.add_argument("--limit", type=int, default=5000, help="Max rows after dedup")
    parser.add_argument(
        "--pages-per-source",
        type=int,
        default=125,
        help="Pages of discover per source (popular and top-rated)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Fetch + dedup; do not write to DB")
    return parser.parse_args()


async def fetch_pages(
    client: TmdbClient,
    sort_by: str,
    pages: int,
    base_filters: dict[str, Any],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for page in range(1, pages + 1):
        data = await client.discover(page=page, sort_by=sort_by, **base_filters)
        page_results = data.get("results", [])
        if not isinstance(page_results, list):
            break
        results.extend(page_results)
        if len(page_results) < 20:
            break
    return results


async def main() -> None:
    args = parse_args()
    settings = EtlSettings()

    async with TmdbClient(settings) as client:
        popular, toprated = await asyncio.gather(
            fetch_pages(client, "popularity.desc", args.pages_per_source, BASE_FILTERS),
            fetch_pages(client, "vote_average.desc", args.pages_per_source, BASE_FILTERS),
        )

    api_rows = [*popular, *toprated]
    rows = dedupe_by_tmdb_id([to_movie_row(r) for r in api_rows])
    rows = rows[: args.limit]

    print(
        f"fetched {len(popular)} popular + {len(toprated)} top-rated; "
        f"after dedup + limit: {len(rows)} movies"
    )

    if args.dry_run:
        print(f"would upsert {len(rows)} movies (dry-run)")
        return

    engine = make_engine(settings)
    session_factory = make_session_factory(engine)
    try:
        async with session_factory() as session:
            count = await pg_upsert(session, Movie, rows, conflict_cols=["tmdb_id"])
        print(f"upserted {count} movies")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
