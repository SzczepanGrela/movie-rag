from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.search import SearchRequest, SearchResponse
from app.search import service
from app.search.embedder import Embedder, get_embedder

router = APIRouter(prefix="/api", tags=["search"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
EmbedderDep = Annotated[Embedder, Depends(get_embedder)]


@router.post("/search", response_model=SearchResponse)
async def search_endpoint(
    body: SearchRequest,
    session: SessionDep,
    embedder: EmbedderDep,
) -> SearchResponse:
    return await service.search(session, embedder, query=body.query, limit=body.limit)
