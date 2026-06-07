from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Query

from ...commodity_trend_radar import build_commodity_trend_radar
from ...db import all

router = APIRouter()


@router.get("/")
def get_commodity_trend_radar(topic: str = Query("commodities"), limit: int = Query(20, ge=1, le=100)):
    """Early-warning commodity trend radar for IT and defense supply chains.

    The radar is static-safe for demos, but it becomes dynamic when commodity
    news rows exist: latest matching news boosts the related commodity, updates
    price/BOM summary, and refreshes the proof hash.
    """

    rows: List[Dict[str, Any]] = []
    try:
        rows = all(
            """SELECT item_id, fetched_at, published_at, topic, source, title, url, summary, severity, signals, case_id
                 FROM news_items
                 WHERE topic=:topic
                 ORDER BY severity DESC, fetched_at DESC
                 LIMIT :lim""",
            topic=str(topic),
            lim=int(limit),
        )
    except Exception:
        rows = []
    return build_commodity_trend_radar(rows)
