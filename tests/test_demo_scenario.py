from __future__ import annotations

from fastapi.testclient import TestClient

from app.api_main import create_app


def test_demo_scenarios_list() -> None:
    app = create_app()
    client = TestClient(app)
    r = client.get('/demo/scenarios')
    assert r.status_code == 200
    js = r.json()
    assert js.get('ok') is True
    names = [s.get('name') for s in js.get('scenarios') or []]
    assert 'card_resolve_approval' in names


def test_demo_run_scenario_dry_run() -> None:
    app = create_app()
    client = TestClient(app)
    r = client.post('/demo/run_scenario', json={'dry_run': True})
    assert r.status_code == 200
    js = r.json()
    assert js.get('ok') is True
    assert js.get('dry_run') is True
    assert js.get('scenario') == 'card_resolve_approval'
    assert 'plan' in js

    # request-id must be set
    rid = r.headers.get('X-Request-Id')
    assert rid is not None and len(rid) >= 8
