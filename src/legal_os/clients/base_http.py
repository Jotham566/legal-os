from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional, TypeVar, Awaitable

import httpx


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    reset_seconds: int = 30
    failures: int = 0
    opened_at: Optional[float] = None

    def allow(self) -> bool:
        if self.opened_at is None:
            return True
        if time.time() - self.opened_at >= self.reset_seconds:
            # half-open
            return True
        return False

    def on_success(self) -> None:
        self.failures = 0
        self.opened_at = None

    def on_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.opened_at = time.time()


T = TypeVar("T")


async def retry_request(
    func: Callable[[], Awaitable[T]],
    attempts: int = 3,
    backoff_base: float = 0.2,
    jitter: float = 0.1,
) -> T:
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            return await func()
        except (httpx.ConnectError, httpx.ReadTimeout) as e:  # transient
            last_exc = e
            await _sleep_with_jitter(backoff_base * (2**i), jitter)
    if last_exc:
        raise last_exc
    raise RuntimeError("retry_request failed without exception")


async def _sleep_with_jitter(duration: float, jitter: float) -> None:
    import asyncio
    import random

    await asyncio.sleep(duration + random.uniform(0, jitter))
