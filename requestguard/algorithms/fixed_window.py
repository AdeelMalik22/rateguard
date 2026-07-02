import time

class FixedWindowLimiter:

    def __init__(
        self,
        policy,
        storage
    ):
        self.policy = policy
        self.storage = storage


    def allow(self, key):
        now = time.monotonic()
        record = self.storage.get(key)
        
        limit = self.policy.limit
        window = self.policy.window_seconds

        # first request
        if record is None:

            self.storage.set(
                key,
                {
                    "count": 1,
                    "start": now
                }
            )

            return {
                "allowed": True,
                "remaining": limit - 1,
                "retry_after": 0.0,
                "reset_after": float(window),
                "limit": limit
            }


        elapsed = now - record["start"]


        # window expired
        if elapsed >= window:
            self.storage.set(
                key,
                {
                    "count": 1,
                    "start": now
                }
            )

            return {
                "allowed": True,
                "remaining": limit - 1,
                "retry_after": 0.0,
                "reset_after": float(window),
                "limit": limit
            }

        reset_after = window - elapsed

        # limit reached
        if record["count"] >= limit:
            return {
                "allowed": False,
                "remaining": 0,
                "retry_after": reset_after,
                "reset_after": reset_after,
                "limit": limit
            }


        # allow request
        record["count"] += 1

        self.storage.set(
            key,
            record
        )


        return {
            "allowed": True,
            "remaining": limit - record["count"],
            "retry_after": 0.0,
            "reset_after": reset_after,
            "limit": limit
        }