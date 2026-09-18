import time
from collections import defaultdict, deque
from threading import Lock

from app.core.config import settings
from app.core.exceptions import RateLimitExceededError


class InMemoryRateLimiter:
    """Single-instance sliding-window limiter for the public MVP deployment."""

    def __init__(self):
        self._requests: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, client_key: str, scope: str, limit: int | None = None) -> None:
        max_requests = limit or settings.RATE_LIMIT_MAX_REQUESTS
        now = time.monotonic()
        window = settings.RATE_LIMIT_WINDOW_SECONDS
        key = (client_key, scope)

        with self._lock:
            timestamps = self._requests[key]
            while timestamps and now - timestamps[0] >= window:
                timestamps.popleft()
            if len(timestamps) >= max_requests:
                retry_after = max(1, int(window - (now - timestamps[0])))
                raise RateLimitExceededError(retry_after)
            timestamps.append(now)

    def reset(self) -> None:
        """Clear counters for process lifecycle changes and isolated tests."""
        with self._lock:
            self._requests.clear()


rate_limiter = InMemoryRateLimiter()
