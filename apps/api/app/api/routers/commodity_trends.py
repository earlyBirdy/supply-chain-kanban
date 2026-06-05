from __future__ import annotations

from fastapi import APIRouter

from ...commodity_trend_radar import build_commodity_trend_radar

router = APIRouter()


@router.get("/")
def get_commodity_trend_radar():
    """Early-warning commodity trend radar for IT and defense supply chains."""
    return build_commodity_trend_radar()
