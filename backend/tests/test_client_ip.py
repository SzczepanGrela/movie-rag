from starlette.requests import Request

from app.explain.ip import client_ip


def _request(headers: dict[str, str], client_host: str = "10.0.0.9") -> Request:
    scope = {
        "type": "http",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        "client": (client_host, 12345),
    }
    return Request(scope)


def test_prefers_cf_connecting_ip() -> None:
    req = _request({"cf-connecting-ip": "203.0.113.7", "x-forwarded-for": "9.9.9.9"})
    assert client_ip(req, trusted_hops=2) == "203.0.113.7"


def test_takes_nth_from_right_when_no_cf() -> None:
    req = _request({"x-forwarded-for": "1.1.1.1, 203.0.113.7, 172.20.0.5"})
    assert client_ip(req, trusted_hops=2) == "203.0.113.7"


def test_falls_back_to_leftmost_when_too_few_entries() -> None:
    req = _request({"x-forwarded-for": "203.0.113.7"})
    assert client_ip(req, trusted_hops=2) == "203.0.113.7"


def test_falls_back_to_peer_when_no_headers() -> None:
    req = _request({})
    assert client_ip(req, trusted_hops=2) == "10.0.0.9"
