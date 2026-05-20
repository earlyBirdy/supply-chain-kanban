"""Kinetic execution pipeline.

This module is the single place where the system "changes the world".
It:
1) validates guardrails (demo version)
2) records an auditable action row
3) calls the connector / writeback adapter
4) writes back the result

In a Foundry-like system, this is the boundary between ontology & operational systems.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Tuple

from .db import q, one
from .connectors.governed_writeback import connector_family_for_action, get_governed_writeback_adapter, spec_for
from .policy_store import load_policy
from .lifecycle_store import allowed_transitions as lifecycle_allowed_transitions, lifecycle_object
from .audit import with_audit


def _card_policy() -> dict:
    pol = load_policy() or {}
    return pol.get("card_status_policy", {}) or {}


def _allowed_transitions() -> dict:
    model = lifecycle_allowed_transitions("kanban_card")
    if model:
        return model
    cps = _card_policy()
    return cps.get("allowed_transitions", {}) or {}


def _resolve_gate() -> dict:
    life = lifecycle_object("kanban_card") or {}
    gate = (((life.get("guardrails") or {}).get("approval_gate")) or {})
    if gate:
        return {
            "require_channel": gate.get("require_channel"),
            "require_high_risk_case": gate.get("require_case_risk_score_gte") is not None,
            "high_risk_threshold": gate.get("require_case_risk_score_gte"),
        }
    cps = _card_policy()
    return ((cps.get("approval_gate") or {}).get("resolve") or {})


def _guardrails(case_id: str, channel: str, action_type: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
    qty = payload.get("qty")
    if qty is not None:
        try:
            if float(qty) < 0:
                return False, "blocked: qty must be >= 0"
        except Exception:
            return False, "blocked: qty must be numeric"

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

        if card.get("case_id") and str(card["case_id"]) != str(case_id):
            return False, "blocked: card.case_id must match request.case_id"

        current_status = str(card.get("status") or "todo")
        allowed = set(_allowed_transitions().get(current_status, []) or [])
        if new_status == current_status:
            return True, "ok"
        if new_status not in allowed:
            return False, f"blocked: illegal card status transition {current_status} -> {new_status}"

        sla = (((lifecycle_object("kanban_card") or {}).get("guardrails") or {}) or (_card_policy().get("sla_guardrails") or {}))
        if new_status == "blocked":
            if bool(sla.get("blocked_requires_reason", True)) and not payload.get("blocked_reason"):
                return False, "blocked: blocked_reason is required when new_status='blocked'"
        if new_status == "resolved":
            if bool(sla.get("resolved_requires_timestamp", True)) and not payload.get("resolved_at"):
                return False, "blocked: resolved_at is required when new_status='resolved' (ISO 8601)"

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


def _writeback_summary(action_type: str, payload: Dict[str, Any], preview: Dict[str, Any]) -> str:
    target = preview.get("target_system") or "an operational system"
    resource = payload.get("resource_id") or payload.get("supplier_id") or payload.get("card_id") or "the selected object"
    if action_type == "ExpediteShipment":
        return f"Would send an expedite request for {resource} to {target}."
    if action_type == "TriggerPurchase":
        return f"Would create a governed purchase writeback for {resource} in {target}."
    if action_type == "RebalanceAllocation":
        return f"Would rebalance supply allocation for {resource} in {target}."
    if action_type == "OpenSupplierTicket":
        return f"Would open a governed supplier portal escalation for {resource}."
    if action_type == "CreateOpsTicket":
        return f"Would create a governed ops ticket for {resource} in {target}."
    return f"Would perform governed writeback for {action_type} in {target}."


def _persist_writeback_receipt(
    *,
    case_id: str,
    pending_id: str | None,
    action_id: str,
    action_type: str,
    adapter_result: Dict[str, Any],
    payload: Dict[str, Any],
) -> None:
    receipt = dict(adapter_result.get("receipt") or {})
    spec = spec_for(action_type)
    q(
        """
        INSERT INTO governed_writebacks(
          action_id, case_id, pending_id, adapter_name, connector_name, target_system,
          action_type, status, external_ref, policy_gate, approval_state,
          connector_family, approval_policy, receipt_summary,
          request_payload, result_payload
        )
        VALUES(
          CAST(:aid AS UUID), CAST(:cid AS UUID), CAST(:pid AS UUID), :adapter, :connector, :target,
          :atype, :status, :external_ref, :policy_gate, :approval_state,
          :connector_family, :approval_policy, :receipt_summary,
          CAST(:request_payload AS JSONB), CAST(:result_payload AS JSONB)
        )
        """,
        aid=str(action_id),
        cid=str(case_id),
        pid=str(pending_id) if pending_id else None,
        adapter=str(adapter_result.get("adapter_name") or "governed_writeback"),
        connector=str(adapter_result.get("connector_name") or "unknown"),
        target=str(adapter_result.get("target_system") or "erp.unspecified"),
        atype=action_type,
        status="ok" if adapter_result.get("ok") else "blocked",
        external_ref=str(adapter_result.get("external_ref") or ""),
        policy_gate=str(adapter_result.get("policy_gate") or ""),
        approval_state=str(adapter_result.get("approval_state") or ""),
        connector_family=str(adapter_result.get("connector_family") or connector_family_for_action(action_type)),
        approval_policy=str(adapter_result.get("approval_policy_key") or spec.get("approval_policy_key") or "default"),
        receipt_summary=str(receipt.get("summary") or adapter_result.get("message") or "governed writeback"),
        request_payload=json.dumps(payload),
        result_payload=json.dumps(adapter_result),
    )


def execute_action(
    *,
    case_id: str,
    channel: str,
    action_type: str,
    payload: Dict[str, Any],
    dry_run: bool = False,
) -> dict:
    payload = dict(payload or {})
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

    adapter = get_governed_writeback_adapter()
    is_local_action = action_type == "UpdateCardStatus"

    if dry_run:
        if not passed:
            return {"ok": False, "dry_run": True, "blocked": True, "message": msg}
        if is_local_action:
            preview = {
                "connector": "local_db",
                "update": {"card_id": str(payload.get("card_id")), "new_status": str(payload.get("new_status"))},
            }
            return {
                "ok": True,
                "dry_run": True,
                "message": "ok (dry_run)",
                "would_execute": preview,
                "simulation": {
                    "mode": "state_transition",
                    "summary": f"Would move card {payload.get('card_id', '—')} to {payload.get('new_status', '—')}",
                },
            }
        preview = adapter.preview(action_type=action_type, payload=payload)
        return {
            "ok": True,
            "dry_run": True,
            "message": "ok (dry_run)",
            "would_execute": {
                "connector": preview.get("connector_name") or "mock",
                "adapter": preview.get("adapter"),
                "target_system": preview.get("target_system"),
                "action_type": action_type,
            },
            "simulation": {
                "mode": "governed_writeback",
                "summary": _writeback_summary(action_type, payload, preview),
                "writeback_preview": preview,
            },
        }

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
        return {"ok": False, "blocked": True, "message": msg, "action_id": str(row[0]), "result": msg}

    if is_local_action:
        card_id = str(payload.get("card_id"))
        new_status = str(payload.get("new_status"))
        blocked_reason = payload.get("blocked_reason")
        resolved_at = payload.get("resolved_at")

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
            "result": f"ok: card status updated -> {new_status}",
            "action_id": str(row[0]),
            "connector": "local_db",
            "data": {
                "card_id": str(upd[0]) if upd else card_id,
                "status": str(upd[1]) if upd else new_status,
                "blocked_reason": upd[2] if upd else blocked_reason,
                "resolved_at": str(upd[3]) if upd and upd[3] else resolved_at,
            },
        }

    adapter_result = adapter.execute(action_type=action_type, payload=payload).as_dict()

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
        res=str(adapter_result.get("message") or ""),
    ).fetchone()

    try:
        _persist_writeback_receipt(
            case_id=case_id,
            pending_id=str(payload.get("pending_id") or "") or None,
            action_id=str(row[0]),
            action_type=action_type,
            adapter_result=adapter_result,
            payload=payload,
        )
    except Exception:
        pass

    return {
        "ok": bool(adapter_result.get("ok")),
        "message": str(adapter_result.get("message") or ""),
        "result": str(adapter_result.get("message") or ""),
        "action_id": str(row[0]),
        "connector": str(adapter_result.get("connector_name") or "mock"),
        "writeback": {
            "adapter": adapter_result.get("adapter_name"),
            "target_system": adapter_result.get("target_system"),
            "external_ref": adapter_result.get("external_ref"),
            "policy_gate": adapter_result.get("policy_gate"),
            "approval_state": adapter_result.get("approval_state"),
        },
        "data": adapter_result.get("connector_data") or {},
    }
