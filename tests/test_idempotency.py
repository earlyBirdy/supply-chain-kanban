from __future__ import annotations

import json

import pytest

import app.idempotency as idem


def test_request_hash_is_stable_for_same_object() -> None:
    obj = {"b": 2, "a": 1, "nested": {"z": 9, "y": 8}}
    h1 = idem.request_hash(obj)
    h2 = idem.request_hash({"nested": {"y": 8, "z": 9}, "a": 1, "b": 2})
    assert h1 == h2


def test_check_or_replay_replays_on_match(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_one(sql: str, **params):
        assert "idempotency_keys" in sql
        return {"key": params["k"], "request_hash": "abc", "response": {"ok": True, "x": 1}}

    monkeypatch.setattr(idem, "_one", fake_one)
    replayed, resp, conflict = idem.check_or_replay(key="k1", req_hash="abc")
    assert replayed is True
    assert resp == {"ok": True, "x": 1}
    assert conflict is None


def test_check_or_replay_conflicts_on_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_one(sql: str, **params):
        return {"key": params["k"], "request_hash": "abc", "response": {"ok": True}}

    monkeypatch.setattr(idem, "_one", fake_one)
    replayed, resp, conflict = idem.check_or_replay(key="k1", req_hash="DIFF")
    assert replayed is False
    assert resp is None
    assert "different request" in (conflict or "").lower()


def test_store_inserts_jsonb(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {}

    def fake_q(sql: str, **params):
        calls["sql"] = sql
        calls["params"] = params
        return None

    monkeypatch.setattr(idem, "_q", fake_q)
    idem.store("k1", "h1", {"ok": True, "n": 3})
    assert "INSERT INTO idempotency_keys" in calls["sql"]
    assert calls["params"]["k"] == "k1"
    assert calls["params"]["h"] == "h1"
    # response stored as canonical JSON string
    stored = json.loads(calls["params"]["r"])
    assert stored == {"n": 3, "ok": True}
