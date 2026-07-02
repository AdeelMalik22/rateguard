# RateGuard Usage Guide

**GitHub Repository:** [AdeelMalik22/rateguard](https://github.com/AdeelMalik22/rateguard)

RateGuard is a **framework-agnostic** rate limiting library. Its core `RateLimiter` class can be used in **any** Python framework (Flask, Django, FastAPI, Celery, or pure Python scripts). When a limit is hit, RateGuard raises a single generic exception — `RateLimitExceeded` — and it's up to each framework's own error-handling mechanism to turn that into an HTTP response.

---

## 1. Framework-Agnostic Usage (Any Python App)

Using the `@limit` decorator directly (no framework) raises `RateLimitExceeded`, a plain Python exception with no web-framework dependency:

```python
from requestguard import limit
from requestguard import RateLimitExceeded

@limit(max_retries=5, ttl=60)
def do_something(user_id):
    return "done"

try:
    do_something("user_42")
except RateLimitExceeded as exc:
    print(exc.detail)  # {"error": "Too many requests", "retry_after": 12.4, "reset_after": 12.4, "limit": 5}
```

---

### 1a. Selecting an Algorithm

RateGuard supports multiple rate-limiting algorithms. By default, it uses the **Fixed Window** algorithm, but you can easily switch to the **Token Bucket** algorithm for smoother rate limiting that allows bursts.

**Available Algorithms:**
- `Algorithm.FIXED_WINDOW`: Counts requests in a fixed time window. Resets completely at the end of the window. Simple and predictable.
- `Algorithm.TOKEN_BUCKET`: Allows up to a maximum capacity of requests, continuously refilling them at a constant rate over time. Ideal for smooth traffic shaping and allowing temporary bursts.

```python
from requestguard import limit, Algorithm

# Fixed Window (Default)
@limit(max_retries=5, ttl=60)
def fixed_window_endpoint():
    pass

# Token Bucket
# max_retries = Capacity (burst size)
# ttl = Refill window (refill rate = max_retries / ttl)
# Example below: Burst of 10, refills at 10/60 = 0.16 tokens per second
@limit(max_retries=10, ttl=60, algorithm=Algorithm.TOKEN_BUCKET)
def token_bucket_endpoint():
    pass
```

---

## 2. How Exception Handling Works

`RateLimitExceeded` is **not** an HTTP exception — it carries no status code or framework awareness. Each framework has its own place to catch it and translate it into a `429 Too Many Requests` response. You register this translation **once**, at app startup; you never need to `try/except` it in every view.

```python
# requestguard/exceptions.py
class RateLimitExceeded(Exception):
    def __init__(self, retry_after=None, reset_after=None, limit=None, message="Too many requests"):
        self.message = message
        self.retry_after = retry_after
        self.reset_after = reset_after
        self.limit = limit
        self.detail = {
            "error": message,
            "retry_after": retry_after,
            "reset_after": reset_after,
            "limit": limit
        }
        super().__init__(message)
```

---

### 2a. FastAPI

Register a global exception handler on the `app` instance. FastAPI will call this automatically anytime a view raises `RateLimitExceeded`, anywhere in the call stack.

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from requestguard import limit
from requestguard import RateLimitExceeded

app = FastAPI()

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content=exc.detail)

@limit(max_retries=5, ttl=60)
def my_endpoint(request: Request):
    return {"message": "Hello!"}

@app.get("/hello")
def hello_route(request: Request):
    return my_endpoint(request)
```

No `try/except` needed inside `my_endpoint` — the exception propagates up and FastAPI routes it to the handler.

---

### 2b. Django REST Framework (DRF)

Plug into DRF's `EXCEPTION_HANDLER` setting. This runs for every view using DRF's dispatch, so again — no per-view `try/except` needed.

```python
# your_app/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from requestguard import RateLimitExceeded

def custom_exception_handler(exc, context):
    if isinstance(exc, RateLimitExceeded):
        return Response(exc.detail, status=429)
    return exception_handler(exc, context)  # fall back to DRF's default
```

```python
# settings.py
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "your_app.exceptions.custom_exception_handler",
}
```

```python
from requestguard import limit
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

class UserViewSet(viewsets.ModelViewSet):
    @limit(max_retries=3, ttl=30)
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
```

---

### 2c. Plain Django (no DRF)

DRF's `EXCEPTION_HANDLER` only applies to DRF views. For plain Django views, use middleware's `process_exception` hook instead.

```python
# your_app/middleware.py
from django.http import JsonResponse
from requestguard import RateLimitExceeded

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, RateLimitExceeded):
            return JsonResponse(exception.detail, status=429)
        return None  # let Django handle everything else normally
```

```python
# settings.py
MIDDLEWARE = [
    ...,
    "your_app.middleware.RateLimitMiddleware",
]
```

---

### 2d. Flask

Use `@app.errorhandler`, registered once against the exception class.

```python
from flask import Flask, jsonify
from requestguard import limit
from requestguard import RateLimitExceeded

app = Flask(__name__)

@app.errorhandler(RateLimitExceeded)
def handle_rate_limit(exc):
    return jsonify(exc.detail), 429

@app.route("/hello")
@limit(max_retries=5, ttl=60)
def hello_route():
    return {"message": "Hello!"}
```

---

## 3. Summary Table

| Framework    | Registration point                          | Where the exception is caught |
|--------------|----------------------------------------------|--------------------------------|
| FastAPI      | `@app.exception_handler(RateLimitExceeded)`   | Global, per-app                |
| DRF          | `REST_FRAMEWORK["EXCEPTION_HANDLER"]`         | Global, all DRF views          |
| Plain Django | Middleware `process_exception`                | Global, all views              |
| Flask        | `@app.errorhandler(RateLimitExceeded)`        | Global, per-app                |

The pattern is the same everywhere: **`rateguard` only raises `RateLimitExceeded`; your app registers one handler, once, to turn it into a 429.** No view or endpoint ever needs its own `try/except RateLimitExceeded` block.