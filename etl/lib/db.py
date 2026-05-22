from collections.abc import Sequence
from typing import Any

from sqlalchemy import Table, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from lib.config import EtlSettings


def make_engine(settings: EtlSettings) -> AsyncEngine:
    return create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
    )


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def pg_upsert(
    session: AsyncSession,
    model: type[DeclarativeBase],
    rows: Sequence[dict[str, Any]],
    conflict_cols: Sequence[str],
    update_cols: Sequence[str] | None = None,
    chunk_size: int = 500,
) -> int:
    if not rows:
        return 0

    table = model.__table__
    all_col_names = {c.name for c in table.columns}

    if update_cols is None:
        row_keys: set[str] = set()
        for row in rows:
            row_keys.update(row.keys())
        pk_names = {c.name for c in table.columns if c.primary_key}
        excluded = set(conflict_cols) | pk_names
        update_cols = [k for k in row_keys if k not in excluded]

    has_updated_at = "updated_at" in all_col_names

    total = 0
    for offset in range(0, len(rows), chunk_size):
        chunk = list(rows[offset : offset + chunk_size])
        stmt = insert(model).values(chunk)
        set_: dict[str, Any] = {name: stmt.excluded[name] for name in update_cols}
        if has_updated_at:
            set_["updated_at"] = func.now()
        stmt = stmt.on_conflict_do_update(
            index_elements=list(conflict_cols),
            set_=set_,
        )
        await session.execute(stmt)
        total += len(chunk)

    await session.commit()
    return total


async def pg_insert_ignore(
    session: AsyncSession,
    target: type[DeclarativeBase] | Table,
    rows: Sequence[dict[str, Any]],
    conflict_cols: Sequence[str],
    chunk_size: int = 500,
) -> int:
    if not rows:
        return 0

    total = 0
    for offset in range(0, len(rows), chunk_size):
        chunk = list(rows[offset : offset + chunk_size])
        stmt = insert(target).values(chunk)
        stmt = stmt.on_conflict_do_nothing(index_elements=list(conflict_cols))
        await session.execute(stmt)
        total += len(chunk)

    await session.commit()
    return total
