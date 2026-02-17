from __future__ import annotations

import os
import time
from datetime import datetime, timezone

from .cleanup import cleanup_idempotency
from ..policy_store import load_policy


def main():
    policy = load_policy() or {}
    ttl_hours = int(((policy.get("idempotency_policy") or {}).get("ttl_hours") or os.getenv("IDEMPOTENCY_TTL_HOURS") or 24))
    interval = int(((policy.get("idempotency_policy") or {}).get("cleanup_interval_seconds") or os.getenv("IDEMPOTENCY_CLEANUP_INTERVAL") or 3600))

    while True:
        try:
            res = cleanup_idempotency(ttl_hours=ttl_hours)
            print(f"[cleanup_loop] {datetime.now(timezone.utc).isoformat()} deleted={res.get('deleted_count')}")
        except Exception as e:
            print(f"[cleanup_loop] error: {e}")
        time.sleep(interval)


if __name__ == "__main__":
    main()
