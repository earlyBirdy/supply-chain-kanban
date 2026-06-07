from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List


def _hash_payload(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


_AGENT_SKILLS: List[Dict[str, Any]] = [
    {
        "skill_id": "clarify_operator_ask",
        "label": "Clarify operator ask",
        "trigger": "A planner, buyer, or executive asks an ambiguous supply-chain question.",
        "inputs": ["business_question", "persona", "SLA", "affected_customer_or_program"],
        "outputs": ["primary_question", "acceptance_criteria", "owner", "approval_path"],
        "ux_surface": "Next Decision / AI Agent Workbench",
    },
    {
        "skill_id": "source_map_erp_mes",
        "label": "Map ERP/MES source records",
        "trigger": "A card needs traceability to PO, WO, inventory, production, shipment, or supplier portal data.",
        "inputs": ["SourceSystemConnector", "SourceRecordReference", "field_mapping", "trust_tier"],
        "outputs": ["ontology_object_refs", "missing_fields", "writeback_target", "source_confidence"],
        "ux_surface": "Connect Existing Systems",
    },
    {
        "skill_id": "commodity_news_to_risk",
        "label": "Convert live news into commodity risk",
        "trigger": "Commodity, logistics, supplier, policy, or price signal arrives from RSS/API/manual research.",
        "inputs": ["headline", "publisher", "published_at", "summary", "structured_signals"],
        "outputs": ["NewsRiskSignal", "CommodityRiskSignal", "BillOfMaterialsExposure", "recommended_arrangement"],
        "ux_surface": "Live News for Commodity Arrangements",
    },
    {
        "skill_id": "build_decision_packet",
        "label": "Build governed decision packet",
        "trigger": "Risk is high enough to need manager approval or external writeback.",
        "inputs": ["case", "scenario", "cost_impact", "service_impact", "risk_exposure"],
        "outputs": ["AgentDecision", "approval_story", "decision_hash", "EvidenceReceipt"],
        "ux_surface": "Decide / Simulate + Execute / Prove",
    },
    {
        "skill_id": "autoresearch_risk_sprint",
        "label": "Autoresearch risk sprint",
        "trigger": "The model needs a measurable improvement for forecast, supplier, inventory, or news-risk prediction.",
        "inputs": ["hypothesis", "baseline_metric", "candidate_rule_or_model", "test_dataset"],
        "outputs": ["experiment_result", "promotion_decision", "model_confidence_delta", "audit_note"],
        "ux_surface": "Power Templates",
    },
]


_AUTO_RESEARCH_EXTENSIONS: List[Dict[str, Any]] = [
    {
        "extension_id": "commodity_arrangement_research",
        "label": "Commodity arrangement research",
        "goal": "Find early signals that should change buy timing, buffer targets, LTA strategy, or supplier allocation.",
        "promotion_gate": "Earlier warning without increasing false-positive approval work.",
        "metric": "days_of_warning_before_ERP_shortage",
    },
    {
        "extension_id": "forecast_capacity_gap_research",
        "label": "Forecast-capacity gap research",
        "goal": "Detect demand/capacity mismatches before customer commitment misses.",
        "promotion_gate": "Lower forecast exception noise and better service-impact ranking.",
        "metric": "weighted_forecast_exception_precision",
    },
    {
        "extension_id": "supplier_recovery_playbook_research",
        "label": "Supplier recovery playbook research",
        "goal": "Compare supplier ticket, expedite, allocation, substitute, and redesign paths using historical receipts.",
        "promotion_gate": "Improves recovery recommendation precision and keeps human approval for external changes.",
        "metric": "approved_recommendation_success_rate",
    },
]


def build_agent_skill_catalog() -> Dict[str, Any]:
    skills: List[Dict[str, Any]] = []
    for skill in _AGENT_SKILLS:
        enriched = dict(skill)
        enriched["skill_hash"] = _hash_payload({
            "skill_id": skill["skill_id"],
            "trigger": skill["trigger"],
            "outputs": skill["outputs"],
        })
        skills.append(enriched)

    extensions: List[Dict[str, Any]] = []
    for extension in _AUTO_RESEARCH_EXTENSIONS:
        enriched = dict(extension)
        enriched["evidence_policy"] = "log hypothesis, dataset, baseline, candidate result, operator impact, and promote/reject decision"
        enriched["extension_hash"] = _hash_payload(enriched)
        extensions.append(enriched)

    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "title": "Agent Skills + Autoresearch Extension Catalog",
        "principle": "Keep the dashboard simple for operators while giving the AI agent repeatable, auditable skills for research, risk prediction, approval, and proof.",
        "skills": skills,
        "autoresearch_extensions": extensions,
        "operating_loop": [
            "clarify business ask or ingest live signal",
            "map ERP/MES/WMS/TMS/news records to ontology objects",
            "detect risk and produce a human-readable decision packet",
            "run bounded autoresearch only when a measurable prediction improvement is needed",
            "require human approval before external-system change",
            "write back through governed connector and attach EvidenceReceipt / BlockchainAnchor proof",
        ],
        "simple_ui_rule": "Simple default UI shows major issue, affected object, recommended action, approval owner, target system, and proof; raw ERP/MES tables stay behind source references.",
    }
