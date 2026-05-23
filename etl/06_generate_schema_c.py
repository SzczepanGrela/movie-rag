import argparse
import asyncio

from app.models import (
    Atmosphere,
    CharacterDescription,
    Movie,
    PlotVariant,
    Quote,
    Scene,
    SourceText,
    Theme,
)
from sqlalchemy import delete, exists, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from lib.config import EtlSettings
from lib.db import make_engine, make_session_factory
from lib.gemini import GeminiClient, VertexGeminiClient, generate_async
from lib.overview import OVERVIEW_SOURCE
from lib.plots import SOURCE as PLOT_SOURCE
from lib.schema_c import SchemaCOut, to_rows

# rough blended estimate; gemini-2.5-flash prices output (~$2.50/1M) far above input (~$0.30/1M),
# and our output is large, so the blended rate skews high. Approximate only.
USD_PER_MILLION_TOKENS = 1.1

TABLE_MAP = {
    "plot_variants": PlotVariant,
    "scenes": Scene,
    "themes": Theme,
    "atmosphere": Atmosphere,
    "quotes": Quote,
    "character_descriptions": CharacterDescription,
}

GenResult = tuple[int, SchemaCOut | None, int]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate schema C (Gemini) into dedicated tables")
    parser.add_argument("--batch-size", type=int, default=10, help="Movies per batch")
    parser.add_argument("--limit", type=int, default=None, help="Cap on movies to process")
    parser.add_argument("--force", action="store_true", help="Re-generate all (DELETE+INSERT)")
    parser.add_argument("--dry-run", action="store_true", help="Count target movies; no API/writes")
    return parser.parse_args()


async def target_movie_ids(session: AsyncSession, *, force: bool, limit: int | None) -> list[int]:
    has_text = exists().where(
        SourceText.movie_id == Movie.id,
        SourceText.source.in_([PLOT_SOURCE, OVERVIEW_SOURCE]),
    )
    stmt = select(Movie.id).where(has_text).order_by(Movie.id)
    if not force:
        stmt = stmt.where(Movie.schema_c_status != "done")
    ids = [row[0] for row in (await session.execute(stmt)).all()]
    if limit is not None:
        ids = ids[:limit]
    return ids


async def load_movie_meta(
    session: AsyncSession, ids: list[int]
) -> dict[int, tuple[str, int | None]]:
    stmt = select(Movie.id, Movie.title, Movie.year).where(Movie.id.in_(ids))
    return {mid: (title, year) for mid, title, year in (await session.execute(stmt)).all()}


async def load_input_text(session: AsyncSession, ids: list[int]) -> dict[int, str]:
    stmt = select(SourceText.movie_id, SourceText.source, SourceText.content).where(
        SourceText.movie_id.in_(ids),
        SourceText.source.in_([PLOT_SOURCE, OVERVIEW_SOURCE]),
    )
    best: dict[int, str] = {}
    for movie_id, source, content in (await session.execute(stmt)).all():
        if movie_id not in best or source == PLOT_SOURCE:
            best[movie_id] = content
    return best


async def generate_one(
    client: GeminiClient,
    sem: asyncio.Semaphore,
    movie_id: int,
    title: str,
    year: int | None,
    text: str,
) -> GenResult:
    try:
        data, tokens = await generate_async(client, sem, title=title, year=year, source_text=text)
        return movie_id, data, tokens
    except Exception as exc:  # noqa: BLE001 - per-movie failure must not abort the run
        print(f"  movie {movie_id} ('{title}') FAILED: {exc}")
        return movie_id, None, 0


async def persist_batch(
    session: AsyncSession, results: list[GenResult], *, force: bool
) -> tuple[int, int, int]:
    done = 0
    failed = 0
    tokens_total = 0
    for movie_id, data, tokens in results:
        if data is None:
            await session.execute(
                update(Movie).where(Movie.id == movie_id).values(schema_c_status="failed")
            )
            failed += 1
            continue
        rows = to_rows(movie_id, data)
        if force:
            for model in TABLE_MAP.values():
                await session.execute(delete(model).where(model.movie_id == movie_id))
        for key, model in TABLE_MAP.items():
            if rows[key]:
                await session.execute(insert(model).values(rows[key]))
        await session.execute(
            update(Movie).where(Movie.id == movie_id).values(schema_c_status="done")
        )
        done += 1
        tokens_total += tokens
    await session.commit()
    return done, failed, tokens_total


async def main() -> None:
    args = parse_args()
    settings = EtlSettings()

    engine = make_engine(settings)
    session_factory = make_session_factory(engine)
    try:
        async with session_factory() as session:
            ids = await target_movie_ids(session, force=args.force, limit=args.limit)
            print(f"target movies for schema C: {len(ids)}")
            if args.dry_run:
                print(f"would generate {len(ids)} movies (dry-run)")
                return

            client: GeminiClient = VertexGeminiClient(settings)
            sem = asyncio.Semaphore(settings.gemini_max_concurrency)

            total_done = 0
            total_failed = 0
            total_tokens = 0
            for offset in range(0, len(ids), args.batch_size):
                batch_ids = ids[offset : offset + args.batch_size]
                meta = await load_movie_meta(session, batch_ids)
                texts = await load_input_text(session, batch_ids)
                tasks = [
                    generate_one(client, sem, mid, meta[mid][0], meta[mid][1], texts[mid])
                    for mid in batch_ids
                    if mid in texts and mid in meta
                ]
                results = await asyncio.gather(*tasks)
                done, failed, tokens = await persist_batch(session, results, force=args.force)
                total_done += done
                total_failed += failed
                total_tokens += tokens
                print(
                    f"batch {offset // args.batch_size + 1}: "
                    f"done {done}, failed {failed}, +{tokens} tokens "
                    f"(total done {total_done}/{len(ids)})"
                )

            est_cost = total_tokens / 1_000_000 * USD_PER_MILLION_TOKENS
            print(
                f"done: {total_done} generated, {total_failed} failed, "
                f"{total_tokens} tokens (est. ~${est_cost:.2f})"
            )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
