from __future__ import annotations

import time
from typing import Any, Callable, Optional, Tuple

from .config import DB_URL

_engine = None
_text = None

def _ensure_engine():
    global _engine, _text
    if _engine is not None and _text is not None:
        return
    try:
        from sqlalchemy import create_engine, text  # type: ignore
    except Exception as e:  # pragma: no cover
        # Allow import-time to succeed in minimal test environments.
        raise RuntimeError("SQLAlchemy is required to use the DB layer. Install agent_runtime/requirements.txt") from e
    _engine = create_engine(DB_URL, pool_pre_ping=True)
    _text = text

def q(sql: str, **params):
    _ensure_engine()
    assert _engine is not None and _text is not None
    with _engine.begin() as conn:
        return conn.execute(_text(sql), params)

def one(sql: str, **params):
    r = q(sql, **params).fetchone()
    return dict(r._mapping) if r else None

def all(sql: str, **params):
    return [dict(x._mapping) for x in q(sql, **params).fetchall()]

def wait_for_db(max_seconds: int = 60, sleep_seconds: float = 2.0) -> None:
    """Block until DB is reachable, or raise after max_seconds."""
    deadline = time.time() + max_seconds
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            _ensure_engine()
            assert _engine is not None and _text is not None
            with _engine.connect() as conn:
                conn.execute(_text("SELECT 1"))
            return
        except Exception as e:  # pragma: no cover
            last_err = e
            time.sleep(sleep_seconds)
    raise RuntimeError(f"DB not reachable after {max_seconds}s: {last_err}")
