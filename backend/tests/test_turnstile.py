import httpx

from app.explain.turnstile import verify_turnstile


def _client(payload: dict[str, object], status: int = 200) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json=payload)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_returns_true_on_success() -> None:
    async with _client({"success": True}) as client:
        ok = await verify_turnstile(
            "secret",
            "token",
            "1.1.1.1",
            verify_url="https://verify.test/siteverify",
            client=client,
        )
    assert ok is True


async def test_returns_false_on_failure() -> None:
    async with _client({"success": False, "error-codes": ["invalid"]}) as client:
        ok = await verify_turnstile(
            "secret",
            "token",
            "1.1.1.1",
            verify_url="https://verify.test/siteverify",
            client=client,
        )
    assert ok is False


async def test_returns_false_on_network_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        ok = await verify_turnstile(
            "secret",
            "token",
            "1.1.1.1",
            verify_url="https://verify.test/siteverify",
            client=client,
        )
    assert ok is False
