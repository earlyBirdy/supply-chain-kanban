from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from ..db import q
from ..policy_store import load_policy


def cleanup_idempotency(ttl_hours: int | None = None) -> Dict[str, Any]:
    policy = load_policy() or {}
    if ttl_hours is None:
        ttl_hours = int(((policy.get("idempotency_policy") or {}).get("ttl_hours") or 24))
    cutoff = datetime.now(timezone.utc) - timedelta(hours=ttl_hours)

    # Delete expired materializations to allow idempotency key reuse after TTL
    r = q("DELETE FROM materializations WHERE created_at < :cutoff RETURNING materialization_id", cutoff=cutoff)
    deleted = [str(x[0]) for x in r.fetchall()] if r else []

    return {
        "ok": True,
        "ttl_hours": ttl_hours,
        "cutoff": cutoff.isoformat(),
        "deleted_materializations": deleted,
        "deleted_count": len(deleted),
    }
