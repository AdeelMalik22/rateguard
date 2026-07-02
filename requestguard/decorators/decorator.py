from functools import wraps
from requestguard.core.exceptions import RateLimitExceeded
from requestguard.core.policy import RateLimitPolicy
from requestguard.storage.storage import MemoryStorage
from requestguard.algorithms.registry import get_algorithm
from requestguard.core.limiter import RateLimiter
from requestguard.core.resolver import KeyResolver
from requestguard.core.enums import Algorithm

storage = MemoryStorage()

def limit(max_retries, ttl, key=None, algorithm: Algorithm = Algorithm.FIXED_WINDOW):
    policy = RateLimitPolicy(limit=max_retries, window_seconds=ttl)
    
    algo_class = get_algorithm(algorithm)
    algo_instance = algo_class(policy, storage)
        
    limiter = RateLimiter(algo_instance)
    resolver = KeyResolver(key)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            client_id = resolver.resolve(*args, **kwargs)
            rl_key = f"{func.__name__}:{client_id}"

            result = limiter.check(rl_key)
            if not result["allowed"]:
                raise RateLimitExceeded(
                    retry_after=result.get("retry_after"),
                    reset_after=result.get("reset_after"),
                    limit=result.get("limit")
                )

            return func(
                *args,
                **kwargs
            )


        return wrapper
    return decorator