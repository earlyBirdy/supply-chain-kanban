from __future__ import annotations

from fastapi.testclient import TestClient

from app.api_main import create_app
from app.commodity_trend_radar import build_commodity_trend_radar


def test_commodity_trend_radar_ranks_it_defense_shortage_watchlist() -> None:
    data = build_commodity_trend_radar()

    assert data["ok"] is True
    assert data["prediction_window"] == "coming 6-12 months"
    assert "mainstream shortage headlines" in data["principle"]
    assert data["top_watchlist"][0]["commodity_id"] == "memory_hbm_dram_nand"
    assert data["top_watchlist"][0]["early_warning_score"] >= 90
    assert any(row["commodity_id"] == "advanced_packaging_abf_cowos_interposer" for row in data["watchlist"])
    assert any(row["commodity_id"] == "critical_semiconductor_minerals" for row in data["watchlist"])
    assert any(row["commodity_id"] == "rare_earth_magnets_dy_tb_ndpr" for row in data["watchlist"])
    assert any(row["commodity_id"] == "defense_metals_tungsten_antimony" for row in data["watchlist"])
    assert any(row["commodity_id"] == "high_reliability_passives_mlcc_tantalum" for row in data["watchlist"])
    assert len(data["watchlist"][0]["evidence_hash"]) == 64
    assert data["watchlist"][0]["source_confidence"] > 0.8
    assert "price_range" in data["watchlist"][0]
    assert "bom_exposure_summary" in data["watchlist"][0]
    assert "arrangement_playbook" in data["watchlist"][0]
    assert "erp_material_ids" in data["watchlist"][0]["erp_mes_link_fields"]
    assert "Price range" in data["simple_ui_cards"]
    assert "Next follow-up trigger" in data["simple_ui_cards"]
    assert data["arrangement_summary"][0]["recommended_arrangement"] == "buy_timing_review"
    assert "require human approval" in data["agent_action_loop"]


def test_commodity_trend_radar_api_and_api_mirror_are_available_without_db() -> None:
    client = TestClient(create_app())

    direct = client.get("/commodity_trends/")
    mirror = client.get("/api/commodity_trends/")

    assert direct.status_code == 200
    assert mirror.status_code == 200
    body = direct.json()
    assert body["title"] == "IT / Defense Commodity Trend Radar"
    assert body["top_watchlist"][0]["commodity"].startswith("Memory chips")
    assert "BOM_exposure" in body["scoring_model"]["factors"]
    assert "source_confidence" in body["scoring_model"]["factors"]
    assert "operator_buttons" in body["ux_contract"]
