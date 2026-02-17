from __future__ import annotations

import json
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from app.api_main import create_app
import app.api.routers.actions as actions_mod
import app.idempotency as idem_mod


def test_actions_execute_idempotency_replay_and_conflict(monkeypatch: pytest.MonkeyPatch) -> None:
    # In-memory idempotency store
    store: Dict[str, Dict[str, Any]] = {}

    def fake_idem_one(sql: str, **params):
        if "idempotency_keys" in sql.lower():
            return store.get(params.get("k"))
        return None

    def fake_idem_q(sql: str, **params):
        if "insert into idempotency_keys" in sql.lower():
            store[params["k"]] = {
                "key": params["k"],
                "request_hash": params["h"],
                "response": json.loads(params["r"]),
            }
        return None

    # Patch idempotency module callables
    monkeypatch.setattr(idem_mod, "_one", fake_idem_one)
    monkeypatch.setattr(idem_mod, "_q", fake_idem_q)

    # Fake DB lookup for case
    def fake_one(sql: str, **params):
        if "from agent_cases" in sql.lower():
            return {"case_id": params["cid"], "risk_score": 0.9}
        return None

    monkeypatch.setattr(actions_mod, "one", fake_one)

    # Always allow RBAC
    monkeypatch.setattr(actions_mod, "can_execute", lambda *a, **k: (True, ""))

    # Policy enables idempotency
    monkeypatch.setattr(actions_mod, "load_policy", lambda: {"idempotency": {"enabled": True, "header_name": "Idempotency-Key"}})

    # Deterministic actor
    monkeypatch.setattr(actions_mod, "get_actor", lambda request, channel="api": {"sub": "u1", "role": "system"})
    monkeypatch.setattr(actions_mod, "get_channel", lambda request, default="api": "api")

    calls = {"n": 0}

    def fake_execute_action(*, case_id: str, channel: str, action_type: str, payload: Dict[str, Any], dry_run: bool):
        calls["n"] += 1
        return {"ok": True, "action_id": "a1", "result": {"did": action_type, "case_id": case_id}}

    monkeypatch.setattr(actions_mod, "execute_action", fake_execute_action)

    app = create_app()
    client = TestClient(app)

    body = {"case_id": "c1", "channel": "api", "action_type": "UpdateCardStatus", "payload": {"x": 1}}
    r1 = client.post("/actions/execute", json=body, headers={"Idempotency-Key": "k1"})
    assert r1.status_code == 200
    assert calls["n"] == 1

    r2 = client.post("/actions/execute", json=body, headers={"Idempotency-Key": "k1"})
    assert r2.status_code == 200
    assert calls["n"] == 1  # replayed
    assert r2.json() == r1.json()

    # Conflict: same key, different payload
    body2 = {"case_id": "c1", "channel": "api", "action_type": "UpdateCardStatus", "payload": {"x": 999}}
    r3 = client.post("/actions/execute", json=body2, headers={"Idempotency-Key": "k1"})
    assert r3.status_code == 409
