from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, Header, Request
from pydantic import BaseModel, Field

from ...db import one, all, q
from ...execution import execute_action
from ...policy_store import load_policy
from ...auth import get_actor, get_channel
from ...rbac import can_approve, can_execute
from ...audit import with_audit

router = APIRouter()


def _scoped_idem_key(endpoint: str, subject: str, card_id: str, raw: str) -> str:
    base = f"{endpoint}|{subject}|{card_id}|{raw}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _pa_transition_allowed(policy: Dict[str, Any], frm: str, to: str) -> bool:
    pol = (policy or {}).get("pending_action_policy") or {}
    allowed = pol.get("allowed_transitions") or {}
    return to in set(allowed.get(frm, []) or [])


def _audit_action(
    *,
    case_id: str,
    channel: str,
    action_type: str,
    payload: Dict[str, Any],
    result: str,
) -> None:
    try:
        q(
            """
            INSERT INTO agent_actions (case_id, channel, action_type, payload, result)
            VALUES (:cid, :ch, :at, :pl::jsonb, :res)
            """,
            cid=case_id,
            ch=channel,
            at=action_type,
            pl=payload,
            res=result,
        )
    except Exception:
        # Best-effort audit: never throw.
        pass


def _audit_violation(
    *,
    request: Request,
    actor: Dict[str, Any],
    case_id: str,
    channel: str,
    pending_id: str,
    frm: str,
    to: str,
    reason: str,
    materialization_id: str | None = None,
) -> None:
    pl = with_audit(
        {
            "pending_id": pending_id,
            "from_status": frm,
            "to_status": to,
            "reason": reason,
        },
        actor=actor,
        request=request,
        materialization_id=materialization_id,
    )
    _audit_action(
        case_id=case_id,
        channel=channel,
        action_type="PendingActionTransitionViolation",
        payload=pl,
        result=f"blocked: {reason}",
    )


class DecisionRequest(BaseModel):
    decision: str = Field("approve", description="approve | reject")
    note: str = Field("", description="Optional note")


@router.get("/")
def list_pending_actions(
    case_id: Optional[str] = Query(None),
    card_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="pending|approved|rejected|executed|blocked|canceled"),
    limit: int = Query(200, ge=1, le=500),
):
    where = []
    params: Dict[str, Any] = {"lim": limit}
    if case_id:
        where.append("p.case_id=:cid")
        params["cid"] = case_id
    if card_id:
        where.append("p.card_id=:kid")
        params["kid"] = card_id
    if status:
        where.append("p.status=:st")
        params["st"] = status

    w = ("WHERE " + " AND ".join(where)) if where else ""
    return all(
        f"""
        SELECT * FROM v_pending_actions p
        {w}
        ORDER BY p.updated_at DESC, p.rank ASC
        LIMIT :lim
        """,
        **params,
    )


@router.get("/{pending_id}")
def get_pending_action(pending_id: str):
    r = one("SELECT * FROM v_pending_actions WHERE pending_id=:pid", pid=pending_id)
    if not r:
        raise HTTPException(status_code=404, detail=f"Pending action not found: {pending_id}")
    return r


