import json
import time
from contextlib import contextmanager
from typing import Any, Callable, Optional
from requestguard.core.exceptions import StorageUnavailableError


class RedisStorage:
    """Redis-backed storage with optimistic atomic updates.

    Pass an already configured ``redis.Redis`` client to avoid making Redis a
    mandatory dependency for users who only need MemoryStorage.
    """

    def __init__(self, client, prefix: str = "requestguard:", lock_timeout: float = 30.0,
                 retries: int = 2, retry_delay: float = 0.05, failure_mode: str = "closed"):
        if lock_timeout <= 0:
            raise ValueError("lock_timeout must be greater than zero")
        if retries < 0:
            raise ValueError("retries must be zero or greater")
        if retry_delay < 0:
            raise ValueError("retry_delay must be zero or greater")
        if failure_mode not in {"open", "closed"}:
            raise ValueError("failure_mode must be 'open' or 'closed'")
        self.client = client
        self.prefix = prefix
        self.lock_timeout = lock_timeout
        self.retries = retries
        self.retry_delay = retry_delay
        self.failure_mode = failure_mode

    def _call(self, operation):
        for attempt in range(self.retries + 1):
            try:
                return operation()
            except Exception as exc:
                retryable = isinstance(exc, (TimeoutError, ConnectionError)) or \
                    exc.__class__.__module__.startswith("redis")
                if not retryable or attempt == self.retries:
                    if retryable:
                        raise StorageUnavailableError(
                            "Redis storage is unavailable after retries"
                        ) from exc
                    raise
                if self.retry_delay:
                    time.sleep(self.retry_delay * (2 ** attempt))

    def _key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    def get(self, key: str) -> Any:
        value = self._call(lambda: self.client.get(self._key(key)))
        if value is None:
            return None
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        return json.loads(value)

    def set(self, key: str, value: Any) -> None:
        self._call(lambda: self.client.set(self._key(key), json.dumps(value)))

    def set_with_ttl(self, key: str, value: Any, ttl: float) -> None:
        if ttl <= 0:
            raise ValueError("ttl must be greater than zero")
        self._call(lambda: self.client.set(self._key(key), json.dumps(value), ex=ttl))

    def delete(self, key: str) -> None:
        self._call(lambda: self.client.delete(self._key(key)))

    @contextmanager
    def locked(self, key: Optional[str] = None):
        """Hold a per-key distributed lock across an algorithm update."""
        if key is None:
            raise ValueError("a key is required for RedisStorage.locked")
        lock = self._call(lambda: self.client.lock(
            f"{self._key(key)}:lock",
            timeout=self.lock_timeout,
            blocking_timeout=self.lock_timeout,
        ))
        acquired = self._call(lock.acquire)
        if not acquired:
            raise StorageUnavailableError("Could not acquire Redis rate-limit lock")
        try:
            yield
        finally:
            self._call(lock.release)

    def atomic_update(self, key: str,
                      updater: Callable[[Any], tuple[Any, Any]]) -> Any:
        redis_key = self._key(key)
        while True:
            with self.client.pipeline() as pipe:
                try:
                    pipe.watch(redis_key)
                    raw = pipe.get(redis_key)
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8")
                    current = None if raw is None else json.loads(raw)
                    updated, result = updater(current)
                    pipe.multi()
                    pipe.set(redis_key, json.dumps(updated))
                    pipe.execute()
                    return result
                except Exception as exc:
                    if exc.__class__.__name__ != "WatchError":
                        raise

    def clear(self) -> None:
        keys = list(self.client.scan_iter(match=f"{self.prefix}*"))
        if keys:
            self.client.delete(*keys)
