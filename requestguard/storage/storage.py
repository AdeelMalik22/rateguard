
import threading
from typing import Any, Callable


class MemoryStorage:

    def __init__(self):
        self.data: dict[str, Any] = {}
        self._lock = threading.RLock()


    def get(self, key):
        with self._lock:
            return self.data.get(key)


    def set(self, key, value):
        with self._lock:
            self.data[key] = value


    def delete(self, key):
        with self._lock:
            self.data.pop(key, None)

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
            return result

    def clear(self) -> None:
        """Remove all stored values (primarily useful for tests)."""
        with self._lock:
            self.data.clear()
