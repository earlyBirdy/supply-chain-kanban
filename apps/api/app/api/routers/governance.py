import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, Body, Header, HTTPException, Response

from ...policy_store import load_policy, save_policy, policy_path_str, policy_etag, policy_revision

router = APIRouter()


def _is_dev_mode() -> bool:
    if os.getenv("DEV_MODE", "").strip() in ("1", "true", "True", "yes", "YES"):
        return True
    env = os.getenv("APP_ENV", "").strip().lower()
    return env in ("dev", "development", "local")


# ----------------------------
# Policy validation (structure)
# ----------------------------

_ALLOWED_STATUSES = ("todo", "in_progress", "blocked", "resolved")


def _validate_policy_strict(p: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Validate policy structure & usability.

    Returns (errors, warnings). Does not raise by itself.
    """
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(p, dict):
        return (["policy must be a JSON object"], warnings)

    csp = p.get("card_status_policy")
    if not isinstance(csp, dict):
        errors.append("policy.card_status_policy is required and must be an object")
        csp = {}
    # idempotency config (optional)
    idem = p.get("idempotency")
    if idem is not None:
        if not isinstance(idem, dict):
            errors.append("idempotency must be an object")
        else:
            hn = idem.get("header_name")
            if hn is not None and not isinstance(hn, str):
                errors.append("idempotency.header_name must be a string")

    # rbac-lite (optional)
    rbac = p.get("rbac")
    if rbac is not None:
        if not isinstance(rbac, dict):
            errors.append("rbac must be an object")
        else:
            ch = rbac.get("channels")
            if ch is not None and not isinstance(ch, dict):
                errors.append("rbac.channels must be an object mapping channel->role")
            perms = rbac.get("permissions")
            if perms is not None and not isinstance(perms, dict):
                errors.append("rbac.permissions must be an object")
            else:
                if isinstance(perms, dict):
                    for k in ("approve","execute"):
                        if k in perms and not isinstance(perms[k], dict):
                            errors.append(f"rbac.permissions.{k} must be an object mapping role->list")



    at = csp.get("allowed_transitions")
    if not isinstance(at, dict):
        errors.append("policy.card_status_policy.allowed_transitions is required and must be an object")
    else:
        # validate keys and values
        for st in at.keys():
            if st not in _ALLOWED_STATUSES:
                warnings.append(f"allowed_transitions has unknown status key: {st}")
        for st in _ALLOWED_STATUSES:
            if st not in at:
                warnings.append(f"allowed_transitions missing status key: {st}")
        for src, dsts in at.items():
            if not isinstance(dsts, list):
                errors.append(f"allowed_transitions.{src} must be a list")
                continue
            for d in dsts:
                if d not in _ALLOWED_STATUSES:
                    errors.append(f"allowed_transitions.{src} contains invalid status: {d}")

    ag = csp.get("approval_gate", {})
    if ag is not None and not isinstance(ag, dict):
        errors.append("policy.card_status_policy.approval_gate must be an object")
    else:
        res = (ag or {}).get("resolve", {})
        if res and not isinstance(res, dict):
            errors.append("policy.card_status_policy.approval_gate.resolve must be an object")
        elif isinstance(res, dict) and res:
            rc = res.get("require_channel")
            if rc is not None and not isinstance(rc, str):
                errors.append("approval_gate.resolve.require_channel must be a string")
            rh = res.get("require_high_risk_case")
            if rh is not None and not isinstance(rh, bool):
                errors.append("approval_gate.resolve.require_high_risk_case must be a boolean")
            thr = res.get("high_risk_threshold")
            if thr is not None and not isinstance(thr, int):
                errors.append("approval_gate.resolve.high_risk_threshold must be an integer")

    sla = csp.get("sla_guardrails", {})
    if sla is not None and not isinstance(sla, dict):
        errors.append("policy.card_status_policy.sla_guardrails must be an object")
    else:
        for k in ("blocked_requires_reason", "resolved_requires_timestamp"):
            if k in (sla or {}) and not isinstance((sla or {}).get(k), bool):
                errors.append(f"sla_guardrails.{k} must be a boolean")

    
    # action_payload_rules matcher validation (optional)
    if isinstance(rbac, dict):
        rules = rbac.get("action_payload_rules")
        if rules is not None:
            if not isinstance(rules, list):
                errors.append("rbac.action_payload_rules must be a list")
            else:
                allowed_ops = {"contains", "regex", "in", "eq"}
                for i, rule in enumerate(rules):
                    if not isinstance(rule, dict):
                        errors.append(f"rbac.action_payload_rules[{i}] must be an object")
                        continue
                    # required fields
                    if not isinstance(rule.get("action_type"), str) or not rule.get("action_type"):
                        errors.append(f"rbac.action_payload_rules[{i}].action_type is required and must be a non-empty string")
                    when = rule.get("when")
                    if when is None or not isinstance(when, dict):
                        errors.append(f"rbac.action_payload_rules[{i}].when is required and must be an object")
                        continue
                    # rule-level type checks (stricter)
                    if "require_roles" in rule and (not isinstance(rule.get("require_roles"), list) or any(not isinstance(x, str) or not x.strip() for x in (rule.get("require_roles") or []))):
                        errors.append(f"rbac.action_payload_rules[{i}].require_roles must be a list[str]")
                    if "deny_roles" in rule and (not isinstance(rule.get("deny_roles"), list) or any(not isinstance(x, str) or not x.strip() for x in (rule.get("deny_roles") or []))):
                        errors.append(f"rbac.action_payload_rules[{i}].deny_roles must be a list[str]")
                    if "require_risk_ge" in rule and not isinstance(rule.get("require_risk_ge"), (int, float)):
                        errors.append(f"rbac.action_payload_rules[{i}].require_risk_ge must be a number")

                    for k, v in when.items():
                        if not isinstance(k, str) or not k:
                            errors.append(f"rbac.action_payload_rules[{i}].when has invalid key")
                            continue
                        # scalar match
                        if isinstance(v, (str, int, float, bool)) or v is None:
                            continue
                        # list match (any-of)
                        if isinstance(v, list):
                            if not v:
                                errors.append(f"rbac.action_payload_rules[{i}].when.{k} list must not be empty")
                            continue
                        # operator object (exactly one operator, whitelisted)
                        if isinstance(v, dict):
                            if len(v.keys()) != 1:
                                errors.append(f"rbac.action_payload_rules[{i}].when.{k} must specify exactly one operator; got {list(v.keys())}")
                                continue
                            op = next(iter(v.keys()))
                            if op not in allowed_ops:
                                errors.append(f"rbac.action_payload_rules[{i}].when.{k} has unknown operator: {op}")
                                continue
                            val = v.get(op)
                            if op == "contains":
                                if not isinstance(val, str) or not val:
                                    errors.append(f"rbac.action_payload_rules[{i}].when.{k}.contains must be a non-empty string")
                            elif op == "in":
                                if not isinstance(val, list) or not val:
                                    errors.append(f"rbac.action_payload_rules[{i}].when.{k}.in must be a non-empty list")
                            elif op == "regex":
                                if not isinstance(val, str) or not val:
                                    errors.append(f"rbac.action_payload_rules[{i}].when.{k}.regex must be a non-empty string")
                                else:
                                    try:
                                        re.compile(val)
                                    except Exception as e:
                                        errors.append(f"rbac.action_payload_rules[{i}].when.{k}.regex invalid: {e}")
                            elif op == "eq":
                                # any scalar is ok
                                if isinstance(val, dict) or isinstance(val, list):
                                    errors.append(f"rbac.action_payload_rules[{i}].when.{k}.eq must be a scalar")
                            continue
                        errors.append(f"rbac.action_payload_rules[{i}].when.{k} has unsupported matcher type: {type(v).__name__}")

        # role mapping validation (optional)
        rm = rbac.get("role_mapping") if isinstance(rbac, dict) else None
        if rm is not None:
            if not isinstance(rm, dict):
                errors.append("rbac.role_mapping must be an object")
            else:
                rp = rm.get("role_priority")
                if rp is not None and not isinstance(rp, list):
                    errors.append("rbac.role_mapping.role_priority must be a list")
                fmw = rm.get("first_match_wins")
                if fmw is not None and not isinstance(fmw, bool):
                    errors.append("rbac.role_mapping.first_match_wins must be a boolean")
                deny = rm.get("deny")
                if deny is not None and not isinstance(deny, dict):
                    errors.append("rbac.role_mapping.deny must be an object with groups/entitlements lists")
                if isinstance(deny, dict):
                    for cname in ["groups", "entitlements"]:
                        dv = deny.get(cname)
                        if dv is not None and not isinstance(dv, list):
                            errors.append(f"rbac.role_mapping.deny.{cname} must be a list")
                        if isinstance(dv, list):
                            for j, item in enumerate(dv):
                                if isinstance(item, str):
                                    continue
                                if isinstance(item, dict):
                                    # allow patterns/regex/contains/in
                                    allowed = {"patterns", "regex", "contains", "in"}
                                    bad = set(item.keys()) - allowed
                                    if bad:
                                        errors.append(f"rbac.role_mapping.deny.{cname}[{j}] has unsupported keys: {sorted(bad)}")
                                    # must have at least one key
                                    if not item:
                                        errors.append(f"rbac.role_mapping.deny.{cname}[{j}] must not be empty")
                                    if "patterns" in item and (not isinstance(item.get("patterns"), list) or any(not isinstance(x, str) for x in item.get("patterns"))):
                                        errors.append(f"rbac.role_mapping.deny.{cname}[{j}].patterns must be list[str]")
                                    if "regex" in item and not isinstance(item.get("regex"), str):
                                        errors.append(f"rbac.role_mapping.deny.{cname}[{j}].regex must be str")
                                    if isinstance(item.get("regex"), str):
                                        try:
                                            re.compile(item.get("regex"))
                                        except Exception:
                                            errors.append(f"rbac.role_mapping.deny.{cname}[{j}].regex is invalid")
                                    if "contains" in item and not isinstance(item.get("contains"), str):
                                        errors.append(f"rbac.role_mapping.deny.{cname}[{j}].contains must be str")
                                    if "in" in item and (not isinstance(item.get("in"), list) or any(not isinstance(x, str) for x in item.get("in"))):
                                        errors.append(f"rbac.role_mapping.deny.{cname}[{j}].in must be list[str]")
                                    continue
                                errors.append(f"rbac.role_mapping.deny.{cname}[{j}] must be str or object")
                for rk in ["group_rules", "entitlement_rules"]:
                    rules = rm.get(rk)
                    if rules is not None and not isinstance(rules, list):
                        errors.append(f"rbac.role_mapping.{rk} must be a list")
                    if isinstance(rules, list):
                        for j, rule in enumerate(rules):
                            if not isinstance(rule, dict):
                                errors.append(f"rbac.role_mapping.{rk}[{j}] must be an object")
                                continue
                            if not isinstance(rule.get("role"), str) or not rule.get("role"):
                                errors.append(f"rbac.role_mapping.{rk}[{j}].role must be a non-empty string")
                            when = rule.get("when")
                            if when is None:
                                errors.append(f"rbac.role_mapping.{rk}[{j}].when is required")
                                continue
                            # when can be str | list | object
                            def _validate_when(prefix, w):
                                if isinstance(w, str):
                                    return
                                if isinstance(w, list):
                                    for k, ww in enumerate(w):
                                        _validate_when(f"{prefix}[{k}]", ww)
                                    return
                                if isinstance(w, dict):
                                    allowed = {"patterns", "regex", "contains", "in"}
                                    bad = set(w.keys()) - allowed
                                    if bad:
                                        errors.append(f"{prefix} has unsupported keys: {sorted(bad)}")
                                    if "patterns" in w and (not isinstance(w.get("patterns"), list) or any(not isinstance(x, str) for x in w.get("patterns"))):
                                        errors.append(f"{prefix}.patterns must be list[str]")
                                    if "regex" in w and not isinstance(w.get("regex"), str):
                                        errors.append(f"{prefix}.regex must be str")
                                    if isinstance(w.get("regex"), str):
                                        try:
                                            re.compile(w.get("regex"))
                                        except Exception:
                                            errors.append(f"{prefix}.regex is invalid")
                                    if "contains" in w and not isinstance(w.get("contains"), str):
                                        errors.append(f"{prefix}.contains must be str")
                                    if "in" in w and (not isinstance(w.get("in"), list) or any(not isinstance(x, str) for x in w.get("in"))):
                                        errors.append(f"{prefix}.in must be list[str]")
                                    return
                                errors.append(f"{prefix} must be str, list, or object")
                            _validate_when(f"rbac.role_mapping.{rk}[{j}].when", when)
                sources = rm.get("sources")
                if sources is not None:
                    if not isinstance(sources, list):
                        errors.append("rbac.role_mapping.sources must be a list")
                    else:
                        for j, s in enumerate(sources):
                            if not isinstance(s, dict):
                                errors.append(f"rbac.role_mapping.sources[{j}] must be an object")
                                continue
                            if not isinstance(s.get("claim"), str) or not s.get("claim"):
                                errors.append(f"rbac.role_mapping.sources[{j}].claim must be a non-empty string")
                            mp = s.get("map")
                            if mp is None or not isinstance(mp, dict):
                                errors.append(f"rbac.role_mapping.sources[{j}].map must be an object mapping group/entitlement->role")
                            else:
                                for kk, vv in mp.items():
                                    if not isinstance(kk, str) or not isinstance(vv, str):
                                        errors.append(f"rbac.role_mapping.sources[{j}].map entries must be string->string")

    _validate_audit_cfg(p, errors)
    _validate_identity_cfg(p, errors)

    return (errors, warnings)


def _require_valid_policy(p: Dict[str, Any]) -> None:
    errors, _warnings = _validate_policy_strict(p)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})


# ----------------------------
# Merge patch (RFC7396-ish)
# ----------------------------

def _merge_patch(target: Any, patch: Any) -> Any:
    """Apply JSON Merge Patch semantics (RFC7396).

    - If patch is not an object, it replaces target.
    - If patch is an object: keys with null delete; others recursively merge.
    """
    if not isinstance(patch, dict):
        return patch
    if not isinstance(target, dict):
        target = {}
    result = dict(target)
    for k, v in patch.items():
        if v is None:
            result.pop(k, None)
        else:
            result[k] = _merge_patch(result.get(k), v)
    return result


# ----------------------------
# Endpoints
# ----------------------------

@router.get("/policy")
def get_policy(response: Response):
    """Return effective governance policy + meta (ETag/revision/path)."""
    p = load_policy()
    etag = policy_etag(p)
    rev = policy_revision(p)
    response.headers["ETag"] = etag
    response.headers["X-Policy-Revision"] = str(rev)
    return {"policy": p, "meta": {"etag": etag, "revision": rev}, "path": policy_path_str()}


@router.post("/policy/validate")
def validate_policy(payload: Dict[str, Any] = Body(...)):
    """Validate a candidate policy structure & usability (no persistence)."""
    errors, warnings = _validate_policy_strict(payload)
    return {"ok": len(errors) == 0, "errors": errors, "warnings": warnings}


@router.patch("/policy")
def patch_policy(
    response: Response,
    payload: Dict[str, Any] = Body(...),
    if_match: str | None = Header(default=None, alias="If-Match"),
):
    """Patch governance policy (DEV ONLY) with merge-patch semantics.

    Requires If-Match with current ETag to prevent lost updates.
    """
    if not _is_dev_mode():
        raise HTTPException(status_code=403, detail="Policy updates are only allowed in dev mode (set APP_ENV=dev or DEV_MODE=1)")

    current = load_policy()
    current_etag = policy_etag(current)
    if not if_match:
        raise HTTPException(status_code=428, detail="Missing If-Match header (ETag) for policy patch")
    # allow quoted etags
    if_match_clean = if_match.strip().strip('"')
    if if_match_clean != current_etag:
        raise HTTPException(status_code=412, detail={"message": "ETag mismatch", "current_etag": current_etag})

    merged = _merge_patch(current, payload)

    # bump revision + updated_at
    try:
        rev = int(merged.get("revision", policy_revision(current)))
    except Exception:
        rev = policy_revision(current)
    merged["revision"] = rev + 1
    merged["updated_at"] = datetime.now(timezone.utc).isoformat()

    _require_valid_policy(merged)
    save_policy(merged)

    effective = load_policy()
    etag = policy_etag(effective)
    rev2 = policy_revision(effective)
    response.headers["ETag"] = etag
    response.headers["X-Policy-Revision"] = str(rev2)
    return {"ok": True, "path": policy_path_str(), "meta": {"etag": etag, "revision": rev2}, "policy": effective}


def _validate_identity_cfg(policy: dict, errors: list[str]) -> None:
    ident = (policy or {}).get("identity") or {}
    providers = ident.get("providers")
    if providers is not None and not isinstance(providers, dict):
        errors.append("identity.providers must be an object")
    if isinstance(providers, dict):
        for pname, m in providers.items():
            if not isinstance(m, dict):
                errors.append(f"identity.providers.{pname} must be an object")
                continue
            for field in ["sub", "email", "groups", "entitlements", "name"]:
                if field in m and not isinstance(m[field], list):
                    errors.append(f"identity.providers.{pname}.{field} must be list[str]")
                if isinstance(m.get(field), list) and any(not isinstance(x, str) for x in m[field]):
                    errors.append(f"identity.providers.{pname}.{field} must be list[str]")


# Audit pattern validation (glob + regex) + redact_headers
def _validate_audit_cfg(policy: dict, errors: list[str]) -> None:
    audit = (policy or {}).get("audit") or {}
    req = audit.get("request") or {}

    def _validate_pattern_list(field: str, val):
        if val is None:
            return
        if not isinstance(val, list):
            errors.append(f"{field} must be a list")
            return
        for i, item in enumerate(val):
            if isinstance(item, str):
                s = item.strip()
                if not s:
                    errors.append(f"{field}[{i}] must be a non-empty string")
                    continue
                sl = s.lower()
                if sl.startswith("re:") or sl.startswith("regex:"):
                    pat = s.split(":", 1)[1]
                    if not pat:
                        errors.append(f"{field}[{i}] regex must not be empty")
                        continue
                    try:
                        re.compile(pat)
                    except Exception as e:
                        errors.append(f"{field}[{i}] regex invalid: {e}")
                # else: glob string ok
                continue
            if isinstance(item, dict):
                keys = set(item.keys())
                if keys == {"glob"}:
                    gv = item.get("glob")
                    if not isinstance(gv, str) or not gv.strip():
                        errors.append(f"{field}[{i}].glob must be a non-empty string")
                elif keys == {"regex"}:
                    rv = item.get("regex")
                    if not isinstance(rv, str) or not rv.strip():
                        errors.append(f"{field}[{i}].regex must be a non-empty string")
                    else:
                        try:
                            re.compile(rv)
                        except Exception as e:
                            errors.append(f"{field}[{i}].regex invalid: {e}")
                else:
                    errors.append(f"{field}[{i}] must be {{'glob':...}} or {{'regex':...}}")
                continue
            errors.append(f"{field}[{i}] must be string or object")

    _validate_pattern_list("audit.request.allowlist_headers", req.get("allowlist_headers"))
    _validate_pattern_list("audit.request.redact_headers", req.get("redact_headers"))

    allow_q = req.get("allowlist_query")
    if allow_q is not None and not isinstance(allow_q, list):
        errors.append("audit.request.allowlist_query must be a list[str]")
    if isinstance(allow_q, list) and any(not isinstance(x, str) for x in allow_q):
        errors.append("audit.request.allowlist_query must be a list[str]")

    for k in ["header_value_max_len", "query_value_max_len"]:
        if k in req:
            try:
                int(req.get(k))
            except Exception:
                errors.append(f"audit.request.{k} must be an int")
