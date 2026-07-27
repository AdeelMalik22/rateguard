import inspect
from functools import wraps

from requestguard.algorithms.registry import get_algorithm
from requestguard.core.enums import Algorithm
from requestguard.core.exceptions import RateLimitExceeded
from requestguard.core.limiter import RateLimiter
from requestguard.core.policy import RateLimitPolicy
from requestguard.core.resolver import KeyResolver
from requestguard.storage.storage import MemoryStorage


class RequestGuard:
    def __init__(self, storage=None):
        self.storage = storage or MemoryStorage()

    def limit(self, max_retries, ttl, key=None,
              algorithm: Algorithm = Algorithm.FIXED_WINDOW, namespace=None):
        policy = RateLimitPolicy(limit=max_retries, window_seconds=ttl)
        algo_instance = get_algorithm(algorithm)(policy, self.storage)
        limiter = RateLimiter(algo_instance)
        resolver = KeyResolver(key)

        def decorator(func):
            def rate_key(*args, **kwargs):
                client_id = resolver.resolve(*args, **kwargs)
                key_namespace = namespace or f"{func.__module__}.{func.__qualname__}"
                return f"{key_namespace}:{client_id}"

            def check(*args, **kwargs):
                result = limiter.check(rate_key(*args, **kwargs))
                if not result["allowed"]:
                    raise RateLimitExceeded(
                        retry_after=result.get("retry_after"),
                        reset_after=result.get("reset_after"),
                        limit=result.get("limit"),
                    )

            if inspect.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    check(*args, **kwargs)
                    return await func(*args, **kwargs)
                return async_wrapper

            @wraps(func)
            def wrapper(*args, **kwargs):
                check(*args, **kwargs)
                return func(*args, **kwargs)
            return wrapper

        return decorator


default_guard = RequestGuard()
limit = default_guard.limit
