import argparse
import asyncio

import httpx
from app.models import Movie
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from lib.blurhash_util import encode_blurhash
from lib.config import EtlSettings
from lib.db import make_engine, make_session_factory
from lib.r2_client import R2Client
from lib.tmdb_client import TmdbClient

IMAGE_BASE = "https://image.tmdb.org/t/p"
SIZES = ("w154", "w500")
BLURHASH_SIZE = "w154"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill movie posters to R2 (w154 + w500) and store blurhash"
    )
    parser.add_argument("--batch-size", type=int, default=50, help="Movies processed per batch")
    parser.add_argument("--limit", type=int, default=None, help="Cap on movies to process")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-process all movies, not only those without blurhash",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Count target movies; no fetch/write"
    )
    return parser.parse_args()


async def target_tmdb_ids(session: AsyncSession, *, force: bool, limit: int | None) -> list[int]:
    stmt = select(Movie.tmdb_id).order_by(Movie.tmdb_id)
    if not force:
        stmt = stmt.where(Movie.blurhash.is_(None))
    ids = [row[0] for row in (await session.execute(stmt)).all()]
    if limit is not None:
        ids = ids[:limit]
    return ids


async def process_movie(
    client: TmdbClient,
    img: httpx.AsyncClient,
    r2: R2Client,
    tmdb_id: int,
) -> tuple[int, str | None, str | None, str]:
    try:
        detail = await client.get_movie(tmdb_id, append_credits=False)
    except httpx.HTTPStatusError as exc:
        return tmdb_id, None, None, f"detail_http_{exc.response.status_code}"

    poster_path = detail.get("poster_path")
    if not poster_path:
        return tmdb_id, None, None, "no_poster"

    bitmaps: dict[str, bytes] = {}
    for size in SIZES:
        resp = await img.get(f"{IMAGE_BASE}/{size}{poster_path}")
        if resp.status_code != 200:
            return tmdb_id, None, None, f"image_http_{resp.status_code}"
        bitmaps[size] = resp.content

    blurhash = encode_blurhash(bitmaps[BLURHASH_SIZE])
    for size in SIZES:
        await asyncio.to_thread(r2.put_jpeg, f"posters/{size}/{tmdb_id}.jpg", bitmaps[size])

    return tmdb_id, poster_path, blurhash, "ok"


async def persist_batch(
    session: AsyncSession,
    results: list[tuple[int, str | None, str | None, str]],
) -> None:
    for tmdb_id, poster_path, blurhash, status in results:
        if status != "ok":
            continue
        await session.execute(
            update(Movie)
            .where(Movie.tmdb_id == tmdb_id)
            .values(poster_path=poster_path, blurhash=blurhash)
        )
    await session.commit()


async def main() -> None:
    args = parse_args()
    settings = EtlSettings()

    engine = make_engine(settings)
    session_factory = make_session_factory(engine)
    try:
        async with session_factory() as session:
            ids = await target_tmdb_ids(session, force=args.force, limit=args.limit)
            print(f"target movies to backfill: {len(ids)}")

            if args.dry_run:
                print(f"would backfill {len(ids)} movies (dry-run)")
                return

            r2 = R2Client(settings)
            totals = {"ok": 0, "no_poster": 0, "error": 0}

            async with (
                TmdbClient(settings) as client,
                httpx.AsyncClient(timeout=settings.request_timeout_s) as img,
            ):
                for offset in range(0, len(ids), args.batch_size):
                    batch = ids[offset : offset + args.batch_size]
                    results = await asyncio.gather(
                        *[process_movie(client, img, r2, tid) for tid in batch]
                    )
                    await persist_batch(session, results)

                    for _tid, _pp, _bh, status in results:
                        if status == "ok":
                            totals["ok"] += 1
                        elif status == "no_poster":
                            totals["no_poster"] += 1
                        else:
                            totals["error"] += 1

                    done = offset + len(batch)
                    print(
                        f"batch {offset // args.batch_size + 1}: "
                        f"ok={totals['ok']} no_poster={totals['no_poster']} "
                        f"error={totals['error']} (total {done}/{len(ids)})"
                    )

            print(
                f"done: {totals['ok']} posters uploaded, "
                f"{totals['no_poster']} without poster, {totals['error']} errors"
            )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
