from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import engine

app = FastAPI()


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
