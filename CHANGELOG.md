# Changelog

## 0.2.0

- Added shared Redis locking for safe rate-limit updates across workers and pods.
- Added bounded LRU eviction and active TTL cleanup to `MemoryStorage`.
- Optimized exact sliding-window pruning to avoid duplicate list allocations.
- Added Redis concurrency integration tests to CI.
- Added Python 3.13 compatibility coverage in CI.
- Standardized documentation on `requests` and `window`, while retaining the
  `max_retries` and `ttl` aliases for compatibility.
