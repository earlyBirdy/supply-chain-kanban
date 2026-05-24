from __future__ import annotations

from fastapi.testclient import TestClient

from app.api_main import create_app


def test_api_root_guides_user_to_dashboard_and_docs() -> None:
    client = TestClient(create_app())

    r = client.get("/")

    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "Supply Chain Kanban API"
    assert body["status"] == "ok"
    assert body["links"]["web_dashboard"] == "http://localhost:8080"
    assert body["links"]["api_docs"] == "/docs"


def test_favicon_does_not_generate_noisy_404() -> None:
    client = TestClient(create_app())

    r = client.get("/favicon.ico")

    assert r.status_code == 204
