from __future__ import annotations

import base64
import json
import os
import re
from typing import Any, Dict, Optional

from fastapi import Request


def _b64url_decode(seg: str) -> bytes:
    seg = seg.strip()
    pad = '=' * (-len(seg) % 4)
    return base64.urlsafe_b64decode(seg + pad)


def _decode_jwt_unverified(token: str) -> Dict[str, Any]:
    # token format: header.payload.signature
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    try:
        payload = json.loads(_b64url_decode(parts[1]).decode("utf-8"))
        if isinstance(payload, dict):
            return payload
    except Exception:
        return {}
    return {}


def _decode_jwt(token: str, verify: bool) -> Dict[str, Any]:
    if not verify:
        return _decode_jwt_unverified(token)
    # Optional local verification (HS256) for internal environments.
    # In production, prefer API gateway / SSO to verify JWT and pass role headers.
    secret = os.getenv("JWT_SECRET", "")
    alg = os.getenv("JWT_ALG", "HS256")
    if not secret:
        return _decode_jwt_unverified(token)
    try:
        import jwt  # PyJWT
        return jwt.decode(token, secret, algorithms=[alg])
    except Exception:
        return _decode_jwt_unverified(token)


def _first_claim(payload: Dict[str, Any], keys: Any) -> Optional[Any]:
    if not payload:
        return None
    if isinstance(keys, str):
        keys = [keys]
    if not isinstance(keys, list):
        return None
    for k in keys:
        if k in payload:
            return payload.get(k)
    return None


def _split_csv(val: Any) -> list[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    s = str(val)
    if not s:
        return []
    # comma or semicolon separated
    parts = re.split(r"[;,]", s)
    return [p.strip() for p in parts if p.strip()]

def _pick_highest_role(candidates: list[str], priority: list[str]) -> Optional[str]:
    if not candidates:
        return None
    cand = [str(c) for c in candidates]
    if not priority:
        return cand[0]
    # smaller index = higher priority
    best = None
    best_i = 10**9
    for r in cand:
        try:
            i = priority.index(r)
        except ValueError:
            i = 10**8
        if i < best_i:
            best_i = i
            best = r
    return best

def _derive_role_from_mappings(policy: Dict[str, Any], request: Request, jwt_payload: Dict[str, Any]) -> Optional[str]:
    rbac = (policy or {}).get("rbac") or {}
    rm = rbac.get("role_mapping") or {}
    sources = rm.get("sources") or []
    priority = rm.get("role_priority") or ["system", "supervisor", "operator", "ui"]
    candidates: list[str] = []

    # allow gateway to pass groups/entitlements as headers too
    header_groups = _split_csv(request.headers.get("X-User-Groups") or request.headers.get("X-Groups"))
    header_ent = _split_csv(request.headers.get("X-User-Entitlements") or request.headers.get("X-Entitlements"))

    for src in sources:
        if not isinstance(src, dict):
            continue
        claim = str(src.get("claim") or "")
        mapping = src.get("map") or {}
        if not isinstance(mapping, dict) or not claim:
            continue

        values: list[str] = []
        if claim.lower() == "groups":
            values = header_groups or _split_csv(jwt_payload.get(claim) or jwt_payload.get("groups"))
        elif claim.lower() == "entitlements":
            values = header_ent or _split_csv(jwt_payload.get(claim) or jwt_payload.get("entitlements"))
        else:
            values = _split_csv(jwt_payload.get(claim))

        for v in values:
            if v in mapping:
                candidates.append(str(mapping[v]))

    return _pick_highest_role(candidates, [str(x) for x in priority])



def get_actor(request: Request, channel: str = "ui") -> Dict[str, Any]:
    """Return normalized actor used for RBAC + auditing.

    Prefer API gateway/SSO headers. If absent, decode JWT claims (unverified unless JWT_VERIFY=1).
    Actor is normalized to stable enterprise fields: sub/email/groups/role.
    """
    auth = (request.headers.get("Authorization") or "").strip()
    jwt_payload: Dict[str, Any] = {}
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
        verify = os.getenv("JWT_VERIFY", "0") in ("1", "true", "True")
        jwt_payload = _decode_jwt(token, verify=verify) or {}

    from .actor_normalization import normalize_actor
    return normalize_actor(request, channel=channel, jwt_payload=jwt_payload)

def get_channel(request: Request, default: str = "ui") -> str:
    return (request.headers.get("X-Channel") or default).strip() or default
