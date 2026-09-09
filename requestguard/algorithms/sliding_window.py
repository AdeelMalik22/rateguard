import time
from requestguard.storage.storage import synchronized_allow

class SlidingWindowLimiter:

    def __init__(self, policy, storage):
        self.policy = policy
        self.storage = storage

    def _store(self, key, record, ttl):
        set_with_ttl = getattr(self.storage, "set_with_ttl", None)
        if set_with_ttl is not None:
            set_with_ttl(key, record, ttl)
        else:
            self.storage.set(key, record)

    @synchronized_allow
    def allow(self, key):
        now = time.monotonic()
        record = self.storage.get(key)
        
        limit = self.policy.limit
        window = self.policy.window_seconds

        # Initialize empty timestamps list if no record
        if record is None:
            self._store(
                key,
                {
                    "timestamps": [now],
                    "count": 1
                },
                window,
            )
            
            return {
                "allowed": True,
                "remaining": limit - 1,
                "retry_after": 0.0,
                "reset_after": float(window),
                "limit": limit
            }


        timestamps = record["timestamps"]
        count = record["count"]
        
        # Remove timestamps outside the sliding window
        cutoff = now - window
        # Timestamps are append-only and ordered. Prune in place to avoid
        # allocating a second list during large bursts.
        first_valid = 0
        while first_valid < len(timestamps) and timestamps[first_valid] < cutoff:
            first_valid += 1
        if first_valid:
            del timestamps[:first_valid]
        valid_timestamps = timestamps
        valid_count = len(timestamps)

        # Check if limit is reached
        if valid_count >= limit:
            # Calculate retry after based on oldest timestamp in window
            oldest_valid = valid_timestamps[0] if valid_timestamps else now
            retry_after = oldest_valid + window - now
            newest_valid = valid_timestamps[-1] if valid_timestamps else now
            
            # Save pruned timestamps even if rejected
            self._store(
                key,
                {
                    "timestamps": valid_timestamps,
                    "count": valid_count
                },
                max(0.001, valid_timestamps[-1] + window - now),
            )
            
            return {
                "allowed": False,
                "remaining": 0,
                "retry_after": max(0.0, retry_after),
                "reset_after": max(0.0, newest_valid + window - now),
                "limit": limit
            }

        # Allow request and add new timestamp
        valid_timestamps.append(now)
        valid_count += 1

        self._store(
            key,
            {
                "timestamps": valid_timestamps,
                "count": valid_count
            },
            max(0.001, valid_timestamps[-1] + window - now),
        )

        # Calculate reset after based on newest timestamp
        reset_after = valid_timestamps[-1] + window - now

        return {
            "allowed": True,
            "remaining": limit - valid_count,
            "retry_after": 0.0,
            "reset_after": max(0.0, reset_after),
            "limit": limit
        }
