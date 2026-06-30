from functools import wraps

from rateguard.policy import RateLimitPolicy
from rateguard.storage import MemoryStorage
from rateguard.algorithms.fixed_window import FixedWindowLimiter
from rateguard.limiter import RateLimiter
from rateguard.resolver import KeyResolver


storage = MemoryStorage()


def limit(
    requests,
    window,
    key=None
):

    policy = RateLimitPolicy(
        limit=requests,
        window_seconds=window
    )


    algorithm = FixedWindowLimiter(
        policy,
        storage
    )


    limiter = RateLimiter(
        algorithm
    )


    # 4. Create resolver
    resolver = KeyResolver(key)


    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            # Find who is making request
            client_id = resolver.resolve(
                *args,
                **kwargs
            )
            print("client_id: ", client_id)


            # Check limit
            result = limiter.check(
                client_id
            )


            if not result["allowed"]:
                return {
                    "error": "Too many requests",
                    "retry_after":
                        result.get("retry_after")
                }


            return func(
                *args,
                **kwargs
            )


        return wrapper


    return decorator