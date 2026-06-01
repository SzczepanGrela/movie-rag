import httpx


async def verify_turnstile(
    secret: str,
    token: str,
    remoteip: str,
    *,
    verify_url: str,
    client: httpx.AsyncClient | None = None,
) -> bool:
    owns = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=5.0)
    try:
        resp = await client.post(
            verify_url,
            data={"secret": secret, "response": token, "remoteip": remoteip},
        )
        data = resp.json()
        return bool(data.get("success"))
    except (httpx.HTTPError, ValueError):
        return False
    finally:
        if owns:
            await client.aclose()
