import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi import FastAPI

from requestguard import RequestGuard, RateLimitExceeded
from requestguard.integrations.fastapi import rate_limit_exception_handler


@pytest.mark.asyncio
async def test_fastapi_rate_limit_handler_returns_standard_headers():
    app = FastAPI()
    app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
    guard = RequestGuard()

    @app.get("/limited")
    @guard.limit(1, 60, key=lambda: "fastapi-client")
    def endpoint():
        return {"ok": True}

    response = await rate_limit_exception_handler(
        None, RateLimitExceeded(retry_after=2, reset_after=10, limit=1)
    )
    assert response.status_code == 429
    assert response.headers["RateLimit-Limit"] == "1"
    assert response.headers["RateLimit-Remaining"] == "0"
