"""
RateGuard — Lightweight rate limiting for FastAPI.

Quick start:

    from rateguard import limit

    @limit(requests=5, window=60)
    def my_endpoint(request: Request):
        return {"status": "ok"}
"""

from rateguard.decorators.decorator import limit
from rateguard.core.policy import RateLimitPolicy
from rateguard.core.limiter import RateLimiter
from rateguard.core.resolver import KeyResolver
from rateguard.storage.storage import MemoryStorage
from rateguard.algorithms.fixed_window import FixedWindowLimiter

__all__ = [
    "limit",
    "RateLimitPolicy",
    "RateLimiter",
    "KeyResolver",
    "MemoryStorage",
    "FixedWindowLimiter",
]

__version__ = "0.1.0"
__author__ = "AdeelMalik22"
