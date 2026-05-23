from fastapi.testclient import TestClient
import pytest

from app.api_main import create_app
from app.api.routers import operator as op_mod


def test_operator_board_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_all(sql: str, **params):
        if 'from v_kanban_cards' in sql.lower():
            return [
                {
                    'card_id': 'k1', 'case_id': 'c1', 'title': 'DDR5 risk', 'description': 'demo', 'status': 'todo',
                    'resource_id': 'dram_ddr5', 'priority': 2, 'assignee': 'planner@demo', 'updated_at': '2026-04-01T10:00:00Z',
                    'case_risk_score': 82, 'pending_decisions': 1, 'ready_to_execute': 0, 'blocked_actions': 0,
                    'next_pending_action': 'ExpediteShipment', 'approval_state': 'needs_approval', 'sla_state': 'at_risk',
                    'age_hours': 12, 'sla_remaining_hours': 4, 'scope': {'product_milestone': 'commodity_supplier'},
                },
                {
                    'card_id': 'k2', 'case_id': 'c2', 'title': 'Supplier escalation', 'description': 'demo', 'status': 'in_progress',
                    'resource_id': 'battery_cells_lfp', 'priority': 1, 'assignee': 'opslead@demo', 'updated_at': '2026-04-01T09:00:00Z',
                    'case_risk_score': 91, 'pending_decisions': 0, 'ready_to_execute': 1, 'blocked_actions': 0,
                    'next_pending_action': 'OpenSupplierTicket', 'approval_state': 'ready', 'sla_state': 'breached',
                    'age_hours': 20, 'sla_remaining_hours': -2, 'scope': {'product_milestone': 'oqc'},
                }
            ]
        return []

    monkeypatch.setattr(op_mod, 'db_all', fake_all)

    app = create_app()
    client = TestClient(app)
    r = client.get('/operator/board')
    assert r.status_code == 200
    js = r.json()
    assert js['ok'] is True
    assert len(js['lanes']) == 4
    assert js['lanes'][0]['status'] == 'todo'
    assert js['lanes'][0]['cards'][0]['case_id'] == 'c1'
    assert 'erp' in js['filters']['connector_families']
    assert 'supplier_portal' in js['filters']['connector_families']
    assert [row['key'] for row in js['product_flow']] == ['commodity_supplier', 'iqc', 'assembly', 'test', 'packing', 'oqc']
    assert js['product_flow'][0]['count'] == 1
    assert js['product_flow'][-1]['count'] == 1

    r = client.get('/operator/board?product_milestone=oqc')
    assert r.status_code == 200
    oqc = r.json()
    assert len(oqc['items']) == 1
    assert oqc['items'][0]['product_milestone_label'] == 'OQC'


def test_operator_case_detail_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_one(sql: str, **params):
        sl = sql.lower()
        if 'from agent_cases' in sl:
            return {
                'case_id': 'c1', 'status': 'AT_RISK', 'resource_id': 'dram_ddr5', 'risk_score': 82,
                'confidence': 0.74, 'owner': 'planner@demo', 'last_observed_period': '2025-W03',
            }
        if 'from v_kanban_cards' in sl:
            return {
                'card_id': 'k1', 'case_id': 'c1', 'title': 'DDR5 risk', 'status': 'todo', 'pending_decisions': 1,
                'ready_to_execute': 0, 'blocked_actions': 0, 'sla_state': 'at_risk', 'age_hours': 12, 'sla_remaining_hours': 4,
            }
        return None

    def fake_all(sql: str, **params):
        sl = sql.lower()
        if 'from agent_recommendations' in sl:
            return [{'rank': 1, 'action_type': 'ExpediteShipment', 'rationale': 'reduce risk'}]
        if 'from agent_scenarios' in sl:
            return [
                {'scenario_name': 'Expedite', 'service_impact': 3, 'cost_impact': 5, 'risk_exposure': 8},
                {'scenario_name': 'Do nothing', 'service_impact': 7, 'cost_impact': 2, 'risk_exposure': 20},
            ]
        if 'from v_pending_actions' in sl:
            return [{'pending_id': 'p1', 'status': 'pending', 'action_type': 'ExpediteShipment', 'rank': 0}]
        if 'from agent_actions' in sl:
            return [{'action_id': 'a1', 'action_type': 'PendingActionDecision', 'result': 'ok: approved', 'created_at': '2026-04-01T10:00:00Z', 'audit': {'request_id': 'rid-1'}}]
        if 'from market_signals' in sl:
            return [{'signal_type': 'price_index_up', 'value': 12, 'period': '2025-W03'}]
        if 'from governed_writebacks' in sl:
            return [{'writeback_id': 'w1', 'target_system': 'erp.shipments', 'external_ref': 'WB-1', 'status': 'ok', 'action_type': 'ExpediteShipment', 'adapter_name': 'governed_writeback', 'connector_name': 'mock', 'connector_family': 'erp', 'approval_policy': 'erp_high_impact', 'receipt_summary': 'Send an expedite request', 'created_at': '2026-04-01T10:00:00Z', 'result_payload': {'receipt': {'change_ticket': 'CHG-1'}}}]
        return []

    monkeypatch.setattr(op_mod, 'db_one', fake_one)
    monkeypatch.setattr(op_mod, 'db_all', fake_all)

    app = create_app()
    client = TestClient(app)
    r = client.get('/operator/cases/c1')
    assert r.status_code == 200
    js = r.json()
    assert js['ok'] is True
    assert js['case']['case_id'] == 'c1'
    assert js['card']['card_id'] == 'k1'
    assert js['operator_state']['needs_approval'] == 1
    assert js['recommendations'][0]['action_type'] == 'ExpediteShipment'
    assert 'headline' in js['approval_story']
    assert js['writebacks'][0]['external_ref'] == 'WB-1'
    assert js['scenario_comparison']['recommended_scenario']['scenario_name'] == 'Expedite'


