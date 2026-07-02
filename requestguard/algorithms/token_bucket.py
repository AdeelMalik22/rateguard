import time

class TokenBucketLimiter:

    def __init__(self, policy, storage):
        self.policy = policy
        self.storage = storage
        # Use algorithm-specific properties if they exist, fallback to general policy
        self.capacity = getattr(self.policy, "capacity", self.policy.limit)
        self.refill_rate = getattr(self.policy, "refill_rate", self.policy.limit / self.policy.window_seconds)

    def allow(self, key):
        now = time.monotonic()
        record = self.storage.get(key)
        
        limit = self.capacity

        if record is None:
            self.storage.set(
                key,
                {
                    "tokens": float(limit - 1),
                    "last_refill": now
                }
            )
            return {
                "allowed": True,
                "remaining": limit - 1,
                "retry_after": 0.0,
                "reset_after": 1 / self.refill_rate if self.refill_rate > 0 else 0.0,
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

        tokens_to_fill = limit - current_tokens
        reset_after = tokens_to_fill / self.refill_rate if self.refill_rate > 0 else float('inf')

        return {
            "allowed": allowed,
            "remaining": int(current_tokens),
            "retry_after": retry_after,
            "reset_after": reset_after,
            "limit": limit
        }
