from fastapi.testclient import TestClient


def test_readyz_ok(monkeypatch):
    from app.api_main import create_app
    from app.api.routers import health as health_router

    app = create_app()

    monkeypatch.setattr(health_router, "wait_for_db", lambda *a, **k: None)

    # Pretend all critical tables exist.
    monkeypatch.setattr(
        health_router.dbmod,
        "all",
        lambda *a, **k: [{"table_name": n} for n in k.get("names", [])],
    )
    # Pretend extensions exist.
    monkeypatch.setattr(
        health_router.dbmod,
        "one",
        lambda *a, **k: {"extname": k.get("ext")} if k.get("ext") else None,
    )

    c = TestClient(app)
    r = c.get("/readyz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_readyz_missing_tables(monkeypatch):
    from app.api_main import create_app
    from app.api.routers import health as health_router

    app = create_app()

    monkeypatch.setattr(health_router, "wait_for_db", lambda *a, **k: None)
    # Return only one table.
    monkeypatch.setattr(
        health_router.dbmod,
        "all",
        lambda *a, **k: [{"table_name": "kanban_cards"}],
    )
    monkeypatch.setattr(
        health_router.dbmod,
        "one",
        lambda *a, **k: {"extname": "pgcrypto"},
    )

    c = TestClient(app)
    r = c.get("/readyz")
    assert r.status_code == 503

    body = r.json()
    assert body["error"]["code"] == "http_503"
    details = body["error"]["details"]
    assert details["status"] == "not_ready"
    assert "missing_tables" in details
