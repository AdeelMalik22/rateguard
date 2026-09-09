import json
from typing import Any, Callable, Optional

from requestguard.algorithms.registry import get_algorithm
from requestguard.core.enums import Algorithm
from requestguard.core.policy import RateLimitPolicy
from requestguard.core.resolver import KeyResolver
from requestguard.storage.storage import MemoryStorage


class RateLimitMiddleware:
    """ASGI middleware for protecting routes that cannot use a decorator."""

    def __init__(self, app, requests: int, window: float,
                 storage: Optional[Any] = None,
                 algorithm: Algorithm = Algorithm.FIXED_WINDOW,
                 key: Optional[Callable[..., str]] = None):
        self.app = app
        self.storage = storage or MemoryStorage()
        policy = RateLimitPolicy(requests, window)
        self.limiter = get_algorithm(algorithm)(policy, self.storage)
        self.key = KeyResolver(key)
        self.algorithm = algorithm

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        client = scope.get("client")
        key = self.key.resolve(_ASGIRequest(scope))
        client_id = str(key).strip()
        if not client_id:
            raise ValueError("rate-limit key resolver returned an empty value")
        namespace = scope.get("path", "asgi")
        algorithm_name = getattr(self.algorithm, "value", str(self.algorithm))
        result = self.limiter.allow(
            f"requestguard:{algorithm_name}:{namespace}:{client_id}"
        )
        if not result["allowed"]:
            body = json.dumps({"detail": "Too many requests", **result}).encode()
            headers = [(b"content-type", b"application/json"),
                       (b"content-length", str(len(body)).encode())]
            await send({"type": "http.response.start", "status": 429,
                        "headers": headers})
            await send({"type": "http.response.body", "body": body})
            return
        await self.app(scope, receive, send)


class _ASGIRequest:
    def __init__(self, scope):
        self.scope = scope
