import pytest

from requestguard import RedisStorage, RequestGuard, StorageUnavailableError


class UnavailableRedis:
    def get(self, key):
        raise ConnectionError("Redis is down")

    def set(self, *args, **kwargs):
        raise ConnectionError("Redis is down")

    def lock(self, *args, **kwargs):
        raise ConnectionError("Redis is down")


def test_redis_storage_retries_then_raises_storage_error():
    storage = RedisStorage(UnavailableRedis(), retries=2, retry_delay=0)
    with pytest.raises(StorageUnavailableError):
        storage.get("client")


def test_fail_open_allows_request_when_redis_is_unavailable():
    guard = RequestGuard(RedisStorage(UnavailableRedis(), retries=0, failure_mode="open"))

    @guard.limit(1, 60, key=lambda: "client")
    def endpoint():
        return "ok"

    assert endpoint() == "ok"


def test_fail_closed_surfaces_storage_error_when_redis_is_unavailable():
    guard = RequestGuard(RedisStorage(UnavailableRedis(), retries=0, failure_mode="closed"))

    @guard.limit(1, 60, key=lambda: "client")
    def endpoint():
        return "ok"

    with pytest.raises(StorageUnavailableError):
        endpoint()
