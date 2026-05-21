from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional, Callable


# Lazy DB callables so unit tests don't require SQLAlchemy installed.
_one: Callable[..., Any] | None = None
_q: Callable[..., Any] | None = None


def _get_one() -> Callable[..., Any]:
    global _one
    if _one is None:
        from .db import one as _one_fn
        _one = _one_fn
    return _one


def _get_q() -> Callable[..., Any]:
    global _q
    if _q is None:
        from .db import q as _q_fn
        _q = _q_fn
    return _q


def canonical_json(obj: Any) -> str:
    """Stable JSON for hashing (sort keys, no whitespace)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def request_hash(obj: Any) -> str:
    """SHA-256 hash of canonical JSON representation."""
    s = canonical_json(obj).encode("utf-8")
    return hashlib.sha256(s).hexdigest()


def get_existing(key: str) -> Optional[Dict[str, Any]]:
    one = _get_one()
    row = one("SELECT key, request_hash, response FROM idempotency_keys WHERE key=:k", k=key)
    return row


def store(key: str, req_hash: str, response_obj: Any) -> None:
    q = _get_q()
    payload = canonical_json(response_obj)
    q(
        "INSERT INTO idempotency_keys(key, request_hash, response) VALUES(:k, :h, CAST(:r AS JSONB))",
        k=key,
        h=req_hash,
        r=payload,
    )


def check_or_replay(*, key: str, req_hash: str) -> tuple[bool, Optional[Any], Optional[str]]:
    """Return (replayed, response, conflict_reason)."""
    row = get_existing(key)
    if not row:
        return (False, None, None)
    if str(row.get("request_hash")) != str(req_hash):
        return (False, None, "Idempotency-Key reuse with different request payload")
    return (True, row.get("response"), None)
