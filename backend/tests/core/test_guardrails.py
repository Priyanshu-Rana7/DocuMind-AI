import pytest

from app.core.config import settings
from app.core.exceptions import RateLimitExceededError
from app.core.guardrails import InMemoryRateLimiter


def test_rate_limiter_rejects_requests_in_same_window(monkeypatch):
    limiter = InMemoryRateLimiter()
    monkeypatch.setattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60)

    limiter.check("showcase-client", "processing", limit=1)

    with pytest.raises(RateLimitExceededError) as error:
        limiter.check("showcase-client", "processing", limit=1)

    assert error.value.status_code == 429
    assert error.value.error_code == "RATE_LIMIT_EXCEEDED"
    assert error.value.extra["retry_after_seconds"] >= 1


def test_rate_limiter_scopes_clients_and_operations():
    limiter = InMemoryRateLimiter()

    limiter.check("client-a", "processing", limit=1)
    limiter.check("client-a", "upload", limit=1)
    limiter.check("client-b", "processing", limit=1)
