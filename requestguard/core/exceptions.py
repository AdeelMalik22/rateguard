
class RateLimitExceeded(Exception):
    """Raised when a rate limit is exceeded. Framework-agnostic."""
    def __init__(self, retry_after=None, reset_after=None, limit=None,
                 message="Too many requests", remaining=0):
        self.message = message
        self.retry_after = retry_after
        self.reset_after = reset_after
        self.limit = limit
        self.remaining = remaining
        self.detail = {
            "error": message,
            "retry_after": retry_after,
            "reset_after": reset_after,
            "limit": limit,
            "remaining": remaining,
        }
        super().__init__(message)


class UnsupportedAlgorithmError(ValueError):
    """Raised when a limiter algorithm is not registered."""
