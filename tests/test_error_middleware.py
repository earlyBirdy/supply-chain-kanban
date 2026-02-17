from fastapi.testclient import TestClient


def test_unhandled_exception_returns_request_id():
    from app.api_main import create_app

    app = create_app()

    @app.get("/boom")
    def boom():
        raise RuntimeError("kaboom")

    c = TestClient(app)
    r = c.get("/boom")
    assert r.status_code == 500
    assert "X-Request-Id" in r.headers
    body = r.json()
    assert body.get("request_id") == r.headers["X-Request-Id"]


def test_request_id_is_echoed_if_provided():
    from app.api_main import create_app

    app = create_app()

    @app.get("/ok")
    def ok():
        return {"ok": True}

    c = TestClient(app)
    r = c.get("/ok", headers={"X-Request-Id": "demo-123"})
    assert r.status_code == 200
    assert r.headers.get("X-Request-Id") == "demo-123"
