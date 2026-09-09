
import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Optional


class MemoryStorage:

    def __init__(self, max_keys: Optional[int] = 100_000, cleanup_interval: int = 256):
        if max_keys is not None and max_keys <= 0:
            raise ValueError("max_keys must be greater than zero or None")
        if cleanup_interval <= 0:
            raise ValueError("cleanup_interval must be greater than zero")
        self.data: OrderedDict[str, Any] = OrderedDict()
        self._expires_at: dict[str, float] = {}
        self._lock = threading.RLock()
        self.max_keys = max_keys
        self.cleanup_interval = cleanup_interval
        self._operations = 0

    def _maintain(self) -> None:
        self._operations += 1
        if self._operations % self.cleanup_interval == 0:
            now = time.monotonic()
            expired = [key for key, deadline in self._expires_at.items()
                       if deadline <= now]
            for key in expired:
                self.data.pop(key, None)
                self._expires_at.pop(key, None)
        if self.max_keys is not None:
            while len(self.data) > self.max_keys:
                key, _ = self.data.popitem(last=False)
                self._expires_at.pop(key, None)


    def get(self, key: str) -> Any:
        with self._lock:
            expires_at = self._expires_at.get(key)
            if expires_at is not None and expires_at <= time.monotonic():
                self.data.pop(key, None)
                self._expires_at.pop(key, None)
                return None
            value = self.data.get(key)
            if value is not None:
                self.data.move_to_end(key)
            self._maintain()
            return value


    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self.data[key] = value
            self.data.move_to_end(key)
            self._expires_at.pop(key, None)
            self._maintain()

    def set_with_ttl(self, key: str, value: Any, ttl: float) -> None:
        if ttl <= 0:
            raise ValueError("ttl must be greater than zero")
        with self._lock:
            self.data[key] = value
            self.data.move_to_end(key)
            self._expires_at[key] = time.monotonic() + ttl
            self._maintain()


    def delete(self, key: str) -> None:
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
            self.data.move_to_end(key)
            self._expires_at.pop(key, None)
            self._maintain()
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
    def locked(self, key: Optional[str] = None):
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
        with locked(args[0] if args else kwargs.get("key")):
            return func(self, *args, **kwargs)
    return wrapper