@router.patch("/{pending_id}/decision")
def decide_pending_action(
    request: Request,
    pending_id: str,
    req: DecisionRequest,
    channel: str = Query("supervisor", description="Decision channel (ui|supervisor|system)"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    pa = one("SELECT * FROM pending_actions WHERE pending_id=:pid", pid=pending_id)
    if not pa:
        raise HTTPException(status_code=404, detail=f"Pending action not found: {pending_id}")

    decision = (req.decision or "").lower().strip()
    if decision not in {"approve", "reject"}:
        raise HTTPException(status_code=400, detail="decision must be approve or reject")
    new_status = "approved" if decision == "approve" else "rejected"

    policy = load_policy()
    if not channel:
        channel = get_channel(request, default="ui")
    actor = get_actor(request, channel=channel)
    subject = str(actor.get("sub") or actor.get("email") or "anonymous")

    # hashes for idempotency conflict detection
    decision_body = {"decision": decision, "note": req.note or "", "channel": channel}
    req_hash = hashlib.sha256(json.dumps(decision_body, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    scoped_idem = _scoped_idem_key("/pending_actions/decision", subject, str(pa.get("card_id") or ""), idempotency_key) if idempotency_key else None

    mid = str(pa.get("materialization_id") or "") or None
    case_id = str(pa.get("case_id") or "")
    frm = str(pa.get("status") or "")

    # Idempotency replay/conflict (scoped)
    if scoped_idem and str(pa.get("decision_idempotency_key") or "") == scoped_idem:
        if str(pa.get("decision_request_hash") or "") and str(pa.get("decision_request_hash") or "") != req_hash:
            pl = with_audit(
                {
                    "endpoint": "/pending_actions/decision",
                    "subject": subject,
                    "card_id": str(pa.get("card_id") or ""),
                    "pending_id": pending_id,
                    "idempotency_key": idempotency_key,
                    "expected_request_hash": str(pa.get("decision_request_hash") or ""),
                    "received_request_hash": req_hash,
                },
                actor=actor,
                request=request,
                materialization_id=mid,
            )
            _audit_action(
                case_id=case_id,
                channel="system",
                action_type="IdempotencyConflict",
                payload=pl,
                result="blocked: Idempotency-Key reuse with different payload",
            )
            raise HTTPException(status_code=409, detail="Idempotency-Key reuse with different payload (request_hash mismatch).")

        # already decided: replay current state
        if str(pa.get("status") or "") in ("approved", "rejected"):
            return one("SELECT * FROM v_pending_actions WHERE pending_id=:pid", pid=pending_id)

    # RBAC + payload rule enforcement for approvals
    risk_row = one("SELECT risk_score FROM agent_cases WHERE case_id=:cid", cid=case_id)
    case_risk = None
    if risk_row and risk_row.get("risk_score") is not None:
        try:
            case_risk = float(risk_row.get("risk_score"))
        except Exception:
            case_risk = None

    ok, reason = can_approve(
        policy,
        channel=channel,
        action_type=str(pa.get("action_type") or ""),
        role=actor.get("role"),
        payload=dict(pa.get("action_payload") or {}),
        case_risk_score=case_risk,
    )
    if not ok:
        _audit_violation(
            request=request,
            actor=actor,
            case_id=case_id,
            channel=channel,
            pending_id=pending_id,
            frm=frm,
            to="(decision)",
            reason=f"rbac: {reason}",
            materialization_id=mid,
        )
        raise HTTPException(status_code=403, detail=reason)

    if not _pa_transition_allowed(policy, frm, new_status):
        _audit_violation(
            request=request,
            actor=actor,
            case_id=case_id,
            channel=channel,
            pending_id=pending_id,
            frm=frm,
            to=new_status,
            reason=f"illegal transition {frm} -> {new_status}",
            materialization_id=mid,
        )
        raise HTTPException(status_code=409, detail=f"Illegal pending_action transition: {frm} -> {new_status}")

    q(
        """
        UPDATE pending_actions
        SET status=:st,
            approved_by=:ab,
            approved_at=CASE WHEN :st = 'approved' THEN now() ELSE NULL END,
            decision_idempotency_key=COALESCE(:dik, decision_idempotency_key),
            decision_request_hash=COALESCE(:drh, decision_request_hash),
            updated_at=now(),
            execution_result=CASE WHEN :note <> '' THEN :note ELSE execution_result END
        WHERE pending_id=:pid
        """,
        st=new_status,
        ab=subject,
        note=req.note or "",
        dik=scoped_idem,
        drh=req_hash,
        pid=pending_id,
    )

    pl = with_audit(
        {
            "pending_id": pending_id,
            "decision": decision,
            "note": req.note or "",
            "idempotency_key_scoped": scoped_idem,
        },
        actor=actor,
        request=request,
        materialization_id=mid,
    )
    _audit_action(
        case_id=case_id,
        channel=channel,
        action_type="DecidePendingAction",
        payload=pl,
        result=f"ok: {new_status}",
    )

    return one("SELECT * FROM v_pending_actions WHERE pending_id=:pid", pid=pending_id)


@router.post("/{pending_id}/execute")
def execute_pending_action(
    request: Request,
    pending_id: str,
    dry_run: bool = Query(True, description="If true, validate only; do not write audit/DB."),
    channel: str = Query("ui", description="Execution channel (ui|supervisor|system)"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    pa = one("SELECT * FROM pending_actions WHERE pending_id=:pid", pid=pending_id)
    if not pa:
        raise HTTPException(status_code=404, detail=f"Pending action not found: {pending_id}")

    policy = load_policy()
    if not channel:
        channel = get_channel(request, default="ui")
    actor = get_actor(request, channel=channel)
    subject = str(actor.get("sub") or actor.get("email") or "anonymous")
    case_id = str(pa.get("case_id") or "")
    frm = str(pa.get("status") or "")
    mid = str(pa.get("materialization_id") or "") or None

    exec_body = {"pending_id": pending_id, "dry_run": bool(dry_run), "channel": channel}
    exec_req_hash = hashlib.sha256(json.dumps(exec_body, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    scoped_idem = _scoped_idem_key("/pending_actions/execute", subject, str(pa.get("card_id") or ""), idempotency_key) if idempotency_key else None

    # Idempotency replay/conflict (scoped)
    if scoped_idem and str(pa.get("execution_idempotency_key") or "") == scoped_idem:
        if str(pa.get("execution_request_hash") or "") and str(pa.get("execution_request_hash") or "") != exec_req_hash:
            pl = with_audit(
                {
                    "endpoint": "/pending_actions/execute",
                    "subject": subject,
                    "card_id": str(pa.get("card_id") or ""),
                    "pending_id": pending_id,
                    "idempotency_key": idempotency_key,
                    "expected_request_hash": str(pa.get("execution_request_hash") or ""),
                    "received_request_hash": exec_req_hash,
                },
                actor=actor,
                request=request,
                materialization_id=mid,
            )
            _audit_action(
                case_id=case_id,
                channel="system",
                action_type="IdempotencyConflict",
                payload=pl,
                result="blocked: Idempotency-Key reuse with different payload",
            )
            raise HTTPException(status_code=409, detail="Idempotency-Key reuse with different payload (request_hash mismatch).")

        if str(pa.get("status") or "") in ("executed", "blocked"):
            return {
                "pending_id": pending_id,
                "dry_run": False,
                "idempotent": True,
                "status": str(pa.get("status") or ""),
                "executed_action_id": str(pa.get("executed_action_id") or ""),
                "execution_result": str(pa.get("execution_result") or ""),
            }

    # RBAC + payload rule enforcement for execution
    risk_row = one("SELECT risk_score FROM agent_cases WHERE case_id=:cid", cid=case_id)
    case_risk = None
    if risk_row and risk_row.get("risk_score") is not None:
        try:
            case_risk = float(risk_row.get("risk_score"))
        except Exception:
            case_risk = None

    ok, reason = can_execute(
        policy,
        channel=channel,
        action_type=str(pa.get("action_type") or ""),
        role=actor.get("role"),
        payload=dict(pa.get("action_payload") or {}),
        case_risk_score=case_risk,
    )
    if not ok:
        if not dry_run:
            _audit_violation(
                request=request,
                actor=actor,
                case_id=case_id,
                channel=channel,
                pending_id=pending_id,
                frm=frm,
                to="(execute)",
                reason=f"rbac: {reason}",
                materialization_id=mid,
            )
        raise HTTPException(status_code=403, detail=reason)

    if pa.get("approval_required") and frm != "approved":
        if not dry_run:
            _audit_violation(
                request=request,
                actor=actor,
                case_id=case_id,
                channel=channel,
                pending_id=pending_id,
                frm=frm,
                to="executed",
                reason="execution attempted without approval",
                materialization_id=mid,
            )
        raise HTTPException(status_code=409, detail="Pending action requires approval before execution.")

    action_type = str(pa.get("action_type") or "")
    base_payload = dict(pa.get("action_payload") or {})
    base_payload["_actor"] = actor
    base_payload["materialization_id"] = mid or ""
    payload = with_audit(base_payload, actor=actor, request=request, materialization_id=mid)

    res = execute_action(
        case_id=case_id,
        channel=channel,
        action_type=action_type,
        payload=payload,
        dry_run=bool(dry_run),
    )

    to_status = "executed" if res.get("ok") else "blocked"

    if dry_run:
        if not _pa_transition_allowed(policy, frm, to_status):
            raise HTTPException(status_code=409, detail=f"Illegal pending_action transition: {frm} -> {to_status}")
        return {"pending_id": pending_id, "dry_run": True, "would_transition": f"{frm}->{to_status}", "execution": res}

    if not _pa_transition_allowed(policy, frm, to_status):
        _audit_violation(
            request=request,
            actor=actor,
            case_id=case_id,
            channel=channel,
            pending_id=pending_id,
            frm=frm,
            to=to_status,
            reason=f"illegal transition {frm} -> {to_status}",
            materialization_id=mid,
        )
        raise HTTPException(status_code=409, detail=f"Illegal pending_action transition: {frm} -> {to_status}")

    if res.get("ok"):
        action_id = res.get("action_id")
        q(
            """
            UPDATE pending_actions
            SET status='executed',
                executed_action_id=:aid,
                execution_idempotency_key=COALESCE(:eik, execution_idempotency_key),
                execution_request_hash=COALESCE(:erh, execution_request_hash),
                execution_result=:er,
                updated_at=now()
            WHERE pending_id=:pid
            """,
            aid=action_id,
            er=str(res.get("result") or "ok"),
            eik=scoped_idem,
            erh=exec_req_hash,
            pid=pending_id,
        )
    else:
        q(
            """
            UPDATE pending_actions
            SET status='blocked',
                execution_result=:er,
                execution_idempotency_key=COALESCE(:eik, execution_idempotency_key),
                execution_request_hash=COALESCE(:erh, execution_request_hash),
                updated_at=now()
            WHERE pending_id=:pid
            """,
            er=str(res.get("result") or res.get("error") or "blocked"),
            eik=scoped_idem,
            erh=exec_req_hash,
            pid=pending_id,
        )

    return {"pending_id": pending_id, "dry_run": False, "transition": f"{frm}->{to_status}", "execution": res}
