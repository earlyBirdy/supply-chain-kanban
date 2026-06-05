from __future__ import annotations

from fastapi.testclient import TestClient

from app.api_main import create_app
from app.business_submission import build_business_submission_snapshot


def test_business_submission_snapshot_has_real_business_components() -> None:
    data = build_business_submission_snapshot()

    assert data["ok"] is True
    assert "continuous_agent" in data
    assert "Read ERP/MES/WMS mock data." in data["continuous_agent"]["steps"]
    assert "Read news and market risk signals." in data["continuous_agent"]["steps"]
    assert data["agent_decision_log"]
    assert data["evidence_log"]
    assert data["human_approval_gate"]["safe_default"] == "Read-only monitoring; no autonomous external writeback without approval."
    assert "Pilot package" in data["business_readiness"]["pricing_model"]
    assert "prompt_id" in data["gemini_trace_stub"]["usage_fields_for_submission"]
    assert len(data["agent_decision_log"][0]["decision_hash"]) == 64
    assert len(data["evidence_log"][0]["receipt_hash"]) == 64


def test_business_submission_api_endpoint_is_available_without_db() -> None:
    client = TestClient(create_app())

    response = client.get("/business_submission/")

    assert response.status_code == 200
    body = response.json()
    assert body["submission_title"].startswith("Supply Chain Kanban AI")
    assert body["continuous_agent"]["mode"] == "demo_continuous_loop"
    assert body["human_approval_gate"]["writeback_behavior"].startswith("Only approved actions")


def test_business_submission_api_mirror_and_run_endpoint() -> None:
    client = TestClient(create_app())

    mirror = client.get("/api/business_submission/")
    run = client.post("/business_submission/run")

    assert mirror.status_code == 200
    assert run.status_code == 200
    assert run.json()["run_mode"] == "on_demand_demo_cycle"
