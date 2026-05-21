from __future__ import annotations

import fnmatch
import re
from typing import Any, Dict, List, Tuple, Union

from fastapi import Request

from .policy_store import load_policy, policy_revision
from .request_context import get_request_id


def _truncate(s: Any, n: int) -> str:
    try:
        t = str(s)
    except Exception:
        t = ""
    if n <= 0:
        return t
    return t if len(t) <= n else t[: n - 1] + "…"


PatternSpec = Union[str, Dict[str, str]]  # e.g. "x-b3-*", "re:^x-.*$", {"glob":"x-b3-*"}, {"regex":"^x-.*$"}


def _normalize_pattern_list(raw: Any) -> List[PatternSpec]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        return []
    out: List[PatternSpec] = []
    for item in raw:
        if isinstance(item, str):
            s = item.strip()
            if s:
                out.append(s)
        elif isinstance(item, dict):
            if "glob" in item and isinstance(item.get("glob"), str) and item.get("glob").strip():
                out.append({"glob": item.get("glob").strip()})
            elif "regex" in item and isinstance(item.get("regex"), str) and item.get("regex").strip():
                out.append({"regex": item.get("regex").strip()})
    return out


def _compile_patterns(specs: List[PatternSpec]) -> List[Tuple[str, Union[str, re.Pattern]]]:
    """Compile pattern specs into matchers.

    Returns list of tuples: ("glob", pattern_str_lower) or ("regex", compiled_regex).
    """
    compiled: List[Tuple[str, Union[str, re.Pattern]]] = []
    for spec in specs:
        if isinstance(spec, str):
            s = spec.strip()
            if not s:
                continue
            sl = s.lower()
            if sl.startswith("re:") or sl.startswith("regex:"):
                pat = s.split(":", 1)[1]
                try:
                    compiled.append(("regex", re.compile(pat, flags=re.IGNORECASE)))
                except Exception:
                    continue
            else:
                compiled.append(("glob", sl))
        elif isinstance(spec, dict):
            if "regex" in spec:
                pat = str(spec.get("regex"))
                try:
                    compiled.append(("regex", re.compile(pat, flags=re.IGNORECASE)))
                except Exception:
                    continue
            elif "glob" in spec:
                compiled.append(("glob", str(spec.get("glob")).lower()))
    return compiled


def _match_any(name_lower: str, compiled: List[Tuple[str, Union[str, re.Pattern]]]) -> bool:
    for kind, pat in compiled:
        if kind == "glob":
            if fnmatch.fnmatch(name_lower, str(pat)):
                return True
        elif kind == "regex":
            try:
                if isinstance(pat, re.Pattern) and pat.search(name_lower):
                    return True
            except Exception:
                continue
    return False


def _sanitize_request(request: Request, policy: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize request data for SIEM/ELK.

    - headers: allowlist + redact (supports glob + regex patterns)
    - query: allowlist keys only
    - hard denylist prevents accidental leakage even if patterns are too broad
    """
    audit_cfg = (policy or {}).get("audit") or {}
    req_cfg = audit_cfg.get("request") or {}

    allow_specs = _normalize_pattern_list(req_cfg.get("allowlist_headers"))
    redact_specs = _normalize_pattern_list(req_cfg.get("redact_headers"))
    allow_compiled = _compile_patterns(allow_specs)
    redact_compiled = _compile_patterns(redact_specs)

    deny_headers = {"authorization", "cookie", "set-cookie", "proxy-authorization"}

    allow_query = [str(x) for x in (req_cfg.get("allowlist_query") or []) if isinstance(x, str)]
    hmax = int(req_cfg.get("header_value_max_len") or 256)
    qmax = int(req_cfg.get("query_value_max_len") or 256)

    headers_out: Dict[str, str] = {}
    if allow_compiled or redact_compiled:
        for k, v in request.headers.items():
            kl = k.lower()
            if kl in deny_headers:
                continue

            if redact_compiled and _match_any(kl, redact_compiled):
                headers_out[kl] = "REDACTED"
                continue

            if allow_compiled and _match_any(kl, allow_compiled):
                headers_out[kl] = _truncate(v, hmax)

    query_out: Dict[str, str] = {}
    if allow_query:
        for k in allow_query:
            if k in request.query_params:
                query_out[k] = _truncate(request.query_params.get(k), qmax)

    return {
        "path": str(request.url.path),
        "method": str(request.method),
        "query": query_out,
        "headers": headers_out,
    }


def build_audit_envelope(
    *,
    actor: Dict[str, Any] | None,
    request: Request | None,
    request_path: str | None = None,
    request_method: str | None = None,
    materialization_id: str | None = None,
) -> Dict[str, Any]:
    """Create a normalized audit envelope.

    Stored under payload['_audit'] for every agent_actions row.
    """
    p = load_policy()
    rev = policy_revision(p)

    if request is not None:
        req_obj = _sanitize_request(request, p)
    else:
        req_obj = {"path": str(request_path or ""), "method": str(request_method or ""), "query": {}, "headers": {}}

    rid = get_request_id()
    return {
        "actor": actor or {},
        "request": req_obj,
        "policy_revision": rev,
        "materialization_id": str(materialization_id or ""),
        "request_id": rid,
        "correlation_id": rid,
    }


def with_audit(
    payload: Dict[str, Any] | None,
    *,
    actor: Dict[str, Any] | None,
    request: Request | None,
    materialization_id: str | None = None,
    request_path: str | None = None,
    request_method: str | None = None,
) -> Dict[str, Any]:
    """Return a copy of payload with a normalized '_audit' envelope."""
    base = dict(payload or {})
    base["_audit"] = build_audit_envelope(
        actor=actor,
        request=request,
        request_path=request_path,
        request_method=request_method,
        materialization_id=materialization_id,
    )
    return base
