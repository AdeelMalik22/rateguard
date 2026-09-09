import pytest

from requestguard import RateLimitMiddleware


async def _app(scope, receive, send):
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"ok"})


async def _call(app):
    events = []
    scope = {"type": "http", "path": "/limited", "client": ("127.0.0.1", 1234)}
    async def send(event):
        events.append(event)
    await app(scope, lambda: None, send)
    return events


@pytest.mark.asyncio
async def test_asgi_middleware_rejects_after_limit():
    middleware = RateLimitMiddleware(_app, requests=1, window=60)
    first = await _call(middleware)
    second = await _call(middleware)
    assert first[0]["status"] == 200
    assert second[0]["status"] == 429


@pytest.mark.asyncio
async def test_asgi_middleware_passes_non_http_scopes():
    events = []
    middleware = RateLimitMiddleware(_app, requests=1, window=60)
    async def send(event):
        events.append(event)
    await middleware({"type": "lifespan"}, None, send)
    assert events[0]["status"] == 200
