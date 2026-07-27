import time
from typing import List
from requestguard.storage.storage import synchronized_allow

class SlidingWindowLimiter:

    def __init__(self, policy, storage):
        self.policy = policy
        self.storage = storage

    @synchronized_allow
    def allow(self, key):
        now = time.monotonic()
        record = self.storage.get(key)
        
        limit = self.policy.limit
        window = self.policy.window_seconds

        # Initialize empty timestamps list if no record
        if record is None:
            self.storage.set(
                key,
                {
                    "timestamps": [now],
                    "count": 1
                }
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
        valid_timestamps = [ts for ts in timestamps if ts >= cutoff]
        valid_count = len(valid_timestamps)

        # Check if limit is reached
        if valid_count >= limit:
            # Calculate retry after based on oldest timestamp in window
            oldest_valid = valid_timestamps[0] if valid_timestamps else now
            retry_after = oldest_valid + window - now
            newest_valid = valid_timestamps[-1] if valid_timestamps else now
            
            # Save pruned timestamps even if rejected
            self.storage.set(
                key,
                {
                    "timestamps": valid_timestamps,
                    "count": valid_count
                }
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

        self.storage.set(
            key,
            {
                "timestamps": valid_timestamps,
                "count": valid_count
            }
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