def test_operator_executive_and_story_pack(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_one(sql: str, **params):
        if 'select' in sql.lower() and 'total_cards' in sql.lower():
            return {'total_cards': 3, 'high_risk_cards': 2, 'approvals_waiting': 1, 'overdue_cards': 1, 'writebacks_24h': 2}
        if 'sum(revenue_at_risk)' in sql.lower():
            return {'revenue_at_risk': 550000, 'cost_impact': 42000, 'gap_qty': 30, 'avg_service_impact': 4}
        return {}

    def fake_all(sql: str, **params):
        sl = sql.lower()
        if 'from v_kanban_cards' in sl:
            return [{'title': 'LFP battery cells delayed at port', 'case_risk_score': 91, 'resource_id': 'battery_cells_lfp', 'assignee': 'opslead@demo', 'sla_state': 'breached'}]
        if 'from governed_writebacks' in sl:
            return [{'connector_name': 'supplier_portal_stub', 'target_system': 'supplier.portal', 'executions': 1}]
        return []

    monkeypatch.setattr(op_mod, 'db_one', fake_one)
    monkeypatch.setattr(op_mod, 'db_all', fake_all)

    app = create_app()
    client = TestClient(app)
    r = client.get('/operator/story_pack')
    assert r.status_code == 200
    assert r.json()['ok'] is True
    r = client.get('/operator/executive?persona=coo&theme=ev_launch')
    assert r.status_code == 200
    js = r.json()
    assert js['ok'] is True
    assert 'COO / Operations Leader view for EV Launch' in js['headline']
    assert js['top_risks'][0]['resource_id'] == 'battery_cells_lfp'
    assert js['connector_mix'][0]['target_system'] == 'supplier.portal'
    assert js['theme_key'] == 'ev_launch'


def test_operator_executive_brief(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_one(sql: str, **params):
        if 'select' in sql.lower() and 'total_cards' in sql.lower():
            return {'total_cards': 3, 'high_risk_cards': 2, 'approvals_waiting': 1, 'overdue_cards': 1, 'writebacks_24h': 2}
        if 'sum(revenue_at_risk)' in sql.lower():
            return {'revenue_at_risk': 550000, 'cost_impact': 42000, 'gap_qty': 30, 'avg_service_impact': 4}
        return {}

    def fake_all(sql: str, **params):
        sl = sql.lower()
        if 'from v_kanban_cards' in sl:
            return [{'title': 'LFP battery cells delayed at port', 'case_risk_score': 91, 'resource_id': 'battery_cells_lfp', 'assignee': 'opslead@demo', 'sla_state': 'breached'}]
        if 'from governed_writebacks' in sl:
            return [{'connector_name': 'supplier_portal_stub', 'target_system': 'supplier.portal', 'executions': 1}]
        return []

    monkeypatch.setattr(op_mod, 'db_one', fake_one)
    monkeypatch.setattr(op_mod, 'db_all', fake_all)

    app = create_app()
    client = TestClient(app)
    r = client.get('/operator/executive_brief?persona=vp_supply_chain&theme=data_center')
    assert r.status_code == 200
    js = r.json()
    assert js['ok'] is True
    assert js['persona_key'] == 'vp_supply_chain'
    assert 'One-Page Brief' in js['markdown']
    assert js['sections'][0]['title'] == 'Executive headline'


def test_operator_simulate_pending(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_one(sql: str, **params):
        sl = sql.lower()
        if 'from v_pending_actions' in sl:
            return {
                'pending_id': 'p1', 'case_id': 'c1', 'status': 'approved', 'action_type': 'OpenSupplierTicket',
                'action_payload': {'resource_id': 'battery_cells_lfp', 'priority': 'high'}, 'materialization_id': None,
            }
        if 'from agent_scenarios' in sl:
            return {'service_impact': 3, 'cost_impact': 5, 'risk_exposure': 8}
        return None

    monkeypatch.setattr(op_mod, 'db_one', fake_one)
    monkeypatch.setattr(op_mod, 'execute_action', lambda **kwargs: {
        'ok': True, 'dry_run': True,
        'simulation': {'summary': 'Would open supplier ticket', 'writeback_preview': {'target_system': 'supplier.portal', 'external_ref': 'SIM-123', 'policy_gate': 'approved_action_required', 'connector_family': 'supplier_portal', 'connector_name': 'supplier_portal_stub', 'approval_policy_key': 'supplier_external_escalation', 'receipt': {'change_ticket': 'CHG-1', 'summary': 'Open a supplier portal escalation'}}}
    })

    app = create_app()
    client = TestClient(app)
    r = client.get('/operator/pending/p1/simulate')
    assert r.status_code == 200
    js = r.json()
    assert js['ok'] is True
    assert js['business_preview']['target_system'] == 'supplier.portal'
    assert js['business_preview']['connector_family'] == 'supplier_portal'
    assert js['business_preview']['receipt']['change_ticket'] == 'CHG-1'
    assert 'supplier_portal' in js['approval_narrative']['connector_story']


def test_operator_case_transparency_and_report(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_one(sql: str, **params):
        sl = sql.lower()
        if 'from agent_cases' in sl:
            return {'case_id': 'c1'}
        return {}

    def fake_all(sql: str, **params):
        sl = sql.lower()
        if 'from evidence_receipts r' in sl and 'group by r.case_id' not in sl:
            return [
                {
                    'receipt_id': 'r1', 'case_id': 'c1', 'trace_event_id': 'e1', 'evidence_type': 'shipment_traceability',
                    'validation_status': 'cross_checked', 'confidence_score': 0.86, 'summary': 'WMS and ERP match',
                    'source_id': 'wms_shipments', 'source_label': 'WMS Shipments', 'source_type': 'wms', 'trust_tier': 'high',
                    'validation_method': 'shipment_cross_check', 'anchor_id': 'a1', 'ledger_name': 'demo-ledger',
                    'anchor_status': 'stubbed', 'tx_ref': 'DEMO-TX-1', 'content_hash': 'sha256:demo',
                }
            ]
        if 'group by r.case_id' in sl:
            return [
                {
                    'case_id': 'c1', 'receipt_count': 1, 'average_confidence': 0.86,
                    'ledger_proof_count': 1, 'source_count': 1, 'validation_statuses': 'cross_checked',
                }
            ]
        return []

    monkeypatch.setattr(op_mod, 'db_one', fake_one)
    monkeypatch.setattr(op_mod, 'db_all', fake_all)

    app = create_app()
    client = TestClient(app)
    r = client.get('/operator/cases/c1/transparency')
    assert r.status_code == 200
    js = r.json()
    assert js['ok'] is True
    assert js['transparency']['summary']['receipt_count'] == 1
    assert js['transparency']['summary']['ledger_proof_count'] == 1
    assert 'Why this data is trustworthy' in js['transparency']['buyer_trust_panel']['headline']

    r = client.get('/operator/transparency_report?case_id=c1')
    assert r.status_code == 200
    js = r.json()
    assert js['ok'] is True
    assert 'Supply Chain Transparency Report' in js['markdown']
    assert js['rows'][0]['receipt_count'] == 1
