import json
from typing import Any, Callable


class RedisStorage:
    """Redis-backed storage with optimistic atomic updates.

    Pass an already configured ``redis.Redis`` client to avoid making Redis a
    mandatory dependency for users who only need MemoryStorage.
    """

    def __init__(self, client, prefix: str = "requestguard:"):
        self.client = client
        self.prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    def get(self, key: str) -> Any:
        value = self.client.get(self._key(key))
        if value is None:
            return None
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        return json.loads(value)

    def set(self, key: str, value: Any) -> None:
        self.client.set(self._key(key), json.dumps(value))

    def set_with_ttl(self, key: str, value: Any, ttl: float) -> None:
        if ttl <= 0:
            raise ValueError("ttl must be greater than zero")
        self.client.set(self._key(key), json.dumps(value), ex=ttl)

    def delete(self, key: str) -> None:
        self.client.delete(self._key(key))

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
