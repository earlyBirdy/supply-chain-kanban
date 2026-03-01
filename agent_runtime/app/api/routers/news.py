from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...config import DEV_MODE
from ...db import all, one, q
from ...auth import get_actor, get_channel
from ...audit import with_audit

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
    channel = get_channel(request, default="system")
    actor = get_actor(request, channel=channel)

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

    channel = get_channel(request, default="ui")
    actor = get_actor(request, channel=channel)

    now = datetime.now(timezone.utc)

    samples = [
        {
            "topic": topic,
            "source": "Channel Checks (demo)",
            "title": "DRAM spot prices soften as 'leakage' inventory hits secondary channels",
            "url": f"demo://memory/{topic}/dram-leakage",
            "published_at": now,
            "summary": "Multiple channel checks cite excess server DRAM inventory leaking into spot markets, pressuring prices.",
            "severity": 78,
            "signals": {"category": "dram", "theme": "leakage", "market": "spot", "magnitude_hint": "soften"},
        },
        {
            "topic": topic,
            "source": "Industry Brief (demo)",
            "title": "NAND flash price cuts rumored as AI DC demand shifts to HBM priority",
            "url": f"demo://memory/{topic}/nand-price-cut",
            "published_at": now,
            "summary": "Brief suggests suppliers may discount NAND contracts amid inventory overhang; AI spend focuses on HBM stacks.",
            "severity": 72,
            "signals": {"category": "nand", "theme": "discount", "market": "contract", "magnitude_hint": "cuts"},
        },
        {
            "topic": topic,
            "source": "Hyperscaler Note (demo)",
            "title": "AI data center procurement flags memory lead-time volatility in next quarter",
            "url": f"demo://memory/{topic}/leadtime-volatility",
            "published_at": now,
            "summary": "Procurement note highlights increased volatility and recommends buffer/hedge review for server DRAM/NAND.",
            "severity": 66,
            "signals": {"category": "server_memory", "theme": "volatility", "window": "next_quarter"},
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
