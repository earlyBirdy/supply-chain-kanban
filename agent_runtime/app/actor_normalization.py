from __future__ import annotations

import re
import fnmatch
from typing import Any, Dict, List, Optional

from fastapi import Request

from .policy_store import load_policy
from .rbac import role_for_channel


def _split_csv(val: Any) -> List[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    s = str(val).strip()
    if not s:
        return []
    parts = re.split(r"[;,]", s)
    return [p.strip() for p in parts if p.strip()]


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


def _detect_provider(policy: Dict[str, Any], jwt_payload: Dict[str, Any]) -> str:
    ident = (policy or {}).get("identity") or {}
    hints = ident.get("provider_hint_claims") or []
    default_provider = str(ident.get("default_provider") or "oidc")
    for k in hints:
        v = jwt_payload.get(k)
        if isinstance(v, str) and v:
            # very light heuristic
            s = v.lower()
            if "saml" in s:
                return "saml"
            if "oidc" in s or "auth0" in s or "okta" in s or "azure" in s or "cognito" in s:
                return "oidc"
    return default_provider


def _match_any(value: str, rule: Dict[str, Any]) -> bool:
    """Match a single value against a rule.when structure supporting patterns/regex/contains."""
    if not isinstance(rule, dict):
        return False
    # direct string => exact
    if isinstance(rule, str):
        return value == rule
    # "patterns": ["x-*", ...]
    pats = rule.get("patterns") if isinstance(rule.get("patterns"), list) else None
    if pats:
        for p in pats:
            if isinstance(p, str) and fnmatch.fnmatch(value, p):
                return True
    # regex
    rx = rule.get("regex")
    if isinstance(rx, str) and rx:
        try:
            return re.search(rx, value) is not None
        except re.error:
            return False
    # contains
    sub = rule.get("contains")
    if isinstance(sub, str) and sub:
        return sub in value
    # in (list of exact strings)
    in_list = rule.get("in")
    if isinstance(in_list, list) and in_list:
        return value in [str(x) for x in in_list]
    return False


def _derive_role_from_mappings(policy: Dict[str, Any], values: List[str], claim_name: str) -> Optional[str]:
    """Use policy.rbac.role_mapping to map group/entitlement values to a role.

    Supports:
      - deny lists (glob/regex/contains)
      - ordered rules (first match wins)
      - exact map sources (backward compatible)
      - priority-based selection
    """
    rbac = (policy or {}).get("rbac") or {}
    rm = rbac.get("role_mapping") or {}

    # deny list: if any value matches deny rules, return special role "denied"
    deny_cfg = rm.get("deny") or {}
    deny_rules = deny_cfg.get(claim_name) or []
    for v in values:
        for r in deny_rules if isinstance(deny_rules, list) else []:
            if isinstance(r, str) and fnmatch.fnmatch(v, r):
                return "denied"
            if isinstance(r, dict) and _match_any(v, r):
                return "denied"

    first_match = bool(rm.get("first_match_wins", True))
    priority = [str(x) for x in (rm.get("role_priority") or ["system", "supervisor", "operator", "ui"])]

    # ordered rules (priority order): group_rules / entitlement_rules
    rules_key = "group_rules" if claim_name.lower() == "groups" else "entitlement_rules"
    rules = rm.get(rules_key) or []
    if isinstance(rules, list) and rules:
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            role = rule.get("role")
            when = rule.get("when")
            if not isinstance(role, str) or not role:
                continue
            # match ANY value
            matched = False
            for v in values:
                if isinstance(when, dict) and _match_any(v, when):
                    matched = True
                    break
                if isinstance(when, list):
                    for w in when:
                        if isinstance(w, str) and fnmatch.fnmatch(v, w):
                            matched = True
                            break
                        if isinstance(w, dict) and _match_any(v, w):
                            matched = True
                            break
                    if matched:
                        break
                if isinstance(when, str) and fnmatch.fnmatch(v, when):
                    matched = True
                    break
            if matched:
                if first_match:
                    return role
                # else collect candidate
                # (fall through to collect candidates below)
                break

    candidates: List[str] = []

    # old exact mapping sources (backward compatible)
    sources = rm.get("sources") or []
    for src in sources:
        if not isinstance(src, dict):
            continue
        claim = str(src.get("claim") or "")
        mapping = src.get("map") or {}
        if not claim or not isinstance(mapping, dict):
            continue
        if claim.lower() != claim_name.lower():
            continue
        for v in values:
            if v in mapping:
                candidates.append(str(mapping[v]))

    # also from rules if not first match
    if not first_match and isinstance(rules, list) and rules:
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            role = rule.get("role")
            when = rule.get("when")
            if not isinstance(role, str) or not role:
                continue
            for v in values:
                ok=False
                if isinstance(when, dict) and _match_any(v, when):
                    ok=True
                elif isinstance(when, str) and fnmatch.fnmatch(v, when):
                    ok=True
                elif isinstance(when, list):
                    for w in when:
                        if isinstance(w, str) and fnmatch.fnmatch(v, w):
                            ok=True; break
                        if isinstance(w, dict) and _match_any(v, w):
                            ok=True; break
                if ok:
                    candidates.append(role)
                    break

    if not candidates:
        return None
    # pick highest priority
    best = None
    best_i = 10**9
    for r in candidates:
        try:
            i = priority.index(r)
        except ValueError:
            i = 10**8
        if i < best_i:
            best_i = i
            best = r
    return best

def normalize_actor(
    request: Request,
    *,
    channel: str,
    jwt_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Normalize actor to stable enterprise fields: sub/email/groups/role.

    Sources:
      - Trusted gateway headers (preferred)
      - JWT claims (verified upstream by gateway)
      - Role mapping from groups/entitlements (policy hot-reload)
      - Channel fallback
    """
    policy = load_policy()
    jwt_payload = jwt_payload or {}
    provider = _detect_provider(policy, jwt_payload)
    ident = (policy or {}).get("identity") or {}
    providers = ident.get("providers") or {}
    claim_map = providers.get(provider) or {}

    # 1) Gateway headers (recommended)
    hdr_role = request.headers.get("X-User-Role") or request.headers.get("X-Role")
    hdr_email = request.headers.get("X-User-Email") or request.headers.get("X-Email")
    hdr_sub = request.headers.get("X-User-Id") or request.headers.get("X-Subject") or request.headers.get("X-User")
    hdr_groups = request.headers.get("X-User-Groups") or request.headers.get("X-Groups")
    hdr_ent = request.headers.get("X-User-Entitlements") or request.headers.get("X-Entitlements")
    hdr_name = request.headers.get("X-User-Name") or request.headers.get("X-Name")

    sub = (hdr_sub or "").strip() or None
    email = (hdr_email or "").strip() or None
    role = (hdr_role or "").strip() or None
    groups = _split_csv(hdr_groups)
    entitlements = _split_csv(hdr_ent)
    name = (hdr_name or "").strip() or None

    source = "headers"
    # 2) JWT claims (if missing)
    if not (sub and email and role):
        source = "jwt"
        if not sub:
            v = _first_claim(jwt_payload, claim_map.get("sub") or ["sub"])
            if isinstance(v, str) and v.strip():
                sub = v.strip()
        if not email:
            v = _first_claim(jwt_payload, claim_map.get("email") or ["email"])
            if isinstance(v, str) and v.strip():
                email = v.strip()
        if not name:
            v = _first_claim(jwt_payload, claim_map.get("name") or ["name"])
            if isinstance(v, str) and v.strip():
                name = v.strip()
        if not groups:
            v = _first_claim(jwt_payload, claim_map.get("groups") or ["groups"])
            groups = _split_csv(v)
        if not entitlements:
            v = _first_claim(jwt_payload, claim_map.get("entitlements") or ["entitlements"])
            entitlements = _split_csv(v)

    # 3) Role mapping from groups/entitlements if role missing
    if not role:
        derived = _derive_role_from_mappings(policy, groups, "groups") or _derive_role_from_mappings(policy, entitlements, "entitlements")
        if derived:
            role = derived
            source = "mapped"

    # 4) Fallback channel mapping
    if not role:
        role = role_for_channel(policy, channel)
        source = "channel"

    return {
        "channel": channel,
        "role": role,
        "email": email or "",
        "sub": sub or "",
        "groups": groups,
        "entitlements": entitlements,
        "name": name or "",
        "identity_provider": provider,
        "source": source,
    }
