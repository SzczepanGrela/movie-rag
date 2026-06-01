import time
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session
from app.explain import service
from app.explain.ip import client_ip
from app.explain.provider import LLMProvider
from app.explain.ratelimit import RateLimiter
from app.explain.turnstile import verify_turnstile
from app.schemas.explain import ExplainRequest
from app.search.embedder import Embedder, get_embedder

router = APIRouter(prefix="/api", tags=["explain"])

TurnstileVerifier = Callable[[str | None, str], Awaitable[bool]]


def get_provider(request: Request) -> LLMProvider | None:
    provider: LLMProvider | None = request.app.state.provider
    return provider


def get_rate_limiter(request: Request) -> RateLimiter:
    limiter: RateLimiter | None = getattr(request.app.state, "rate_limiter", None)
    if limiter is None:
        limiter = RateLimiter(
            per_ip_limit=settings.explain_rate_per_ip,
            window_seconds=settings.explain_rate_window_seconds,
            global_daily_cap=settings.explain_global_daily_cap,
        )
        request.app.state.rate_limiter = limiter
    return limiter


def get_turnstile_verifier() -> TurnstileVerifier:
    # Secret-gate: with no secret (dev) verification is skipped so local dev needs
    # no Cloudflare. With a secret (prod) a missing/invalid token is rejected.
    async def _verify(token: str | None, ip: str) -> bool:
        if settings.turnstile_secret is None:
            return True
        if not token:
            return False
        return await verify_turnstile(
            settings.turnstile_secret,
            token,
            ip,
            verify_url=settings.turnstile_verify_url,
        )

    return _verify


SessionDep = Annotated[AsyncSession, Depends(get_session)]
EmbedderDep = Annotated[Embedder, Depends(get_embedder)]
ProviderDep = Annotated[LLMProvider | None, Depends(get_provider)]
RateLimiterDep = Annotated[RateLimiter, Depends(get_rate_limiter)]
VerifierDep = Annotated[TurnstileVerifier, Depends(get_turnstile_verifier)]


@router.post("/explain")
async def explain_endpoint(
    request: Request,
    body: ExplainRequest,
    session: SessionDep,
    embedder: EmbedderDep,
    provider: ProviderDep,
    verifier: VerifierDep,
    rate_limiter: RateLimiterDep,
) -> StreamingResponse:
    if provider is None:
        raise HTTPException(status_code=503, detail="explain_unavailable")

    ip = client_ip(request, trusted_hops=settings.trusted_proxy_hops)

    if not await verifier(body.turnstile_token, ip):
        raise HTTPException(status_code=403, detail="turnstile_failed")

    result = rate_limiter.check(ip, now=time.time())
    if not result.allowed:
        headers = {"Retry-After": str(result.retry_after)}
        if result.reason == "per_ip":
            raise HTTPException(429, detail="rate_limited", headers=headers)
        raise HTTPException(503, detail="service_busy", headers=headers)

    stream = service.explain_stream(session, embedder, provider, body.query)
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
