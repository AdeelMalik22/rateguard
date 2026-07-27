import time
from requestguard.storage.storage import synchronized_allow

class TokenBucketLimiter:

    def __init__(self, policy, storage):
        self.policy = policy
        self.storage = storage
        # Use algorithm-specific properties if they exist, fallback to general policy
        self.capacity = getattr(self.policy, "capacity", self.policy.limit)
        self.refill_rate = getattr(self.policy, "refill_rate", self.policy.limit / self.policy.window_seconds)

    @synchronized_allow
    def allow(self, key):
        now = time.monotonic()
        record = self.storage.get(key)
        
        limit = self.capacity

        if record is None:
            current_tokens = float(limit - 1)
            self.storage.set(
                key,
                {
                    "tokens": current_tokens,
                    "last_refill": now
                }
            )
            reset_after = (limit - current_tokens) / self.refill_rate
            return {
                "allowed": True,
                "remaining": limit - 1,
                "retry_after": 0.0,
                "reset_after": reset_after if self.refill_rate > 0 else float("inf"),
                "limit": limit
            }

        elapsed = now - record["last_refill"]
        new_tokens = elapsed * self.refill_rate
        
        current_tokens = min(float(limit), record["tokens"] + new_tokens)

        # allow request
        if current_tokens >= 1:
            current_tokens -= 1
            allowed = True
            retry_after = 0.0
        else:
            allowed = False
            tokens_needed = 1 - current_tokens
            retry_after = tokens_needed / self.refill_rate if self.refill_rate > 0 else float('inf')

        # always persist the updated bucket state after refilling, even when rejected
        self.storage.set(
            key,
            {
                "tokens": current_tokens,
                "last_refill": now
            }
        )

        # reset_after always means time until the bucket is completely full.
        tokens_to_fill = max(0.0, limit - current_tokens)
        reset_after = tokens_to_fill / self.refill_rate if self.refill_rate > 0 else float('inf')

        return {
            "allowed": allowed,
            "remaining": max(0, int(current_tokens)),
            "retry_after": retry_after,
            "reset_after": reset_after,
            "limit": limit
        }
