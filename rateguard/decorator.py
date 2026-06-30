from functools import wraps

from rateguard.policy import RateLimitPolicy
from rateguard.storage import MemoryStorage
from rateguard.algorithms.fixed_window import FixedWindowLimiter
from rateguard.limiter import RateLimiter


storage = MemoryStorage()


def limit(
    requests,
    window
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


    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            # for now
            # later this becomes:
            # IP address
            # user id
            # api key

            client_id = "default"


            result = limiter.check(
                client_id
            )


            if not result["allowed"]:
                return {
                    "error": "Too many requests",
                    "retry_after":
                        result["retry_after"]
                }


            return func(
                *args,
                **kwargs
            )


        return wrapper


    return decorator