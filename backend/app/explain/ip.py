from starlette.requests import Request


def client_ip(request: Request, *, trusted_hops: int) -> str:
    # Naive leftmost X-Forwarded-For is spoofable: a client can inject the header
    # and dodge per-IP limits. The trustworthy address is the one appended by the
    # outermost trusted proxy. If Cloudflare proxies the domain, CF-Connecting-IP
    # is authoritative; otherwise take the entry trusted_hops-from-right in XFF.
    cf = request.headers.get("cf-connecting-ip")
    if cf:
        return cf.strip()

    xff = request.headers.get("x-forwarded-for")
    if xff:
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if len(parts) >= trusted_hops:
            return parts[-trusted_hops]
        if parts:
            return parts[0]

    return request.client.host if request.client else "unknown"
