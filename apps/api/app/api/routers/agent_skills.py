from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Query

from ...agent_skills import build_agent_skill_catalog
from ...db import all

router = APIRouter()


@router.get("/")
def get_agent_skills(topic: str = Query("commodities"), limit: int = Query(20, ge=1, le=100)):
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
    return build_agent_skill_catalog(rows)
