from sqlalchemy import create_engine, text
from .config import DB_URL

engine = create_engine(DB_URL, pool_pre_ping=True)

def q(sql: str, **params):
    with engine.begin() as conn:
        return conn.execute(text(sql), params)

def one(sql: str, **params):
    r = q(sql, **params).fetchone()
    return dict(r._mapping) if r else None

def all(sql: str, **params):
    return [dict(x._mapping) for x in q(sql, **params).fetchall()]


import time

def wait_for_db(max_seconds: int = 60, sleep_seconds: float = 2.0) -> None:
    """Block until DB is reachable, or raise after max_seconds."""
    deadline = time.time() + max_seconds
    last_err = None
    while time.time() < deadline:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception as e:
            last_err = e
            time.sleep(sleep_seconds)
    raise RuntimeError(f"DB not reachable after {max_seconds}s: {last_err}")
