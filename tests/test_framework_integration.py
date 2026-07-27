import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi import FastAPI
from fastapi.testclient import TestClient

from requestguard import RequestGuard, RateLimitExceeded


def test_fastapi_sync_endpoint_executes_and_limits():
    app = FastAPI()
    guard = RequestGuard()

    @app.get("/limited")
    @guard.limit(1, 60, key=lambda: "fastapi-client")
    def endpoint():
        return {"ok": True}

    client = TestClient(app)
    assert client.get("/limited").status_code == 200
    with pytest.raises(RateLimitExceeded):
        client.get("/limited")
