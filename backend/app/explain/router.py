from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.explain import service
from app.explain.provider import LLMProvider
from app.schemas.explain import ExplainRequest
from app.search.embedder import Embedder, get_embedder

router = APIRouter(prefix="/api", tags=["explain"])


def get_provider(request: Request) -> LLMProvider | None:
    provider: LLMProvider | None = request.app.state.provider
    return provider


SessionDep = Annotated[AsyncSession, Depends(get_session)]
EmbedderDep = Annotated[Embedder, Depends(get_embedder)]
ProviderDep = Annotated[LLMProvider | None, Depends(get_provider)]


@router.post("/explain")
async def explain_endpoint(
    body: ExplainRequest,
    session: SessionDep,
    embedder: EmbedderDep,
    provider: ProviderDep,
) -> StreamingResponse:
    if provider is None:
        raise HTTPException(status_code=503, detail="explain_unavailable")

    stream = service.explain_stream(session, embedder, provider, body.query)
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
