from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


@dataclass
class RateLimitResult:
    allowed: bool
    reason: str | None = None
    retry_after: int = 0


def _seconds_to_utc_midnight(now: float) -> int:
    dt = datetime.fromtimestamp(now, tz=UTC)
    nxt = (dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int((nxt - dt).total_seconds())


# In-memory is intentional: single api container means no shared state needed,
# reset-on-deploy is acceptable, and _hits grows only with unique IPs per uptime cycle.
@dataclass
class RateLimiter:
    per_ip_limit: int
    window_seconds: int
    global_daily_cap: int
    _hits: dict[str, deque[float]] = field(default_factory=dict)
    _global_day: str = ""
    _global_count: int = 0

    def check(self, ip: str, now: float) -> RateLimitResult:
        day = datetime.fromtimestamp(now, tz=UTC).strftime("%Y-%m-%d")
        if day != self._global_day:
            self._global_day = day
            self._global_count = 0

        dq = self._hits.get(ip)
        if dq is None:
            dq = deque()
            self._hits[ip] = dq
        cutoff = now - self.window_seconds
        while dq and dq[0] <= cutoff:
            dq.popleft()

        if len(dq) >= self.per_ip_limit:
            retry = int(dq[0] + self.window_seconds - now) + 1
            return RateLimitResult(False, "per_ip", max(retry, 1))

        if self._global_count >= self.global_daily_cap:
            return RateLimitResult(False, "global", _seconds_to_utc_midnight(now))

        dq.append(now)
        self._global_count += 1
        return RateLimitResult(True)
