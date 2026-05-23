from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import engine
from app.routers import search as search_router
from app.search.embedder import GemmaEmbedder


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.embedder = GemmaEmbedder()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(search_router.router)


class HealthResponse(BaseModel):
    status: str
    db: str


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return HealthResponse(status="ok", db="ok")
    except (SQLAlchemyError, OSError):
        return HealthResponse(status="degraded", db="down")
