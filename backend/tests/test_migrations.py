from sqlalchemy import Connection, inspect

from app.db import engine

EXPECTED_TABLES = {
    "movies",
    "genres",
    "people",
    "movie_genres",
    "movie_cast",
    "movie_crew",
    "source_texts",
}

EXPECTED_COLUMNS = {
    "movies": {
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
    },
    "people": {"id", "tmdb_id", "imdb_id", "name", "created_at", "updated_at"},
    "movie_cast": {"id", "movie_id", "person_id", "character", "billing_order"},
    "movie_crew": {"id", "movie_id", "person_id", "job", "department"},
    "source_texts": {
        "id",
        "movie_id",
        "source",
        "lang",
        "content",
        "source_url",
        "char_count",
        "fetched_at",
    },
}


def _table_names(conn: Connection) -> set[str]:
    return set(inspect(conn).get_table_names())


def _column_names(conn: Connection, table: str) -> set[str]:
    return {col["name"] for col in inspect(conn).get_columns(table)}


async def test_schema_has_expected_tables_and_columns() -> None:
    async with engine.connect() as conn:
        table_names = await conn.run_sync(_table_names)
        assert table_names >= EXPECTED_TABLES

        for table, expected in EXPECTED_COLUMNS.items():
            columns = await conn.run_sync(_column_names, table)
            assert columns >= expected, f"{table} missing columns: {expected - columns}"
