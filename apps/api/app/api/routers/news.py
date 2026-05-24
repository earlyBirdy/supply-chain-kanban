from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...config import DEV_MODE
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
            "signals": {"category": "lfp_battery", "theme": "delay", "arrangement": "rebalance_allocation"},
        },
        {
            "topic": topic,
            "source": "Channel Checks (demo)",
            "title": "DRAM spot prices soften as leakage inventory hits secondary channels",
            "url": f"demo://commodities/{topic}/dram-leakage",
            "published_at": now,
            "summary": "Multiple channel checks cite excess server DRAM inventory leaking into spot markets, creating a buy-timing review opportunity.",
            "severity": 78,
            "signals": {"category": "dram", "theme": "price", "market": "spot", "arrangement": "review_buy_timing"},
        },
        {
            "topic": topic,
            "source": "Logistics Brief (demo)",
            "title": "Copper and industrial components face lead-time volatility on regional freight disruption",
            "url": f"demo://commodities/{topic}/copper-freight-volatility",
            "published_at": now,
            "summary": "Freight disruption may affect inbound ETA for constrained components; AI should compare buffer stock, alternate supplier, and expedite cost.",
            "severity": 71,
            "signals": {"category": "copper_components", "theme": "lead_time", "arrangement": "buffer_or_expedite"},
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
