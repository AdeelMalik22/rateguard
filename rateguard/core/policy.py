from dataclasses import dataclass


@dataclass
class RateLimitPolicy:
    limit: int
    window_seconds: int