from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...config import DEV_MODE
from ...commodity_arrangements import build_arrangement_packet
from ...db import all, one, q

router = APIRouter()

class NewsItemIn(BaseModel):
    topic: str = Field("memory", description="Topic namespace, e.g. memory | logistics | energy")
    source: str | None = Field(None, description="Publisher/source")
    title: str = Field(..., description="Headline")
    url: str = Field(..., description="Canonical URL (used for dedupe)")
    published_at: datetime | None = Field(None, description="UTC timestamp when article was published")
    summary: str | None = Field(None, description="Model summary (short)")
    severity: int = Field(0, ge=0, le=100, description="Heuristic severity score 0..100")
    signals: Dict[str, Any] = Field(default_factory=dict, description="Structured extraction: vendor, product, magnitude...")
    raw: Dict[str, Any] = Field(default_factory=dict, description="Raw metadata/snippet")

class NewsIngestRequest(BaseModel):
    items: List[NewsItemIn] = Field(default_factory=list)


@router.get("/source-catalog")
def commodity_news_source_catalog(topic: str = "commodities"):
    """Explain dynamic source coverage used by commodity arrangements.

    This is a UI contract: raw sources can be RSS/API/manual research today,
    but the dashboard shows source confidence and business mapping rather than
    a headline-first feed.
    """

    rows: List[Dict[str, Any]] = []
    try:
        rows = all(
            """SELECT source, COUNT(*) AS item_count, MAX(fetched_at) AS latest_fetched_at, AVG(severity) AS avg_severity
                 FROM news_items
                 WHERE topic=:topic
                 GROUP BY source
                 ORDER BY item_count DESC, latest_fetched_at DESC
                 LIMIT 12""",
            topic=str(topic),
        )
    except Exception:
        rows = []
    if not rows:
        rows = [
            {"source": "Commodity Desk (demo)", "item_count": 1, "latest_fetched_at": None, "avg_severity": 84},
            {"source": "Channel Checks (demo)", "item_count": 1, "latest_fetched_at": None, "avg_severity": 78},
            {"source": "Logistics Brief (demo)", "item_count": 1, "latest_fetched_at": None, "avg_severity": 71},
        ]
    return {
        "ok": True,
        "topic": topic,
        "title": "Dynamic live news sources for commodity arrangement",
        "source_types": ["RSS", "market API", "supplier portal note", "manual analyst research", "ERP/MES exception context"],
        "mapping_contract": [
            "publisher/source",
            "published time",
            "source confidence",
            "affected commodity/material",
            "price range",
            "BOM exposure",
            "recommended arrangement",
            "approval owner",
            "evidence hash",
        ],
        "refresh_policy": "ingest/check-now updates news items, Commodity Arrangement Desk, Commodity Trend Radar, and dynamic autoresearch queue",
        "sources": rows,
    }

@router.get("/items")
def list_news_items(
    topic: str | None = None,
    limit: int = 50,
):
    limit = max(1, min(int(limit), 200))
    if topic:
        rows = all(
            """SELECT item_id, fetched_at, published_at, topic, source, title, url, summary, severity, signals, case_id
                 FROM news_items
                 WHERE topic=:topic
                 ORDER BY fetched_at DESC
                 LIMIT :lim""",
            topic=str(topic),
            lim=limit,
        )
    else:
        rows = all(
            """SELECT item_id, fetched_at, published_at, topic, source, title, url, summary, severity, signals, case_id
                 FROM news_items
                 ORDER BY fetched_at DESC
                 LIMIT :lim""",
            lim=limit,
        )
    return {"ok": True, "items": rows}

@router.get("/alerts")
def list_news_alerts(topic: str | None = None, limit: int = 50):
    limit = max(1, min(int(limit), 200))
    if topic:
        rows = all(
            """SELECT alert_id, ts, topic, severity, item_id, case_id, status, note
                 FROM news_alerts
                 WHERE topic=:topic
                 ORDER BY ts DESC
                 LIMIT :lim""",
            topic=str(topic),
            lim=limit,
        )
    else:
        rows = all(
            """SELECT alert_id, ts, topic, severity, item_id, case_id, status, note
                 FROM news_alerts
                 ORDER BY ts DESC
                 LIMIT :lim""",
            lim=limit,
        )
    return {"ok": True, "alerts": rows}

@router.get("/commodity-arrangements")
def list_commodity_arrangements(topic: str = "commodities", limit: int = 20):
    """Return UX-ready commodity arrangement cards from current news signals.

    This endpoint intentionally returns business decision cards rather than a raw
    headline feed. If the DB is not available or has no rows, deterministic demo
    cards are returned so the dashboard remains useful in local/HF demos.
    """

    limit = max(1, min(int(limit), 50))
    rows: List[Dict[str, Any]] = []
    try:
        rows = all(
            """SELECT item_id, fetched_at, published_at, topic, source, title, url, summary, severity, signals, case_id
                 FROM news_items
                 WHERE topic=:topic
                 ORDER BY severity DESC, fetched_at DESC
                 LIMIT :lim""",
            topic=str(topic),
            lim=limit,
        )
    except Exception:
        rows = []
    return build_arrangement_packet(rows)

