from __future__ import annotations

import re

from typing import Any, Dict, Optional, Tuple


def role_for_channel(policy: Dict[str, Any], channel: str) -> str:
    rbac = (policy or {}).get("rbac") or {}
    channels = rbac.get("channels") or {}
    role = channels.get(channel)
    return str(role or channel or "ui")


def _list_allows(lst: Any, action_type: str) -> bool:
    if not isinstance(lst, list):
        return False
    if "*" in lst:
        return True
    return action_type in lst


def _get_by_path(obj: Any, path: str) -> Any:
    """Fetch nested value by dot path: a.b.c"""
    if not isinstance(path, str) or not path:
        return None
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur

def _match_value(actual: Any, matcher: Any) -> bool:
    """Flexible matcher supporting list, regex, contains, in."""
    # list matcher => membership
    if isinstance(matcher, list):
        return actual in matcher or str(actual) in [str(x) for x in matcher]
    # dict matcher => operator
    if isinstance(matcher, dict):
        if "in" in matcher and isinstance(matcher.get("in"), list):
            lst = matcher.get("in")
            return actual in lst or str(actual) in [str(x) for x in lst]
        if "eq" in matcher:
            return str(actual) == str(matcher.get("eq"))
        if "contains" in matcher:
            needle = str(matcher.get("contains"))
            if isinstance(actual, list):
                return any(needle in str(x) for x in actual)
            return needle in str(actual)
        if "regex" in matcher:
            pat = str(matcher.get("regex") or "")
            try:
                return re.search(pat, str(actual)) is not None
            except Exception:
                return False
        # unknown operator => strict compare as fallback
        return str(actual) == str(matcher)
    # scalar => equality
    return str(actual) == str(matcher)

def _payload_rule_applies(rule: Dict[str, Any], action_type: str, payload: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(rule, dict):
        return False
    if str(rule.get("action_type") or "") != str(action_type or ""):
        return False
    when = rule.get("when") or {}
    if not when:
        return True
    if not isinstance(payload, dict):
        return False
    if not isinstance(when, dict):
        return False

    for k, matcher in when.items():
        # support dot paths for nested payload
        actual = payload.get(k) if (isinstance(k, str) and "." not in k) else _get_by_path(payload, str(k))
        if not _match_value(actual, matcher):
            return False
    return True



def _enforce_action_payload_rules(
    policy: Dict[str, Any],
    action_type: str,
    payload: Optional[Dict[str, Any]],
    role: str,
    case_risk_score: Optional[float] = None,
) -> Tuple[bool, str]:
    rbac = (policy or {}).get("rbac") or {}
    rules = rbac.get("action_payload_rules") or []
    if not isinstance(rules, list):
        return True, "ok"

    for rule in rules:
        if not _payload_rule_applies(rule, action_type, payload):
            continue

        req_roles = rule.get("require_roles") or []
        if isinstance(req_roles, list) and req_roles:
            if role not in [str(r) for r in req_roles]:
                return False, str(rule.get("reason") or f"role '{role}' not permitted by payload rule")

        req_ge = rule.get("require_risk_ge")
        if req_ge is not None:
            try:
                thr = float(req_ge)
                rs = float(case_risk_score) if case_risk_score is not None else None
            except Exception:
                thr = None
                rs = None
            if thr is not None:
                if rs is None or rs < thr:
                    return False, str(rule.get("reason") or f"case risk_score {rs} below required threshold {thr}")

    return True, "ok"


def can_approve(
    policy: Dict[str, Any],
    channel: str,
    action_type: str,
    role: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    case_risk_score: Optional[float] = None,
) -> Tuple[bool, str]:
    rbac = (policy or {}).get("rbac") or {}
    perms = (rbac.get("permissions") or {}).get("approve") or {}
    role = str(role or role_for_channel(policy, channel))
    allow = perms.get(role, [])
    if not _list_allows(allow, action_type):
        return False, f"role '{role}' not permitted to approve action_type '{action_type}'"

    ok, reason = _enforce_action_payload_rules(policy, action_type, payload, role, case_risk_score=case_risk_score)
    if not ok:
        return False, f"payload rule: {reason}"

    return True, "ok"


def can_execute(
    policy: Dict[str, Any],
    channel: str,
    action_type: str,
    payload: Optional[Dict[str, Any]] = None,
    role: Optional[str] = None,
    case_risk_score: Optional[float] = None,
) -> Tuple[bool, str]:
    rbac = (policy or {}).get("rbac") or {}
    perms = (rbac.get("permissions") or {}).get("execute") or {}
    role = str(role or role_for_channel(policy, channel))
    allow = perms.get(role, [])
    if not _list_allows(allow, action_type):
        return False, f"role '{role}' not permitted to execute action_type '{action_type}'"

    # Fine-grained constraints (legacy)
    constraints = rbac.get("constraints") or {}
    if role == "operator" and action_type == "UpdateCardStatus":
        c = constraints.get("operator_update_cardstatus") or {}
        deny = set(c.get("deny_new_status") or [])
        new_status = ""
        if isinstance(payload, dict):
            new_status = str(payload.get("new_status") or "")
        if new_status and new_status in deny:
            return False, f"operator cannot set card status to '{new_status}'"

    ok, reason = _enforce_action_payload_rules(policy, action_type, payload, role, case_risk_score=case_risk_score)
    if not ok:
        return False, f"payload rule: {reason}"

    return True, "ok"
