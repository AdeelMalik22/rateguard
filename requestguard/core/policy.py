from dataclasses import dataclass


@dataclass
class RateLimitPolicy:
    limit: int
    window_seconds: int

    @property
    def capacity(self) -> int:
        return self.limit

    @property
    def refill_rate(self) -> float:
        return self.limit / self.window_seconds if self.window_seconds > 0 else 0.0