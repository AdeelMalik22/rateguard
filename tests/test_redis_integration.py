import os
from concurrent.futures import ThreadPoolExecutor

import pytest

redis = pytest.importorskip("redis")

from requestguard import RateLimitExceeded, RedisStorage, RequestGuard


@pytest.mark.integration
def test_redis_storage_enforces_shared_limit_under_concurrency():
    client = redis.Redis.from_url(
        os.getenv("REQUESTGUARD_REDIS_URL", "redis://127.0.0.1:6379/15"),
        decode_responses=True,
    )
    try:
        client.ping()
    except redis.exceptions.RedisError:
        pytest.skip("Redis is not available")

    prefix = "requestguard:test:"
    key = f"{prefix}requestguard:fixed_window:redis-integration:test-client"
    client.delete(key, f"{key}:lock")
    guard = RequestGuard(RedisStorage(client, prefix=prefix))

    @guard.limit(100, 60, key=lambda: "test-client", namespace="redis-integration")
    def endpoint():
        return True

    def call(_):
        try:
            endpoint()
            return True
        except RateLimitExceeded:
            return False

    with ThreadPoolExecutor(max_workers=32) as executor:
        results = list(executor.map(call, range(1000)))

    assert sum(results) == 100
    client.delete(key, f"{key}:lock")
