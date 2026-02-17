from __future__ import annotations
import os
from pathlib import Path


from typing import Any, Dict, List

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel, Field

from ...db import one, all, q
from ...execution import execute_action
from ...policy_store import load_policy
from ...approval import approval_required_for_action
from ...auth import get_actor, get_channel
from ...audit import with_audit
from ...connectors import nova as nova_connector
from ...config import DEV_MODE
from ...policy_store import policy_revision

router = APIRouter()


class DemoNovaRunRequest(BaseModel):
    card_id: str = Field(..., description="KanbanCard UUID")
    objective: str = Field("both", description="risk_mitigation | agentic_workflow | both")
    dry_run: bool = Field(True, description="Validate proposed actions without writing audit/DB")
    execute: bool = Field(False, description="If true and dry_run=false, execute first N actions")
    max_execute: int = Field(1, ge=0, le=10, description="Max actions to execute when execute=true")


def _load_context(card_id: str) -> Dict[str, Any]:
    card = one("SELECT * FROM v_kanban_cards WHERE card_id=:id", id=card_id)
    if not card:
        raise HTTPException(status_code=404, detail=f"KanbanCard not found: {card_id}")

    case = None
    if card.get("case_id"):
        case = one("SELECT * FROM agent_cases WHERE case_id=:cid", cid=card["case_id"])

    resource_id = (case or {}).get("resource_id") or card.get("resource_id")

    ops = all(
        "SELECT * FROM ops_signals WHERE resource_id=:rid ORDER BY ts DESC LIMIT 10",
        rid=resource_id,
    ) if resource_id else []
    mkt = all(
        "SELECT * FROM market_signals WHERE resource_id=:rid ORDER BY ts DESC LIMIT 10",
        rid=resource_id,
    ) if resource_id else []

    return {
        "card": card,
        "case": case or {},
        "signals": {"ops": ops, "market": mkt},
    }


