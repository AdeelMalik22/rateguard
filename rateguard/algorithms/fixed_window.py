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

        now = time.time()

        record = self.storage.get(key)


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
                "remaining": self.policy.limit - 1
            }


        elapsed = now - record["start"]


        # window expired
        if elapsed >= self.policy.window_seconds:

            self.storage.set(
                key,
                {
                    "count": 1,
                    "start": now
                }
            )

            return {
                "allowed": True,
                "remaining": self.policy.limit - 1
            }


        # limit reached
        if record["count"] >= self.policy.limit:

            return {
                "allowed": False,
                "remaining": 0,
                "retry_after":
                    self.policy.window_seconds - elapsed
            }


        # allow request
        record["count"] += 1

        self.storage.set(
            key,
            record
        )


        return {
            "allowed": True,
            "remaining":
                self.policy.limit - record["count"]
        }