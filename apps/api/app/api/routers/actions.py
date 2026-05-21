from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query, Request, Header
from pydantic import BaseModel, Field

from ...db import one
from ...execution import execute_action
from ...policy_store import load_policy
from ...auth import get_actor, get_channel
from ...audit import with_audit
from ...rbac import can_execute
from ...idempotency import request_hash as _request_hash, check_or_replay as _check_or_replay, store as _idem_store

router = APIRouter()


class ExecuteActionRequest(BaseModel):
    case_id: str = Field(..., description="Case UUID")
    channel: str = Field("api", description="ui|api|slack|agent|supervisor|system")
    action_type: str = Field(..., description="Typed action name (e.g. UpdateCardStatus, ExpediteShipment, TriggerPurchase)")
    payload: Dict[str, Any] = Field(default_factory=dict)


@router.post("/execute")
def execute(
    request: Request,
    req: ExecuteActionRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    dry_run: bool = Query(False, description="If true, validate guardrails only and do not write audit / mutate systems"),
):
    ex = one("SELECT case_id, risk_score FROM agent_cases WHERE case_id=:cid", cid=req.case_id)
    if not ex:
        raise HTTPException(status_code=404, detail=f"Case not found: {req.case_id}")

    policy = load_policy()
    channel = (req.channel or "").strip() or get_channel(request, default="api")
    actor = get_actor(request, channel=channel)

    case_risk = None
    if ex.get("risk_score") is not None:
        try:
            case_risk = float(ex.get("risk_score"))
        except Exception:
            case_risk = None

    ok, reason = can_execute(
        policy,
        channel=channel,
        action_type=req.action_type,
        role=actor.get("role"),
        payload=req.payload or {},
        case_risk_score=case_risk,
    )
    if not ok:
        raise HTTPException(status_code=403, detail=reason)

    # Idempotency (optional; enabled via governance policy)
    idem_cfg = (policy or {}).get("idempotency") or {}
    idem_enabled = bool(idem_cfg.get("enabled", False))
    header_name = str(idem_cfg.get("header_name") or "Idempotency-Key")
    idem_key = (request.headers.get(header_name) or idempotency_key or "").strip() if idem_enabled else ""

    if idem_key and (not dry_run):
        rh = _request_hash(
            {
                "case_id": req.case_id,
                "channel": channel,
                "action_type": req.action_type,
                "payload": req.payload or {},
                "dry_run": False,
            }
        )
        replayed, prior_resp, conflict = _check_or_replay(key=idem_key, req_hash=rh)
        if conflict:
            raise HTTPException(status_code=409, detail=conflict)
        if replayed:
            return prior_resp

    payload = with_audit(
        {**(req.payload or {}), "_actor": actor},
        actor=actor,
        request=request,
        materialization_id=str((req.payload or {}).get("materialization_id") or ""),
    )

    resp = execute_action(
        case_id=req.case_id,
        channel=channel,
        action_type=req.action_type,
        payload=payload,
        dry_run=bool(dry_run),
    )

    if idem_key and (not dry_run):
        rh = _request_hash(
            {
                "case_id": req.case_id,
                "channel": channel,
                "action_type": req.action_type,
                "payload": req.payload or {},
                "dry_run": False,
            }
        )
        # Best-effort store; if a race inserts first, it's OK (replay works next time).
        try:
            _idem_store(idem_key, rh, resp)
        except Exception:
            pass

    return resp
