from __future__ import annotations

from fastapi.testclient import TestClient

from app.api_main import create_app
from app.commodity_arrangements import build_arrangement_packet


def test_commodity_arrangement_packet_turns_news_into_approval_cards() -> None:
    data = build_arrangement_packet([
        {
            "topic": "commodities",
            "source": "Channel Checks",
            "title": "DRAM spot prices soften",
            "summary": "Buy timing signal",
            "severity": 78,
            "signals": {
                "category": "dram",
                "arrangement": "review_buy_timing",
                "source_confidence": 0.74,
                "time_period": "last 30 days",
                "price_range": "spot -3% to -8%",
                "bom_exposure": ["server_dram", "edge_ai_memory"],
                "approval_owner": "commodity_manager",
            },
        }
    ])

    assert data["ok"] is True
    assert data["title"] == "Commodity Arrangement Desk"
    card = data["cards"][0]
    assert card["commodity_or_material"] == "dram"
    assert card["recommended_arrangement"] == "review_buy_timing"
    assert card["approval_owner"] == "commodity_manager"
    assert "erp_material_ids" in card["erp_mes_fields_to_check"]
    assert "server_dram" in card["bom_exposure"]
    assert len(card["evidence_hash"]) == 64
    assert "EvidenceReceipt" in " ".join(data["operator_flow"])


def test_commodity_arrangement_api_and_mirror_are_available_without_db() -> None:
    client = TestClient(create_app())

    direct = client.get("/news/commodity-arrangements?topic=commodities")
    mirror = client.get("/api/news/commodity-arrangements?topic=commodities")

    assert direct.status_code == 200
    assert mirror.status_code == 200
    body = direct.json()
    assert body["cards"]
    assert body["cards"][0]["recommended_arrangement"]
    assert "source confidence" in " ".join(body["simple_ui_cards"]).lower()


def test_commodity_arrangement_cards_include_dynamic_radar_context() -> None:
    data = build_arrangement_packet([
        {
            "topic": "commodities",
            "source": "Channel Checks (test)",
            "title": "DRAM spot prices change",
            "summary": "Buyer should review timing",
            "severity": 78,
            "signals": {"category": "dram", "arrangement": "review_buy_timing", "source_confidence": 0.74, "bom_exposure": ["server_dram"]},
        }
    ])

    card = data["cards"][0]
    assert data["dynamic_behavior"]["news_items_used"] == 1
    assert card["radar_score"] is not None
    assert card["latest_news_confirmation_count"] >= 1
    assert "Commodity Trend Radar" in card["dynamic_refresh_reason"]
