import pytest

from requestguard import MemoryStorage, RateLimitExceeded, RateLimitPolicy, RequestGuard


def test_policy_rejects_invalid_values():
    with pytest.raises(ValueError):
        RateLimitPolicy(0, 60)
    with pytest.raises(ValueError):
        RateLimitPolicy(1, 0)
    with pytest.raises(TypeError):
        RateLimitPolicy(True, 60)


def test_fixed_window_allows_limit_then_rejects():
    guard = RequestGuard()

    @guard.limit(requests=2, window=60, key=lambda: "test-client")
    def endpoint():
        return True

    assert endpoint() is True
    assert endpoint() is True
    with pytest.raises(RateLimitExceeded):
        endpoint()


def test_storage_can_be_reset_between_tests():
    guard = RequestGuard()

    @guard.limit(1, 60, key=lambda: "test-client")
    def endpoint():
        return True

    endpoint()
    guard.storage.clear()
    assert endpoint() is True


def test_memory_storage_evicts_least_recently_used_keys():
    storage = MemoryStorage(max_keys=2, cleanup_interval=1)
    storage.set("first", 1)
    storage.set("second", 2)
    assert storage.get("first") == 1
    storage.set("third", 3)
    assert storage.get("first") == 1
    assert storage.get("second") is None


def test_memory_storage_cleans_expired_keys_during_normal_operations():
    storage = MemoryStorage(cleanup_interval=1)
    storage.set_with_ttl("temporary", 1, 0.001)
    import time
    time.sleep(0.01)
    storage.set("other", 2)
    assert storage.get("temporary") is None
