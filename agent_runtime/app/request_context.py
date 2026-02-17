from __future__ import annotations

import contextvars
from typing import Optional

_REQUEST_ID: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

def get_request_id() -> str:
    return _REQUEST_ID.get()

def set_request_id(request_id: str) -> contextvars.Token:
    return _REQUEST_ID.set(request_id or "-")

def reset_request_id(token: contextvars.Token) -> None:
    try:
        _REQUEST_ID.reset(token)
    except Exception:
        # best-effort; never throw
        pass
