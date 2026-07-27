from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitPolicy:
    limit: int
    window_seconds: float

    def __post_init__(self) -> None:
        if isinstance(self.limit, bool) or not isinstance(self.limit, int):
            raise TypeError("limit must be an integer")
        if self.limit <= 0:
            raise ValueError("limit must be greater than zero")

        if isinstance(self.window_seconds, bool) or not isinstance(
            self.window_seconds, (int, float)
        ):
            raise TypeError("window_seconds must be numeric")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be greater than zero")

    @property
    def capacity(self) -> int:
        return self.limit

    @property
    def refill_rate(self) -> float:
        return self.limit / self.window_seconds
