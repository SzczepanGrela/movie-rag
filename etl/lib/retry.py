from collections.abc import Callable
from typing import Any, TypeVar

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

F = TypeVar("F", bound=Callable[..., Any])


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        return status == 429 or status >= 500
    return False


def with_retry(max_retries: int) -> Callable[[F], F]:
    def decorator(fn: F) -> F:
        return retry(
            retry=retry_if_exception(_is_retryable),
            wait=wait_exponential(multiplier=1, min=1, max=60),
            stop=stop_after_attempt(max_retries),
            reraise=True,
        )(fn)

    return decorator
