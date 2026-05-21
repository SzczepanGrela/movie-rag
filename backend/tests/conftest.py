from collections.abc import AsyncIterator

import pytest

from app.db import engine


@pytest.fixture(autouse=True)
async def _dispose_engine() -> AsyncIterator[None]:
    yield
    await engine.dispose()
