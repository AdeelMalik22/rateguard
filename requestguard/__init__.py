"""
RateGuard — Lightweight rate limiting for FastAPI.

Quick start:

    from requestguard import limit

    @limit(max_retries=5, ttl=60)
    def my_endpoint(request: Request):
        return {"status": "ok"}
"""

from requestguard.decorators.decorator import RequestGuard, default_guard, limit
from requestguard.core.policy import RateLimitPolicy
from requestguard.core.limiter import RateLimiter
from requestguard.core.resolver import KeyResolver
from requestguard.storage.storage import MemoryStorage
from requestguard.algorithms.fixed_window import FixedWindowLimiter
from requestguard.algorithms.token_bucket import TokenBucketLimiter
from requestguard.algorithms.leaky_bucket import LeakyBucketLimiter
from requestguard.algorithms.sliding_window import SlidingWindowLimiter
from requestguard.algorithms.sliding_window_counter import SlidingWindowCounterLimiter
from requestguard.core.exceptions import RateLimitExceeded
from requestguard.core.enums import Algorithm
from requestguard.algorithms.registry import get_algorithm, register_algorithm

__all__ = [
    "limit",
    "RequestGuard",
    "default_guard",
    "RateLimitPolicy",
    "RateLimiter",
    "KeyResolver",
    "MemoryStorage",
    "FixedWindowLimiter",
    "TokenBucketLimiter",
    "LeakyBucketLimiter",
    "SlidingWindowLimiter",
    "SlidingWindowCounterLimiter",
    "RateLimitExceeded",
    "Algorithm",
    "get_algorithm",
    "register_algorithm"
]

__version__ = "0.1.0"
__author__ = "AdeelMalik22"
