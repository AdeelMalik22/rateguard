class KeyResolver:
    def __init__(self, func=None):
        if func is not None and not callable(func):
            raise TypeError("key resolver must be callable or None")
        self.func = func

    def resolve(self, *args, **kwargs):
        if self.func:
            try:
                return self.func(*args, **kwargs)
            except TypeError as exc:
                raise TypeError(
                    "key resolver could not be called with the endpoint arguments"
                ) from exc

        request = self._find_request(args, kwargs)
        if request is None:
            return "anonymous"

        # --- Starlette / FastAPI request ---
        if hasattr(request, "scope"):
            user = request.scope.get("user")
            if user is not None and getattr(user, "id", None):
                return f"user:{user.id}"
            client = request.scope.get("client")
            if client:
                return f"ip:{client[0]}"
            return "anonymous"

        # --- Django / DRF request ---
        if hasattr(request, "META"):
            user = getattr(request, "user", None)
            if user is not None and getattr(user, "is_authenticated", False):
                return f"user:{user.id}"
            ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
            ip = ip or request.META.get("REMOTE_ADDR", "unknown")
            return f"ip:{ip}"

        # --- Flask request ---
        if hasattr(request, "remote_addr"):
            from flask import g
            user = getattr(g, "user", None)
            if user is not None and getattr(user, "id", None):
                return f"user:{user.id}"
            return f"ip:{request.remote_addr}"

        return "anonymous"

    def _find_request(self, args, kwargs):
        # Check both positional and keyword args for something request-like
        candidates = list(args) + list(kwargs.values())
        for value in candidates:
            if hasattr(value, "scope") or hasattr(value, "META") or hasattr(value, "remote_addr"):
                return value
        return None
