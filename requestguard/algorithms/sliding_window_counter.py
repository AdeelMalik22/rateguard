import time
from requestguard.storage.storage import synchronized_allow

class SlidingWindowCounterLimiter:

    def __init__(self, policy, storage):
        self.policy = policy
        self.storage = storage

    @synchronized_allow
    def allow(self, key):
        now = time.monotonic()
        record = self.storage.get(key)
        
        limit = self.policy.limit
        window = self.policy.window_seconds

        current_window = int(now // window)
        current_window_start = current_window * window

        # first request
        if record is None:
            self.storage.set(
                key,
                {
                    "prev_count": 0,
                    "curr_count": 1,
                    "curr_window": current_window
                }
            )
            return {
                "allowed": True,
                "remaining": limit - 1,
                "retry_after": 0.0,
                "reset_after": float(window),
                "limit": limit
            }

        prev_count = record.get("prev_count", 0)
        curr_count = record.get("curr_count", 0)
        stored_window = record.get("curr_window", current_window)

        # Shift windows if necessary
        if stored_window == current_window - 1:
            prev_count = curr_count
            curr_count = 0
        elif stored_window < current_window - 1:
            prev_count = 0
            curr_count = 0

        # Calculate overlap percentage of the previous window
        time_into_current = now - current_window_start
        prev_weight = (window - time_into_current) / window
        
        estimated_count = (prev_count * prev_weight) + curr_count

        # Check if limit is reached
        if estimated_count >= limit:
            if prev_count > 0:
                if curr_count >= limit:
                    retry_after = window - time_into_current
                else:
                    required_weight = (limit - curr_count) / prev_count
                    retry_after = window - time_into_current - (required_weight * window)
                    if retry_after <= 0:
                        retry_after = 0.1
            else:
                retry_after = window - time_into_current

            # In the counter model, the limit fully resets at the end of the current window 
            # if we consider only the requests made. More precisely, it resets when both 
            # prev and curr counts are 0, which happens after 2 windows of inactivity. 
            # But "reset_after" usually denotes when the client can make a full burst again.
            reset_after = (window - time_into_current) + window

            return {
                "allowed": False,
                "remaining": 0,
                "retry_after": max(0.0, retry_after),
                "reset_after": max(0.0, reset_after),
                "limit": limit
            }

        # Allow request
        curr_count += 1
        
        self.storage.set(
            key,
            {
                "prev_count": prev_count,
                "curr_count": curr_count,
                "curr_window": current_window
            }
        )

        reset_after = (window - time_into_current) + window
        
        return {
            "allowed": True,
            "remaining": int(limit - estimated_count - 1),
            "retry_after": 0.0,
            "reset_after": max(0.0, reset_after),
            "limit": limit
        }
