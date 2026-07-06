# RateGuard: AI System Prompt & Development Guidelines

Welcome to the **RateGuard** repository. This document serves as the foundational system prompt and engineering standard for AI assistants contributing to this project. 

Our objective is to maintain a professional, highly scalable, and exceptionally robust codebase. As an AI contributor, you are expected to adhere strictly to the architectural constraints, behavioral flows, and clean-coding principles outlined below.

---

## 1. Architectural Vision & Philosophy

RateGuard is a **framework-agnostic**, high-performance rate limiting library for Python. It is designed to be easily pluggable into any web framework (FastAPI, Flask, Django) or background task processor (Celery).

**Core Tenets:**
- **Decoupled by Design:** The core engine must never couple itself to a specific HTTP framework. RateGuard does not construct HTTP responses.
- **Exception-Driven Enforcement:** RateGuard signals rate limit violations by raising a domain-specific exception (`RateLimitExceeded`). The host framework is responsible for catching this and translating it into an HTTP `429 Too Many Requests` response.
- **Stateless Operation:** All persistent state must be delegated to the storage layer (e.g., `MemoryStorage`, Redis). The core algorithms must remain entirely stateless to support distributed, multi-worker environments safely.

---

## 2. System Flow (The Request Lifecycle)

To modify or extend the system, you must first understand the deterministic flow of a request through the RateGuard pipeline:

1. **Interception:** A request invokes a function wrapped in the `@limit` decorator.
2. **Key Resolution:** The `KeyResolver` determines the identity of the caller (e.g., extracting an IP address, an API key, or a JWT user ID).
3. **Orchestration:** The `RateLimiter` acts as the orchestrator, instantiating the requested rate-limiting strategy (e.g., Token Bucket, Fixed Window) via the Algorithm Registry.
4. **Evaluation:** 
    - The selected algorithm retrieves the caller's current state from the `Storage` backend.
    - It applies its mathematical model using precise monotonic time.
    - It calculates the remaining capacity and updates the storage backend immediately.
5. **Resolution:** 
    - **Allowed:** The algorithm returns a success state, and the underlying function executes.
    - **Denied:** The algorithm returns a failure state, prompting the `RateLimiter` to instantly raise a `RateLimitExceeded` exception, halting execution.

---

## 3. General Golden Rules for Coding

When writing code for RateGuard, apply these universally recognized software engineering best practices:

- **Single Responsibility Principle (SRP):** Every class and module should have one, and only one, reason to change. Keep algorithms focused strictly on math and evaluation, storage on persistence, and resolvers on identity extraction.
- **Fail Fast & Early Returns:** Avoid deep nesting (the "Arrow Anti-Pattern"). Validate conditions immediately and return or raise early. This keeps the primary happy-path code unindented and readable.
- **Self-Documenting Code:** Favor highly descriptive variable and function names over inline comments. Code should read like well-written prose. Use comments only to explain *why* a complex decision was made, not *what* the code is doing.
- **Strict Type Safety:** Utilize Python's `typing` module comprehensively. Every function signature and class property must have explicit type hints.
- **Idempotency & Purity:** Where possible, design functions to be pure—producing the same output for the same input without invisible side effects.

---

## 4. RateGuard-Specific Engineering Standards

- **Precision Timekeeping:** **Never** use `time.time()` for rate limiting math, as it is susceptible to system clock drifts and NTP synchronizations. **Always** use `time.monotonic()` to guarantee accurate, forward-moving interval calculations.
- **Storage Mutations:** Assume the system will eventually run in a highly concurrent Redis cluster. Do not mutate state in local variables and assume it persists. Always explicitely read from and write to the storage adapter (e.g., `self.storage.get()` and `self.storage.set()`).
- **Framework Isolation:** Never import modules from `fastapi`, `django`, or `flask` inside `requestguard/core/` or `requestguard/algorithms/`. 

---

## 5. Algorithm Implementation Contract

When implementing a new rate-limiting algorithm, it must conform to a strict interface contract.

### Class Structure
The algorithm must accept the policy and storage adapter during initialization:
```python
class MyCustomLimiter:
    def __init__(self, policy: RateLimitPolicy, storage: StorageBackend):
        self.policy = policy
        self.storage = storage
```

### The `allow` Method
The algorithm must expose an `allow(key: str)` method that returns a strictly typed dictionary:
```python
def allow(self, key: str) -> dict:
    # ... evaluation logic ...
    return {
        "allowed": bool,      # True if permitted, False if limit exceeded
        "remaining": int,     # Count of requests left in the current window
        "retry_after": float, # Seconds until at least 1 request is permitted again
        "reset_after": float, # Seconds until the client's state resets to 100% capacity
        "limit": int          # The total configured capacity
    }
```

### Registration Protocol
A new algorithm does not exist until it is properly exposed. You must perform the following lifecycle registrations:
1. Define it in `requestguard/core/enums.py`.
2. Register the mapping in `requestguard/algorithms/registry.py`.
3. Export the class in `requestguard/__init__.py`.
