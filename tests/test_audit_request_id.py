from __future__ import annotations

from app.audit import build_audit_envelope
from app.request_context import set_request_id, reset_request_id


def test_audit_envelope_includes_request_id() -> None:
    tok = set_request_id("abc-req")
    try:
        env = build_audit_envelope(actor={"sub": "u"}, request=None, request_path="/x", request_method="GET")
    finally:
        reset_request_id(tok)
    assert env.get("request_id") == "abc-req"
    assert env.get("correlation_id") == "abc-req"
