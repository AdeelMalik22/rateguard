import pytest

from requestguard import RateLimitExceeded, RateLimitPolicy, RequestGuard


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
