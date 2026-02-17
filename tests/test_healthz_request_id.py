from __future__ import annotations

from fastapi.testclient import TestClient

from app.api_main import create_app


def test_healthz_sets_request_id_header() -> None:
    app = create_app()
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
    rid = r.headers.get("X-Request-Id")
    assert rid is not None
    assert len(rid) >= 8

    r2 = client.get("/healthz", headers={"X-Request-Id": "req-123"})
    assert r2.status_code == 200
    assert r2.headers.get("X-Request-Id") == "req-123"
