# RateGuard 🛡️

A lightweight, modular **rate limiting library** for [FastAPI](https://fastapi.tiangolo.com/) applications. RateGuard provides a clean decorator-based API to protect your endpoints from abuse, with pluggable algorithms and storage backends.

---

## Features

- ✅ Simple `@limit` decorator — drop onto any route handler
- ✅ **Fixed Window** algorithm out of the box
- ✅ Smart key resolution — auto-detects authenticated users or falls back to client IP
- ✅ Custom key resolver support for advanced use cases
- ✅ Pluggable storage backend (in-memory by default, extensible)
- ✅ Returns `429 Too Many Requests` with `retry_after` metadata
- ✅ Zero external dependencies beyond FastAPI

---

## Project Structure

```
rateguard/
├── algorithms/
│   ├── __init__.py
│   └── fixed_window.py       # Fixed Window rate limiting algorithm
├── core/
│   ├── limiter.py            # RateLimiter — orchestrates algorithm checks
│   ├── policy.py             # RateLimitPolicy — limit & window config
│   └── resolver.py           # KeyResolver — identifies the client
├── decorators/
│   └── decorator.py          # @limit decorator — the main public API
├── storage/
│   └── storage.py            # MemoryStorage — in-memory key/value store
├── test.py                   # Example FastAPI app using RateGuard
├── requirements.txt
└── README.md
```

---

## Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/AdeelMalik22/rateguard.git
cd rateguard
pip install -r requirements.txt
```

---

## Quick Start

```python
from fastapi import FastAPI, Request
from decorators.decorator import limit

app = FastAPI()


@limit(requests=5, window=60)
def my_handler(request: Request):
    return {"message": "Hello!"}


@app.get("/hello")
def hello_route(request: Request):
    return my_handler(request)
```

### Run the server

```bash
uvicorn test:app --reload
```

---

## Usage

### `@limit(requests, window, key=None)`

| Parameter  | Type       | Description                                                   |
|------------|------------|---------------------------------------------------------------|
| `requests` | `int`      | Maximum number of requests allowed within the window          |
| `window`   | `int`      | Time window in **seconds**                                    |
| `key`      | `callable` | *(Optional)* Custom function to resolve the client identifier |

#### Basic — 3 requests per 10 seconds

```python
@limit(requests=3, window=10)
def my_endpoint(request: Request):
    return {"status": "ok"}
```

#### Custom Key Resolver

```python
def resolve_by_api_key(*args, **kwargs):
    request = kwargs.get("request")
    return request.headers.get("X-API-Key", "anonymous")

@limit(requests=100, window=60, key=resolve_by_api_key)
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
  ├─► KeyResolver.resolve()     → Identifies client (user ID or IP)
  │
  ├─► RateLimiter.check()       → Delegates to the algorithm
  │
  ├─► FixedWindowLimiter.allow()
  │     ├─ Fetch record from MemoryStorage
  │     ├─ Reset window if expired
  │     ├─ Block if limit reached → raise HTTPException(429)
  │     └─ Increment counter & allow
  │
  └─► Route handler executes normally
```

### Key Resolution Priority

1. **Custom resolver** — if a `key` function is passed to `@limit`
2. **Authenticated user** — reads `request.scope["user"].id` (set by auth middleware)
3. **Client IP** — falls back to `request.client.host`

---

## Algorithms

### Fixed Window

Counts requests within a fixed time window. Once the window expires, the counter resets.

- **Pros**: Simple, predictable, low memory usage
- **Cons**: Burst traffic possible at window boundaries

| Field           | Description                          |
|-----------------|--------------------------------------|
| `allowed`       | `bool` — whether the request passes  |
| `remaining`     | `int` — requests left in window      |
| `retry_after`   | `float` — seconds until window resets (only on `429`) |

---

## Storage Backends

### `MemoryStorage` (default)

In-memory dictionary store. Fast and dependency-free, but **not shared** across multiple processes or workers.

```python
from storage.storage import MemoryStorage

storage = MemoryStorage()
storage.set("key", {"count": 1, "start": 1234567890.0})
storage.get("key")     # → {"count": 1, "start": ...}
storage.delete("key")
```

> **Note:** For production deployments with multiple workers, replace `MemoryStorage` with a Redis-backed implementation to share state across processes.

---

## Response Behavior

| Scenario           | HTTP Status | Response Body                                           |
|--------------------|-------------|----------------------------------------------------------|
| Request allowed    | `2xx`       | Normal route response                                    |
| Limit exceeded     | `429`       | `{"error": "Too many requests", "retry_after": <float>}` |

---

## Requirements

| Package            | Version   |
|--------------------|-----------|
| fastapi            | ≥ 0.138.2 |
| pydantic           | ≥ 2.13.4  |
| starlette          | ≥ 1.3.1   |

Install with:

```bash
pip install -r requirements.txt
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/sliding-window`
3. Commit your changes: `git commit -m "feat: add sliding window algorithm"`
4. Push to the branch: `git push origin feature/sliding-window`
5. Open a Pull Request

---

## License

This project is open-source. Feel free to use, modify, and distribute it.
