from app.explain.ratelimit import RateLimiter


def _limiter() -> RateLimiter:
    return RateLimiter(per_ip_limit=2, window_seconds=60, global_daily_cap=5)


def test_allows_under_per_ip_limit() -> None:
    rl = _limiter()
    assert rl.check("1.1.1.1", now=1000.0).allowed
    assert rl.check("1.1.1.1", now=1001.0).allowed


def test_blocks_over_per_ip_limit() -> None:
    rl = _limiter()
    rl.check("1.1.1.1", now=1000.0)
    rl.check("1.1.1.1", now=1001.0)
    res = rl.check("1.1.1.1", now=1002.0)
    assert not res.allowed
    assert res.reason == "per_ip"
    assert res.retry_after > 0


def test_per_ip_window_slides() -> None:
    rl = _limiter()
    rl.check("1.1.1.1", now=1000.0)
    rl.check("1.1.1.1", now=1001.0)
    assert rl.check("1.1.1.1", now=1062.0).allowed


def test_per_ip_is_isolated_between_ips() -> None:
    rl = _limiter()
    rl.check("1.1.1.1", now=1000.0)
    rl.check("1.1.1.1", now=1001.0)
    assert rl.check("2.2.2.2", now=1002.0).allowed


def test_global_cap_blocks_after_threshold() -> None:
    rl = RateLimiter(per_ip_limit=100, window_seconds=60, global_daily_cap=3)
    for i in range(3):
        assert rl.check(f"ip-{i}", now=1000.0 + i).allowed
    res = rl.check("ip-x", now=1004.0)
    assert not res.allowed
    assert res.reason == "global"
    assert res.retry_after > 0


def test_global_cap_resets_next_utc_day() -> None:
    rl = RateLimiter(per_ip_limit=100, window_seconds=60, global_daily_cap=1)
    assert rl.check("a", now=1000.0).allowed
    assert not rl.check("b", now=1001.0).allowed
    assert rl.check("c", now=1000.0 + 86_400).allowed


def test_blocked_request_does_not_consume_global_budget() -> None:
    rl = RateLimiter(per_ip_limit=1, window_seconds=60, global_daily_cap=10)
    rl.check("1.1.1.1", now=1000.0)
    rl.check("1.1.1.1", now=1001.0)
    for i in range(9):
        assert rl.check(f"ip-{i}", now=1002.0 + i).allowed
