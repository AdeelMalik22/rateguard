import pytest

from requestguard import Algorithm, RequestGuard


def test_legacy_arguments_emit_deprecation_warnings():
    guard = RequestGuard()
    with pytest.warns(DeprecationWarning, match="max_retries"):
        guard.limit(max_retries=1, window=60)
    with pytest.warns(DeprecationWarning, match="ttl"):
        guard.limit(requests=1, ttl=60)


def test_invalid_algorithm_has_actionable_error():
    with pytest.raises(TypeError, match="algorithm must be an Algorithm"):
        RequestGuard().limit(requests=1, window=60, algorithm="fixed_window")


def test_invalid_key_resolver_has_actionable_error():
    with pytest.raises(TypeError, match="key resolver must be callable"):
        RequestGuard().limit(requests=1, window=60, key="not-callable")


def test_key_resolver_signature_error_is_actionable():
    guard = RequestGuard()

    @guard.limit(requests=1, window=60, key=lambda required: required)
    def endpoint():
        return True

    with pytest.raises(TypeError, match="key resolver could not be called"):
        endpoint()
