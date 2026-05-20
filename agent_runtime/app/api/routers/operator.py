from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from ...db import all as db_all, one as db_one
from ...execution import execute_action
from ...demo_story_store import customer_themes, story_personas
from ...demo_experience_store import branding_options, guided_scripts, seed_pack_catalog

router = APIRouter()


LANE_CONFIG = [
    ("todo", "Risk Board"),
    ("in_progress", "In Motion"),
    ("blocked", "Blocked"),
    ("resolved", "Resolved"),
]


def _lane_buckets(cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {key: [] for key, _ in LANE_CONFIG}
    for card in cards:
        grouped.setdefault(str(card.get("status") or "todo"), []).append(card)
    return [
        {"status": key, "label": label, "count": len(grouped.get(key, [])), "cards": grouped.get(key, [])}
        for key, label in LANE_CONFIG
    ]


def _board_filters(cards: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "assignees": sorted({str(card.get("assignee") or "unassigned") for card in cards}),
        "approval_states": sorted({str(card.get("approval_state") or "none") for card in cards}),
        "sla_states": sorted({str(card.get("sla_state") or "unknown") for card in cards}),
        "connector_families": sorted({str(card.get("connector_family") or "none") for card in cards}),
    }


def _operator_story(case_row: Dict[str, Any], card_row: Dict[str, Any] | None, pending_actions: List[Dict[str, Any]], scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    risk_score = int(case_row.get("risk_score") or 0)
    pending_count = sum(1 for row in pending_actions if str(row.get("status") or "") == "pending")
    approved_count = sum(1 for row in pending_actions if str(row.get("status") or "") == "approved")
    next_action = next((str(row.get("action_type") or "") for row in pending_actions if str(row.get("status") or "") in {"pending", "approved"}), "Monitor case")
    latest_scenario = scenarios[0] if scenarios else {}
    service_impact = latest_scenario.get("service_impact")
    cost_impact = latest_scenario.get("cost_impact")
    exposure = latest_scenario.get("risk_exposure")

    if pending_count:
        headline = f"Manager approval needed before {next_action} can change an operating system."
        next_step = "Review the simulation and scenario comparison, approve the action, then execute the governed writeback."
    elif approved_count:
        headline = f"Action is approved and ready for governed execution: {next_action}."
        next_step = "Run the simulation preview, confirm the connector destination, then execute when ready."
    else:
        headline = "No approvals are blocking this case right now."
        next_step = "Continue monitoring the board or materialize a new action from recommendations."

    impact_bits = []
    if service_impact is not None:
        impact_bits.append(f"service impact {service_impact}")
    if cost_impact is not None:
        impact_bits.append(f"cost impact {cost_impact}")
    if exposure is not None:
        impact_bits.append(f"risk exposure {exposure}")
    if not impact_bits:
        impact_bits.append("risk remains governed through the board workflow")

    return {
        "headline": headline,
        "why_it_matters": f"Case {case_row.get('case_id')} is risk {risk_score} on resource {case_row.get('resource_id')}",
        "business_impact": ", ".join(str(x) for x in impact_bits),
        "next_step": next_step,
        "board_status": str((card_row or {}).get("status") or case_row.get("status") or "—"),
        "owner": case_row.get("owner"),
    }


def _safe_num(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _scenario_comparison(scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not scenarios:
        return {"rows": [], "recommended_scenario": None, "chart": []}
    rows = []
    max_risk = max(_safe_num(s.get("risk_exposure")) for s in scenarios) or 1.0
    max_cost = max(_safe_num(s.get("cost_impact")) for s in scenarios) or 1.0
    max_service = max(_safe_num(s.get("service_impact")) for s in scenarios) or 1.0
    for scenario in scenarios:
        risk = _safe_num(scenario.get("risk_exposure"))
        cost = _safe_num(scenario.get("cost_impact"))
        service = _safe_num(scenario.get("service_impact"))
        score = round((risk * 0.5) + (cost * 0.3) + (service * 0.2), 2)
        row = dict(scenario)
        row["composite_score"] = score
        rows.append(row)
    rows.sort(key=lambda row: (row.get("composite_score") or 0, _safe_num(row.get("risk_exposure")), _safe_num(row.get("cost_impact"))))
    recommended = rows[0] if rows else None
    chart = []
    for row in rows:
        chart.append(
            {
                "scenario_name": row.get("scenario_name"),
                "risk_pct": round((_safe_num(row.get("risk_exposure")) / max_risk) * 100, 1),
                "cost_pct": round((_safe_num(row.get("cost_impact")) / max_cost) * 100, 1),
                "service_pct": round((_safe_num(row.get("service_impact")) / max_service) * 100, 1),
            }
        )
    return {"rows": rows, "recommended_scenario": recommended, "chart": chart}




def _connector_family_for(action_type: str) -> str:
    mapping = {
        "ExpediteShipment": "erp",
        "TriggerPurchase": "erp",
        "RebalanceAllocation": "erp",
        "OpenSupplierTicket": "supplier_portal",
        "CreateOpsTicket": "ticketing",
    }
    return mapping.get(str(action_type or ""), "none")


def _default_story_keys() -> tuple[str, str]:
    personas = story_personas()
    themes = customer_themes()
    persona_key = next(iter(personas.keys()), "coo")
    theme_key = next(iter(themes.keys()), "data_center")
    return persona_key, theme_key


def _story_context(persona: str | None, theme: str | None) -> dict:
    personas = story_personas()
    themes = customer_themes()
    default_persona, default_theme = _default_story_keys()
    persona_key = persona if persona in personas else default_persona
    theme_key = theme if theme in themes else default_theme
    return {
        "persona_key": persona_key,
        "persona": personas.get(persona_key, {}),
        "theme_key": theme_key,
        "theme": themes.get(theme_key, {}),
        "personas": personas,
        "themes": themes,
    }


def _pack_context(seed_pack: str | None) -> dict:
    packs = seed_pack_catalog()
    default_key = next(iter(packs.keys()), 'portfolio')
    pack_key = seed_pack if seed_pack in packs else default_key
    return {
        'seed_pack_key': pack_key,
        'seed_pack': packs.get(pack_key, {}),
        'seed_packs': packs,
    }


def _brand_context(brand: str | None) -> dict:
    brands = branding_options()
    default_key = next(iter(brands.keys()), 'neutral')
    brand_key = brand if brand in brands else default_key
    return {
        'brand_key': brand_key,
        'brand': brands.get(brand_key, {}),
        'brands': brands,
    }


def _resolved_story_context(persona: str | None, theme: str | None, seed_pack: str | None, brand: str | None) -> dict:
    pack_ctx = _pack_context(seed_pack)
    pack = pack_ctx['seed_pack']
    story = _story_context(persona or pack.get('default_persona'), theme or pack.get('default_theme'))
    brand_ctx = _brand_context(brand or pack.get('default_brand'))
    merged = {}
    merged.update(story)
    merged.update(pack_ctx)
    merged.update(brand_ctx)
    return merged


def _script_steps(seed_pack: str | None) -> list[dict[str, Any]]:
    pack = _pack_context(seed_pack)['seed_pack']
    scripts = guided_scripts()
    base = ((scripts.get('guided_buyer_walkthrough') or {}).get('steps') or [])
    resolved = []
    for idx, step in enumerate(base, start=1):
        row = dict(step)
        row['step_number'] = idx
        row['focus_case_id'] = pack.get('focus_case_id')
        row['pack_label'] = pack.get('label')
        resolved.append(row)
    return resolved


def _top_case_cards(limit: int = 5) -> List[Dict[str, Any]]:
    return db_all(
        """
        SELECT
          k.case_id,
          k.card_id,
          k.title,
          k.resource_id,
          k.assignee,
          k.status,
          COALESCE(k.case_risk_score, 0) AS case_risk_score,
          COALESCE((SELECT COUNT(*) FROM v_pending_actions p WHERE p.card_id = k.card_id AND p.status = 'pending'), 0) AS approvals_waiting,
          CASE
            WHEN k.status = 'resolved' THEN 'resolved'
            WHEN k.breached = true THEN 'breached'
            WHEN now() > (COALESCE(k.sla_due_at, (k.created_at + (k.sla_hours || ' hours')::interval)) - interval '8 hours') THEN 'at_risk'
            ELSE 'on_track'
          END AS sla_state
        FROM v_kanban_cards k
        ORDER BY COALESCE(k.case_risk_score, 0) DESC, k.updated_at DESC
        LIMIT :lim
        """,
        lim=limit,
    )


def _case_transparency(case_id: str) -> Dict[str, Any]:
    receipts = db_all(
        """
        SELECT
          r.receipt_id, r.case_id, r.trace_event_id, r.evidence_type, r.validation_status,
          r.confidence_score, r.summary, r.generated_at, r.receipt_payload,
          e.event_type, e.object_ref, e.observed_at, e.evidence_confidence, e.payload AS event_payload,
          s.source_id, s.label AS source_label, s.source_type, s.trust_tier, s.validation_method,
          a.anchor_id, a.ledger_name, a.anchor_status, a.tx_ref, a.content_hash, a.anchored_at, a.proof_payload
        FROM evidence_receipts r
        LEFT JOIN traceability_events e ON e.event_id = r.trace_event_id
        LEFT JOIN external_data_sources s ON s.source_id = e.source_id
        LEFT JOIN blockchain_anchors a ON a.receipt_id = r.receipt_id
        WHERE r.case_id=:cid
        ORDER BY r.generated_at DESC, r.confidence_score DESC
        """,
        cid=case_id,
    )
    sources = sorted({str(row.get("source_label") or row.get("source_id") or "unknown") for row in receipts})
    statuses = sorted({str(row.get("validation_status") or "pending") for row in receipts})
    avg_conf = round(sum(float(row.get("confidence_score") or 0) for row in receipts) / len(receipts), 2) if receipts else 0.0
    anchored = sum(1 for row in receipts if row.get("anchor_status") in {"stubbed", "anchored"})
    verified = sum(1 for row in receipts if row.get("validation_status") in {"verified", "cross_checked"})
    if not receipts:
        narrative = "No traceability evidence has been attached to this case yet. Treat AI recommendations as unproven until data sources are validated."
    elif verified == len(receipts) and anchored:
        narrative = "This case has validated external evidence and ledger proof stubs. The demo can explain what data was checked, which source provided it, and how the receipt would be anchored."
    else:
        narrative = "Some evidence is still pending validation. The system makes this visible instead of presenting blockchain as proof of truth."
    return {
        "case_id": case_id,
        "summary": {
            "receipt_count": len(receipts),
            "source_count": len(sources),
            "ledger_proof_count": anchored,
            "average_confidence": avg_conf,
            "validation_statuses": statuses,
        },
        "sources": sources,
        "receipts": receipts,
        "buyer_trust_panel": {
            "headline": "Why this data is trustworthy",
            "narrative": narrative,
            "proof_points": [
                "External data enters through named ERP, WMS, IoT, supplier, or news sources.",
                "Oracle-style validation status is shown before evidence is used as buyer-facing proof.",
                "Evidence confidence is scored separately from the AI recommendation confidence.",
                "BlockchainAnchor is a ledger proof stub; it preserves a proof pointer but does not claim the raw data was true by itself.",
            ],
        },
    }


@router.get("/summary")
def operator_summary():
    counts = db_one(
        """
        SELECT
          (SELECT COUNT(*) FROM kanban_cards) AS total_cards,
          (SELECT COUNT(*) FROM kanban_cards WHERE status='todo') AS todo_cards,
          (SELECT COUNT(*) FROM kanban_cards WHERE status='in_progress') AS in_progress_cards,
          (SELECT COUNT(*) FROM kanban_cards WHERE status='blocked') AS blocked_cards,
          (SELECT COUNT(*) FROM kanban_cards WHERE status='resolved') AS resolved_cards,
          (SELECT COUNT(*) FROM v_pending_actions WHERE status='pending') AS approvals_waiting,
          (SELECT COUNT(*) FROM v_pending_actions WHERE status='approved') AS ready_to_execute,
          (SELECT COUNT(*) FROM v_pending_actions WHERE status='blocked') AS execution_blocked,
          (SELECT COUNT(*) FROM agent_actions WHERE created_at >= now() - interval '24 hours') AS recent_actions_24h,
          (SELECT COUNT(*) FROM v_kanban_cards WHERE status <> 'resolved' AND breached = true) AS overdue_cards,
          (SELECT COUNT(*) FROM v_kanban_cards WHERE COALESCE(case_risk_score, 0) >= 70) AS high_risk_cards,
          (SELECT COUNT(*) FROM governed_writebacks WHERE created_at >= now() - interval '24 hours') AS writebacks_24h,
          (SELECT COUNT(*) FROM evidence_receipts) AS evidence_receipts,
          (SELECT COUNT(*) FROM blockchain_anchors WHERE anchor_status IN ('stubbed','anchored')) AS ledger_proofs
        """
    ) or {}
    return {"ok": True, "summary": counts}


@router.get("/executive")
def operator_executive(persona: Optional[str] = Query(None), theme: Optional[str] = Query(None), seed_pack: Optional[str] = Query(None), brand: Optional[str] = Query(None)):
    story = _resolved_story_context(persona, theme, seed_pack, brand)
    summary = operator_summary().get("summary", {})
    top_cards = _top_case_cards(limit=5)
    connector_mix = db_all(
        """
        SELECT connector_name, target_system, COUNT(*) AS executions
        FROM governed_writebacks
        GROUP BY connector_name, target_system
        ORDER BY executions DESC, connector_name ASC
        LIMIT 6
        """
    )
    scenario_totals = db_one(
        """
        SELECT
          COALESCE(SUM(revenue_at_risk), 0) AS revenue_at_risk,
          COALESCE(SUM(cost_impact), 0) AS cost_impact,
          COALESCE(SUM(gap_qty), 0) AS gap_qty,
          COALESCE(AVG(service_impact), 0) AS avg_service_impact
        FROM (
          SELECT DISTINCT ON (case_id) case_id, revenue_at_risk, cost_impact, gap_qty, service_impact
          FROM agent_scenarios
          ORDER BY case_id, created_at DESC
        ) s
        """
    ) or {}
    headline = (
        f"{story['persona'].get('label', 'Executive')} view for {story['theme'].get('label', 'the selected customer theme')}: "
        f"{summary.get('high_risk_cards', 0)} high-risk cards are active, "
        f"{summary.get('approvals_waiting', 0)} actions are waiting for approval, "
        f"and {summary.get('overdue_cards', 0)} cards are already beyond SLA."
    )
    talking_points = [
        str(story['persona'].get('headline_template') or "Executive mode keeps the story focused on revenue, service, and decision bottlenecks instead of operator mechanics."),
        f"The highest-risk case is {top_cards[0].get('title')} at risk score {top_cards[0].get('case_risk_score')}" if top_cards else "No risk cards are currently seeded.",
        f"Governed writebacks now span {len(connector_mix)} connector destinations including ERP, supplier portal, and ticketing." if connector_mix else "No governed writebacks have been executed yet.",
    ]
    return {
        "ok": True,
        "headline": headline,
        "persona_key": story["persona_key"],
        "theme_key": story["theme_key"],
        "seed_pack_key": story["seed_pack_key"],
        "seed_pack": story["seed_pack"],
        "brand_key": story["brand_key"],
        "brand": story["brand"],
        "persona": story["persona"],
        "theme": story["theme"],
        "summary": summary,
        "financial_snapshot": scenario_totals,
        "top_risks": top_cards,
        "connector_mix": connector_mix,
        "talking_points": talking_points,
    }


@router.get("/board")
def operator_board(
    limit: int = Query(100, ge=1, le=500),
    q: Optional[str] = Query(None),
    assignee: Optional[str] = Query(None),
    approval_state: Optional[str] = Query(None),
    sla_state: Optional[str] = Query(None),
    connector_family: Optional[str] = Query(None),
    risk_min: Optional[int] = Query(None, ge=0, le=100),
):
    cards = db_all(
        """
        SELECT
          k.*,
          EXTRACT(EPOCH FROM (now() - k.created_at)) / 3600.0 AS age_hours,
          EXTRACT(EPOCH FROM (COALESCE(k.sla_due_at, (k.created_at + (k.sla_hours || ' hours')::interval)) - now())) / 3600.0 AS sla_remaining_hours,
          CASE
            WHEN k.status = 'resolved' THEN 'resolved'
            WHEN k.breached = true THEN 'breached'
            WHEN now() > (COALESCE(k.sla_due_at, (k.created_at + (k.sla_hours || ' hours')::interval)) - interval '8 hours') THEN 'at_risk'
            ELSE 'on_track'
          END AS sla_state,
          COALESCE((SELECT COUNT(*) FROM v_pending_actions p WHERE p.card_id = k.card_id AND p.status = 'pending'), 0) AS pending_decisions,
          COALESCE((SELECT COUNT(*) FROM v_pending_actions p WHERE p.card_id = k.card_id AND p.status = 'approved'), 0) AS ready_to_execute,
          COALESCE((SELECT COUNT(*) FROM v_pending_actions p WHERE p.card_id = k.card_id AND p.status = 'blocked'), 0) AS blocked_actions,
          CASE
            WHEN COALESCE((SELECT COUNT(*) FROM v_pending_actions p WHERE p.card_id = k.card_id AND p.status = 'pending'), 0) > 0 THEN 'needs_approval'
            WHEN COALESCE((SELECT COUNT(*) FROM v_pending_actions p WHERE p.card_id = k.card_id AND p.status = 'approved'), 0) > 0 THEN 'ready'
            WHEN COALESCE((SELECT COUNT(*) FROM v_pending_actions p WHERE p.card_id = k.card_id AND p.status = 'blocked'), 0) > 0 THEN 'blocked'
            ELSE 'none'
          END AS approval_state,
          (
            SELECT p.action_type
            FROM v_pending_actions p
            WHERE p.card_id = k.card_id AND p.status IN ('pending', 'approved', 'blocked')
            ORDER BY p.updated_at DESC, p.rank ASC
            LIMIT 1
          ) AS next_pending_action
        FROM v_kanban_cards k
        ORDER BY COALESCE(k.case_risk_score, 0) DESC, k.priority ASC, k.updated_at DESC
        LIMIT :lim
        """,
        lim=limit,
    )

    for card in cards:
        card["connector_family"] = _connector_family_for(card.get("next_pending_action"))

    qv = (q or "").strip().lower()
    if qv:
        cards = [
            card for card in cards
            if qv in " ".join(str(card.get(key) or "") for key in ("title", "description", "resource_id", "assignee", "next_pending_action", "case_status")).lower()
        ]
    if assignee and assignee != "all":
        cards = [card for card in cards if str(card.get("assignee") or "unassigned") == assignee]
    if approval_state and approval_state != "all":
        cards = [card for card in cards if str(card.get("approval_state") or "none") == approval_state]
    if sla_state and sla_state != "all":
        cards = [card for card in cards if str(card.get("sla_state") or "unknown") == sla_state]
    if connector_family and connector_family != "all":
        cards = [card for card in cards if str(card.get("connector_family") or "none") == connector_family]
    if risk_min is not None:
        cards = [card for card in cards if float(card.get("case_risk_score") or 0) >= float(risk_min)]

    return {"ok": True, "lanes": _lane_buckets(cards), "items": cards, "filters": _board_filters(cards)}


@router.get("/cases/{case_id}")
def operator_case_detail(case_id: str, audit_limit: int = Query(50, ge=1, le=200)):
    case_row = db_one("SELECT * FROM agent_cases WHERE case_id=:cid", cid=case_id)
    if not case_row:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")

    card_row = db_one(
        """
        SELECT
          k.*,
          EXTRACT(EPOCH FROM (now() - k.created_at)) / 3600.0 AS age_hours,
          EXTRACT(EPOCH FROM (COALESCE(k.sla_due_at, (k.created_at + (k.sla_hours || ' hours')::interval)) - now())) / 3600.0 AS sla_remaining_hours,
          CASE
            WHEN k.status = 'resolved' THEN 'resolved'
            WHEN k.breached = true THEN 'breached'
            WHEN now() > (COALESCE(k.sla_due_at, (k.created_at + (k.sla_hours || ' hours')::interval)) - interval '8 hours') THEN 'at_risk'
            ELSE 'on_track'
          END AS sla_state,
          COALESCE((SELECT COUNT(*) FROM v_pending_actions p WHERE p.card_id = k.card_id AND p.status = 'pending'), 0) AS pending_decisions,
          COALESCE((SELECT COUNT(*) FROM v_pending_actions p WHERE p.card_id = k.card_id AND p.status = 'approved'), 0) AS ready_to_execute,
          COALESCE((SELECT COUNT(*) FROM v_pending_actions p WHERE p.card_id = k.card_id AND p.status = 'blocked'), 0) AS blocked_actions
        FROM v_kanban_cards k
        WHERE k.case_id=:cid
        ORDER BY k.updated_at DESC
        LIMIT 1
        """,
        cid=case_id,
    )
    recommendations = db_all("SELECT * FROM agent_recommendations WHERE case_id=:cid ORDER BY rank ASC, created_at DESC", cid=case_id)
    scenarios = db_all("SELECT * FROM agent_scenarios WHERE case_id=:cid ORDER BY created_at DESC", cid=case_id)
    pending_actions = db_all(
        """
        SELECT * FROM v_pending_actions
        WHERE case_id=:cid
        ORDER BY CASE status WHEN 'pending' THEN 0 WHEN 'approved' THEN 1 WHEN 'blocked' THEN 2 WHEN 'executed' THEN 3 WHEN 'rejected' THEN 4 ELSE 5 END,
                 updated_at DESC,
                 rank ASC
        """,
        cid=case_id,
    )
    for row in pending_actions:
        row["connector_family"] = _connector_family_for(row.get("action_type"))
    audit_items = db_all(
        """
        SELECT action_id, case_id, channel, action_type, result, created_at, payload->'_audit' AS audit, payload
        FROM agent_actions
        WHERE case_id=:cid
        ORDER BY created_at DESC
        LIMIT :lim
        """,
        cid=case_id,
        lim=audit_limit,
    )
    signals = db_all("SELECT ts, signal_type, value, period FROM market_signals WHERE resource_id=:rid ORDER BY ts DESC LIMIT 12", rid=str(case_row.get("resource_id") or ""))
    writebacks = db_all(
        """
        SELECT
          writeback_id, action_id, pending_id, adapter_name, connector_name, target_system,
          action_type, status, external_ref, policy_gate, approval_state, connector_family, approval_policy, receipt_summary, created_at, result_payload
        FROM governed_writebacks
        WHERE case_id=:cid
        ORDER BY created_at DESC
        LIMIT 12
        """,
        cid=case_id,
    )

    operator_state = {
        "needs_approval": sum(1 for row in pending_actions if str(row.get("status") or "") == "pending"),
        "ready_to_execute": sum(1 for row in pending_actions if str(row.get("status") or "") == "approved"),
        "execution_blocked": sum(1 for row in pending_actions if str(row.get("status") or "") == "blocked"),
    }

    return {
        "ok": True,
        "case": case_row,
        "card": card_row,
        "recommendations": recommendations,
        "scenarios": scenarios,
        "scenario_comparison": _scenario_comparison(scenarios),
        "pending_actions": pending_actions,
        "audit": audit_items,
        "signals": signals,
        "writebacks": writebacks,
        "operator_state": operator_state,
        "approval_story": _operator_story(case_row, card_row, pending_actions, scenarios),
        "transparency": _case_transparency(case_id),
    }


@router.get("/cases/{case_id}/scenario_compare")
def operator_case_scenario_compare(case_id: str):
    scenarios = db_all("SELECT * FROM agent_scenarios WHERE case_id=:cid ORDER BY created_at DESC", cid=case_id)
    if not scenarios:
        raise HTTPException(status_code=404, detail=f"No scenarios found for case: {case_id}")
    return {"ok": True, "case_id": case_id, "comparison": _scenario_comparison(scenarios)}


@router.get("/cases/{case_id}/transparency")
def operator_case_transparency(case_id: str):
    case_row = db_one("SELECT case_id FROM agent_cases WHERE case_id=:cid", cid=case_id)
    if not case_row:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")
    return {"ok": True, "transparency": _case_transparency(case_id)}


@router.get("/transparency_report")
def operator_transparency_report(case_id: Optional[str] = Query(None)):
    where = "WHERE r.case_id=:cid" if case_id else ""
    params = {"cid": case_id} if case_id else {}
    rows = db_all(
        f"""
        SELECT r.case_id,
               COUNT(*) AS receipt_count,
               AVG(r.confidence_score) AS average_confidence,
               COUNT(a.anchor_id) AS ledger_proof_count,
               COUNT(DISTINCT s.source_id) AS source_count,
               STRING_AGG(DISTINCT r.validation_status, ', ' ORDER BY r.validation_status) AS validation_statuses
        FROM evidence_receipts r
        LEFT JOIN traceability_events e ON e.event_id = r.trace_event_id
        LEFT JOIN external_data_sources s ON s.source_id = e.source_id
        LEFT JOIN blockchain_anchors a ON a.receipt_id = r.receipt_id
        {where}
        GROUP BY r.case_id
        ORDER BY average_confidence DESC, receipt_count DESC
        """,
        **params,
    )
    markdown_lines = [
        "# Supply Chain Transparency Report",
        "",
        "This report separates validated external evidence from AI recommendations and ledger proof stubs.",
        "",
    ]
    for row in rows:
        markdown_lines.append(
            f"- Case `{row.get('case_id')}`: {row.get('receipt_count', 0)} receipts, "
            f"{round(float(row.get('average_confidence') or 0), 2)} confidence, "
            f"{row.get('source_count', 0)} sources, {row.get('ledger_proof_count', 0)} ledger proofs, "
            f"statuses: {row.get('validation_statuses') or 'none'}"
        )
    if not rows:
        markdown_lines.append("- No evidence receipts are currently available.")
    return {
        "ok": True,
        "case_id": case_id,
        "rows": rows,
        "markdown": "\n".join(markdown_lines),
    }


@router.get("/pending")
def operator_pending(limit: int = Query(100, ge=1, le=500), status: Optional[str] = Query(None)):
    params: Dict[str, Any] = {"lim": limit}
    where = ""
    if status:
        where = "WHERE p.status=:st"
        params["st"] = status
    items = db_all(
        f"""
        SELECT
          p.pending_id, p.case_id, p.card_id, p.status, p.approval_required,
          p.action_type, p.action_payload, p.rationale, p.rank, p.updated_at,
          p.created_at, p.case_status, p.case_risk_score, p.case_confidence,
          p.card_status, p.card_resource_id, k.title AS card_title
        FROM v_pending_actions p
        LEFT JOIN kanban_cards k ON k.card_id = p.card_id
        {where}
        ORDER BY CASE p.status WHEN 'pending' THEN 0 WHEN 'approved' THEN 1 WHEN 'blocked' THEN 2 ELSE 3 END,
                 p.updated_at DESC,
                 p.rank ASC
        LIMIT :lim
        """,
        **params,
    )
    for row in items:
        row["connector_family"] = _connector_family_for(row.get("action_type"))
    return {"ok": True, "items": items}


@router.get("/pending/{pending_id}/simulate")
def operator_simulate_pending(pending_id: str, channel: str = Query("supervisor")):
    pending = db_one("SELECT * FROM v_pending_actions WHERE pending_id=:pid", pid=pending_id)
    if not pending:
        raise HTTPException(status_code=404, detail=f"Pending action not found: {pending_id}")

    payload = dict(pending.get("action_payload") or {})
    payload["pending_id"] = pending_id
    payload["materialization_id"] = str(pending.get("materialization_id") or "")
    payload.setdefault("_actor", {"role": "supervisor", "sub": "operator-surface"})

    simulation = execute_action(
        case_id=str(pending.get("case_id") or ""),
        channel=channel,
        action_type=str(pending.get("action_type") or ""),
        payload=payload,
        dry_run=True,
    )

    latest_scenario = db_one("SELECT * FROM agent_scenarios WHERE case_id=:cid ORDER BY created_at DESC LIMIT 1", cid=str(pending.get("case_id") or "")) or {}
    writeback_preview = ((simulation.get("simulation") or {}).get("writeback_preview") or {})
    connector_family = writeback_preview.get("connector_family") or _connector_family_for(pending.get("action_type"))
    preview_receipt = writeback_preview.get("receipt") or {}
    business_preview = {
        "summary": (simulation.get("simulation") or {}).get("summary") or f"Would execute {pending.get('action_type')}",
        "service_impact": latest_scenario.get("service_impact"),
        "cost_impact": latest_scenario.get("cost_impact"),
        "risk_exposure": latest_scenario.get("risk_exposure"),
        "target_system": writeback_preview.get("target_system"),
        "connector_family": connector_family,
        "connector_name": writeback_preview.get("connector_name"),
        "approval_policy_key": writeback_preview.get("approval_policy_key"),
        "receipt": preview_receipt,
    }
    return {
        "ok": True,
        "pending": pending,
        "simulation": simulation,
        "business_preview": business_preview,
        "approval_narrative": {
            "title": f"Approve {pending.get('action_type')} before writeback",
            "plain_language": "This preview shows what would happen in the operating system before anything is changed.",
            "next_step": "Approve first, then execute when the business preview looks acceptable." if str(pending.get("status") or "") == "pending" else "This action is approved. Use execute when you are ready to write back.",
            "connector_story": f"This action is routed through the {connector_family} connector pack into {writeback_preview.get('target_system', 'the target system')}.",
        },
    }



@router.get("/story_pack")
def operator_story_pack(seed_pack: Optional[str] = Query(None), brand: Optional[str] = Query(None)):
    ctx = _resolved_story_context(None, None, seed_pack, brand)
    return {
        "ok": True,
        "default_persona": ctx["persona_key"],
        "default_theme": ctx["theme_key"],
        "default_brand": ctx["brand_key"],
        "default_seed_pack": ctx["seed_pack_key"],
        "personas": ctx["personas"],
        "themes": ctx["themes"],
        "brands": ctx["brands"],
        "seed_packs": ctx["seed_packs"],
    }


@router.get("/experience_pack")
def operator_experience_pack():
    packs = seed_pack_catalog()
    brands = branding_options()
    scripts = guided_scripts()
    default_pack = next(iter(packs.keys()), 'portfolio')
    default_brand = next(iter(brands.keys()), 'neutral')
    return {
        "ok": True,
        "default_seed_pack": default_pack,
        "default_brand": default_brand,
        "seed_packs": packs,
        "brands": brands,
        "demo_scripts": scripts,
    }


@router.get("/demo_script")
def operator_demo_script(seed_pack: Optional[str] = Query(None), persona: Optional[str] = Query(None), theme: Optional[str] = Query(None), brand: Optional[str] = Query(None)):
    ctx = _resolved_story_context(persona, theme, seed_pack, brand)
    return {
        "ok": True,
        "seed_pack_key": ctx["seed_pack_key"],
        "seed_pack": ctx["seed_pack"],
        "brand_key": ctx["brand_key"],
        "brand": ctx["brand"],
        "persona_key": ctx["persona_key"],
        "theme_key": ctx["theme_key"],
        "steps": _script_steps(ctx["seed_pack_key"]),
    }


@router.get("/screenshot_manifest")
def operator_screenshot_manifest(case_id: Optional[str] = Query(None), seed_pack: Optional[str] = Query(None), persona: Optional[str] = Query(None), theme: Optional[str] = Query(None), brand: Optional[str] = Query(None)):
    ctx = _resolved_story_context(persona, theme, seed_pack, brand)
    summary = operator_summary().get("summary", {})
    executive = operator_executive(persona=ctx["persona_key"], theme=ctx["theme_key"])
    effective_case_id = case_id or ctx['seed_pack'].get('focus_case_id')
    detail = None
    if effective_case_id:
        try:
            detail = operator_case_detail(case_id=effective_case_id)
        except HTTPException:
            detail = None
    case_row = (detail or {}).get('case') or {}
    approval_story = (detail or {}).get('approval_story') or {}
    comparison = ((detail or {}).get('scenario_comparison') or {}).get('recommended_scenario') or {}
    top_risk = ((executive.get('top_risks') or [{}])[0] if executive.get('top_risks') else {})
    shots = [
        {
            'shot_id': 'executive_overview',
            'title': f"{ctx['brand'].get('logo_text', 'Demo')} — Executive Overview",
            'subtitle': executive.get('headline') or ctx['seed_pack'].get('description') or '',
            'metrics': [
                f"High risk cards: {summary.get('high_risk_cards', 0)}",
                f"Approvals waiting: {summary.get('approvals_waiting', 0)}",
                f"Writebacks (24h): {summary.get('writebacks_24h', 0)}",
            ],
        },
        {
            'shot_id': 'risk_board',
            'title': f"{ctx['seed_pack'].get('label', 'Seed Pack')} — Risk Board",
            'subtitle': ctx['seed_pack'].get('talk_track') or 'Governed operator board',
            'metrics': [
                f"Lead case: {top_risk.get('title', 'N/A')}",
                f"Resource: {top_risk.get('resource_id', 'N/A')}",
                f"SLA state: {top_risk.get('sla_state', 'N/A')}",
            ],
        },
        {
            'shot_id': 'case_detail',
            'title': f"Case Detail — {case_row.get('resource_id', effective_case_id or 'selected case')}",
            'subtitle': approval_story.get('headline') or 'Governed case detail',
            'metrics': [
                f"Risk score: {case_row.get('risk_score', '—')}",
                f"Owner: {case_row.get('owner', '—')}",
                f"Recommended scenario: {comparison.get('scenario_name', '—')}",
            ],
        },
        {
            'shot_id': 'governed_receipt',
            'title': 'Governed Writeback Proof',
            'subtitle': approval_story.get('next_step') or 'Typed action, approval, simulation, and receipt.',
            'metrics': [
                f"Connector family: {(((detail or {}).get('writebacks') or [{}])[0] if (detail or {}).get('writebacks') else {}).get('connector_family', 'preview')}",
                f"Approval checkpoint: {((((detail or {}).get('writebacks') or [{}])[0] if (detail or {}).get('writebacks') else {}).get('approval_policy', 'policy pending'))}",
                f"Audit events: {len((detail or {}).get('audit') or [])}",
            ],
        },
    ]
    return {
        'ok': True,
        'seed_pack_key': ctx['seed_pack_key'],
        'brand_key': ctx['brand_key'],
        'persona_key': ctx['persona_key'],
        'theme_key': ctx['theme_key'],
        'shots': shots,
    }


@router.get("/executive_brief")
def operator_executive_brief(persona: Optional[str] = Query(None), theme: Optional[str] = Query(None), seed_pack: Optional[str] = Query(None), brand: Optional[str] = Query(None)):
    story = _resolved_story_context(persona, theme, seed_pack, brand)
    executive = operator_executive(persona=story["persona_key"], theme=story["theme_key"], seed_pack=story["seed_pack_key"], brand=story["brand_key"])
    top_risks = executive.get("top_risks") or []
    lead_case = top_risks[0] if top_risks else {}
    summary = executive.get("summary") or {}
    financial = executive.get("financial_snapshot") or {}
    proof_points = story["theme"].get("proof_points") or []
    sections = [
        {
            "title": "Executive headline",
            "body": executive.get("headline") or "No current executive headline.",
        },
        {
            "title": "Business impact",
            "body": f"Revenue at risk {financial.get('revenue_at_risk', 0)}, cost impact {financial.get('cost_impact', 0)}, approvals waiting {summary.get('approvals_waiting', 0)}, overdue cards {summary.get('overdue_cards', 0)}.",
        },
        {
            "title": "What the customer sees",
            "body": f"Top risk: {lead_case.get('title', 'No active case')} with risk {lead_case.get('case_risk_score', 0)} on {lead_case.get('resource_id', 'the selected resource')}.",
        },
        {
            "title": "Why this builds confidence",
            "body": "All recommended actions flow through typed approvals, connector-specific policies, governed writeback, and audit-ready receipts.",
        },
    ]
    markdown = "\n\n".join(
        [
            f"# One-Page Brief — {story['theme'].get('label', 'Customer Theme')}",
            f"**Persona:** {story['persona'].get('label', 'Executive')}  ",
            f"**Theme:** {story['theme'].get('label', 'Customer Theme')}  ",
            f"**Summary:** {story['theme'].get('summary', '')}",
            *[f"## {section['title']}\n{section['body']}" for section in sections],
            "## Customer proof points\n" + "\n".join(f"- {item}" for item in proof_points),
        ]
    )
    return {
        "ok": True,
        "persona_key": story["persona_key"],
        "theme_key": story["theme_key"],
        "seed_pack_key": story["seed_pack_key"],
        "seed_pack": story["seed_pack"],
        "brand_key": story["brand_key"],
        "brand": story["brand"],
        "persona": story["persona"],
        "theme": story["theme"],
        "sections": sections,
        "proof_points": proof_points,
        "markdown": markdown,
    }


@router.get("/writebacks/{writeback_id}/receipt")
def operator_writeback_receipt(writeback_id: str):
    row = db_one(
        """
        SELECT writeback_id, case_id, pending_id, connector_name, connector_family, target_system,
               action_type, status, external_ref, approval_policy, receipt_summary, created_at, result_payload
        FROM governed_writebacks
        WHERE writeback_id=:wid
        """,
        wid=writeback_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail=f"Writeback not found: {writeback_id}")
    result_payload = dict(row.get("result_payload") or {})
    return {
        "ok": True,
        "writeback": row,
        "receipt": result_payload.get("receipt") or {},
    }
