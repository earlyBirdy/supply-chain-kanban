from fastapi.testclient import TestClient
import pytest

from app.api_main import create_app
from app.api.routers import pending_actions as pa_mod


def test_pending_execute_requires_approval(monkeypatch: pytest.MonkeyPatch) -> None:
    pending_id = "p1"
    pa_row = {
        "pending_id": pending_id,
        "case_id": "c1",
        "card_id": "k1",
        "materialization_id": None,
        "status": "pending",
        "approval_required": True,
        "action_type": "UpdateCardStatus",
        "action_payload": {"to_status": "resolved"},
    }

    def fake_one(sql: str, **params):
        sl = sql.lower()
        if "from pending_actions" in sl:
            return pa_row
        if "select risk_score" in sl:
            return {"risk_score": 0.9}
        return None

    monkeypatch.setattr(pa_mod, "one", fake_one)
    monkeypatch.setattr(pa_mod, "can_execute", lambda *a, **k: (True, ""))
    monkeypatch.setattr(
        pa_mod,
        "load_policy",
        lambda: {
            "pending_action_policy": {
                "allowed_transitions": {"pending": ["blocked"], "approved": ["executed", "blocked"]}
            }
        },
    )

    monkeypatch.setattr(pa_mod, "get_actor", lambda request, channel="ui": {"sub": "u1", "role": "system"})
    monkeypatch.setattr(pa_mod, "get_channel", lambda request, default="ui": "ui")

    # Ensure execute_action isn't called because approval gate should block first
    monkeypatch.setattr(pa_mod, "execute_action", lambda *a, **k: {"ok": True})

    app = create_app()
    client = TestClient(app)

    r = client.post(f"/pending_actions/{pending_id}/execute?dry_run=false&channel=ui")
    assert r.status_code == 409

    body = r.json()
    # Standard error shape
    assert "error" in body
    assert "requires approval" in (body["error"].get("message") or "").lower()
    assert "request_id" in body
