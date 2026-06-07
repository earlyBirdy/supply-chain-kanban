from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

from .commodity_trend_radar import build_commodity_trend_radar


def _hash_payload(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _normalize_signal(value: Any) -> Dict[str, Any]:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return value if isinstance(value, dict) else {}


def _demo_news_signals() -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "topic": "commodities",
            "source": "Commodity Desk (demo)",
            "title": "LFP battery material shipment delay raises allocation risk for EV launch builds",
            "published_at": now,
            "summary": "Port congestion and supplier confirmation gaps may require battery allocation rebalance and alternate routing.",
            "severity": 84,
            "signals": {
                "category": "lfp_battery",
                "arrangement": "rebalance_allocation",
                "source_confidence": 0.78,
                "time_period": "current week",
                "price_range": "freight premium +4% to +9%",
                "bom_exposure": ["battery_cells_lfp", "EV launch packs"],
                "approval_owner": "ops_lead",
            },
        },
        {
            "topic": "commodities",
            "source": "Channel Checks (demo)",
            "title": "DRAM spot prices soften as leakage inventory hits secondary channels",
            "published_at": now,
            "summary": "Channel checks show server DRAM leakage inventory; buyer should review buy timing before new PO release.",
            "severity": 78,
            "signals": {
                "category": "dram",
                "arrangement": "review_buy_timing",
                "source_confidence": 0.74,
                "time_period": "last 30 days",
                "price_range": "spot -3% to -8%, contract watch",
                "bom_exposure": ["server_dram", "edge_ai_memory"],
                "approval_owner": "commodity_manager",
            },
        },
        {
            "topic": "commodities",
            "source": "Logistics Brief (demo)",
            "title": "Copper and industrial components face lead-time volatility on regional freight disruption",
            "published_at": now,
            "summary": "Freight disruption may affect inbound ETA; compare buffer stock, alternate supplier, and expedite cost.",
            "severity": 71,
            "signals": {
                "category": "copper_components",
                "arrangement": "buffer_or_expedite",
                "source_confidence": 0.71,
                "time_period": "current quarter",
                "price_range": "expedite cost +6% to +15%",
                "bom_exposure": ["industrial_components", "power_harness"],
                "approval_owner": "supply_chain_manager",
            },
        },
    ]


def build_arrangement_packet(news_items: Iterable[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """Build UX-ready commodity arrangement cards from news and radar signals.

    The point is to avoid a headline feed. Each card has a commodity/material focus,
    business impact, recommended action, human approval owner, ERP/MES fields to
    check, and a proof hash that can later be anchored.
    """

    radar = build_commodity_trend_radar()
    radar_by_key = {
        row["commodity_id"]: row
        for row in radar.get("watchlist", [])
    }
    rows: List[Dict[str, Any]] = []
    source_items = list(news_items or []) or _demo_news_signals()

    for index, item in enumerate(source_items):
        signals = _normalize_signal(item.get("signals"))
        category = str(signals.get("category") or item.get("topic") or "commodity")
        radar_row = radar_by_key.get("memory_hbm_dram_nand") if category in {"dram", "memory", "server_dram"} else None
        price_range = signals.get("price_range") or (radar_row or {}).get("price_range") or "price watch"
        bom_exposure = signals.get("bom_exposure") or [(radar_row or {}).get("bom_exposure_summary") or "BOM exposure pending"]
        if isinstance(bom_exposure, str):
            bom_exposure = [bom_exposure]
        approval_owner = signals.get("approval_owner") or (radar_row or {}).get("arrangement_playbook", {}).get("approval_owner") or "supply_chain_leader"
        arrangement = signals.get("arrangement") or (radar_row or {}).get("arrangement_options", ["review_buy_timing"])[0]
        severity = int(item.get("severity") or ((radar_row or {}).get("early_warning_score") or 70))
        source_confidence = float(signals.get("source_confidence") or (radar_row or {}).get("source_confidence") or 0.7)
        packet = {
            "arrangement_id": f"arr-{category}-{index + 1}",
            "commodity_or_material": category,
            "headline": item.get("title") or "Commodity signal",
            "source": item.get("source") or "demo signal",
            "time_period": signals.get("time_period") or (radar_row or {}).get("time_period") or "current review window",
            "severity": severity,
            "source_confidence": source_confidence,
            "price_range": price_range,
            "bom_exposure": bom_exposure,
            "recommended_arrangement": arrangement,
            "business_action": _business_action(arrangement),
            "approval_owner": approval_owner,
            "erp_mes_fields_to_check": [
                "erp_material_ids",
                "open_purchase_orders",
                "work_orders",
                "plant_inventory",
                "supplier_confirmations",
                "quote_validity_window",
            ],
            "simple_ux_copy": (
                f"{category}: {arrangement.replace('_', ' ')}. "
                f"Confidence {round(source_confidence * 100)}%, {price_range}; "
                f"check {', '.join(bom_exposure[:2])} before approval."
            ),
        }
        packet["evidence_hash"] = _hash_payload(packet)
        rows.append(packet)

    rows.sort(key=lambda row: (row["severity"], row["source_confidence"]), reverse=True)
    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "title": "Commodity Arrangement Desk",
        "principle": "Convert live news and radar signals into approval-ready commodity arrangements, not a raw headline list.",
        "cards": rows,
        "simple_ui_cards": [
            "Commodity/material",
            "Recommended arrangement",
            "Source confidence",
            "Price range",
            "BOM exposure",
            "Approval owner",
            "ERP/MES fields to check",
            "Evidence hash",
        ],
        "operator_flow": [
            "review source confidence and time period",
            "map BOM and open PO/WO exposure",
            "compare buy timing, buffer, LTA, alternate supplier, expedite, or allocation options",
            "route human approval",
            "write back only through governed connector",
            "attach EvidenceReceipt / BlockchainAnchor-ready hash",
        ],
    }


def _business_action(arrangement: str) -> str:
    mapping = {
        "review_buy_timing": "Delay, split, or accelerate PO release after commodity manager review.",
        "rebalance_allocation": "Rebalance constrained supply across launch/customer priorities.",
        "buffer_or_expedite": "Compare buffer increase against premium freight and supplier expedite cost.",
        "buffer_or_safety_stock": "Raise safety stock only for exposed programs with approved demand.",
        "long_term_agreement": "Open LTA or allocation reservation review for critical SKUs.",
        "alternate_supplier_or_substitution": "Start engineering and quality review for approved alternates.",
    }
    return mapping.get(arrangement, "Open an S&OP exception and require manager approval before writeback.")
