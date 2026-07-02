# RateGuard 🛡️

A lightweight, modular **rate limiting library** for [FastAPI](https://fastapi.tiangolo.com/) applications. RateGuard provides a clean decorator-based API to protect your endpoints from abuse, with pluggable algorithms and storage backends.

---

## Features

- ✅ Simple `@limit` decorator — drop onto any route handler
- ✅ **Fixed Window** and **Token Bucket** algorithms out of the box
- ✅ Smart key resolution — auto-detects authenticated users or falls back to client IP
- ✅ Custom key resolver support for advanced use cases
- ✅ Pluggable storage backend (in-memory by default, extensible)
- ✅ Returns `429 Too Many Requests` with `retry_after`, `reset_after`, and `limit` metadata
- ✅ Zero external dependencies

---

## Project Structure

```
rateguard/                        ← project root
├── rateguard/                    ← installable Python package
│   ├── __init__.py               # Public API surface
│   ├── py.typed                  # PEP 561 type marker
│   ├── algorithms/
│   │   ├── registry.py           # Algorithm factory/registry
│   │   ├── fixed_window.py       # Fixed Window rate limiting algorithm
│   │   └── token_bucket.py       # Token Bucket rate limiting algorithm
│   ├── core/
│   │   ├── limiter.py            # RateLimiter — orchestrates algorithm checks
│   │   ├── policy.py             # RateLimitPolicy — limit & window config
│   │   ├── resolver.py           # KeyResolver — identifies the client
│   │   ├── exceptions.py         # RateLimitExceeded exception
│   │   └── enums.py              # Algorithm enum
│   ├── decorators/
│   │   └── decorator.py          # @limit decorator — the main public API
│   └── storage/
│       └── storage.py            # MemoryStorage — in-memory key/value store
├── examples/
│   └── basic_usage.py            # Example FastAPI app
├── pyproject.toml                # Package metadata & build config
├── setup.py                      # Editable install shim
├── requirements.txt
└── README.md
```

---

## Installation

### From source (recommended for development)

```bash
git clone https://github.com/AdeelMalik22/rateguard.git
cd requestguard
pip install -e .
```

The `-e` flag installs it in **editable mode** — any changes you make to the source are reflected immediately without reinstalling.

### From PyPI *(once published)*

```bash
pip install requestguard
```

---

## Quick Start

```python
from fastapi import FastAPI, Request
from requestguard import limit, Algorithm

app = FastAPI()


@limit(max_retries=5, ttl=60)
def my_handler(request: Request):
    return {"message": "Hello!"}


@app.get("/hello")
def hello_route(request: Request):
    return my_handler(request)
```

### Run the server

```bash
uvicorn examples.basic_usage:app --reload
```

---

## Usage

### `@limit(max_retries, ttl, key=None, algorithm=Algorithm.FIXED_WINDOW)`

| Parameter      | Type         | Description                                                   |
|----------------|--------------|---------------------------------------------------------------|
| `max_retries`  | `int`        | Maximum number of requests allowed (capacity)                 |
| `ttl`          | `int`        | Time window in **seconds**                                    |
| `key`          | `callable`   | *(Optional)* Custom function to resolve the client identifier |
| `algorithm`    | `Algorithm`  | *(Optional)* The algorithm to use. Default is `FIXED_WINDOW`. |

#### Basic — 3 requests per 10 seconds (Fixed Window)

```python
from requestguard import limit

@limit(max_retries=3, ttl=10)
def my_endpoint(request: Request):
    return {"status": "ok"}
```

#### Token Bucket

```python
from requestguard import limit, Algorithm

# max_retries acts as the Capacity (maximum burst size)
# ttl acts as the refill window (refill rate = max_retries / ttl)
# Example below: Burst of 10, refills at 10/60 tokens per second
@limit(max_retries=10, ttl=60, algorithm=Algorithm.TOKEN_BUCKET)
def smooth_endpoint(request: Request):
    return {"status": "ok"}
```

#### Custom Key Resolver

```python
from requestguard import limit

def resolve_by_api_key(*args, **kwargs):
    request = kwargs.get("request")
    return request.headers.get("X-API-Key", "anonymous")

@limit(max_retries=100, ttl=60, key=resolve_by_api_key)
def protected_endpoint(request: Request):
    return {"data": "..."}
```

---

## How It Works

```
Request
  │
  ▼
@limit decorator
  │
  ├─► KeyResolver.resolve()       → Identifies client (user ID or IP)
  │
  ├─► get_algorithm(algorithm)    → Fetches the requested Algorithm class
  │
  ├─► RateLimiter.check()         → Delegates to the algorithm instance
  │
  ├─► Limiter.allow()             → Uses time.monotonic() to evaluate rate limit
  │     ├─ Fetch record from MemoryStorage
  │     ├─ Update buckets/windows
  │     ├─ Block if limit reached → raise HTTPException(429)
  │     └─ Increment/Decrement & save to storage
  │
  └─► Route handler executes normally
```

### Key Resolution Priority

1. **Custom resolver** — if a `key` function is passed to `@limit`
2. **Authenticated user** — reads `request.scope["user"].id` (set by auth middleware)
3. **Client IP** — falls back to `request.client.host`

---

## Algorithms

### Fixed Window (`Algorithm.FIXED_WINDOW`)

Counts requests within a fixed time window. Once the window expires, the counter resets entirely.

- **Pros**: Simple, predictable, low memory usage
- **Cons**: Burst traffic possible at window boundaries

### Token Bucket (`Algorithm.TOKEN_BUCKET`)

Allows up to a maximum capacity of tokens (requests), continuously refilling tokens at a constant rate over time.

- **Pros**: Extremely smooth rate limiting, allows for bursts while maintaining a steady long-term rate
- **Cons**: Slightly more floating-point math overhead

### Returned State

All algorithms implement a consistent interface returning:

| Field           | Description                          |
|-----------------|--------------------------------------|
| `allowed`       | `bool` — whether the request passes  |
| `remaining`     | `int` — requests left for this client|
| `retry_after`   | `float` — seconds until at least 1 request can be made (only on `429`) |
| `reset_after`   | `float` — seconds until the rate limit fully resets |
| `limit`         | `int` — the total limit configured   |

---

## Storage Backends

### `MemoryStorage` (default)

In-memory dictionary store. Fast and dependency-free, but **not shared** across multiple processes or workers.

```python
from requestguard import MemoryStorage

storage = MemoryStorage()
storage.set("key", {"tokens": 10, "last_refill": 1234567890.0})
storage.get("key")     # → {"tokens": 10, "last_refill": ...}
storage.delete("key")
```

> **Note:** For production deployments with multiple workers, replace `MemoryStorage` with a Redis-backed implementation to share state across processes.

---

## Response Behavior

| Scenario           | HTTP Status | Response Body                                           |
|--------------------|-------------|----------------------------------------------------------|
| Request allowed    | `2xx`       | Normal route response                                    |
| Limit exceeded     | `429`       | `{"error": "Too many requests", "retry_after": <float>, "reset_after": <float>, "limit": <int>}` |

---

## Publishing to PyPI

```bash
# Install build tools
pip install build twine

# Build the distribution
python -m build

# Upload to PyPI
twine upload dist/*
```

---

## Requirements

| Package            | Version   |
|--------------------|-----------|
| fastapi            | ≥ 0.100.0 |
| starlette          | ≥ 0.27.0  |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/sliding-window`
3. Commit your changes: `git commit -m "feat: add sliding window algorithm"`
4. Push to the branch: `git push origin feature/sliding-window`
5. Open a Pull Request

---

## License

This project is open-source and available under the MIT License.
