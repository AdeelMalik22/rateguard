
import threading
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable


class MemoryStorage:

    def __init__(self):
        self.data: dict[str, Any] = {}
        self._expires_at: dict[str, float] = {}
        self._lock = threading.RLock()


    def get(self, key):
        with self._lock:
            expires_at = self._expires_at.get(key)
            if expires_at is not None and expires_at <= time.monotonic():
                self.data.pop(key, None)
                self._expires_at.pop(key, None)
                return None
            return self.data.get(key)


    def set(self, key, value):
        with self._lock:
            self.data[key] = value
            self._expires_at.pop(key, None)

    def set_with_ttl(self, key: str, value: Any, ttl: float) -> None:
        if ttl <= 0:
            raise ValueError("ttl must be greater than zero")
        with self._lock:
            self.data[key] = value
            self._expires_at[key] = time.monotonic() + ttl


    def delete(self, key):
        with self._lock:
            self.data.pop(key, None)
            self._expires_at.pop(key, None)

    def atomic_update(
        self,
        key: str,
        updater: Callable[[Any], tuple[Any, Any]],
    ) -> Any:
        """Atomically read, update, and store a value for ``key``.

        ``updater`` receives the current value and returns ``(new_value,
        result)``. The callback executes while the storage lock is held, so
        callers can safely implement read-modify-write rate-limit operations.
        """
        with self._lock:
            updated_value, result = updater(self.data.get(key))
            self.data[key] = updated_value
            self._expires_at.pop(key, None)
            return result

    def cleanup_expired(self) -> int:
        """Remove expired records and return the number removed."""
        now = time.monotonic()
        with self._lock:
            expired = [key for key, deadline in self._expires_at.items()
                       if deadline <= now]
            for key in expired:
                self.data.pop(key, None)
                self._expires_at.pop(key, None)
            return len(expired)

    def clear(self) -> None:
        """Remove all stored values (primarily useful for tests)."""
        with self._lock:
            self.data.clear()
            self._expires_at.clear()

    @contextmanager
    def locked(self):
        """Hold the storage lock across a complete algorithm update."""
        with self._lock:
            yield


def synchronized_allow(func):
    """Serialize an algorithm's read-modify-write operation when supported."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        locked = getattr(self.storage, "locked", None)
        if locked is None:
            return func(self, *args, **kwargs)
        with locked():
            return func(self, *args, **kwargs)
    return wrapper
