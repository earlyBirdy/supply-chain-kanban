"""Kinetic execution pipeline.

This module is the single place where the system "changes the world".
It:
1) validates guardrails (demo version)
2) records an auditable action row
3) calls the connector
4) writes back the result

In a Foundry-like system, this is the boundary between ontology & operational systems.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Tuple

from .db import q, one
from .connectors.erp import get_erp_connector
from .policy_store import load_policy
from .audit import with_audit


# --- Card status policy ---
# Loaded from governance/policy.yaml (hot-reload).


def _card_policy() -> dict:
    pol = load_policy() or {}
    return pol.get("card_status_policy", {}) or {}


def _allowed_transitions() -> dict:
    cps = _card_policy()
    return cps.get("allowed_transitions", {}) or {}


def _resolve_gate() -> dict:
    cps = _card_policy()
    return ((cps.get("approval_gate") or {}).get("resolve") or {})



def _guardrails(case_id: str, channel: str, action_type: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
    """Return (passed, message).

    Guardrails are intentionally explicit and conservative. They should be
    *business* rules, not just type checks.
    """
    # Generic demo guardrails
    qty = payload.get("qty")
    if qty is not None:
        try:
            if float(qty) < 0:
                return False, "blocked: qty must be >= 0"
        except Exception:
            return False, "blocked: qty must be numeric"


    # Card status transition guardrails
    if action_type == "UpdateCardStatus":
        card_id = payload.get("card_id")
        new_status = payload.get("new_status")
        if not card_id:
            return False, "blocked: payload.card_id is required"
        if new_status not in ("todo", "in_progress", "blocked", "resolved"):
            return False, "blocked: payload.new_status must be one of todo|in_progress|blocked|resolved"

        card = one(
            "SELECT card_id, case_id, status FROM kanban_cards WHERE card_id=:id",
            id=str(card_id),
        )
        if not card:
            return False, f"blocked: card not found: {card_id}"

        # The action is always attached to a case; require the card to belong to the same case.
        if card.get("case_id") and str(card["case_id"]) != str(case_id):
            return False, "blocked: card.case_id must match request.case_id"

        # State machine rules (allowed transitions)
        current_status = str(card.get("status") or "todo")
        allowed = set(_allowed_transitions().get(current_status, []) or [])
        if new_status == current_status:
            return True, "ok"  # idempotent
        if new_status not in allowed:
            return False, f"blocked: illegal card status transition {current_status} -> {new_status}"

        # SLA guardrails (policy-driven)
        sla = (_card_policy().get("sla_guardrails") or {})
        if new_status == "blocked":
            if bool(sla.get("blocked_requires_reason", True)) and not payload.get("blocked_reason"):
                return False, "blocked: blocked_reason is required when new_status='blocked'"
        if new_status == "resolved":
            if bool(sla.get("resolved_requires_timestamp", True)) and not payload.get("resolved_at"):
                return False, "blocked: resolved_at is required when new_status='resolved' (ISO 8601)"

            # Approval gate (policy-driven): resolving may require supervisor channel and/or high-risk case.
            gate = _resolve_gate()
            req_channel = gate.get("require_channel")
            if req_channel and channel != str(req_channel):
                return False, f"blocked: resolving a card requires channel='{req_channel}'"

            if bool(gate.get("require_high_risk_case", False)):
                threshold = int(gate.get("high_risk_threshold", 0) or 0)
                case = one(
                    "SELECT risk_score FROM agent_cases WHERE case_id=:cid",
                    cid=str(case_id),
                )
                if not case:
                    return False, "blocked: case not found"
                if int(case.get("risk_score") or 0) < threshold:
                    return False, f"blocked: resolving a card requires a high-risk case (risk_score >= {threshold})"

    return True, "ok"


def execute_action(
    *,
    case_id: str,
    channel: str,
    action_type: str,
    payload: Dict[str, Any],
    dry_run: bool = False,
) -> dict:
    """Execute an action and persist an audit record."""

    payload = dict(payload or {})
    # Ensure a normalized audit envelope exists on every audit row.
    if "_audit" not in payload:
        payload = with_audit(
            payload,
            actor=dict(payload.get("_actor") or {}),
            request=None,
            request_path="internal:execute_action",
            request_method="",
            materialization_id=str(payload.get("materialization_id") or payload.get("materialization_id")) if payload.get("materialization_id") is not None else None,
        )

    passed, msg = _guardrails(case_id, channel, action_type, payload)

    if dry_run:
        if not passed:
            return {"ok": False, "dry_run": True, "blocked": True, "message": msg}
        # Do not write audit / do not call connectors / do not mutate DB.
        preview: dict = {"ok": True, "dry_run": True, "message": "ok (dry_run)"}
        if action_type == "UpdateCardStatus":
            preview["would_execute"] = {
                "connector": "local_db",
                "update": {"card_id": str(payload.get("card_id")), "new_status": str(payload.get("new_status"))},
            }
        else:
            preview["would_execute"] = {
                "connector": get_erp_connector().name,
                "action_type": action_type,
            }
        return preview

    if not passed:
        row = q(
            """
            INSERT INTO agent_actions(case_id, channel, action_type, payload, result)
            VALUES(:cid, :ch, :at, CAST(:pl AS JSONB), :res)
            RETURNING action_id
            """,
            cid=case_id,
            ch=channel,
            at=action_type,
            pl=json.dumps(payload),
            res=msg,
        ).fetchone()
        return {"ok": False, "blocked": True, "message": msg, "action_id": str(row[0])}

    
    # Local (in-DB) Kinetic actions
    if action_type == "UpdateCardStatus":
        card_id = str(payload.get("card_id"))
        new_status = str(payload.get("new_status"))
        blocked_reason = payload.get("blocked_reason")
        resolved_at = payload.get("resolved_at")

        # Perform update
        upd = q(
            """
            UPDATE kanban_cards
            SET status=:st,
                blocked_reason=CASE WHEN :st='blocked' THEN :br ELSE NULL END,
                resolved_at=CASE WHEN :st='resolved' THEN CAST(:ra AS TIMESTAMPTZ) ELSE NULL END,
                last_activity_at=now(),
                updated_at=now()
            WHERE card_id=:id
            RETURNING card_id, status, blocked_reason, resolved_at
            """,
            st=new_status,
            br=blocked_reason,
            ra=resolved_at,
            id=card_id,
        ).fetchone()

        row = q(
            """
            INSERT INTO agent_actions(case_id, channel, action_type, payload, result)
            VALUES(:cid, :ch, :at, CAST(:pl AS JSONB), :res)
            RETURNING action_id
            """,
            cid=case_id,
            ch=channel,
            at=action_type,
            pl=json.dumps(payload),
            res=f"ok: card status updated -> {new_status}",
        ).fetchone()

        return {
            "ok": True,
            "message": f"card status updated -> {new_status}",
            "action_id": str(row[0]),
            "connector": "local_db",
            "data": {
                "card_id": str(upd[0]) if upd else card_id,
                "status": str(upd[1]) if upd else new_status,
                "blocked_reason": upd[2] if upd else blocked_reason,
                "resolved_at": str(upd[3]) if upd and upd[3] else resolved_at,
            },
        }

    connector = get_erp_connector()
    res = connector.execute(action_type, payload)

    row = q(
        """
        INSERT INTO agent_actions(case_id, channel, action_type, payload, result)
        VALUES(:cid, :ch, :at, CAST(:pl AS JSONB), :res)
        RETURNING action_id
        """,
        cid=case_id,
        ch=channel,
        at=action_type,
        pl=json.dumps(payload),
        res=res.message,
    ).fetchone()

    return {
        "ok": bool(res.ok),
        "message": res.message,
        "action_id": str(row[0]),
        "connector": connector.name,
        "data": res.data or {},
    }
