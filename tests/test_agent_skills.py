from __future__ import annotations

from fastapi.testclient import TestClient

from app.agent_skills import build_agent_skill_catalog
from app.api_main import create_app


def test_agent_skill_catalog_exposes_governed_skills_and_autoresearch() -> None:
    data = build_agent_skill_catalog()

    assert data["ok"] is True
    assert "simple" in data["simple_ui_rule"].lower()
    skill_ids = {row["skill_id"] for row in data["skills"]}
    assert "source_map_erp_mes" in skill_ids
    assert "commodity_news_to_risk" in skill_ids
    assert "build_decision_packet" in skill_ids
    assert all(len(row["skill_hash"]) == 64 for row in data["skills"])
    extension_ids = {row["extension_id"] for row in data["autoresearch_extensions"]}
    assert "commodity_arrangement_research" in extension_ids
    assert "live_news_arrangement_research" in extension_ids
    assert "commodity_arrangement_card" in data["ux_contract"]
    assert "open commodity arrangement card" in data["operator_quick_actions"]
    assert "require human approval" in " ".join(data["operating_loop"])


def test_agent_skills_api_and_api_mirror_are_available_without_db() -> None:
    client = TestClient(create_app())

    direct = client.get("/agent_skills/")
    mirror = client.get("/api/agent_skills/")

    assert direct.status_code == 200
    assert mirror.status_code == 200
    body = direct.json()
    assert body["title"] == "Agent Skills + Autoresearch Extension Catalog"
    assert body["skills"][0]["ux_surface"]


def test_agent_skills_dynamic_autoresearch_queue_uses_live_signals() -> None:
    data = build_agent_skill_catalog([
        {"topic": "commodities", "source": "demo", "title": "DRAM price moves", "severity": 78, "signals": {"category": "dram"}}
    ])

    dynamic = data["dynamic_auto_research"]
    assert dynamic["live_signal_count"] == 1
    assert dynamic["queue"][0]["queue_id"] == "dynamic_live_news_to_arrangement"
    assert "ERP/MES writeback still requires approval" in dynamic["human_stop_rule"]
