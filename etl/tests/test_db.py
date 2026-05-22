from typing import Any
from unittest.mock import AsyncMock

from app.models import Movie, MovieCrew, movie_genres
from sqlalchemy.dialects import postgresql

from lib.db import pg_insert_ignore, pg_upsert


async def test_pg_upsert_empty_rows_returns_zero() -> None:
    session = AsyncMock()

    count = await pg_upsert(session, Movie, [], conflict_cols=["tmdb_id"])

    assert count == 0
    session.execute.assert_not_called()
    session.commit.assert_not_called()


async def test_pg_upsert_compiles_to_on_conflict_do_update() -> None:
    session = AsyncMock()
    captured: list[Any] = []

    async def capture(stmt: Any) -> None:
        captured.append(stmt)

    session.execute.side_effect = capture

    await pg_upsert(
        session,
        Movie,
        [{"tmdb_id": 550, "title": "Fight Club", "original_title": "Fight Club", "year": 1999}],
        conflict_cols=["tmdb_id"],
    )

    assert len(captured) == 1
    dialect = postgresql.dialect()  # type: ignore[no-untyped-call]
    sql = str(captured[0].compile(dialect=dialect, compile_kwargs={"literal_binds": True})).lower()
    assert "insert into movies" in sql
    assert "on conflict" in sql
    assert "do update set" in sql
    assert "excluded.title" in sql
    assert "updated_at = now()" in sql

    session.commit.assert_awaited_once()


async def test_pg_upsert_chunks_rows_by_chunk_size() -> None:
    session = AsyncMock()
    rows: list[dict[str, Any]] = [{"tmdb_id": i, "title": f"Movie {i}"} for i in range(1200)]

    count = await pg_upsert(session, Movie, rows, conflict_cols=["tmdb_id"], chunk_size=500)

    assert count == 1200
    assert session.execute.await_count == 3
    session.commit.assert_awaited_once()


async def test_pg_insert_ignore_empty_rows_returns_zero() -> None:
    session = AsyncMock()

    count = await pg_insert_ignore(
        session, movie_genres, [], conflict_cols=["movie_id", "genre_id"]
    )

    assert count == 0
    session.execute.assert_not_called()
    session.commit.assert_not_called()


async def test_pg_insert_ignore_compiles_to_on_conflict_do_nothing() -> None:
    session = AsyncMock()
    captured: list[Any] = []

    async def capture(stmt: Any) -> None:
        captured.append(stmt)

    session.execute.side_effect = capture

    await pg_insert_ignore(
        session,
        movie_genres,
        [{"movie_id": 1, "genre_id": 28}],
        conflict_cols=["movie_id", "genre_id"],
    )

    assert len(captured) == 1
    dialect = postgresql.dialect()  # type: ignore[no-untyped-call]
    sql = str(captured[0].compile(dialect=dialect, compile_kwargs={"literal_binds": True})).lower()
    assert "insert into movie_genres" in sql
    assert "on conflict" in sql
    assert "do nothing" in sql

    session.commit.assert_awaited_once()


async def test_pg_insert_ignore_supports_three_column_conflict_target() -> None:
    session = AsyncMock()
    captured: list[Any] = []

    async def capture(stmt: Any) -> None:
        captured.append(stmt)

    session.execute.side_effect = capture

    await pg_insert_ignore(
        session,
        MovieCrew,
        [{"movie_id": 1, "person_id": 2, "job": "Director"}],
        conflict_cols=["movie_id", "person_id", "job"],
    )

    assert len(captured) == 1
    dialect = postgresql.dialect()  # type: ignore[no-untyped-call]
    sql = str(captured[0].compile(dialect=dialect, compile_kwargs={"literal_binds": True})).lower()
    assert "insert into movie_crew" in sql
    assert "on conflict" in sql
    assert "do nothing" in sql
    assert "movie_id" in sql
    assert "person_id" in sql
    assert "job" in sql

    session.commit.assert_awaited_once()


async def test_pg_insert_ignore_chunks_rows_by_chunk_size() -> None:
    session = AsyncMock()
    rows: list[dict[str, Any]] = [{"movie_id": i, "genre_id": 28} for i in range(1200)]

    count = await pg_insert_ignore(
        session, movie_genres, rows, conflict_cols=["movie_id", "genre_id"], chunk_size=500
    )

    assert count == 1200
    assert session.execute.await_count == 3
    session.commit.assert_awaited_once()
