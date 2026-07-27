import time
from requestguard.storage.storage import synchronized_allow

class LeakyBucketLimiter:

    def __init__(self, policy, storage):
        self.policy = policy
        self.storage = storage
        self.capacity = getattr(self.policy, "capacity", self.policy.limit)
        self.leak_rate = getattr(self.policy, "refill_rate", self.policy.limit / self.policy.window_seconds)

    @synchronized_allow
    def allow(self, key):
        now = time.monotonic()
        record = self.storage.get(key)
        
        limit = self.capacity

        if record is None:
            self.storage.set(
                key,
                {
                    "water_level": 1.0,
                    "last_leak": now
                }
            )
            return {
                "allowed": True,
                "remaining": limit - 1,
                "retry_after": 0.0,
                "reset_after": 1 / self.leak_rate if self.leak_rate > 0 else 0.0,
                "limit": limit
            }

        elapsed = now - record["last_leak"]
        leaked = elapsed * self.leak_rate
        
        current_water = max(0.0, record["water_level"] - leaked)

        if current_water + 1 <= limit:
            current_water += 1
            allowed = True
            retry_after = 0.0
        else:
            allowed = False
            drops_to_leak = (current_water + 1) - limit
            retry_after = drops_to_leak / self.leak_rate if self.leak_rate > 0 else float('inf')

        self.storage.set(
            key,
            {
                "water_level": current_water,
                "last_leak": now
            }
        )

        reset_after = current_water / self.leak_rate if self.leak_rate > 0 else float('inf')

        return {
            "allowed": allowed,
            "remaining": int(limit - current_water),
            "retry_after": retry_after,
            "reset_after": reset_after,
            "limit": limit
        }
