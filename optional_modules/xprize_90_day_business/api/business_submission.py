from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List


def _hash_payload(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _agent_decision_log() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = [
        {
            "decision_id": "AD-001",
            "cycle": 1,
            "source_inputs": ["ERP: PO-8841", "MES: PLANT-TX1-LINE-2", "WMS: WH-SG-01", "NewsRiskSignal: lithium-port-delay"],
            "detected_risk": "Battery material supplier delay can break launch allocation in 12 days.",
            "risk_type": "supplier_inventory",
            "risk_score": 86,
            "confidence": 0.82,
            "recommended_action": "Open supplier escalation and simulate expedite shipment for constrained SKUs.",
            "approval_gate": "Planner or CFO approval required before ERP/MES writeback.",
            "writeback_target": "ERP purchase-order note + MES build-priority hold",
        },
        {
            "decision_id": "AD-002",
            "cycle": 1,
            "source_inputs": ["MES: yield-shift", "WMS: finished-goods-shortage", "ERP: customer-commit-date"],
            "detected_risk": "Yield drop creates pack-out shortage for a committed order.",
            "risk_type": "production_quality",
            "risk_score": 78,
            "confidence": 0.74,
            "recommended_action": "Create quality containment task and rebalance available inventory to the highest-margin order.",
            "approval_gate": "Operations approval required before allocation writeback.",
            "writeback_target": "WMS allocation reservation + MES containment ticket",
        },
    ]
    for row in rows:
        row["decision_hash"] = _hash_payload(row)
    return rows


def _evidence_log(decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    receipts: List[Dict[str, Any]] = []
    for row in decisions:
        payload = {
            "decision_id": row["decision_id"],
            "decision_hash": row["decision_hash"],
            "approval_gate": row["approval_gate"],
            "writeback_target": row["writeback_target"],
            "evidence_sources": row["source_inputs"],
        }
        receipts.append(
            {
                "receipt_id": f"XR-{row['decision_id']}",
                "receipt_type": "blockchain_ready_evidence",
                "summary": f"Traceable receipt for {row['decision_id']} with approval gate and writeback target.",
                "receipt_hash": _hash_payload(payload),
                "ledger_status": "stubbed_for_demo",
                "payload": payload,
            }
        )
    return receipts


def build_business_submission_snapshot() -> Dict[str, Any]:
    decisions = _agent_decision_log()
    receipts = _evidence_log(decisions)
    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "submission_title": "Supply Chain Kanban AI: AI-Native Operating System for Supply Chains",
        "business_readiness": {
            "target_customer": "SME manufacturers and supply-chain teams that already run ERP, MES, WMS, TMS, supplier portals, and spreadsheets.",
            "buyer": "CFO, COO, supply-chain leader, operations leader, or plant manager.",
            "pricing_model": "Pilot package, then subscription per site plus optional integration services.",
            "revenue_evidence": [
                "Pilot offer: 2-week supply-chain risk cockpit setup with read-only ERP/MES/WMS import.",
                "LOI-ready evidence: customer problem statement, before/after KPI targets, and approval-gated writeback scope.",
                "Paid service path: implementation fee for connector mapping plus monthly AI-agent monitoring subscription.",
            ],
        },
        "continuous_agent": {
            "mode": "demo_continuous_loop",
            "cadence": "Every 15 minutes in production; on-demand in the demo API.",
            "steps": [
                "Read ERP/MES/WMS mock data.",
                "Read news and market risk signals.",
                "Detect inventory, supplier, and production risks.",
                "Create recommended actions with confidence and business impact.",
                "Route human approval before simulated ERP/MES/WMS writeback.",
                "Create evidence receipts with decision hashes and blockchain-ready proof.",
            ],
        },
        "source_systems": [
            {"system": "ERP", "mock_data": "orders, purchase orders, material masters, cost exposure"},
            {"system": "MES", "mock_data": "yield, scrap, downtime, IQC/OQC holds, line capacity"},
            {"system": "WMS", "mock_data": "stock, allocation, inbound/outbound movement, pick-pack state"},
            {"system": "NewsRiskSignal", "mock_data": "commodity, supplier, logistics, and geopolitical risk events"},
            {"system": "BlockchainEvidence", "mock_data": "receipt hash, decision hash, ledger anchor status"},
        ],
        "agent_decision_log": decisions,
        "human_approval_gate": {
            "approvers": ["Planner", "CFO", "Operations manager"],
            "decisions": ["approve", "reject", "request more evidence"],
            "writeback_behavior": "Only approved actions create simulated ERP/MES/WMS writeback receipts.",
            "safe_default": "Read-only monitoring; no autonomous external writeback without approval.",
        },
        "evidence_log": receipts,
        "gemini_trace_stub": {
            "model_role": "risk reasoning and recommendation drafting",
            "usage_fields_for_submission": ["prompt_id", "input_sources", "output_recommendation", "confidence", "reviewer_decision"],
            "current_status": "API trace schema is ready; live Gemini key is intentionally not required for local demo.",
        },
    }
