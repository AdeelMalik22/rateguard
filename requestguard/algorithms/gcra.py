import time

from requestguard.storage.storage import synchronized_allow


class GCRALimiter:
    """Generic Cell Rate Algorithm using a theoretical arrival time (TAT)."""

    def __init__(self, policy, storage):
        self.policy = policy
        self.storage = storage
        self.interval = policy.window_seconds / policy.limit
        self.tolerance = (policy.limit - 1) * self.interval

    @synchronized_allow
    def allow(self, key):
        now = time.monotonic()
        record = self.storage.get(key)
        tat = now if record is None else float(record["tat"])
        theoretical = max(now, tat)
        allowed_at = tat - self.tolerance

        if now < allowed_at:
            retry_after = allowed_at - now
            return {
                "allowed": False,
                "remaining": 0,
                "retry_after": retry_after,
                "reset_after": max(0.0, tat - now),
                "limit": self.policy.limit,
            }

        new_tat = theoretical + self.interval
        self.storage.set(key, {"tat": new_tat})
        remaining = max(0, int((self.tolerance - max(0.0, new_tat - now)) / self.interval))
        return {
            "allowed": True,
            "remaining": remaining,
            "retry_after": 0.0,
            "reset_after": max(0.0, new_tat - now),
            "limit": self.policy.limit,
        }