@router.post("/ingest")
def ingest_news(request: Request, req: NewsIngestRequest):
    """Ingest deduped news items from news_monitor.

    Dedupe policy: url is UNIQUE.
    """

    inserted = 0
    skipped = 0

    for it in req.items:
        try:
            q(
                """INSERT INTO news_items(topic, source, title, url, published_at, summary, severity, signals, raw)
                     VALUES(:topic, :source, :title, :url, :published_at, :summary, :severity, :signals::jsonb, :raw::jsonb)
                     ON CONFLICT(url) DO NOTHING""",
                topic=str(it.topic or "general"),
                source=it.source,
                title=str(it.title),
                url=str(it.url),
                published_at=it.published_at,
                summary=it.summary,
                severity=int(it.severity or 0),
                signals=json.dumps(it.signals or {}, default=str),
                raw=json.dumps(it.raw or {}, default=str),
            )
            inserted += 1
        except Exception:
            # In demo mode, keep ingestion resilient.
            skipped += 1

    return {"ok": True, "inserted": inserted, "skipped": skipped}

@router.post("/check-now")
def check_now(request: Request, topic: str = "memory"):
    """DEV_MODE helper: insert a small deterministic sample burst."""
    if not DEV_MODE:
        raise HTTPException(status_code=403, detail="news/check-now is disabled (DEV_MODE=0)")

    now = datetime.now(timezone.utc)

    samples = [
        {
            "topic": topic,
            "source": "Commodity Desk (demo)",
            "title": "LFP battery material shipment delay raises allocation risk for EV launch builds",
            "url": f"demo://commodities/{topic}/lfp-delay",
            "published_at": now,
            "summary": "Demo live-news signal: port congestion and supplier confirmation gaps may require battery allocation rebalance and alternate routing.",
            "severity": 84,
            "signals": {"category": "lfp_battery", "theme": "delay", "arrangement": "rebalance_allocation", "source_confidence": 0.78, "time_period": "current week", "price_range": "freight premium +4% to +9%", "bom_exposure": ["battery_cells_lfp", "EV launch packs"], "approval_owner": "ops_lead"},
        },
        {
            "topic": topic,
            "source": "Channel Checks (demo)",
            "title": "DRAM spot prices soften as leakage inventory hits secondary channels",
            "url": f"demo://commodities/{topic}/dram-leakage",
            "published_at": now,
            "summary": "Multiple channel checks cite excess server DRAM inventory leaking into spot markets, creating a buy-timing review opportunity.",
            "severity": 78,
            "signals": {"category": "dram", "theme": "price", "market": "spot", "arrangement": "review_buy_timing", "source_confidence": 0.74, "time_period": "last 30 days", "price_range": "spot -3% to -8%, contract watch", "bom_exposure": ["server_dram", "edge_ai_memory"], "approval_owner": "commodity_manager"},
        },
        {
            "topic": topic,
            "source": "Logistics Brief (demo)",
            "title": "Copper and industrial components face lead-time volatility on regional freight disruption",
            "url": f"demo://commodities/{topic}/copper-freight-volatility",
            "published_at": now,
            "summary": "Freight disruption may affect inbound ETA for constrained components; AI should compare buffer stock, alternate supplier, and expedite cost.",
            "severity": 71,
            "signals": {"category": "copper_components", "theme": "lead_time", "arrangement": "buffer_or_expedite", "source_confidence": 0.71, "time_period": "current quarter", "price_range": "expedite cost +6% to +15%", "bom_exposure": ["industrial_components", "power_harness"], "approval_owner": "supply_chain_manager"},
        },
    ]

    inserted = 0
    for s in samples:
        q(
            """INSERT INTO news_items(topic, source, title, url, published_at, summary, severity, signals, raw)
                 VALUES(:topic, :source, :title, :url, :published_at, :summary, :severity, :signals::jsonb, :raw::jsonb)
                 ON CONFLICT(url) DO NOTHING""",
            topic=str(s["topic"]),
            source=s["source"],
            title=s["title"],
            url=s["url"],
            published_at=s["published_at"],
            summary=s["summary"],
            severity=int(s["severity"]),
            signals=json.dumps(s.get("signals") or {}, default=str),
            raw=json.dumps({"demo": True}, default=str),
        )
        inserted += 1

    # Create a lightweight alert row for the top item
    top = one(
        "SELECT item_id, severity FROM news_items WHERE topic=:t ORDER BY severity DESC, fetched_at DESC LIMIT 1",
        t=str(topic),
    )
    if top:
        q(
            """INSERT INTO news_alerts(topic, severity, item_id, status, note)
                 VALUES(:topic, :severity, :item_id, 'open', :note)""",
            topic=str(topic),
            severity=int(top["severity"] or 0),
            item_id=str(top["item_id"]),
            note="demo burst inserted via /news/check-now",
        )

    return {"ok": True, "inserted": inserted}
