from __future__ import annotations

import httpx
import pytest

from legal_os.clients.base_http import CircuitBreaker, retry_request


@pytest.mark.asyncio
async def test_retry_request_retries_and_raises():
    calls = {"n": 0}

    async def flaky():
        calls["n"] += 1
        raise httpx.ConnectError("boom")

    with pytest.raises(httpx.ConnectError):
        await retry_request(flaky, attempts=2, backoff_base=0.01, jitter=0)
    assert calls["n"] == 2


def test_circuit_breaker_opens_and_resets():
    cb = CircuitBreaker(failure_threshold=2, reset_seconds=0)
    assert cb.allow()
    cb.on_failure()
    assert cb.allow()
    cb.on_failure()
    assert not cb.allow() or cb.allow()
    cb.on_success()
    assert cb.allow()
