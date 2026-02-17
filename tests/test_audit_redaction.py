from starlette.requests import Request

from app.audit import _sanitize_request


def _make_request(*, headers: dict[str, str] | None = None, query_string: str = "") -> Request:
    hdrs = []
    for k, v in (headers or {}).items():
        hdrs.append((k.lower().encode("utf-8"), str(v).encode("utf-8")))
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/demo",
        "raw_path": b"/demo",
        "query_string": query_string.encode("utf-8"),
        "headers": hdrs,
        "client": ("testclient", 1234),
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_audit_sanitize_applies_allowlist_and_redaction_and_hard_deny() -> None:
    policy = {
        "audit": {
            "request": {
                "allowlist_headers": ["x-b3-*", {"glob": "x-keep-*"}],
                "redact_headers": ["re:^x-secret-", {"regex": "^x-pii-"}],
                "allowlist_query": ["case_id"],
                "header_value_max_len": 8,
                "query_value_max_len": 8,
            }
        }
    }

    req = _make_request(
        headers={
            "x-b3-traceid": "0123456789abcdef",
            "x-secret-token": "supersecret",
            "x-pii-email": "a@b.com",
            "x-keep-note": "hello world",
            "authorization": "Bearer should_never_leak",
        },
        query_string="case_id=abcdef012345&other=zzz",
    )

    out = _sanitize_request(req, policy)

    # allowlisted header kept + truncated
    assert out["headers"]["x-b3-traceid"].startswith("012345")
    assert len(out["headers"]["x-b3-traceid"]) <= 8

    # redact patterns win over allowlist
    assert out["headers"]["x-secret-token"] == "REDACTED"
    assert out["headers"]["x-pii-email"] == "REDACTED"

    # glob allowlist works
    assert "x-keep-note" in out["headers"]

    # hard denylist always removed
    assert "authorization" not in out["headers"]

    # query allowlist only
    assert out["query"] == {"case_id": "abcdef0…"}
