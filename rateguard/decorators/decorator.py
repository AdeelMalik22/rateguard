from functools import wraps
from fastapi import HTTPException
from rateguard.core.policy import RateLimitPolicy
from rateguard.storage.storage import MemoryStorage
from rateguard.algorithms.fixed_window import FixedWindowLimiter
from rateguard.core.limiter import RateLimiter
from rateguard.core.resolver import KeyResolver


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
            key = f"{func.__name__}:{client_id}"

            print("client_id: ", key)


            # Check limit
            result = limiter.check(
                key
            )

            if not result["allowed"]:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Too many requests",
                        "retry_after": result.get("retry_after")
                    }
                )


            return func(
                *args,
                **kwargs
            )


        return wrapper


    return decorator