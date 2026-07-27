import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest

from requestguard import Algorithm, MemoryStorage, RateLimitExceeded, RequestGuard
from requestguard.core.policy import RateLimitPolicy
from requestguard.algorithms.fixed_window import FixedWindowLimiter
from requestguard.algorithms.leaky_bucket import LeakyBucketLimiter
from requestguard.algorithms.sliding_window import SlidingWindowLimiter
from requestguard.algorithms.sliding_window_counter import SlidingWindowCounterLimiter
from requestguard.algorithms.token_bucket import TokenBucketLimiter


@pytest.mark.parametrize("limiter_type", [
    FixedWindowLimiter,
    TokenBucketLimiter,
    LeakyBucketLimiter,
    SlidingWindowLimiter,
    SlidingWindowCounterLimiter,
])
def test_algorithm_allows_limit_and_rejects_next(limiter_type):
    limiter = limiter_type(RateLimitPolicy(2, 60), MemoryStorage())
    assert limiter.allow("client")["allowed"] is True
    assert limiter.allow("client")["allowed"] is True
    result = limiter.allow("client")
    assert result["allowed"] is False
    assert result["limit"] == 2
    assert result["remaining"] == 0


def test_concurrent_requests_never_exceed_limit():
    guard = RequestGuard()

    @guard.limit(10, 60, key=lambda: "same-client")
    def endpoint():
        return True

    def call(_):
        try:
            endpoint()
            return True
        except RateLimitExceeded:
            return False

    with ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(call, range(100)))
    assert sum(results) == 10


def test_async_endpoint_is_awaited():
    guard = RequestGuard()

    @guard.limit(1, 60, key=lambda: "async-client")
    async def endpoint():
        return "ok"

    assert asyncio.run(endpoint()) == "ok"
    with pytest.raises(RateLimitExceeded):
        asyncio.run(endpoint())
