from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException, Query, Request

from ...jobs.cleanup import cleanup_idempotency
from ...policy_store import load_policy

router = APIRouter()

def _is_dev() -> bool:
    env = (os.getenv("APP_ENV", "") or "").lower()
    dev_mode = os.getenv("DEV_MODE", "0") in ("1","true","True")
    return dev_mode or env in ("dev","development","local")


@router.post("/cleanup")
def cleanup(request: Request, ttl_hours: int | None = Query(default=None, description="Override TTL hours for this run (dev only).")):
    if not _is_dev():
        raise HTTPException(status_code=403, detail="maintenance endpoints only enabled in dev mode")
    return cleanup_idempotency(ttl_hours=ttl_hours)


@router.get("/status")
def status():
    policy = load_policy() or {}
    return {
        "ok": True,
        "idempotency_policy": (policy.get("idempotency_policy") or {}),
    }
