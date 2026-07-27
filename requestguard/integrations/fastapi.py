from requestguard.core.exceptions import RateLimitExceeded


def _headers(exc: RateLimitExceeded) -> dict[str, str]:
    headers: dict[str, str] = {}
    if exc.retry_after is not None:
        headers["Retry-After"] = str(max(1, int(exc.retry_after)))
    if exc.limit is not None:
        headers["RateLimit-Limit"] = str(exc.limit)
    headers["RateLimit-Remaining"] = str(max(0, exc.remaining))
    if exc.reset_after is not None:
        headers["RateLimit-Reset"] = str(max(0, int(exc.reset_after)))
    return headers


async def rate_limit_exception_handler(request, exc: RateLimitExceeded):
    """FastAPI/Starlette handler returning standard rate-limit metadata."""
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=429,
        content={
            "detail": exc.message,
            "retry_after": exc.retry_after,
            "reset_after": exc.reset_after,
            "limit": exc.limit,
            "remaining": exc.remaining,
        },
        headers=_headers(exc),
    )