@router.post("/nova/run")
def demo_nova_run(
    request: Request,
    req: DemoNovaRunRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    """Hackathon demo endpoint (no DB materialization).

    Card -> Nova -> proposed actions -> (dry_run) validation -> (optional) execute + audit.
    """
    channel = get_channel(request, default="ui")
    actor = get_actor(request, channel=channel)

    ctx = _load_context(req.card_id)
    gen = nova_connector.generate(ctx, objective=req.objective)

    proposals: List[Dict[str, Any]] = []
    validations: List[Dict[str, Any]] = []
    executions: List[Dict[str, Any]] = []

    proposed_actions = gen.proposed_actions or []
    for a in proposed_actions:
        if not isinstance(a, dict):
            continue
        at = a.get("action_type") or a.get("type")
        pl = a.get("payload") or {}
        proposals.append(
            {
                "action_type": str(at),
                "payload": dict(pl),
                "rationale": a.get("rationale") or a.get("why") or "",
            }
        )

    case_id = str((ctx.get("case") or {}).get("case_id") or ctx["card"].get("case_id") or "")
    if not case_id:
        raise HTTPException(status_code=400, detail="Card is missing case_id binding (cannot validate actions).")

    for p in proposals:
        res = execute_action(
            case_id=case_id,
            channel=channel,
            action_type=str(p["action_type"]),
            payload=dict(p["payload"]),
            dry_run=True,
        )
        validations.append({"proposal": p, "validation": res})

    if req.execute and (not req.dry_run):
        to_exec = proposals[: int(req.max_execute)]
        for p in to_exec:
            payload = with_audit({**(p["payload"] or {}), "_actor": actor}, actor=actor, request=request, materialization_id="")
            res = execute_action(
                case_id=case_id,
                channel=channel,
                action_type=str(p["action_type"]),
                payload=payload,
                dry_run=False,
            )
            executions.append({"proposal": p, "execution": res})

    return {
        "ok": True,
        "idempotency_key": idempotency_key,
        "mode": "bedrock" if "bedrock" in (gen.message or "") else "mock",
        "message": gen.message,
        "context": {
            "card_id": req.card_id,
            "case_id": case_id,
            "resource_id": (ctx.get("case") or {}).get("resource_id") or ctx["card"].get("resource_id"),
        },
        "recommendation": gen.recommendation,
        "proposals": proposals,
        "validations": validations,
        "executions": executions,
    }
class DemoNovaMaterializeRequest(DemoNovaRunRequest):
    """Materialize recommendations and pending actions for UI."""
    # keep defaults; materialization always happens
    dry_run: bool = Field(True, description="Validate proposals without executing; still materializes recs + pending actions.")
    execute: bool = Field(False, description="Optionally auto-execute first N actions (writes audit) - typically false for approval flow.")


@router.post("/nova/run_and_materialize")
def demo_nova_run_and_materialize(
    request: Request,
    req: DemoNovaMaterializeRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    """Card -> Nova -> write agent_recommendations + pending_actions -> (dry_run) validation -> (optional) execute + audit.

    UI flow:
      AI recommendation -> pending actions (await approval) -> execute -> audit.
    """
    policy = load_policy()
    channel = get_channel(request, default="ui")
    actor = get_actor(request, channel=channel)
    subject = str(actor.get("sub") or actor.get("email") or "anonymous")
    endpoint = "/demo/nova/run_and_materialize"

    ctx = _load_context(req.card_id)
    gen = nova_connector.generate(ctx, objective=req.objective)

    policy = load_policy()
    import uuid, json, hashlib
    batch_id = str(uuid.uuid4())
    idem_key = idempotency_key or batch_id
    req_hash = hashlib.sha256(json.dumps(req.model_dump(), sort_keys=True, default=str).encode("utf-8")).hexdigest()

    # Idempotency: if (card_id, idem_key) already materialized, return existing materialization
    card_id_for_idem = str(ctx["card"].get("card_id") or "")
    existing = None
    if card_id_for_idem and idem_key:
        existing = one(
            "SELECT materialization_id, request_hash, expires_at FROM materializations WHERE endpoint=:ep AND subject=:sub AND card_id=:cid AND idempotency_key=:k",
            ep=endpoint,
            sub=subject,
            cid=card_id_for_idem,
            k=idem_key,
        )
        if existing:
            if str(existing.get("request_hash") or "") != req_hash:
                # Audit idempotency conflicts (non-dry-run endpoints: this is a write intent)
                try:
                    case_id_for_audit = str((ctx.get("case") or {}).get("case_id") or ctx.get("case_id") or "")
                    q(
                        """INSERT INTO agent_actions (case_id, channel, action_type, payload, result)
                           VALUES (:case_id, 'system', 'IdempotencyConflict', :pl::jsonb, :res)""",
                        case_id=case_id_for_audit,
                        pl=json.dumps(
                            with_audit(
                                {
                                    "endpoint": endpoint,
                                    "subject": subject,
                                    "card_id": card_id_for_idem,
                                    "idempotency_key": idem_key,
                                    "existing_materialization_id": str(existing.get("materialization_id") or ""),
                                    "expected_request_hash": str(existing.get("request_hash") or ""),
                                    "received_request_hash": req_hash,
                                },
                                actor=actor,
                                request=request,
                                materialization_id=str(existing.get("materialization_id") or ""),
                            ),
                            default=str,
                        ),
                        res="blocked: Idempotency-Key reuse with different payload",
                    )
                except Exception:
                    pass
                raise HTTPException(status_code=409, detail="Idempotency-Key reuse with different payload (request_hash mismatch).")
            # TTL expiry: if expired, drop record and allow a new materialization with the same key
            exp = existing.get("expires_at")
            try:
                if exp is not None and getattr(exp, "tzinfo", None) is not None:
                    now = datetime.now(timezone.utc)
                    if exp <= now:
                        q(
                            "DELETE FROM materializations WHERE materialization_id=:mid",
                            mid=str(existing["materialization_id"]),
                        )
                        existing = None
            except Exception:
                pass
        if existing:
            batch_id = str(existing["materialization_id"])
    proposals: List[Dict[str, Any]] = []
    validations: List[Dict[str, Any]] = []
    executions: List[Dict[str, Any]] = []

    proposed_actions = gen.proposed_actions or []
    for a in proposed_actions:
        if not isinstance(a, dict):
            continue
        at = a.get("action_type") or a.get("type")
        pl = a.get("payload") or {}
        proposals.append({
            "action_type": str(at),
            "payload": dict(pl),
            "rationale": a.get("rationale") or a.get("why") or "",
        })

    case_id = str((ctx.get("case") or {}).get("case_id") or ctx["card"].get("case_id") or "")
    if not case_id:
        raise HTTPException(status_code=400, detail="Card is missing case_id binding (cannot materialize).")

    card_id = str(ctx["card"].get("card_id") or "")

    # Ensure materialization record exists (even without external idempotency key)
    if not existing:
        # Idempotency TTL
        ttl_hours = int(((policy or {}).get('idempotency_policy') or {}).get('ttl_hours') or 24)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
        q(
            """INSERT INTO materializations (materialization_id, endpoint, subject, card_id, case_id, idempotency_key, request_hash, objective, source, expires_at)
               VALUES (:mid, :ep, :sub, :cid, :case_id, :k, :h, :obj, :src, :expires_at)""",
            mid=batch_id,
            ep=endpoint,
            sub=subject,
            cid=card_id,
            case_id=case_id,
            k=idem_key,
            h=req_hash,
            obj=req.objective,
            src="nova",
            expires_at=expires_at,
        )

    if existing:
        # Fetch already materialized entities
        recs = all("SELECT * FROM agent_recommendations WHERE materialization_id=:mid ORDER BY rank ASC", mid=batch_id)
        pas = all("SELECT * FROM v_pending_actions WHERE materialization_id=:mid ORDER BY rank ASC", mid=batch_id)

        # Optionally run validations (dry_run) for UI preview
        validations = []
        for p in pas:
            res = execute_action(
                case_id=str(p["case_id"]),
                channel="ui",
                action_type=str(p["action_type"]),
                payload=dict(p.get("action_payload") or {}),
                dry_run=True,
            )
            validations.append({"pending_id": str(p["pending_id"]), "ok": bool(res.get("ok")), "result": res})

        return {
            "ok": True,
            "materialization_id": batch_id,
            "idempotent_replay": True,
            "recommendation": gen.recommendation,
            "proposals": proposals,
            "materialized": {"recommendations": recs, "pending_actions": pas},
            "validations": validations,
            "executions": [],
        }

    # Supersede prior pending actions for this card (dedupe/versioning)
    mat_pol = (policy.get('materialization_policy') or {})
    supersede_statuses = tuple(mat_pol.get('supersede_statuses') or ['pending','approved'])
    if card_id:
        prev = all(
            """SELECT pending_id FROM pending_actions
               WHERE card_id=:cid AND status = ANY(:sts)""",
            cid=card_id,
            sts=list(supersede_statuses),
        )
        if prev:
            q(
                """UPDATE pending_actions
                   SET status='canceled',
                       superseded_by_materialization_id=:bid,
                       superseded_at=now(),
                       canceled_reason=COALESCE(canceled_reason,'superseded'),
                       updated_at=now(),
                       execution_result=COALESCE(execution_result,'') || ' | superseded_by=' || :bid
                   WHERE card_id=:cid AND status = ANY(:sts)""",
                bid=batch_id,
                cid=card_id,
                sts=list(supersede_statuses),
            )
            # Audit the supersede event (system)
            q(
                """INSERT INTO agent_actions (case_id, channel, action_type, payload, result)
                   VALUES (:case_id, 'system', 'SupersedePendingActions', :pl::jsonb, :res)""",
                case_id=case_id,
                pl={'card_id': card_id, 'materialization_id': batch_id, 'superseded_pending_ids': [str(r['pending_id']) for r in prev][:50]},
                res=f"ok: canceled {len(prev)} pending actions",
            )

    base_risk = int((ctx.get("case") or {}).get("risk_score") or 70)
    base_conf = float((ctx.get("case") or {}).get("confidence") or 0.7)
    source = "amazon_nova" if "bedrock" in (gen.message or "") else "mock_nova"

    # Materialize: recommendations + pending actions
    for i, p in enumerate(proposals, start=1):
        payload = dict(p["payload"])
        payload["_narrative"] = gen.recommendation or {}
        payload["_rationale"] = p.get("rationale") or ""
        payload["_confidence"] = base_conf
        payload["_source"] = source

        service_score = 80 if p["action_type"] == "ExpediteShipment" else 70
        cost_score = 55 if p["action_type"] == "ExpediteShipment" else 65
        risk_score = min(100, max(0, base_risk))
        decision_score = 75

        q(
            """
            INSERT INTO agent_recommendations
                (case_id, materialization_id, rank, action_type, action_payload, service_score, cost_score, risk_score, decision_score)
            VALUES (:cid, :mid, :rk, :at, :pl::jsonb, :ss, :cs, :rs, :ds)
            """,
            cid=case_id,
            mid=batch_id,
            ep=endpoint,
            sub=subject,
            rk=i,
            at=str(p["action_type"]),
            pl=payload,
            ss=service_score,
            cs=cost_score,
            rs=risk_score,
            ds=decision_score,
        )

        # Policy-aware approval requirement inference
        execution_target = "local_db" if p["action_type"] == "UpdateCardStatus" else "erp"
        approval_required = approval_required_for_action(
            policy,
            action_type=str(p["action_type"]),
            payload=dict(p["payload"]),
            execution_target=execution_target,
        )

        q(
            """
            INSERT INTO pending_actions
                (case_id, card_id, materialization_id, status, approval_required, action_type, action_payload, rationale, rank)
            VALUES (:cid, :kid, :mid, 'pending', :ar, :at, :pl::jsonb, :ra, :rk)
            """,
            cid=case_id,
            kid=card_id if card_id else None,
            mid=batch_id,
            ep=endpoint,
            sub=subject,
            ar=approval_required,
            at=str(p["action_type"]),
            pl=dict(p["payload"]),
            ra=str(p.get("rationale") or ""),
            rk=i,
        )

    # Validate proposals (dry-run) for UI preview
    for p in proposals:
        res = execute_action(
            case_id=case_id,
            channel="ui",
            action_type=str(p["action_type"]),
            payload=dict(p["payload"]),
            dry_run=True,
        )
        validations.append({"proposal": p, "validation": res})

    # Optional auto-execute (not typical)
    if req.execute and (not req.dry_run):
        to_exec = proposals[: int(req.max_execute)]
        for p in to_exec:
            payload = with_audit({**(dict(p["payload"]) or {}), "_actor": actor, "materialization_id": batch_id}, actor=actor, request=request, materialization_id=batch_id)
            res = execute_action(
                case_id=case_id,
                channel="ui",
                action_type=str(p["action_type"]),
                payload=payload,
                dry_run=False,
            )
            executions.append({"proposal": p, "execution": res})

    recs = all(
        """
        SELECT * FROM agent_recommendations
        WHERE case_id=:cid
        ORDER BY created_at DESC, rank ASC
        LIMIT 50
        """,
        cid=case_id,
    )
    pend = all(
        """
        SELECT * FROM v_pending_actions
        WHERE case_id=:cid
        ORDER BY updated_at DESC, rank ASC
        LIMIT 50
        """,
        cid=case_id,
    )

    return {
        "ok": True,
        "materialization_id": batch_id,
        "idempotency_key": idem_key,
        "mode": "bedrock" if "bedrock" in (gen.message or "") else "mock",
        "message": gen.message,
        "context": {"card_id": req.card_id, "case_id": case_id},
        "recommendation": gen.recommendation,
        "proposals": proposals,
        "validations": validations,
        "executions": executions,
        "materialized": {"recommendations": recs, "pending_actions": pend},
    }


@router.get("/summary")
def demo_summary():
    """Quick demo snapshot for UI/debug."""
    p = load_policy()
    counts = one(
        """
        SELECT
          (SELECT COUNT(*) FROM kanban_cards) AS cards,
          (SELECT COUNT(*) FROM agent_cases) AS cases,
          (SELECT COUNT(*) FROM pending_actions WHERE status='pending') AS pending_actions,
          (SELECT COUNT(*) FROM agent_actions) AS actions,
          (SELECT COUNT(*) FROM agent_recommendations) AS recommendations
        """
    ) or {}
    last_pred = one("SELECT MAX(ts) AS last_prediction_ts FROM agent_predictions") or {}
    last_action = one("SELECT MAX(created_at) AS last_action_ts FROM agent_actions") or {}
    return {
        "ok": True,
        "policy_revision": policy_revision,
        "policy_version": (p or {}).get("version"),
        "counts": counts,
        "last": {
            "prediction_ts": last_pred.get("last_prediction_ts"),
            "action_ts": last_action.get("last_action_ts"),
        },
    }


def _exec_sql_script(sql_text: str) -> None:
    """Execute a (simple) SQL script with multiple statements."""
    from ...db import engine
    # naive split is OK for our seed scripts (no functions/dollar-quoting)
    statements = []
    buf = []
    for line in sql_text.splitlines():
        s = line.strip()
        if not s or s.startswith("--"):
            continue
        buf.append(line)
        if ";" in line:
            joined = "\n".join(buf)
            parts = joined.split(";")
            for part in parts[:-1]:
                if part.strip():
                    statements.append(part.strip())
            buf = [parts[-1]] if parts[-1].strip() else []
    if buf and "\n".join(buf).strip():
        statements.append("\n".join(buf).strip())

    with engine.begin() as conn:
        for st in statements:
            conn.exec_driver_sql(st)


@router.post("/reset")
def demo_reset():
    """Reset DB to demo seed. DEV_MODE only."""
    if not DEV_MODE:
        raise HTTPException(status_code=403, detail="demo/reset is disabled (DEV_MODE=0)")
    repo_root = Path(__file__).resolve().parents[4]  # .../agent_runtime/app/api/routers -> repo root
    seed_path = repo_root / "seed" / "01_seed_demo.sql"
    if not seed_path.exists():
        raise HTTPException(status_code=500, detail=f"Seed file missing: {seed_path}")
    sql_text = seed_path.read_text(encoding="utf-8")
    _exec_sql_script(sql_text)
    return {"ok": True, "reset": True}


# --- Demo narrative scenarios (v26) ---


class DemoScenarioRequest(BaseModel):
    name: str = Field(
        "card_resolve_approval",
        description="Scenario name. See /demo/scenarios.",
    )
    reset_first: bool = Field(False, description="If true, run /demo/reset first (DEV_MODE only).")
    dry_run: bool = Field(False, description="If true, do not write DB/audit; only return the plan.")

    # knobs
    risk_score: int = Field(85, ge=0, le=100, description="Risk score for the created case")
    auto_approve: bool = Field(True, description="If true, auto-approve the pending action as supervisor")
    auto_execute: bool = Field(True, description="If true, auto-execute the approved action as supervisor")
    include_blocked_attempt: bool = Field(True, description="If true, attempt the action as ui (expected to be blocked)")


@router.get("/scenarios")
def list_demo_scenarios():
    return {
        "ok": True,
        "scenarios": [
            {
                "name": "card_resolve_approval",
                "description": (
                    "Create a high-risk case + card, propose a resolve action as a pending action, "
                    "show that operator(ui) resolve is blocked, then supervisor approves+executes, "
                    "and finally show audit trail references."
                ),
            }
        ],
    }


@router.post("/run_scenario")
def run_demo_scenario(request: Request, req: DemoScenarioRequest):
    """Run a canned scenario to generate a clean demo narrative.

    This endpoint is intentionally deterministic and UI-friendly.
    """

    if req.reset_first:
        if not DEV_MODE:
            raise HTTPException(status_code=403, detail="demo/reset is disabled (DEV_MODE=0)")
        # Reuse local helper directly to avoid extra HTTP hops.
        demo_reset()

    # DRY RUN: return the plan without touching DB.
    if req.dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "scenario": req.name,
            "plan": {
                "would_create": ["agent_case", "kanban_card", "pending_action(UpdateCardStatus->resolved)"]
                + (["blocked_attempt(ui)"] if req.include_blocked_attempt else [])
                + (["decision(approve)"] if req.auto_approve else [])
                + (["execute(supervisor)"] if req.auto_execute else []),
                "policy_expectations": {
                    "resolve_requires_channel": "supervisor",
                    "resolve_requires_high_risk": True,
                    "threshold": 70,
                },
            },
        }

    if req.name != "card_resolve_approval":
        raise HTTPException(status_code=400, detail=f"Unknown scenario: {req.name}")

    # Actors
    operator_actor = get_actor(request, channel="ui")
    supervisor_actor = {
        "sub": "demo-supervisor",
        "email": "demo-supervisor@example.com",
        "role": "supervisor",
        "channel": "supervisor",
    }

    # Create case + card
    import uuid
    import json

    resource_id = f"DEMO-RES-{uuid.uuid4().hex[:8]}"

    case_row = q(
        """
        INSERT INTO agent_cases(resource_id, scope, risk_score, confidence, status, owner, root_signals)
        VALUES(:rid, '{}'::jsonb, :risk, 0.85, 'AT_RISK', :owner, '{}'::jsonb)
        RETURNING case_id
        """,
        rid=resource_id,
        risk=int(req.risk_score),
        owner=str(operator_actor.get("email") or operator_actor.get("sub") or "operator"),
    ).fetchone()

    case_id = str(case_row[0])

    card_row = q(
        """
        INSERT INTO kanban_cards(case_id, resource_id, scope, title, description, status, priority, assignee, tags)
        VALUES(:cid, :rid, '{}'::jsonb, :title, :desc, 'in_progress', 3, :asg, ARRAY['demo','scenario']::text[])
        RETURNING card_id
        """,
        cid=case_id,
        rid=resource_id,
        title=f"[DEMO] Late shipment risk for {resource_id}",
        desc="Scenario: resolve requires supervisor approval gate (channel + risk threshold).",
        asg=str(operator_actor.get("email") or "operator"),
    ).fetchone()

    card_id = str(card_row[0])

    # Create a pending action for resolve.
    resolved_at = datetime.now(timezone.utc).isoformat()
    pa_payload = {"card_id": card_id, "new_status": "resolved", "resolved_at": resolved_at}
    pending_row = q(
        """
        INSERT INTO pending_actions(case_id, card_id, status, approval_required, action_type, action_payload, rationale, rank)
        VALUES(:cid, :kid, 'pending', true, :at, CAST(:pl AS JSONB), :rat, 0)
        RETURNING pending_id
        """,
        cid=case_id,
        kid=card_id,
        at="UpdateCardStatus",
        pl=json.dumps(pa_payload),
        rat="Resolve card (high-impact): requires supervisor channel + high-risk case.",
    ).fetchone()

    pending_id = str(pending_row[0])

    # Optional: show blocked attempt as operator(ui)
    blocked_attempt = None
    if req.include_blocked_attempt:
        pl = with_audit(
            {**pa_payload, "_actor": operator_actor},
            actor=operator_actor,
            request=request,
            materialization_id=None,
        )
        blocked_attempt = execute_action(
            case_id=case_id,
            channel="ui",
            action_type="UpdateCardStatus",
            payload=pl,
            dry_run=False,
        )

    # Approve as supervisor (DB transition + audit row)
    approval = None
    if req.auto_approve:
        q(
            """
            UPDATE pending_actions
            SET status='approved', approved_by=:ab, approved_at=now(), updated_at=now()
            WHERE pending_id=:pid
            """,
            ab=str(supervisor_actor.get("email")),
            pid=pending_id,
        )
        try:
            _audit_action_payload = with_audit(
                {"pending_id": pending_id, "decision": "approve"},
                actor=supervisor_actor,
                request=request,
                materialization_id=None,
            )
            q(
                """
                INSERT INTO agent_actions(case_id, channel, action_type, payload, result)
                VALUES(:cid, 'supervisor', 'PendingActionDecision', CAST(:pl AS JSONB), :res)
                """,
                cid=case_id,
                pl=json.dumps(_audit_action_payload),
                res="ok: approved",
            )
        except Exception:
            pass
        approval = {"ok": True, "status": "approved", "approved_by": supervisor_actor.get("email")}

    # Execute as supervisor
    execution = None
    if req.auto_execute:
        pl = with_audit(
            {**pa_payload, "_actor": supervisor_actor},
            actor=supervisor_actor,
            request=request,
            materialization_id=None,
        )
        res = execute_action(
            case_id=case_id,
            channel="supervisor",
            action_type="UpdateCardStatus",
            payload=pl,
            dry_run=False,
        )
        execution = res

        # mark pending action executed
        try:
            q(
                """
                UPDATE pending_actions
                SET status='executed', executed_action_id=:aid::uuid, execution_result=:er, updated_at=now()
                WHERE pending_id=:pid
                """,
                aid=str(res.get("action_id")),
                er=str(res.get("message")),
                pid=pending_id,
            )
        except Exception:
            pass

    return {
        "ok": True,
        "scenario": req.name,
        "created": {
            "case_id": case_id,
            "card_id": card_id,
            "pending_id": pending_id,
            "resource_id": resource_id,
        },
        "blocked_attempt": blocked_attempt,
        "approval": approval,
        "execution": execution,
        "next": {
            "audit": [
                f"/audit/by_case/{case_id}?limit=200",
                "/audit/recent?limit=50",
            ],
            "pending_actions": f"/pending_actions?case_id={case_id}",
            "card": f"/objects/cards/{card_id}",
        },
    }
