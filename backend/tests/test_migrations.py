from sqlalchemy import inspect

from app.db import engine

EXPECTED_COLUMNS = {
    "id",
    "tmdb_id",
    "imdb_id",
    "title",
    "original_title",
    "year",
    "runtime",
    "etl_status",
    "created_at",
    "updated_at",
}


async def test_movies_table_exists_with_expected_columns() -> None:
    async with engine.connect() as conn:
        table_names = await conn.run_sync(lambda c: inspect(c).get_table_names())
        assert "movies" in table_names

        columns = await conn.run_sync(lambda c: inspect(c).get_columns("movies"))

    column_names = {col["name"] for col in columns}
    assert column_names >= EXPECTED_COLUMNS
